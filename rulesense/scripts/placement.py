"""Placement analyzer — detect when rules are better fit as hooks, skills, or subagents.

See design/placement-analyzer-v1.md for the full spec. This module implements:

- Three primitive detectors (hook, skill, subagent), each a weighted sum of signals
  defined in scripts/_data/placement_patterns.json
- Compound detection (rule's verb-chain mixes enforceability classes across conjunctions)
- Per-rule best-fit classification + confidence
- Source-file surgery (atomic deletion of promoted rules)

Contract:

    detect_placement(rule: dict) -> dict
        Returns a per-rule detection record (see design §4.1).

    analyze_corpus(rules: list[dict]) -> dict
        Runs the detector over an audit's rules, returns candidates + summary.

    write_promotions(moves: dict, project_root: Path) -> dict
        Assembles .rulesense/PROMOTIONS.md and atomically removes moved rules
        from their source files. All-or-nothing transaction; see §6.2.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import _lib

# ---------------------------------------------------------------------------
# Load patterns at module scope. Per the plugin's performance convention,
# regexes are pre-compiled once; detection runs per-rule without recompilation.
# ---------------------------------------------------------------------------

_PATTERNS = _lib.load_data("placement_patterns")
_CANDIDATE_THRESHOLD = _PATTERNS["candidate_threshold"]
_COMPOUND_THRESHOLD = _PATTERNS["compound_threshold"]


def _compile_flags(flags_str: str | None) -> int:
    if not flags_str:
        return 0
    result = 0
    if "i" in flags_str:
        result |= re.IGNORECASE
    if "m" in flags_str:
        result |= re.MULTILINE
    if "s" in flags_str:
        result |= re.DOTALL
    return result


@dataclass(frozen=True)
class _Signal:
    name: str
    weight: float
    criterion: str
    pattern: re.Pattern[str] | None = None
    factor: str | None = None
    operator: str | None = None
    threshold: float | None = None
    step_patterns: tuple[re.Pattern[str], ...] = field(default_factory=tuple)
    min_steps: int | None = None
    max_action_verbs: int | None = None


def _load_signals(primitive: str) -> list[_Signal]:
    signals: list[_Signal] = []
    for raw in _PATTERNS[primitive]["signals"]:
        criterion = raw["criterion"]
        flags = _compile_flags(raw.get("flags"))
        if criterion == "regex":
            signals.append(_Signal(
                name=raw["name"],
                weight=raw["weight"],
                criterion=criterion,
                pattern=re.compile(raw["pattern"], flags),
            ))
        elif criterion == "factor_threshold":
            signals.append(_Signal(
                name=raw["name"],
                weight=raw["weight"],
                criterion=criterion,
                factor=raw["factor"],
                operator=raw["operator"],
                threshold=raw["threshold"],
            ))
        elif criterion == "step_chain":
            signals.append(_Signal(
                name=raw["name"],
                weight=raw["weight"],
                criterion=criterion,
                step_patterns=tuple(re.compile(p, flags) for p in raw["patterns"]),
                min_steps=raw["min_steps"],
            ))
        elif criterion == "pointer_shape":
            signals.append(_Signal(
                name=raw["name"],
                weight=raw["weight"],
                criterion=criterion,
                max_action_verbs=raw["max_action_verbs"],
            ))
        else:
            raise ValueError(f"Unknown criterion type: {criterion}")
    return signals


_HOOK_SIGNALS = _load_signals("hook")
_SKILL_SIGNALS = _load_signals("skill")
_SUBAGENT_SIGNALS = _load_signals("subagent")

_SKILL_SUB_TYPE_RULES = _PATTERNS["skill"]["sub_type_rules"]
_SUBAGENT_SUB_TYPE_RULES = _PATTERNS["subagent"]["sub_type_rules"]

_COMPOUND_CONJUNCTION_PATTERN = re.compile(
    _PATTERNS["compound"]["conjunction_pattern"], re.IGNORECASE
)
_COMPOUND_COORDINATION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in _PATTERNS["compound"]["coordination_phrases_for_glue"]
]

# Lightweight verb set for pointer-shape counting. We don't need F1's full
# vocabulary here — just a sample that covers common action verbs so we can
# distinguish a pointer ("see the style guide") from a directive ("do X").
_ACTION_VERB_PATTERN = re.compile(
    r"\b(use|run|add|remove|create|update|delete|write|edit|never|always|"
    r"must|should|do\s+not|don't|follow|check|verify|ensure|prefer|avoid|"
    r"implement|refactor|rename|import|export|declare|return|throw|catch)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Signal evaluators
# ---------------------------------------------------------------------------

def _eval_regex(signal: _Signal, text: str) -> bool:
    assert signal.pattern is not None
    return bool(signal.pattern.search(text))


def _eval_factor_threshold(signal: _Signal, factors: dict) -> bool:
    factor = factors.get(signal.factor or "", {})
    val = factor.get("value")
    if val is None:
        return False
    threshold = signal.threshold
    if threshold is None:
        return False
    if signal.operator == "<":
        return val < threshold
    if signal.operator == "<=":
        return val <= threshold
    if signal.operator == ">":
        return val > threshold
    if signal.operator == ">=":
        return val >= threshold
    if signal.operator == "==":
        return val == threshold
    return False


def _eval_step_chain(signal: _Signal, text: str) -> bool:
    """Fires when any of the step-chain patterns matches. Matching requires the
    pattern itself to imply >= min_steps; the patterns in placement_patterns.json
    are already shaped to require the minimum step count via repeated segments."""
    for pattern in signal.step_patterns:
        if pattern.search(text):
            return True
    return False


def _eval_pointer_shape(signal: _Signal, text: str) -> bool:
    """A rule is 'pointer-shaped' when it has few action verbs AND a pointer-style
    phrase (handled via the reference-pointer-phrase signal already). We only fire
    pointer-shape when the action-verb count is low — this acts as a gate on top
    of the lexical reference-pointer signal."""
    verb_count = len(_ACTION_VERB_PATTERN.findall(text))
    max_verbs = signal.max_action_verbs if signal.max_action_verbs is not None else 1
    return verb_count <= max_verbs


def _eval_signal(signal: _Signal, text: str, factors: dict) -> bool:
    if signal.criterion == "regex":
        return _eval_regex(signal, text)
    if signal.criterion == "factor_threshold":
        return _eval_factor_threshold(signal, factors)
    if signal.criterion == "step_chain":
        return _eval_step_chain(signal, text)
    if signal.criterion == "pointer_shape":
        return _eval_pointer_shape(signal, text)
    return False


# ---------------------------------------------------------------------------
# Primitive detectors
# ---------------------------------------------------------------------------

def _score_primitive(signals: list[_Signal], text: str, factors: dict) -> tuple[float, list[str]]:
    """Evaluate all signals for a primitive; return (confidence, evidence)."""
    total = 0.0
    evidence: list[str] = []
    for signal in signals:
        if _eval_signal(signal, text, factors):
            total += signal.weight
            evidence.append(signal.name)
    # Cap at 1.0 — multiple strong signals shouldn't push past certainty.
    return (min(total, 1.0), evidence)


def _skill_sub_type(evidence: list[str]) -> str | None:
    """Classify skill detection into 'reference' or 'action' based on which
    signal group dominated. If both fire, pick the group with more evidence."""
    return _pick_sub_type(evidence, _SKILL_SUB_TYPE_RULES)


def _subagent_sub_type(evidence: list[str]) -> str | None:
    return _pick_sub_type(evidence, _SUBAGENT_SUB_TYPE_RULES)


def _pick_sub_type(evidence: list[str], rules: list[dict]) -> str | None:
    """Generic sub-type picker. A rule with requires_all_groups needs at least
    one signal from each group; requires_any needs one from any listed signal."""
    evidence_set = set(evidence)
    # Check requires_all_groups first (more specific — e.g. subagent 'investigation').
    for rule in rules:
        if "requires_all_groups" in rule:
            groups = rule["requires_all_groups"]
            if all(any(s in evidence_set for s in group) for group in groups):
                return rule["name"]
    # Then requires_any with exclusions.
    best: tuple[str, int] | None = None  # (name, match_count)
    for rule in rules:
        if "requires_any" not in rule:
            continue
        any_hits = [s for s in rule["requires_any"] if s in evidence_set]
        if not any_hits:
            continue
        excluded = rule.get("exclude", [])
        if any(s in evidence_set for s in excluded):
            continue
        if best is None or len(any_hits) > best[1]:
            best = (rule["name"], len(any_hits))
    return best[0] if best else None


def _hook_sub_type(text: str, confidence: float, evidence: list[str]) -> str | None:
    """Hook sub-types aren't rule-driven in placement_patterns.json — we derive
    them from the signal pattern: strong deterministic gates vs lifecycle hooks."""
    if "lifecycle-trigger-keyword" in evidence:
        return "lifecycle-event"
    if confidence >= 0.70 and ("mechanical-verb" in evidence or "tool-invocation-match" in evidence):
        return "deterministic-gate"
    if confidence >= _CANDIDATE_THRESHOLD:
        return "deterministic-gate"  # default for hook candidates
    return None


# ---------------------------------------------------------------------------
# Compound detection
# ---------------------------------------------------------------------------

def _has_conjunction(text: str) -> bool:
    return bool(_COMPOUND_CONJUNCTION_PATTERN.search(text))


def _implies_coordination(text: str) -> bool:
    """Per §12.4 of the design spec: glue-skill suggestion is emitted only when
    the compound rule's parts imply temporal coordination."""
    return any(p.search(text) for p in _COMPOUND_COORDINATION_PATTERNS)


# ---------------------------------------------------------------------------
# Top-level detection
# ---------------------------------------------------------------------------

def detect_placement(rule: dict) -> dict:
    """Return the placement detection record for a single rule.

    Input: a rule dict from the audit corpus with at least 'text' and 'factors'
    (factors may be {} for partially-scored fixtures).
    Output: see design §4.1.

    Two thresholds govern the classification:
      - candidate_threshold (0.60) — a primitive becomes a sole candidate when
        its confidence crosses this bar
      - compound_threshold (0.35) — a primitive contributes to compound detection
        when its confidence crosses this (lower) bar AND another primitive also does

    This split lets a compound rule be detected when one half is a clear primitive
    and the other half has weaker but still meaningful signals — exactly the case
    we care about per §3.4 of the design spec.
    """
    text = rule.get("text", "") or ""
    factors = rule.get("factors") or {}

    # Score all three primitives (even below candidate threshold) so compound
    # detection can see partial signals on either side of a conjunction.
    hook_conf, hook_evidence = _score_primitive(_HOOK_SIGNALS, text, factors)
    skill_conf, skill_evidence = _score_primitive(_SKILL_SIGNALS, text, factors)
    sub_conf, sub_evidence = _score_primitive(_SUBAGENT_SIGNALS, text, factors)

    all_scores = [
        ("hook", hook_conf, hook_evidence, lambda: _hook_sub_type(text, hook_conf, hook_evidence)),
        ("skill", skill_conf, skill_evidence, lambda: _skill_sub_type(skill_evidence)),
        ("subagent", sub_conf, sub_evidence, lambda: _subagent_sub_type(sub_evidence)),
    ]

    # Detections list — primitives above the candidate threshold.
    detections: list[dict] = []
    for primitive, conf, evidence, sub_type_fn in all_scores:
        if conf >= _CANDIDATE_THRESHOLD:
            detections.append({
                "primitive": primitive,
                "confidence": round(conf, 3),
                "evidence": evidence,
                "sub_type": sub_type_fn(),
            })

    # Compound: 2+ primitives above compound_threshold (lower bar than candidate)
    # AND conjunction present in the rule text. This catches compound rules where
    # one half is a clear primitive and the other is a weaker but real signal.
    above_compound_bar = [
        (primitive, conf) for primitive, conf, _, _ in all_scores
        if conf >= _COMPOUND_THRESHOLD
    ]
    is_compound = len(above_compound_bar) >= 2 and _has_conjunction(text)
    needs_glue = is_compound and _implies_coordination(text)

    # best_fit: "compound" if compound, else highest-confidence candidate, else None.
    if is_compound:
        best_fit: str | None = "compound"
    elif detections:
        best_fit = max(detections, key=lambda d: d["confidence"])["primitive"]
    else:
        best_fit = None

    return {
        "rule_id": rule.get("id"),
        "rule_text": text,
        "file": rule.get("file", ""),
        "line_start": rule.get("line_start"),
        "line_end": rule.get("line_end"),
        "detections": detections,
        # Full per-primitive confidence breakdown — useful for compound rules
        # where downstream (the SKILL) needs to know the secondary primitive
        # even when it didn't cross the candidate threshold on its own.
        "scores": {
            "hook": round(hook_conf, 3),
            "skill": round(skill_conf, 3),
            "subagent": round(sub_conf, 3),
        },
        "compound": is_compound,
        "compound_needs_glue": needs_glue,
        "best_fit": best_fit,
    }


def analyze_corpus(audit: dict) -> dict:
    """Run detection over every rule in an audit and return the candidates report.

    Input: audit.json dict (as produced by compose.py).
    Output: see design §4.1 — a dict with 'candidates' list + 'summary' counts.
    Only rules with at least one detection make it into 'candidates'.
    """
    rules = audit.get("rules", [])
    candidates = [detect_placement(r) for r in rules]
    candidates = [c for c in candidates if c["detections"]]

    summary = {
        "total_candidates": len(candidates),
        "hook_candidates": sum(1 for c in candidates if c["best_fit"] == "hook"),
        "skill_candidates": sum(1 for c in candidates if c["best_fit"] == "skill"),
        "subagent_candidates": sum(1 for c in candidates if c["best_fit"] == "subagent"),
        "compound_candidates": sum(1 for c in candidates if c["best_fit"] == "compound"),
    }

    return {
        "schema_version": "0.1",
        "project": audit.get("project", ""),
        "audit_grade": _format_grade(audit),
        "candidates": candidates,
        "summary": summary,
    }


def _format_grade(audit: dict) -> str:
    """Format the audit grade as 'Letter (score)' for the placement report banner."""
    ecq = audit.get("effective_corpus_quality", {})
    score = ecq.get("score")
    if score is None:
        return "unknown"
    # Reuse the same letter-grade bands as report.py.
    if score >= 0.80:
        letter = "A"
    elif score >= 0.65:
        letter = "B"
    elif score >= 0.50:
        letter = "C"
    elif score >= 0.35:
        letter = "D"
    else:
        letter = "F"
    return f"{letter} ({score:.3f})"


# ---------------------------------------------------------------------------
# Source-file surgery (used by run_audit.py --write-promotions).
# Atomic delete: read each source, compute new content, validate against
# rule_text, only write when every file's new content is computed.
# ---------------------------------------------------------------------------

class SourceDriftError(Exception):
    """Raised when a source file's content at the target line range does not
    match the rule_text recorded at audit time."""


def plan_deletions(moves: list[dict], project_root: Path) -> dict[Path, str]:
    """For each move, compute the new content of its source file with the rule
    bullet (and any continuation lines) removed. Returns a map of absolute path
    -> new content. Raises SourceDriftError if any file's content drifted.

    A `move` is a dict with at minimum: file, line_start, line_end, rule_text.
    """
    # Group moves by absolute file path. A single file may have multiple moves.
    by_file: dict[Path, list[dict]] = {}
    for m in moves:
        path = (project_root / m["file"]).resolve()
        by_file.setdefault(path, []).append(m)

    new_contents: dict[Path, str] = {}
    for path, file_moves in by_file.items():
        new_contents[path] = _delete_ranges_from_file(path, file_moves)
    return new_contents


def _delete_ranges_from_file(path: Path, moves: list[dict]) -> str:
    """Read path, delete the line ranges named by moves, return new content.

    Drift check: each move's `rule_text` (after whitespace collapse) must appear
    within its line range. If not, raise SourceDriftError."""
    if not path.exists():
        raise SourceDriftError(f"Source file not found: {path}")

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    # Validate each move's rule_text against the current content before mutating.
    for m in moves:
        line_start = m["line_start"]
        line_end = m["line_end"]
        if line_start is None or line_end is None:
            raise SourceDriftError(f"Move for {path} has null line_start/line_end")
        if line_start < 1 or line_end > len(lines):
            raise SourceDriftError(
                f"Move for {path} out of bounds: lines {line_start}..{line_end} (file has {len(lines)} lines)"
            )
        span = "".join(lines[line_start - 1:line_end])
        if not _rule_text_matches(m.get("rule_text", ""), span):
            raise SourceDriftError(
                f"Source file drift at {path}:{line_start}..{line_end}. "
                f"Expected rule text does not match current content. Re-audit."
            )

    # Sort moves by descending line_start so deletions don't shift later ranges.
    sorted_moves = sorted(moves, key=lambda m: m["line_start"], reverse=True)
    for m in sorted_moves:
        start_idx = m["line_start"] - 1
        end_idx = m["line_end"]
        lines = _delete_with_blank_line_cleanup(lines, start_idx, end_idx)

    return "".join(lines)


def _rule_text_matches(expected: str, span: str) -> bool:
    """Drift check: does the expected rule_text match the content in span?

    Whitespace-tolerant (markdown list markers, indentation, line wraps all
    normalize). We collapse whitespace and bullet markers before comparison."""
    def normalize(s: str) -> str:
        # Remove leading bullet markers and indentation.
        s = re.sub(r"^\s*[-*+]\s+", "", s, flags=re.MULTILINE)
        s = re.sub(r"^\s*\d+\.\s+", "", s, flags=re.MULTILINE)
        # Collapse all whitespace (including newlines) to single spaces.
        s = re.sub(r"\s+", " ", s).strip()
        return s

    return normalize(expected) in normalize(span) or normalize(span) in normalize(expected)


def _delete_with_blank_line_cleanup(lines: list[str], start_idx: int, end_idx: int) -> list[str]:
    """Delete lines[start_idx:end_idx] and remove stacked blank lines at the seam.

    A "stacked blank line" is when the deletion seam now has two blank lines in
    a row where there was content in between. We collapse to one blank line."""
    before = lines[:start_idx]
    after = lines[end_idx:]

    def _is_blank(line: str) -> bool:
        return line.strip() == ""

    # If the last line of 'before' is blank AND the first line of 'after' is blank,
    # drop one of them.
    if before and after and _is_blank(before[-1]) and _is_blank(after[0]):
        after = after[1:]

    return before + after


# ---------------------------------------------------------------------------
# PROMOTIONS.md assembly
# ---------------------------------------------------------------------------

_PRIMITIVE_DEFINITIONS = {
    "hook": (
        "Hooks are shell commands, HTTP endpoints, or prompts that fire "
        "automatically at Claude Code lifecycle events (`PreToolUse`, "
        "`PostToolUse`, `UserPromptSubmit`, `Stop`, and others). They run "
        "outside the model's context, cannot be rationalized around, and can "
        "short-circuit the agent loop. Use hooks for deterministic gates you "
        "want mechanically unavoidable."
    ),
    "skill": (
        "Skills are reusable instructions Claude loads on demand. "
        "**Reference skills** hold knowledge Claude consults during a task "
        "(API style guides, vocabulary). **Action skills** run a workflow "
        "you invoke with `/<name>` (e.g. `/deploy`). They don't burn context "
        "when irrelevant."
    ),
    "subagent": (
        "Subagents are isolated workers that run with their own context and "
        "return only a summary. Use them for tasks that read many files, "
        "involve noisy intermediate work, or benefit from bias independence "
        "(a fresh context unmotivated by the caller's assumptions)."
    ),
    "compound": (
        "A compound candidate is a rule whose verb chain mixes enforceability "
        "classes — one half is a deterministic gate (→ hook), the other is a "
        "judgment call (→ subagent), and a small skill may act as connective "
        "tissue that invokes both at the right moment. The mapping principle: "
        "**hooks** for deterministic gates you want mechanically unavoidable, "
        "**skills** for context-triggered procedural guidance the main agent "
        "follows, **subagents** for delimited tasks needing isolated reasoning "
        "or bias independence. If you find yourself encoding a judgment call "
        "in a hook or a mechanical check in a skill, you've misallocated."
    ),
}

_PRIMITIVE_DOCS_LINKS = {
    "hook": [
        ("Hooks overview", "https://code.claude.com/docs/en/features-overview#hooks"),
        ("Hooks in the agent loop", "https://code.claude.com/docs/en/agent-sdk/agent-loop#hooks"),
        ("Hooks reference", "https://code.claude.com/docs/en/hooks#hooks-reference"),
    ],
    "skill": [
        ("Skills overview", "https://code.claude.com/docs/en/features-overview#skills"),
        ("Skills in Claude Code", "https://code.claude.com/docs/en/agent-sdk/claude-code-features#skills"),
        ("Skills reference", "https://code.claude.com/docs/en/plugins-reference#skills"),
    ],
    "subagent": [
        ("Subagents overview", "https://code.claude.com/docs/en/features-overview#subagents"),
        ("Create custom subagents", "https://code.claude.com/docs/en/sub-agents#create-custom-subagents"),
        ("Use subagents for investigation", "https://code.claude.com/docs/en/best-practices#use-subagents-for-investigation"),
    ],
    "compound": [
        ("Claude Code features overview", "https://code.claude.com/docs/en/features-overview"),
    ],
}

_PRIMITIVE_HEADINGS = {
    "hook": "Hooks",
    "skill": "Skills",
    "subagent": "Subagents",
    "compound": "Compound candidates (rules that split across primitives)",
}

_PRIMITIVE_ORDER = ["hook", "skill", "subagent", "compound"]


def assemble_promotions_doc(moves_by_primitive: dict[str, list[dict]], project: str,
                             audit_grade: str, generated_at: str,
                             existing_content: str | None = None) -> str:
    """Render the full PROMOTIONS.md content. If existing_content is provided,
    the new entries are appended under each primitive heading; entries already
    present (matched by rule_id + file + text) are skipped (dedupe)."""
    # Dedupe against existing content's entries if present.
    existing_keys = _extract_existing_entry_keys(existing_content) if existing_content else set()

    lines: list[str] = []
    if existing_content is None:
        lines.append(_render_banner(project, audit_grade, generated_at))
    else:
        # Preserve the existing content verbatim; we append a new dated block.
        lines.append(existing_content.rstrip())
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## Appended {generated_at}")
        lines.append("")
        lines.append(f"> Audit grade at append time: `{audit_grade}`")
        lines.append("")

    for primitive in _PRIMITIVE_ORDER:
        entries = moves_by_primitive.get(primitive, [])
        new_entries = [e for e in entries if _entry_key(e) not in existing_keys]
        if not new_entries:
            continue
        lines.append("---")
        lines.append("")
        lines.append(f"## {_PRIMITIVE_HEADINGS[primitive]}")
        lines.append("")
        lines.append(_PRIMITIVE_DEFINITIONS[primitive])
        lines.append("")
        lines.append("**Learn more:**")
        for label, url in _PRIMITIVE_DOCS_LINKS[primitive]:
            lines.append(f"- [{label}]({url})")
        lines.append("")
        lines.append("**Candidates from your rules:**")
        lines.append("")
        for entry in new_entries:
            lines.extend(_render_entry(entry, primitive))
            lines.append("")

    return "\n".join(lines) + "\n"


def _render_banner(project: str, audit_grade: str, generated_at: str) -> str:
    return (
        "# Rulesense promotion candidates\n"
        "\n"
        "> ⚠️ **These items are documented, not enforced.** They were flagged "
        "as better-fit for a Claude Code primitive other than a rule. Rulesense "
        "does not re-read this file on subsequent audits — nothing here affects "
        "your grade. Promote each item to the recommended primitive when you "
        "have time, and delete it from this file when you do.\n"
        ">\n"
        f"> **Generated:** {generated_at} · **Project:** {project} · "
        f"**From audit:** `{audit_grade}`\n"
    )


def _render_entry(entry: dict, primitive: str) -> list[str]:
    """Render a single entry. Compound entries have a different shape (part_a/part_b).

    Layout (Dallas-Digital dogfood feedback, 2026-04-18):

        ### `file:line`

        > full rule text — no truncation, bullet markers stripped

        - **Why a hook**: ...
        - **Suggested shape**: ...

    The header is just the source location; the full rule text lives in a
    blockquote below so long rules wrap naturally without dominating a ToC.
    Truncation is wrong here: once a rule moves to PROMOTIONS.md it is
    deleted from source, so the doc IS the canonical copy.
    """
    location = f"`{entry['file']}:{entry['line_start']}`"
    lines = [f"### {location}"]
    rule_text = _strip_bullet_marker((entry.get("rule_text") or "").rstrip())
    if rule_text:
        lines.append("")
        lines.append(f"> {rule_text}")
    lines.append("")
    if primitive == "compound":
        compound = entry.get("compound", {}) or {}
        split_hint = compound.get("split_hint", "")
        if split_hint:
            lines.append(f"- **Why split**: {split_hint}")
        for part_key in ("part_a", "part_b"):
            part = compound.get(part_key, {}) or {}
            if not part:
                continue
            lines.extend(_render_part(part, part_key.replace("_", " ").title()))
        glue = compound.get("glue")
        if glue:
            lines.extend(_render_part(glue, "Optional glue"))
    else:
        judgment = entry.get("judgment", {}) or {}
        if judgment.get("why"):
            lines.append(f"- **Why a {primitive}**: {judgment['why']}")
        if judgment.get("suggested_shape"):
            lines.append(f"- **Suggested shape**: {judgment['suggested_shape']}")
        if judgment.get("next_step"):
            lines.append(f"- **Next step**: {judgment['next_step']}")
        if judgment.get("tradeoff"):
            lines.append(f"- **Trade-off**: {judgment['tradeoff']}")
    return lines


_BULLET_MARKER_PATTERN = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")


def _strip_bullet_marker(text: str) -> str:
    """Strip a leading markdown list marker (`- `, `* `, `+ `, `1. `, etc.).

    Rule text comes straight from the source file where rules live as bullets.
    When rendered into a PROMOTIONS.md blockquote, the leading `- ` would
    become a nested list item inside the quote, which reads poorly. Stripping
    leaves just the directive text.
    """
    return _BULLET_MARKER_PATTERN.sub("", text, count=1)


def _render_part(part: dict, label: str) -> list[str]:
    primitive = part.get("primitive", "").title()
    text = part.get("text", "")
    shape = part.get("suggested_shape", "")
    next_step = part.get("next_step", "")
    tradeoff = part.get("tradeoff")
    out = [f"- **{label}** → **{primitive}**: \"{text}\""]
    if shape:
        out.append(f"  - **Suggested shape**: {shape}")
    if next_step:
        out.append(f"  - **Next step**: {next_step}")
    if tradeoff:
        out.append(f"  - **Trade-off**: {tradeoff}")
    return out


def _entry_key(entry: dict) -> tuple:
    """Dedupe key: file + first 60 chars of normalized text.

    Rule IDs churn across re-audits (R5 may become R3 after a rewrite removes
    earlier rules), so they are NOT part of the key. What stays stable across
    audits is the rule's source location (file) and its text content. Two
    entries pointing at the same file + same text are the same candidate.

    The text prefix is normalized by stripping any leading list marker so the
    key matches on directive content regardless of whether the source was a
    bullet or a paragraph."""
    return (
        entry.get("file"),
        _strip_bullet_marker(entry.get("rule_text") or "")[:60],
    )


# Two header shapes coexist in PROMOTIONS.md: the current shape (file:line on
# its own line, rule text in a blockquote below) and a legacy shape (file:line
# with the rule text quoted on the same line after an em-dash). The legacy
# parser lets existing promotion docs from earlier runs still dedupe cleanly.
_ENTRY_HEADER_NEW_PATTERN = re.compile(r"^###\s+`([^`]+):(\d+)`\s*$")
_ENTRY_HEADER_LEGACY_PATTERN = re.compile(r"^###\s+`([^`]+):(\d+)`\s+—\s+\"(.+)\"\s*$")
_BLOCKQUOTE_LINE_PATTERN = re.compile(r"^>\s+(.+)$")


def _extract_existing_entry_keys(content: str) -> set[tuple]:
    """Scan existing PROMOTIONS.md content and return the set of dedupe keys
    (file + text-prefix) already recorded. Rule IDs aren't in the key (see
    `_entry_key` docstring for rationale).

    Handles both the current entry shape (`### file:line` + `> text` blockquote
    on a following line) and the legacy shape (`### file:line — "text"`)."""
    keys: set[tuple] = set()
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        legacy = _ENTRY_HEADER_LEGACY_PATTERN.match(line)
        if legacy:
            file_path, _, text = legacy.groups()
            keys.add((file_path, _strip_bullet_marker(text)[:60]))
            i += 1
            continue
        new_header = _ENTRY_HEADER_NEW_PATTERN.match(line)
        if new_header:
            file_path, _ = new_header.groups()
            # Look ahead up to 3 lines for the blockquote containing rule text.
            rule_text = ""
            for j in range(i + 1, min(i + 4, len(lines))):
                bq = _BLOCKQUOTE_LINE_PATTERN.match(lines[j])
                if bq:
                    rule_text = bq.group(1)
                    break
            keys.add((file_path, _strip_bullet_marker(rule_text)[:60]))
            i += 1
            continue
        i += 1
    return keys


# ---------------------------------------------------------------------------
# write_promotions orchestration (atomic)
# ---------------------------------------------------------------------------

def _collect_judgment_warnings(moves: list[dict]) -> list[str]:
    """Flag moves that will render as header-only entries because their
    `judgment` payload is empty or missing required fields.

    Dallas-Digital dogfood (2026-04-18) produced a PROMOTIONS.md with two
    entries that had only the file:line header — no 'why', no 'suggested
    shape', no 'next step'. The render code correctly omitted missing fields,
    but the resulting doc was useless for the user. Surfacing a warning in
    the output JSON makes this silent failure mode loud.
    """
    warnings: list[str] = []
    required_fields = ("why", "suggested_shape", "next_step")
    for move in moves:
        rule_id = move.get("rule_id", "<unknown>")
        primitive = move.get("primitive", "")
        if primitive == "compound":
            compound = move.get("compound") or {}
            if not compound.get("part_a") or not compound.get("part_b"):
                warnings.append(
                    f"{rule_id}: compound move is missing part_a or part_b; "
                    "PROMOTIONS.md entry will be header-only"
                )
            continue
        judgment = move.get("judgment") or {}
        missing = [f for f in required_fields if not judgment.get(f)]
        if missing:
            warnings.append(
                f"{rule_id}: move has no {'/'.join(missing)} in judgment; "
                "PROMOTIONS.md entry will be header-only. Generate the judgment "
                "strings per skills/audit/references/promotion-guide.md before "
                "writing."
            )
    return warnings


def write_promotions(payload: dict, project_root: Path) -> dict:
    """Execute the full write-promotions transaction per design §6.2.

    1. Compute new content of .rulesense/PROMOTIONS.md (append or create)
    2. Compute new content of each source file with moved rules removed
    3. Write everything atomically (temp files + rename); fail with no writes
       if any step errors.
    """
    moves = payload.get("moves", [])
    if not moves:
        return {
            "schema_version": "0.1",
            "promotions_file": ".rulesense/PROMOTIONS.md",
            "entries_written": 0,
            "files_modified": [],
            "rules_removed": 0,
            "status": "ok",
        }

    judgment_warnings = _collect_judgment_warnings(moves)

    project = payload.get("project", "")
    audit_grade = payload.get("audit_grade", "unknown")
    generated_at = payload.get("generated_at") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Step 1: group moves by primitive for the doc.
    moves_by_primitive: dict[str, list[dict]] = {}
    for m in moves:
        primitive = m.get("primitive", "hook")
        moves_by_primitive.setdefault(primitive, []).append(m)

    # Step 2: compute source-file deletions (raises on drift; nothing written yet).
    try:
        new_source_contents = plan_deletions(moves, project_root)
    except SourceDriftError as e:
        return {
            "schema_version": "0.1",
            "status": "failed",
            "reason": f"source_file_drift: {e}",
            "promotions_file": ".rulesense/PROMOTIONS.md",
            "entries_written": 0,
            "files_modified": [],
            "rules_removed": 0,
        }

    # Step 3: read existing PROMOTIONS.md (if any), assemble new content.
    promotions_path = project_root / ".rulesense" / "PROMOTIONS.md"
    existing_content: str | None = None
    if promotions_path.exists():
        with open(promotions_path, encoding="utf-8") as f:
            existing_content = f.read()
    new_doc = assemble_promotions_doc(
        moves_by_primitive, project, audit_grade, generated_at, existing_content
    )

    # Step 4: write everything atomically. If a write fails mid-way, the rename
    # is the atomic point — sibling temp files are safe to leave behind on failure.
    written: list[str] = []
    try:
        # PROMOTIONS.md first (creates .rulesense/ if needed).
        promotions_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(promotions_path, new_doc)
        written.append(".rulesense/PROMOTIONS.md")

        for path, content in new_source_contents.items():
            _atomic_write(path, content)
            rel = path.relative_to(project_root) if path.is_relative_to(project_root) else path
            written.append(str(rel).replace("\\", "/"))
    except OSError as e:
        return {
            "schema_version": "0.1",
            "status": "failed",
            "reason": f"write_error: {e}",
            "promotions_file": ".rulesense/PROMOTIONS.md",
            "entries_written": 0,
            "files_modified": written,
            "rules_removed": 0,
        }

    # Surface judgment-field warnings (emit to stderr for visibility AND include
    # in the output JSON so the SKILL layer can detect and react programmatically).
    for w in judgment_warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    result: dict = {
        "schema_version": "0.1",
        "promotions_file": ".rulesense/PROMOTIONS.md",
        "entries_written": len(moves),
        "files_modified": [p for p in written if p != ".rulesense/PROMOTIONS.md"],
        "rules_removed": len(moves),
        "status": "ok",
    }
    if judgment_warnings:
        result["warnings"] = judgment_warnings
    return result


def _atomic_write(path: Path, content: str) -> None:
    """Write content to path via a sibling temp file + os.replace (atomic)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # NamedTemporaryFile with delete=False so we control the rename.
    fd, tmp_path = tempfile.mkstemp(
        prefix=path.name + ".rulesense-tmp-",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        # Clean up temp file on failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# CLI entry point — used when run_audit.py shells out to this module for
# --prepare-placement and --write-promotions modes.
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("usage: placement.py [--prepare-placement <audit.json> | --write-promotions <project_root>]", file=sys.stderr)
        sys.exit(2)

    mode = sys.argv[1]

    if mode == "--prepare-placement":
        if len(sys.argv) < 3:
            print("usage: placement.py --prepare-placement <audit.json>", file=sys.stderr)
            sys.exit(2)
        audit_path = sys.argv[2]
        with open(audit_path, encoding="utf-8") as f:
            audit = json.load(f)
        result = analyze_corpus(audit)
        _lib.write_json_stdout(result)
    elif mode == "--write-promotions":
        if len(sys.argv) < 3:
            print("usage: placement.py --write-promotions <project_root>", file=sys.stderr)
            sys.exit(2)
        project_root = Path(sys.argv[2]).resolve()
        payload = _lib.read_json_stdin()
        result = write_promotions(payload, project_root)
        _lib.write_json_stdout(result)
        if result["status"] != "ok":
            sys.exit(1)
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
