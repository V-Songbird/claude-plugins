"""Score composition: merge judgment patches, compute per-rule/file/corpus scores.

Takes two positional file args: scored_semi.json and judgment_patches.json.
Outputs audit.json to stdout.

Implements the quality model formulas from quality-model.md.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _lib

# ---------------------------------------------------------------------------
# Load configuration
# ---------------------------------------------------------------------------

_WEIGHTS = _lib.load_data("weights")
_FACTOR_WEIGHTS = _WEIGHTS["weights"]  # {"F1": 1.5, "F2": 1.0, ...}
_TOTAL_WEIGHT = _WEIGHTS["total"]      # 6.8 — F8 is a parallel signal, not in composite
_SOFT_FLOOR_THRESHOLD = _WEIGHTS["soft_floor_threshold"]  # 0.2
_SOFT_FLOOR_FACTORS = _WEIGHTS["soft_floor_factors"]  # ["F4", "F7"]
_STALENESS_MULTIPLIER = _WEIGHTS["staleness_multiplier"]  # 0.05
_CATEGORY_FLOORS = _WEIGHTS["category_floors"]
_POSITION_WEIGHTS = _WEIGHTS["position_weights"]
_LENGTH_PENALTY = _WEIGHTS["length_penalty"]
_LOAD_PROB_DEFAULTS = _WEIGHTS["load_prob_defaults"]
_PARALLEL_FACTORS = _WEIGHTS.get("parallel_factors", {})
_F8_HOOK_THRESHOLD = _PARALLEL_FACTORS.get("F8", {}).get("threshold", 0.40)

_KNOWN_FACTORS = set(_FACTOR_WEIGHTS.keys()) | set(_PARALLEL_FACTORS.keys())

# Layer overlay composition.
# Clarity layer: F1, F2, F7 (F6 is absorbed into F7; not a separate factor).
# Mechanism layer is removed — F8 is a parallel signal, not a composite factor.
_CLARITY_FACTORS = ["F1", "F2", "F7"]
_ACTIVATION_FACTORS = ["F3", "F4"]

# Failure-class mapping: which failure mode does each composite factor's
# weakness indicate? Used as a presentation-layer diagnostic — the class is
# derived from the dominant_weakness factor and reported alongside it in the
# audit output. Does not affect scoring.
#
# - drift:     rule is not in Claude's attention when it fires
#              (trigger too distant, or rule not loaded in the right context)
# - ambiguity: rule is in attention but interpretable multiple ways
#              (hedged verbs, negations, abstract nouns)
# - conflict:  rule contradicts another rule (unmeasured in the composite;
#              see report-schema.md "failure_class" notes for the corpus-level
#              conflict signal that will populate this class when available)
_FACTOR_TO_FAILURE_CLASS = {
    "F1": "ambiguity",  # verb strength — hedged verbs read as optional
    "F2": "ambiguity",  # framing polarity — prohibitions harder to execute than positives
    "F3": "drift",      # trigger-action distance — action due at a future moment
    "F4": "drift",      # load-trigger alignment — rule not loaded when it should fire
    "F7": "ambiguity",  # concreteness — abstract nouns leave interpretation open
}


def _suggest_enforcement_layer(rule: dict) -> str:
    """Suggest the enforcement mechanism based on the rule's content.

    Heuristic: look for keywords that typically indicate a specific layer.
    Returns a short phrase for the hook_opportunities report.
    """
    text = rule.get("text", "").lower()
    if any(kw in text for kw in ("commit", "push", "force-push", "pre-commit")):
        return "Git hook (pre-commit / pre-push)"
    if any(kw in text for kw in ("prettier", "eslint", "format", "lint", "tsc")):
        return "Linter or formatter config"
    if any(kw in text for kw in ("import", "export", "barrel", "directive")):
        return "ESLint rule"
    if any(kw in text for kw in ("edit", "write", "delete", "src/")):
        return "Claude Code hook (PreToolUse on Edit/Write)"
    return "Mechanical enforcement (hook or linter)"


# ---------------------------------------------------------------------------
# Conflict detection (corpus-level; populates the third failure class)
# ---------------------------------------------------------------------------

# Polarity categories from F2 (see score_mechanical.py::score_f2).
# A conflict candidate is a mandate-rule pair where one rule's polarity is in
# _PROHIBIT_POLARITIES and the other's is in _ASSERT_POLARITIES, and they
# share at least one concrete marker.
_PROHIBIT_POLARITIES = {"prohibition", "positive_with_negative_clarification"}
_ASSERT_POLARITIES = {"positive_imperative", "positive_with_alternative"}

# Markers too generic to signal a real content overlap. These leak into
# concrete_markers when domain-terms data is broad; filtering them prevents
# false-positive pairs on common English words.
_CONFLICT_MARKER_STOPLIST = {
    "use", "new", "old", "file", "files", "code", "rule", "rules",
    "test", "tests", "data", "line", "error", "name",
}

# Single-character or very short markers are always too generic.
_CONFLICT_MARKER_MIN_LEN = 3


def _rule_markers(rule: dict) -> set[str]:
    """Extract the set of concrete markers a rule references.

    Uses F7's concrete_markers evidence list; filters out markers that are
    too generic to indicate a content overlap (stop-list + min length).
    """
    f7 = rule.get("factors", {}).get("F7", {})
    raw = f7.get("concrete_markers") or []
    out: set[str] = set()
    for m in raw:
        if not isinstance(m, str):
            continue
        lower = m.strip().lower()
        if len(lower) < _CONFLICT_MARKER_MIN_LEN:
            continue
        if lower in _CONFLICT_MARKER_STOPLIST:
            continue
        out.add(lower)
    return out


def _rule_polarity(rule: dict) -> str | None:
    """Return the F2 matched_category for a rule, or None if unavailable."""
    f2 = rule.get("factors", {}).get("F2", {})
    cat = f2.get("matched_category")
    return cat if isinstance(cat, str) else None


def detect_conflicts(rules: list[dict]) -> list[dict]:
    """Detect potential conflict pairs across mandate rules.

    Current signal: polarity mismatch on a shared concrete marker. A pair is
    flagged when one rule reads as a prohibition and another reads as a
    positive directive, and they share at least one non-generic concrete
    marker (typically a file path, API name, or domain term).

    This is a structural-clarity signal, not a compliance predictor. The
    pair is surfaced as a "Potential conflict" for the author to review —
    they may be genuinely contradictory (fix one), legitimately scoped
    differently (add precedence), or a false positive (distinct behaviors
    that happen to share vocabulary).

    Returns a list of conflict dicts with type, rule_a, rule_b, and
    shared_markers. Pairs are ordered by rule id for determinism.
    """
    # Only mandate rules participate in conflict detection. Override and
    # preference rules are expected to relax or refine mandate rules and
    # naturally share vocabulary with them.
    mandate = [r for r in rules if r.get("category") == "mandate"]

    # Precompute markers and polarity for each rule once.
    prepared: list[tuple[dict, set[str], str | None]] = []
    for r in mandate:
        prepared.append((r, _rule_markers(r), _rule_polarity(r)))

    conflicts: list[dict] = []
    for i in range(len(prepared)):
        r_a, markers_a, pol_a = prepared[i]
        if pol_a is None or not markers_a:
            continue
        for j in range(i + 1, len(prepared)):
            r_b, markers_b, pol_b = prepared[j]
            if pol_b is None or not markers_b:
                continue

            # One must be prohibitive, the other assertive.
            if pol_a in _PROHIBIT_POLARITIES and pol_b in _ASSERT_POLARITIES:
                prohibit, assert_ = r_a, r_b
                prohibit_pol, assert_pol = pol_a, pol_b
                prohibit_markers, assert_markers = markers_a, markers_b
            elif pol_b in _PROHIBIT_POLARITIES and pol_a in _ASSERT_POLARITIES:
                prohibit, assert_ = r_b, r_a
                prohibit_pol, assert_pol = pol_b, pol_a
                prohibit_markers, assert_markers = markers_b, markers_a
            else:
                continue

            shared = prohibit_markers & assert_markers
            if not shared:
                continue

            conflicts.append({
                "type": "polarity_mismatch",
                "rule_a": {
                    "id": prohibit["id"],
                    "text": prohibit.get("text", ""),
                    "file": prohibit.get("file", ""),
                    "line_start": prohibit.get("line_start", 0),
                    "polarity": prohibit_pol,
                },
                "rule_b": {
                    "id": assert_["id"],
                    "text": assert_.get("text", ""),
                    "file": assert_.get("file", ""),
                    "line_start": assert_.get("line_start", 0),
                    "polarity": assert_pol,
                },
                "shared_markers": sorted(shared),
            })

    # Deterministic ordering: by (rule_a.id, rule_b.id).
    conflicts.sort(key=lambda c: (c["rule_a"]["id"], c["rule_b"]["id"]))
    return conflicts


# ---------------------------------------------------------------------------
# Formulas
# ---------------------------------------------------------------------------

def smooth_floor(x: float, threshold: float) -> float:
    """Soft floor: min(1.0, x / threshold)."""
    if threshold <= 0:
        return 1.0
    return min(1.0, x / threshold)


def compute_per_rule_score(factors: dict, staleness: dict, category: str) -> dict:
    """Compute per-rule quality score from factor values.

    Null factor values (value is None) are excluded from both numerator and
    denominator. The score represents only the non-null factors — mathematically,
    "this is the score under the assumption that missing factors would score
    equal to the average of the present ones." Rules with null factors are
    flagged as degraded.

    Returns dict with score, pre_floor_score, floor, contributions, layers,
    dominant_weakness, dominant_weakness_gap, degraded, degraded_factors,
    and mechanical_score (score over mechanical/semi-mechanical factors only).
    """
    # Extract factor values — None stays None (not substituted to 0.50)
    factor_values = {}
    degraded_factors = []
    for f_name in _FACTOR_WEIGHTS:
        f_data = factors.get(f_name, {})
        val = f_data.get("value")
        if val is None:
            degraded_factors.append(f_name)
        factor_values[f_name] = val  # may be None

    # F8 is a parallel signal — scored and reported but NOT in composite
    f8_data = factors.get("F8", {})
    f8_value = f8_data.get("value")
    is_hook_candidate = (f8_value is not None and f8_value < _F8_HOOK_THRESHOLD)

    # Weighted linear combination — null factors excluded from both sides
    numerator = 0.0
    active_weight = 0.0
    for f in _FACTOR_WEIGHTS:
        if factor_values[f] is not None:
            numerator += _FACTOR_WEIGHTS[f] * factor_values[f]
            active_weight += _FACTOR_WEIGHTS[f]

    pre_floor_score = numerator / active_weight if active_weight > 0 else 0.0

    # Soft floors — skip if the factor is null (no penalty for unmeasured)
    floor_values = []
    skipped_floors = []
    for f in _SOFT_FLOOR_FACTORS:
        if factor_values[f] is not None:
            floor_values.append(smooth_floor(factor_values[f], _SOFT_FLOOR_THRESHOLD))
        else:
            skipped_floors.append(f)

    # Staleness gate
    if staleness.get("gated", False):
        floor_values.append(_STALENESS_MULTIPLIER)
    else:
        floor_values.append(1.0)

    floor = min(floor_values) if floor_values else 1.0
    score = pre_floor_score * floor

    # Contributions — None for null factors
    contributions = {}
    for f in _FACTOR_WEIGHTS:
        if factor_values[f] is not None:
            contributions[f] = round(_FACTOR_WEIGHTS[f] * factor_values[f] / active_weight, 3) if active_weight > 0 else 0.0
        else:
            contributions[f] = None

    # Layer overlay — F8 is a parallel signal, not a composite layer
    clarity = _compute_layer(_CLARITY_FACTORS, factor_values)
    activation = _compute_layer(_ACTIVATION_FACTORS, factor_values)

    layers = {
        "clarity": round(clarity, 3) if clarity is not None else None,
        "activation": round(activation, 3) if activation is not None else None,
    }

    # Dominant weakness — skip null factors, and skip factors whose evidence
    # indicates the rule is structurally correct on that dimension.
    #
    # F4 special case: when trigger_match == "implicit_scope_trust", the rule
    # is correctly trusting its paths: frontmatter and has no in-text trigger
    # — there is nothing to "fix" on F4, so it must not appear as a dominant
    # weakness. Dogfooding surfaced that users saw "Loaded in the wrong context"
    # on already-well-scoped rules and followed misleading advice to add
    # redundant trigger prefixes.
    def _factor_is_structurally_correct(factor_name: str) -> bool:
        if factor_name != "F4":
            return False
        f4_evidence = factors.get("F4", {})
        return f4_evidence.get("trigger_match") == "implicit_scope_trust"

    dom_weakness = None
    dom_gap = 0.0
    non_null = {f: v for f, v in factor_values.items() if v is not None}
    all_perfect = all(v >= 1.0 for v in non_null.values()) if non_null else True
    if not all_perfect:
        for f, v in non_null.items():
            if _factor_is_structurally_correct(f):
                continue
            gap = _FACTOR_WEIGHTS[f] * (1.0 - v)
            if gap > dom_gap:
                dom_gap = gap
                dom_weakness = f

    # Mechanical-only score (F1+F2+F4+F7 — the non-judgment factors; F6 is absorbed into F7)
    mech_factors = {"F1", "F2", "F4", "F7"}
    mech_num = 0.0
    mech_weight = 0.0
    for f in mech_factors:
        if factor_values.get(f) is not None:
            mech_num += _FACTOR_WEIGHTS[f] * factor_values[f]
            mech_weight += _FACTOR_WEIGHTS[f]
    mechanical_score = round(mech_num / mech_weight, 3) if mech_weight > 0 else None

    degraded = bool(degraded_factors)
    scored_count = len(_FACTOR_WEIGHTS) - len(degraded_factors)

    return {
        "score": round(score, 3),
        "pre_floor_score": round(pre_floor_score, 3),
        "floor": round(floor, 3),
        "contributions": contributions,
        "layers": layers,
        "dominant_weakness": dom_weakness,
        "dominant_weakness_gap": round(dom_gap, 3),
        "failure_class": _FACTOR_TO_FAILURE_CLASS.get(dom_weakness) if dom_weakness else None,
        "degraded": degraded,
        "degraded_factors": degraded_factors,
        "scored_count": scored_count,
        "skipped_floors": skipped_floors,
        "mechanical_score": mechanical_score,
        # Parallel signal: F8 is scored but not in composite
        "f8_value": round(f8_value, 3) if f8_value is not None else None,
        "is_hook_candidate": is_hook_candidate,
    }


def _compute_layer(factor_names: list[str], factor_values: dict) -> float | None:
    """Compute a layer overlay score from its constituent factors.

    Null factor values are excluded. Returns None if all factors are null.
    """
    numerator = 0.0
    denominator = 0.0
    for f in factor_names:
        val = factor_values.get(f)
        if val is not None:
            numerator += _FACTOR_WEIGHTS[f] * val
            denominator += _FACTOR_WEIGHTS[f]
    if denominator == 0:
        return None
    return numerator / denominator


def compute_per_file_score(rules: list[dict], file_info: dict) -> dict:
    """Compute per-file quality score with position weighting and length penalty."""
    if not rules:
        return {
            "file_score": 0.0,
            "length_penalty": 1.0,
            "prohibition_ratio": 0.0,
            "trigger_scope_coherence": 0.0,
            "concreteness_coverage": 0.0,
            "dead_zone_count": 0,
        }

    line_count = file_info.get("line_count", 0)
    total_rules = len(rules)

    # Position weights — smooth triangular: 1.0 at edges, 0.80 at center.
    # Assumption: Claude's parsing attention is stronger at file edges than middle.
    # Unvalidated; documented in quality-model.md §Per-file Score.
    max_w = _POSITION_WEIGHTS["edge"]     # weight at top/bottom of file (default 1.0)
    min_w = _POSITION_WEIGHTS["middle"]   # weight at file midpoint (default 0.80)
    weighted_sum = 0.0
    weight_sum = 0.0
    for i, rule in enumerate(rules):
        position_pct = (rule["line_start"] / max(line_count, 1))
        triangular = 1.0 - abs(2.0 * position_pct - 1.0)
        pos_weight = max_w - (max_w - min_w) * triangular

        weighted_sum += pos_weight * rule.get("score", 0.0)
        weight_sum += pos_weight

    position_weighted_mean = weighted_sum / weight_sum if weight_sum > 0 else 0.0

    # Length penalty — files >120 lines get discounted.
    # Assumption: Claude's ability to apply file-scoped rules degrades with length.
    # Unvalidated; documented in quality-model.md §Per-file Score.
    threshold = _LENGTH_PENALTY["threshold_lines"]
    if line_count <= threshold:
        length_penalty = 1.0
    else:
        penalty = 1.0 - _LENGTH_PENALTY["penalty_per_line"] * (line_count - threshold)
        length_penalty = max(_LENGTH_PENALTY["minimum_penalty"], penalty)

    file_score = position_weighted_mean * length_penalty

    # Per-file metrics — skip null factor values (None is unknown, not 0)
    def _fval(rule: dict, factor: str) -> float | None:
        return rule.get("factors", {}).get(factor, {}).get("value")

    prohibition_count = sum(1 for r in rules if (_fval(r, "F2") is not None and _fval(r, "F2") < 0.60))
    prohibition_ratio = prohibition_count / total_rules if total_rules > 0 else 0.0

    f4_values = [_fval(r, "F4") for r in rules if _fval(r, "F4") is not None]
    trigger_scope_coherence = _stddev(f4_values) if len(f4_values) > 1 else 0.0

    # F6 is absorbed into F7; per-file metric renamed from
    # example_coverage to concreteness_coverage and now uses F7.
    concreteness_count = sum(1 for r in rules if (_fval(r, "F7") is not None and _fval(r, "F7") >= 0.60))
    concreteness_coverage = concreteness_count / total_rules if total_rules > 0 else 0.0

    # Dead zone: high-scoring rules in middle 60%.
    # Depends on position-weighting assumption (see comments above and
    # quality-model.md §Per-file Metrics).
    dead_zone_count = 0
    for rule in rules:
        pos_pct = rule["line_start"] / max(line_count, 1)
        if 0.20 < pos_pct < 0.80 and rule.get("score", 0) > 0.70:
            dead_zone_count += 1

    return {
        "file_score": round(file_score, 3),
        "length_penalty": round(length_penalty, 3),
        # JSON precision invariant: all 0.0–1.0 scores use 3-decimal precision.
        # Markdown/HTML output renders at 2-decimal (see report.py, generate_overview.py).
        "prohibition_ratio": round(prohibition_ratio, 3),
        "trigger_scope_coherence": round(trigger_scope_coherence, 3),
        "concreteness_coverage": round(concreteness_coverage, 3),
        "dead_zone_count": dead_zone_count,
    }


def _stddev(values: list[float]) -> float:
    """Compute population standard deviation."""
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def compute_corpus_scores(rules: list[dict], source_files: list[dict],
                          config: dict) -> tuple[dict, dict]:
    """Compute effective corpus quality and diagnostic rule-mean.

    Returns (effective_corpus_quality, corpus_quality).
    """
    load_prob_overrides = config.get("load_prob_overrides", {})
    severity_overrides = config.get("severity_overrides", {})

    # Group rules by file for file-level scoring
    file_rules: dict[int, list[dict]] = {}
    for rule in rules:
        fi = rule.get("file_index", 0)
        file_rules.setdefault(fi, []).append(rule)

    # Compute per-file scores
    file_scores = {}
    for fi, fi_rules in file_rules.items():
        sf = source_files[fi] if fi < len(source_files) else {}
        file_metrics = compute_per_file_score(fi_rules, sf)
        file_scores[fi] = file_metrics

    # Mandate rules only
    mandate_rules = [r for r in rules if r.get("category") == "mandate"]
    non_mandate_rules = [r for r in rules if r.get("category") != "mandate"]

    # Effective corpus quality: weighted aggregate of file_score over mandate-bearing files
    effective_num = 0.0
    effective_den = 0.0
    for fi, metrics in file_scores.items():
        sf = source_files[fi] if fi < len(source_files) else {}
        sf_path = sf.get("path", "")
        # Only include files with mandate rules
        fi_mandates = [r for r in file_rules.get(fi, []) if r.get("category") == "mandate"]
        if not fi_mandates:
            continue
        load_prob = _get_load_prob(sf, load_prob_overrides)
        severity = severity_overrides.get(sf_path, 1.0)
        effective_num += load_prob * severity * metrics["file_score"]
        effective_den += load_prob * severity

    effective_score = effective_num / effective_den if effective_den > 0 else 0.0

    # Diagnostic rule-mean: per-rule weighted mean ignoring file length penalty
    rule_num = 0.0
    rule_den = 0.0
    for rule in mandate_rules:
        sf = source_files[rule.get("file_index", 0)] if rule.get("file_index", 0) < len(source_files) else {}
        load_prob = _get_load_prob(sf, load_prob_overrides)
        severity = severity_overrides.get(sf.get("path", ""), 1.0)
        rule_num += load_prob * severity * rule.get("score", 0.0)
        rule_den += load_prob * severity

    rule_mean = rule_num / rule_den if rule_den > 0 else 0.0

    # Guideline quality (non-mandate rules)
    guideline_scores = [r.get("score", 0.0) for r in non_mandate_rules]
    guideline_score = sum(guideline_scores) / len(guideline_scores) if guideline_scores else 0.0

    effective_corpus = {
        "score": round(effective_score, 3),
        "methodology": "file-score weighted aggregate over mandate-rule-bearing files",
    }
    corpus = {
        "rule_mean_score": round(rule_mean, 3),
        "rule_count": len(mandate_rules),
        "note": "diagnostic: rule-average ignoring file length penalty",
    }
    guideline = {
        "score": round(guideline_score, 3),
        "rule_count": len(non_mandate_rules),
    }

    return effective_corpus, corpus, guideline, file_scores


def _get_load_prob(source_file: dict, overrides: dict) -> float:
    """Get load probability for a source file."""
    path = source_file.get("path", "")
    if path in overrides:
        return overrides[path]
    if source_file.get("always_loaded", True):
        return _LOAD_PROB_DEFAULTS["always_loaded"]
    return _LOAD_PROB_DEFAULTS["glob_scoped"]


# ---------------------------------------------------------------------------
# Patch merging
# ---------------------------------------------------------------------------

def merge_patches(rules: list[dict], patches_data: dict) -> list[dict]:
    """Apply judgment patches to rules. Returns the modified rules list.

    Patches add F3 and F8 values, and optionally patch F1/F7 for flagged rules
    (F6 is absorbed into F7 — not a separate factor).
    Unknown factor names are ignored with a warning. Missing rules cause a fatal error.
    """
    patches = patches_data.get("patches", {})
    patched_rule_ids = set()

    for rule in rules:
        rule_id = rule["id"]
        if rule_id in patches:
            patched_rule_ids.add(rule_id)
            patch = patches[rule_id]
            for factor_name, factor_data in patch.items():
                if factor_name.endswith("_patch"):
                    # F1_patch, F7_patch — overwrite the existing factor value.
                    # parse_judgment.py validates that factor_data is a dict with
                    # a 'value' key before reaching this point, but be defensive:
                    # a manually-edited patches file could still arrive malformed.
                    base_name = factor_name.replace("_patch", "")
                    if base_name not in rule.get("factors", {}):
                        continue
                    if not isinstance(factor_data, dict) or "value" not in factor_data:
                        print(
                            f"WARNING: {rule_id} {factor_name} is malformed "
                            f"(expected an object with a 'value' key, got {type(factor_data).__name__}); "
                            "skipping patch",
                            file=sys.stderr,
                        )
                        continue
                    rule["factors"][base_name]["value"] = factor_data["value"]
                    rule["factors"][base_name]["method"] = "judgment_patch"
                    if "reasoning" in factor_data:
                        rule["factors"][base_name]["reasoning"] = factor_data["reasoning"]
                elif factor_name in _KNOWN_FACTORS:
                    rule["factors"][factor_name] = factor_data
                else:
                    print(f"WARNING: Unknown factor '{factor_name}' in patch for {rule_id}, ignoring", file=sys.stderr)

    # F-16: After ALL patching, verify every rule has F3 and F8 as keys in
    # factors. The values may be {"value": null, ...} (legitimate null from a
    # rule the model couldn't score) — that is valid. The invariant is key
    # presence, not value presence. Phase 1d's null handling depends on this:
    # null values flow into the formula as excluded factors, but missing keys
    # indicate a broken pipeline.
    for rule in rules:
        factors = rule.get("factors", {})
        missing = [f for f in ("F3", "F8") if f not in factors]
        if missing:
            patched = "patched" if rule["id"] in patched_rule_ids else "unpatched"
            print(f"FATAL: Rule {rule['id']} ({patched}) missing {', '.join(missing)} "
                  f"key(s) in factors — expected from judgment patches; check that "
                  f"the model call completed and judgment_patches.json was written",
                  file=sys.stderr)
            sys.exit(1)

    # Warn about patches for nonexistent rules
    rule_ids = {r["id"] for r in rules}
    for pid in patches:
        if pid not in rule_ids:
            print(f"WARNING: Patch for nonexistent rule {pid}, ignoring", file=sys.stderr)

    return rules


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Extract optional --output flag
    output_path = None
    positional = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        else:
            positional.append(args[i])
            i += 1

    if len(positional) != 2:
        print("Usage: compose.py <scored_semi.json> <judgment_patches.json> [--output file]",
              file=sys.stderr)
        sys.exit(1)

    scored_path = positional[0]
    patches_path = positional[1]

    with open(scored_path, encoding="utf-8") as f:
        scored_data = json.load(f)

    with open(patches_path, encoding="utf-8") as f:
        patches_data = json.load(f)

    # Schema version checks
    scored_version = scored_data.get("schema_version", "0.1")
    if scored_version != "0.1":
        print(f"FATAL: Schema version mismatch — scored_semi has '{scored_version}', expected '0.1'. "
              "Re-run the pipeline end-to-end.", file=sys.stderr)
        sys.exit(1)

    patches_version = patches_data.get("schema_version")
    if patches_version is None:
        print("WARNING: judgment_patches.json has no schema_version field; assuming 0.1",
              file=sys.stderr)
    elif patches_version != "0.1":
        print(f"FATAL: Schema version mismatch — judgment_patches has '{patches_version}', "
              "expected '0.1'. Re-run the pipeline end-to-end.", file=sys.stderr)
        sys.exit(1)

    rules = scored_data.get("rules", [])
    source_files = scored_data.get("source_files", [])
    config = scored_data.get("config", {})
    project_context = scored_data.get("project_context", {})

    # Merge judgment patches
    rules = merge_patches(rules, patches_data)

    # Compute per-rule scores
    for rule in rules:
        result = compute_per_rule_score(
            rule.get("factors", {}),
            rule.get("staleness", {}),
            rule.get("category", "mandate"),
        )
        rule.update(result)

        # Compute leverage for mandate rules
        sf = source_files[rule.get("file_index", 0)] if rule.get("file_index", 0) < len(source_files) else {}
        if rule.get("category") == "mandate":
            load_prob = _get_load_prob(sf, config.get("load_prob_overrides", {}))
            severity = config.get("severity_overrides", {}).get(sf.get("path", ""), 1.0)
            rule["leverage"] = round(load_prob * severity * (1.0 - rule["score"]), 3)
        else:
            rule["leverage"] = None

        rule["stale"] = rule.get("staleness", {}).get("gated", False)

        # Add file path for report convenience
        if rule.get("file_index", 0) < len(source_files):
            rule["file"] = source_files[rule["file_index"]]["path"]

        # Add loading type
        if rule.get("file_index", 0) < len(source_files):
            sf = source_files[rule["file_index"]]
            rule["loading"] = "always-loaded" if sf.get("always_loaded") else "glob-scoped"

    # Sort by leverage descending for mandate rules (non-mandate at end)
    mandate_rules = sorted(
        [r for r in rules if r.get("category") == "mandate"],
        key=lambda r: r.get("leverage", 0) or 0,
        reverse=True,
    )
    non_mandate_rules = [r for r in rules if r.get("category") != "mandate"]
    rules = mandate_rules + non_mandate_rules

    # Compute corpus scores
    effective_corpus, corpus, guideline, file_score_map = compute_corpus_scores(
        rules, source_files, config)

    # Build file metrics
    files_output = []
    for fi, sf in enumerate(source_files):
        fi_rules = [r for r in rules if r.get("file_index") == fi]
        if fi in file_score_map:
            metrics = file_score_map[fi]
        else:
            metrics = compute_per_file_score(fi_rules, sf)

        files_output.append({
            "path": sf.get("path", ""),
            "file_score": metrics["file_score"],
            "line_count": sf.get("line_count", 0),
            "rule_count": len(fi_rules),
            "length_penalty": metrics["length_penalty"],
            "prohibition_ratio": metrics["prohibition_ratio"],
            "trigger_scope_coherence": metrics["trigger_scope_coherence"],
            "concreteness_coverage": metrics["concreteness_coverage"],
            "dead_zone_count": metrics["dead_zone_count"],
        })

    # Positive findings — exclude degraded rules (score on N/6 factors is not
    # a confirmed positive; you don't know what F3/F8 would have been)
    positive = [r for r in rules if r.get("score", 0) > 0.80 and not r.get("degraded", False)]

    # Rewrite candidates (top-3 by leverage)
    rewrite_candidates = [
        {"rule_id": r["id"], "score": r["score"], "dominant_weakness": r.get("dominant_weakness")}
        for r in mandate_rules[:3]
        if r.get("leverage", 0) and r.get("leverage", 0) > 0
    ]

    # Build output
    model_version = patches_data.get("model_version", "unknown")

    output = {
        "schema_version": "0.1",
        "pipeline_version": scored_data.get("pipeline_version", "0.1.0"),
        "project": project_context.get("project_root", scored_data.get("project_root", "")),
        "date": str(date.today()),
        "methodology": {
            "weights_version": _WEIGHTS["version"],
            "pipeline_version": scored_data.get("pipeline_version", "0.1.0"),
            "model_version": model_version,
        },
        "files_scanned": len(source_files),
        "rules_extracted": len(rules),
        "effective_corpus_quality": effective_corpus,
        "corpus_quality": corpus,
        "guideline_quality": guideline,
        "rules": rules,
        "files": files_output,
        "positive_findings": [
            {"file": r.get("file", ""), "line": r.get("line_start"), "text": r.get("text", "")[:100],
             "score": r["score"]}
            for r in positive
        ],
        "rewrite_candidates": rewrite_candidates,
        # Parallel signal: rules with F8 < threshold where a hook/linter
        # would be more reliable than text. Separate from comprehension composite.
        "hook_opportunities": [
            {
                "id": r["id"],
                "text": r.get("text", ""),
                "file": r.get("file", ""),
                "line_start": r.get("line_start", 0),
                "f8_value": r.get("f8_value"),
                "suggested_enforcement": _suggest_enforcement_layer(r),
            }
            for r in rules
            if r.get("is_hook_candidate")
        ],
        # Corpus-level signal: mandate-rule pairs that may contradict each
        # other (currently: polarity mismatch on a shared concrete marker).
        # Presentation-layer diagnostic — does not affect the composite.
        "conflicts": detect_conflicts(rules),
    }

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    else:
        _lib.write_json_stdout(output)


if __name__ == "__main__":
    main()
