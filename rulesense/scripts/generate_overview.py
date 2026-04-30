"""Generate a standalone HTML overview of the rule corpus.

Reads overview_data.json (audit.json + intention/organization analysis),
fills the HTML template with data-driven fragments, writes a standalone
.html file with no external dependencies.

Usage:
    python generate_overview.py --input overview_data.json --output .rulesense-overview.html
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

# UTF-8 on Windows (same pattern as report.py / _lib.py)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

TEMPLATE_DIR = Path(__file__).parent / "assets"

# ---------------------------------------------------------------------------
# Grade thresholds — duplicated from report.py for minimal coupling.
# Future cleanup candidate: move to _lib.py.
# ---------------------------------------------------------------------------

_LETTER_GRADES = [(0.80, "A"), (0.65, "B"), (0.50, "C"), (0.35, "D")]

_GRADE_COLORS = {
    "A": "var(--grade-a)",
    "B": "var(--grade-b)",
    "C": "var(--grade-c)",
    "D": "var(--grade-d)",
    "F": "var(--grade-f)",
}

_FRIENDLY_PROBLEMS = {
    "F1": "Weak verb — Claude isn't sure if this is a command or a suggestion",
    "F2": "Phrased as a prohibition — positive instructions stick better",
    "F3": "Unclear when this applies — Claude won't remember it at the right moment",
    "F4": "Loaded in the wrong context — Claude won't see this rule when it matters",
    "F7": "Too vague — Claude needs specific examples to follow this",
}

_FRIENDLY_STRENGTHS = {
    "F1": "Strong action verb",
    "F2": "Clear positive framing",
    "F3": "Specific trigger context",
    "F4": "Well-scoped to the right files",
    "F7": "Concrete examples or file paths",
}


def _letter_grade(score: float) -> str:
    """Map a 0.0-1.0 quality score to a letter grade."""
    for threshold, grade in _LETTER_GRADES:
        if score >= threshold:
            return grade
    return "F"


_VALID_GRADES = {"A", "B", "C", "D", "F"}


def _normalize_grade(grade_str: str) -> str:
    """Normalize non-standard grades to the A/B/C/D/F system.

    Strips +/- suffixes, maps E->D, defaults unknown to F.
    """
    g = grade_str.strip().upper().rstrip("+-")
    if g in _VALID_GRADES:
        return g
    if g == "E":
        return "D"
    return "F"


def _esc(text: str) -> str:
    """HTML-escape text for safe template insertion."""
    return html.escape(text, quote=True)


def _truncate(text: str, length: int = 120) -> str:
    """Truncate text and append ellipsis if needed."""
    if len(text) <= length:
        return text
    return text[:length] + "..."


def _best_strength(rule: dict) -> str:
    """Return a friendly 'why it works' string from the rule's highest factor."""
    factors = rule.get("factors", {})
    best_fn = None
    best_val = -1.0
    for fn in ("F1", "F2", "F3", "F4", "F7"):
        fdata = factors.get(fn, {})
        val = fdata.get("value")
        if val is not None and val > best_val:
            best_val = val
            best_fn = fn
    if best_fn:
        return _FRIENDLY_STRENGTHS.get(best_fn, "Well-structured rule")
    return "Well-structured rule"


# ---------------------------------------------------------------------------
# HTML fragment builders
# ---------------------------------------------------------------------------

def _build_grade_distribution(audit: dict) -> str:
    """Colored horizontal bar showing A/B/C/D/F counts."""
    rules = audit.get("rules", [])
    mandate = [r for r in rules if r.get("category") == "mandate"]

    counts: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for r in mandate:
        grade = _letter_grade(r.get("score", 0))
        counts[grade] += 1

    total = sum(counts.values())
    if total == 0:
        return '<p class="empty-state">No rules to chart.</p>'

    segments = []
    for grade in ("A", "B", "C", "D", "F"):
        count = counts[grade]
        if count == 0:
            continue
        pct = (count / total) * 100
        css_class = f"grade-{grade.lower()}"
        # Hide label if segment is too narrow
        size_class = " too-small" if pct < 8 else ""
        label = f"{grade} ({count})" if pct >= 8 else ""
        segments.append(
            f'<div class="grade-bar-segment {css_class}{size_class}" '
            f'style="width:{pct:.1f}%;background:{_GRADE_COLORS[grade]}" '
            f'title="{grade}: {count} rule{"s" if count != 1 else ""}">{label}</div>'
        )

    return f'<div class="grade-bar">{"".join(segments)}</div>'


def _build_intentions_table(intentions: list[dict]) -> str:
    """Table of intention themes with counts and avg grade badges."""
    if not intentions:
        return '<p class="empty-state">No intention data available.</p>'

    rows = []
    for item in intentions:
        theme = _esc(item.get("theme", "Unknown"))
        count = item.get("count", 0)
        avg_grade = _normalize_grade(item.get("avg_grade", "F"))
        grade_class = f"grade-{avg_grade.lower()}"
        badge = (
            f'<span class="grade-sm {grade_class}" '
            f'style="background:{_GRADE_COLORS[avg_grade]}">'
            f'{avg_grade}</span>'
        )
        rows.append(f"<tr><td>{theme}</td><td>{count}</td><td>{badge}</td></tr>")

    return (
        '<div class="table-wrap"><table>'
        "<thead><tr><th>Theme</th><th>Rules</th><th>Avg Grade</th></tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table></div>"
    )


def _build_gaps_section(gaps: list[str]) -> str:
    """Bullet list of coverage gaps."""
    if not gaps:
        return '<p class="empty-state">No coverage gaps identified.</p>'

    items = "".join(f"<li>{_esc(g)}</li>" for g in gaps)
    return f'<ul class="gaps-list">{items}</ul>'


def _build_org_section(org: dict) -> str:
    """Two stat cards: CLAUDE.md vs .claude/rules/ organization."""
    claude_md = org.get("claude_md_rules", 0)
    scoped = org.get("scoped_rules", 0)
    always_in_dir = org.get("always_loaded_rules_in_rules_dir", 0)
    claude_md_lines = org.get("claude_md_lines", 0)

    return (
        '<div class="card-row">'
        '<div class="stat-card">'
        "<h3>CLAUDE.md</h3>"
        f'<div class="stat-row"><span class="stat-label">Rules</span>'
        f'<span class="stat-value">{claude_md}</span></div>'
        f'<div class="stat-row"><span class="stat-label">Lines</span>'
        f'<span class="stat-value">{claude_md_lines}</span></div>'
        "</div>"
        '<div class="stat-card">'
        "<h3>.claude/rules/</h3>"
        f'<div class="stat-row"><span class="stat-label">Glob-scoped rules</span>'
        f'<span class="stat-value">{scoped}</span></div>'
        f'<div class="stat-row"><span class="stat-label">Always-loaded rules</span>'
        f'<span class="stat-value">{always_in_dir}</span></div>'
        "</div>"
        "</div>"
    )


def _build_files_table(audit: dict) -> str:
    """Per-file table sorted by file_score ascending (weakest first)."""
    files = audit.get("files", [])
    if not files:
        return '<p class="empty-state">No files found.</p>'

    sorted_files = sorted(files, key=lambda f: f.get("file_score", 0))

    rows = []
    for f in sorted_files:
        path = _esc(f.get("path", "?"))
        count = f.get("rule_count", 0)
        score = f.get("file_score", 0)
        grade = _letter_grade(score)
        grade_class = f"grade-{grade.lower()}"
        badge = (
            f'<span class="grade-sm {grade_class}" '
            f'style="background:{_GRADE_COLORS[grade]}">{grade}</span>'
        )
        rows.append(
            f"<tr><td>{path}</td><td>{count}</td>"
            f"<td>{score:.2f}</td><td>{badge}</td></tr>"
        )

    return (
        '<div class="table-wrap"><table>'
        "<thead><tr><th>File</th><th>Rules</th><th>Score</th><th>Grade</th></tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table></div>"
    )


def _build_best_rules(audit: dict) -> str:
    """Top 5 rules (from positive_findings) with 'why it works'."""
    positives = audit.get("positive_findings", [])
    all_rules = audit.get("rules", [])

    if not positives:
        return '<p class="empty-state">No A-grade rules found.</p>'

    cards = []
    for p in positives[:5]:
        text = _esc(_truncate(p.get("text", ""), 120))
        score = p.get("score", 0)
        grade = _letter_grade(score)
        grade_class = f"grade-{grade.lower()}"

        # Find matching full rule for strength analysis
        full_rule = next(
            (r for r in all_rules
             if r.get("text", "").startswith(p.get("text", "")[:30])),
            None,
        )
        why = _best_strength(full_rule) if full_rule else "Well-structured rule"

        cards.append(
            f'<div class="rule-card">'
            f'<div class="rule-card-header">'
            f'<span class="grade-sm {grade_class}" '
            f'style="background:{_GRADE_COLORS[grade]}">{grade}</span>'
            f'<span class="rule-card-score">{score:.2f}</span>'
            f"</div>"
            f'<div class="rule-text">{text}</div>'
            f'<div class="rule-note">{_esc(why)}</div>'
            f"</div>"
        )

    return "".join(cards)


def _build_worst_rules(audit: dict) -> str:
    """Bottom 5 mandate rules with friendly problem descriptions."""
    rules = audit.get("rules", [])
    mandate = [r for r in rules if r.get("category") == "mandate"]
    weakest = sorted(mandate, key=lambda r: r.get("score", 0))[:5]

    if not weakest:
        return '<p class="empty-state">No rules to show.</p>'

    cards = []
    for r in weakest:
        text = _esc(_truncate(r.get("text", ""), 120))
        score = r.get("score", 0)
        grade = _letter_grade(score)
        grade_class = f"grade-{grade.lower()}"
        dw = r.get("dominant_weakness", "")
        problem = _FRIENDLY_PROBLEMS.get(dw, "Review this rule for clarity")

        cards.append(
            f'<div class="rule-card">'
            f'<div class="rule-card-header">'
            f'<span class="grade-sm {grade_class}" '
            f'style="background:{_GRADE_COLORS[grade]}">{grade}</span>'
            f'<span class="rule-card-score">{score:.2f}</span>'
            f"</div>"
            f'<div class="rule-text">{text}</div>'
            f'<div class="rule-note">{_esc(problem)}</div>'
            f"</div>"
        )

    return "".join(cards)


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------

def generate(data: dict, output_path: str) -> None:
    """Read the HTML template, fill placeholders, write the output file."""
    template = (TEMPLATE_DIR / "template.html").read_text(encoding="utf-8")

    audit = data.get("audit", {})
    intentions = data.get("intentions", [])
    gaps = data.get("coverage_gaps", [])
    org = data.get("organization", {})
    timestamp = data.get("generated_at", "unknown")

    # Corpus-level metrics
    ecq = audit.get("effective_corpus_quality", {})
    ecq_score = ecq.get("score", 0)
    grade = _letter_grade(ecq_score)

    mandate_rules = [r for r in audit.get("rules", []) if r.get("category") == "mandate"]
    rule_count = len(mandate_rules)
    good_count = sum(1 for r in mandate_rules if r.get("score", 0) >= 0.65)

    # Replace all tokens
    replacements = {
        "__GRADE__": grade,
        "__GRADE_LOWER__": grade.lower(),
        "__SCORE__": f"{ecq_score:.2f}",
        "__RULE_COUNT__": str(rule_count),
        "__GOOD_COUNT__": str(good_count),
        "__GRADE_DIST__": _build_grade_distribution(audit),
        "__INTENTIONS__": _build_intentions_table(intentions),
        "__GAPS__": _build_gaps_section(gaps),
        "__ORGANIZATION__": _build_org_section(org),
        "__FILES__": _build_files_table(audit),
        "__BEST_RULES__": _build_best_rules(audit),
        "__WORST_RULES__": _build_worst_rules(audit),
        "__TIMESTAMP__": _esc(timestamp),
    }

    result = template
    for token, value in replacements.items():
        result = result.replace(token, value)

    Path(output_path).write_text(result, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a standalone HTML overview from overview_data.json."
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to overview_data.json",
    )
    parser.add_argument(
        "--output", default=".rulesense-overview.html",
        help="Path for the output HTML file (default: .rulesense-overview.html)",
    )
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    generate(data, args.output)


if __name__ == "__main__":
    main()
