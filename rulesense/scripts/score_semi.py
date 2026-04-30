"""Semi-mechanical factor scoring: F7 (concreteness — absorbs example density).

Pure JSON-in -> JSON-out. Reads scored JSON from stdin (with F1, F2, F4),
outputs same JSON with F7 added and factor_confidence_low flags on
borderline rules.

F6 (example density) is absorbed into F7 — not a separate factor.
F7 (concreteness) counts both example markers and abstract-vs-concrete nouns.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _lib

# ---------------------------------------------------------------------------
# Load data tables
# ---------------------------------------------------------------------------

_MARKERS_DATA = _lib.load_data("markers")
_CONFIDENCE_DATA = _lib.load_data("semi_confidence")

# Pre-compile hot-path patterns at module load to avoid per-rule recompilation.
# For a corpus of N rules, _find_concrete_markers runs on every rule and was
# re-compiling the backtick regex + every concrete_regex string each time.
_BACKTICK_PATTERN = re.compile(r'`([^`]+)`')
_CONCRETE_REGEX_COMPILED: list["re.Pattern[str]"] = []
for _pattern_str in _MARKERS_DATA["concrete_regex"]:
    try:
        _CONCRETE_REGEX_COMPILED.append(re.compile(_pattern_str))
    except re.error:
        # Skip malformed patterns in the data file — matches the original
        # except-and-continue behavior in _find_concrete_markers.
        continue

# Numeric-threshold patterns are compiled with IGNORECASE so that matches
# survive casual capitalization ("Under 15 Words"). Bright-line thresholds
# are what turn "short" into something checkable; see claude.ai system-prompt
# patterns analysis, pattern 5.
_NUMERIC_THRESHOLD_REGEX_COMPILED: list["re.Pattern[str]"] = []
for _pattern_str in _MARKERS_DATA.get("numeric_threshold_regex", []):
    try:
        _NUMERIC_THRESHOLD_REGEX_COMPILED.append(
            re.compile(_pattern_str, flags=re.IGNORECASE)
        )
    except re.error:
        continue

# Pre-lowercase concrete terms once at module load so the hot loop does a
# plain substring check instead of calling .lower() on every term per rule.
_CONCRETE_TERMS_LOWER: list[tuple[str, str]] = [
    (term, term.lower()) for term in _MARKERS_DATA.get("concrete_terms", [])
]


# ---------------------------------------------------------------------------
# F7: Concreteness (absorbs example density — F6 is not a separate factor)
# ---------------------------------------------------------------------------

def _find_numeric_thresholds(text: str) -> list[str]:
    """Find bright-line numeric thresholds in rule text.

    Examples: "fewer than 15 words", "under 100ms", "at least 3 items",
    "between 1 and 10", "80%". A rule with a numeric threshold has
    converted an adjectival standard ("short", "soon", "a lot") into
    something Claude can mechanically check against the input. These
    count as concrete markers for F7.
    """
    markers: list[str] = []
    for pattern in _NUMERIC_THRESHOLD_REGEX_COMPILED:
        for m in pattern.finditer(text):
            phrase = m.group(0).strip()
            # Deduplicate: the bare-number-with-unit pattern overlaps with
            # the comparator pattern ("under 100ms" matches both); keep
            # the first (longest) match and skip any later submatch that
            # is already covered.
            if any(phrase in existing or existing in phrase for existing in markers):
                # If the new phrase is longer, prefer it (more context).
                longer = [existing for existing in markers
                          if existing in phrase and existing != phrase]
                for existing in longer:
                    markers.remove(existing)
                if phrase not in markers:
                    markers.append(phrase)
                continue
            markers.append(phrase)
    return markers


def _find_concrete_markers(text: str) -> list[str]:
    """Find concrete markers in rule text."""
    markers = []

    # Backtick-wrapped identifiers
    for m in _BACKTICK_PATTERN.finditer(text):
        markers.append(m.group(1))

    # Strip backtick-wrapped content before regex search to avoid double-counting
    text_stripped = _BACKTICK_PATTERN.sub('', text)

    # Named APIs/classes (CamelCase with suffixes)
    for pattern in _CONCRETE_REGEX_COMPILED:
        for m in pattern.finditer(text_stripped):
            name = m.group(0)
            if name not in markers:
                markers.append(name)

    # Numeric-threshold phrases (bright-line markers).
    for phrase in _find_numeric_thresholds(text_stripped):
        if phrase not in markers:
            markers.append(phrase)

    # Known domain terms (lowercase multi-word patterns from the data file)
    text_lower = text.lower()
    existing_lower = [m.lower() for m in markers]
    for term, term_lower in _CONCRETE_TERMS_LOWER:
        if term_lower in text_lower:
            # Don't add if any existing marker overlaps with this term
            already_covered = any(
                term_lower in m_lower or m_lower in term_lower
                for m_lower in existing_lower
            )
            if not already_covered:
                markers.append(term)
                existing_lower.append(term_lower)

    return markers


def _find_abstract_markers(text: str) -> list[str]:
    """Find abstract markers in rule text."""
    markers = []
    text_lower = text.lower()

    for abstract in _MARKERS_DATA["abstract_markers"]:
        if abstract.lower() in text_lower:
            markers.append(abstract)

    return markers


def _score_from_ratio(concrete_count: int, abstract_count: int) -> float:
    """Score F7 based on concrete:abstract marker ratio and absolute counts.

    The spec scoring table maps both ratio and absolute quality:
    - All concrete, no abstract: 0.90-1.00
    - Mostly concrete, minor hedges: 0.70-0.85
    - Mixed: 0.45-0.65
    - Mostly abstract with one concrete: 0.25-0.40
    - All abstract, no concrete: 0.05-0.20
    """
    if concrete_count == 0 and abstract_count == 0:
        return 0.05  # No markers = non-specific

    if concrete_count == 0:
        return 0.10  # All abstract

    if abstract_count == 0:
        # All concrete — score based on quantity
        if concrete_count >= 4:
            return 0.95
        elif concrete_count >= 2:
            return 0.85
        else:
            return 0.80  # Single concrete marker with no abstract

    # Mixed: compute ratio-based score
    ratio = concrete_count / (concrete_count + abstract_count)

    if ratio >= 0.80:
        # Mostly concrete with minor hedges
        return 0.75 + 0.10 * min(concrete_count / 4, 1.0)
    elif ratio >= 0.50:
        # Mixed
        return 0.45 + 0.20 * ratio
    elif ratio >= 0.25:
        # Mostly abstract with some concrete
        return 0.25 + 0.15 * ratio
    else:
        # Very abstract
        return 0.10 + 0.10 * ratio


def score_f7(rule_text: str) -> dict:
    """Score F7 (specificity) by counting concrete vs abstract markers."""
    concrete = _find_concrete_markers(rule_text)
    abstract = _find_abstract_markers(rule_text)

    value = _score_from_ratio(len(concrete), len(abstract))

    return {
        "value": round(value, 2),
        "method": "count",
        "concrete_markers": concrete,
        "abstract_markers": abstract,
        "concrete_count": len(concrete),
        "abstract_count": len(abstract),
    }


def should_flag_f7(evidence: dict) -> bool:
    """Check if F7 score should be flagged for judgment fallback."""
    concrete = evidence["concrete_count"]
    abstract = evidence["abstract_count"]
    conf = _CONFIDENCE_DATA["F7"]

    total = concrete + abstract
    if total == 0:
        return False

    ratio = concrete / total
    low, high = conf["flag_when_ratio_between"]

    if low <= ratio <= high:
        return True

    if conf.get("flag_when_abstract_present_with_concrete", False):
        if concrete > 0 and abstract > 0:
            return True

    return False


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    data = _lib.read_json_stdin()
    rules = data.get("rules", [])

    for rule in rules:
        text = rule["text"]

        # F7: Concreteness (absorbs example density — F6 is not a separate factor)
        f7 = score_f7(text)
        rule["factors"]["F7"] = f7

        # Confidence flags
        flags = rule.get("factor_confidence_low", [])
        if should_flag_f7(f7):
            flags.append("F7")
        if flags:
            rule["factor_confidence_low"] = flags

    _lib.write_json_stdout(data)


if __name__ == "__main__":
    main()
