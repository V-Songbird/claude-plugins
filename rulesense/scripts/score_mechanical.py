"""Mechanical factor scoring: F1 (verb strength), F2 (framing polarity), F4 (load-trigger alignment).

Pure JSON-in → JSON-out. Reads rules.json from stdin, outputs same JSON with
F1, F2, F4 added to each rule's factors dict.
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

_VERBS_DATA = _lib.load_data("verbs")
_FRAMING_DATA = _lib.load_data("framing")
_WEIGHTS_DATA = _lib.load_data("weights")

# Build verb patterns sorted by length (longest first for greedy matching).
# Regex pre-compiled at module load to avoid per-rule recompilation cost:
# for a corpus of N rules and V verbs, score_f1 matches every rule against
# every verb, so pre-compiling eliminates N*V cache-lookups in the hot loop.
_VERB_TIERS: list[tuple[str, float, str, "re.Pattern[str]"]] = []
for tier in _VERBS_DATA["patterns"]:
    for verb in tier["verbs"]:
        verb_lower = verb.lower()
        pattern = re.compile(r'(?:^|[\s,;(])(' + re.escape(verb_lower) + r')(?:[\s,;.)!?]|$)')
        _VERB_TIERS.append((verb_lower, tier["score"], tier["label"], pattern))
_VERB_TIERS.sort(key=lambda x: len(x[0]), reverse=True)


# ---------------------------------------------------------------------------
# F1: Verb Strength
# ---------------------------------------------------------------------------

def score_f1(rule_text: str) -> dict:
    """Score F1 (verb strength) using the verb lookup table.

    Returns evidence dict with value, method, matched_verb, matched_score_tier.
    """
    text_lower = rule_text.lower()

    # Compound hedging: find ALL matching patterns, take the lowest
    matches = []
    for verb, score, label, pattern in _VERB_TIERS:
        m = pattern.search(text_lower)
        if m:
            matches.append((verb, score, label, m.start(1)))

    if not matches:
        # Check if it reads as an implicit imperative (statement form)
        # Statements like "Test files mirror source paths" without any verb
        if _looks_like_statement(text_lower):
            return {
                "value": _VERBS_DATA["implicit_verb_default"],
                "method": "implicit_imperative_default",
                "matched_verb": None,
                "matched_score_tier": None,
                "matched_position": None,
            }
        # True extraction failure — no recognizable pattern at all
        return {
            "value": None,
            "method": "extraction_failed",
            "matched_verb": None,
            "matched_score_tier": None,
            "matched_position": None,
        }

    # Check if this is actually a statement form where the "verb" is a false positive
    # e.g., "Test files mirror source paths" — "test" is a noun here
    # But only downgrade to implicit if no strong verb (must, always, never, etc.) was matched
    best_match_score = max(m[1] for m in matches)
    if _looks_like_statement(text_lower) and best_match_score <= 0.85:
        # Only override to implicit for weak matches (bare imperatives that might be nouns)
        # Strong verbs like "must", "always", "never" are never false positives
        return {
            "value": _VERBS_DATA["implicit_verb_default"],
            "method": "implicit_imperative_default",
            "matched_verb": None,
            "matched_score_tier": None,
            "matched_position": None,
        }

    # Compound hedging: if multiple hedging verbs are present, score the lowest
    # e.g., "Try to prefer X where possible" → matches "try to" (0.20) AND "prefer" (0.50)
    # Score should be 0.20 (lowest)
    hedging_labels = {"hedged", "suggestion", "weak_suggestion", "preference"}
    hedging_matches = [m for m in matches if m[2] in hedging_labels]

    if len(hedging_matches) >= 2:
        # Multiple hedges = compound hedging, use lowest
        best = min(hedging_matches, key=lambda x: x[1])
    else:
        # Use strongest match (highest score)
        best = max(matches, key=lambda x: x[1])

    # Special case: "always" + imperative verb = 1.00 (unconditional mandate)
    if any(m[0] == "always" for m in matches):
        non_always = [m for m in matches if m[0] != "always" and m[2] == "bare_imperative"]
        if non_always:
            return {
                "value": 1.00,
                "method": "lookup",
                "matched_verb": f"always + {non_always[0][0]}",
                "matched_score_tier": 1.00,
                "matched_position": non_always[0][3],
            }

    return {
        "value": best[1],
        "method": "lookup",
        "matched_verb": best[0],
        "matched_score_tier": best[1],
        "matched_position": best[3],
    }


# Words that appear in the bare_imperative verb tier but are commonly used
# as nouns at the start of rules. When these appear as the first word AND
# the next token is a plural noun, the word is acting as a noun in a
# compound/possessive role, not as an imperative verb.
#
# NOTE: Articles ("the/a/an") and prepositions ("for/in/on/at/...") are
# NOT included in _NOUN_FOLLOWERS. In English, articles introduce direct
# objects after verbs ("Check the logs" = imperative) and prepositions
# introduce complements ("Watch for changes" = imperative). Both are
# evidence the preceding word IS a verb, not a noun.
_NOUN_VERB_AMBIGUOUS = {
    "document", "format", "log", "name", "set", "watch",
    "report", "display", "record", "test", "check",
    "cache", "scope", "limit", "batch", "profile",
    "audit", "benchmark", "aggregate", "archive",
    "guard", "pin", "drain",
}

# Plural nouns that follow a noun-verb ambiguous word and indicate the
# first word is a noun in a compound role ("Document headers", "Format
# strings", "Log entries", "Test files"). Extend as new noun-noun
# patterns are encountered. The harm from missing a pattern is bounded
# (one rule scores 0.85 instead of 0.70, ~0.023 high on the rule score).
_NOUN_FOLLOWERS = {
    "headers", "files", "strings", "entries", "requests", "messages",
    "logs", "values", "types", "fields", "options",
    "conventions", "names", "rules", "paths", "settings",
    "keys", "items", "objects", "results", "records",
    "operations", "endpoints", "variables", "pages", "data",
    "clauses", "layers", "levels", "lines", "traits",
    "pipes", "pools", "connections", "events", "configs",
}


def _looks_like_statement(text_lower: str) -> bool:
    """Check if text is a statement form where a leading word is a noun, not a verb.

    Handles two cases:
    1. Text starts with a known article/determiner/plural noun (original heuristic).
    2. Text starts with a noun-verb ambiguous word (document, format, log, etc.)
       followed by a plural noun from _NOUN_FOLLOWERS — indicating a compound
       noun phrase ("Document headers", "Format strings", "Log entries").

    Examples that should return True:
    - "Document headers must be at the top" — "document" is a noun (→ headers)
    - "Format strings should use f-strings" — "format" is a noun (→ strings)
    - "Log entries for failed requests" — "log" is a noun (→ entries)
    - "Test files mirror source paths" — "test" is a noun (→ files)

    Examples that should return False (real imperatives):
    - "Document the API endpoints" — "document" is a verb (article "the" = direct object)
    - "Check the logs" — "check" is a verb
    - "Watch for changes" — "watch" is a verb (preposition "for" = complement)
    - "Set the timeout" — "set" is a verb
    """
    words = text_lower.split()
    if not words:
        return False

    # Original heuristic: starts with article/determiner/plural noun.
    # "test/tests" uses a negative lookahead for articles: "Test the X" is a
    # real imperative (article introduces direct object), but "Test code" /
    # "Test coverage" / "Tests should" are noun phrases.
    statement_starts = [
        r'^(?:all|each|every|the|a|an|this|that|these|those)\s',
        r'^(?:files?|code|modules?|components?|functions?|classes|methods)\s',
        r'^tests?\s+(?!the\s|a\s|an\s)',
    ]
    for pat in statement_starts:
        if re.match(pat, text_lower):
            return True

    # Extended: noun-verb ambiguous word followed by a noun-follower
    if len(words) >= 2 and words[0] in _NOUN_VERB_AMBIGUOUS:
        if words[1] in _NOUN_FOLLOWERS:
            return True

    return False


# ---------------------------------------------------------------------------
# F2: Framing Polarity
# ---------------------------------------------------------------------------

def score_f2(rule_text: str, f1_evidence: dict) -> dict:
    """Score F2 (framing polarity) using classification patterns."""
    text_lower = rule_text.lower()

    # Check prohibition markers
    prohibition_patterns = _FRAMING_DATA["categories"][3]["patterns"]  # prohibition at index 3
    is_prohibition = any(p in text_lower for p in prohibition_patterns)

    # Check hedged preference markers
    hedged_patterns = _FRAMING_DATA["categories"][4]["patterns"]  # hedged at index 4
    is_hedged = any(p in text_lower for p in hedged_patterns)

    # Check positive with alternative markers
    alt_patterns = _FRAMING_DATA["categories"][0]["patterns"]  # positive_with_alternative at index 0
    has_alternative = any(p in text_lower for p in alt_patterns)

    # Also check for contrast-form "not": `X` not `Y` or ", not noun"
    # (plain "not " was removed from patterns to avoid false positives on negation)
    if not has_alternative:
        is_contrast, _ = _has_contrast_not(rule_text)
        if is_contrast:
            has_alternative = True

    if is_prohibition:
        # Check if prohibition has a positive follow-up
        # "Never X — use Y" or "Do not X. Use Y instead."
        # Split on sentence boundaries: period/!/? followed by space+capital, or em-dash/semicolon
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])|[;—–]\s*', rule_text)
        if len(sentences) >= 2:
            follow_up = " ".join(sentences[1:])
            if _has_positive_imperative(follow_up):
                return {"value": 0.70, "method": "classify", "matched_category": "positive_with_negative_clarification"}

        return {"value": 0.50, "method": "classify", "matched_category": "prohibition"}

    if is_hedged:
        return {"value": 0.35, "method": "classify", "matched_category": "hedged_preference"}

    if has_alternative:
        return {"value": 0.95, "method": "classify", "matched_category": "positive_with_alternative"}

    # Check for positive with negative clarification (two sentences, first positive, second negative)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', rule_text)
    if len(sentences) >= 2:
        first_positive = _has_positive_imperative(sentences[0])
        rest_has_prohibition = any(
            any(p in s.lower() for p in prohibition_patterns) for s in sentences[1:]
        )
        if first_positive and rest_has_prohibition:
            return {"value": 0.70, "method": "classify", "matched_category": "positive_with_negative_clarification"}

    # Default: positive imperative
    return {"value": 0.85, "method": "classify", "matched_category": "positive_imperative"}


def _has_positive_imperative(text: str) -> bool:
    """Check if text contains a positive imperative (not a prohibition)."""
    text_lower = text.lower().strip()
    prohibition_markers = ["never", "do not", "don't", "avoid", "must not"]
    if any(text_lower.startswith(p) for p in prohibition_markers):
        return False
    # Check for any imperative verb (bare imperative tier OR strong mandate tier)
    for verb, score, label, _pattern in _VERB_TIERS:
        if label in ("bare_imperative", "unconditional_mandate") and re.search(r'(?:^|\s)' + re.escape(verb) + r'(?:\s|$|[,.])', text_lower):
            return True
    return False


def _has_contrast_not(text: str) -> tuple[bool, bool]:
    """Detect contrast-form 'not': 'X, not Y' or '`X` not `Y`'.

    Returns (is_contrast, is_high_confidence).
    High confidence: backtick-wrapped contrast like `X` not `Y`.
    Low confidence: textual contrast like ", not Y" — heuristic, may misfire
    on negation forms like "is not optional" or "should not depend".
    """
    # High confidence: backtick contrast
    if re.search(r'`[^`]+`\s*[,;:]?\s+not\s+`[^`]+`', text):
        return (True, True)

    # Exclude common negation forms before checking for textual contrast
    NEGATION_PATTERNS = [
        r'\b(?:is|are|was|were|be|been|being)\s+not\b',  # predicate negation
        r',\s+not\s+\w+(?:ing|ed|ly)\b',  # gerund/past/adverb (likely verb phrase)
        r',\s+not\s+\w+\s+(?:on|to|in|with|from|by|at|of|as|for|after|before)\b',  # phrasal verb
    ]
    for pat in NEGATION_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return (False, True)  # confident: it's negation, not contrast

    # Low confidence: textual contrast ", not <word>" not caught by exclusions
    if re.search(r',\s+not\s+\w+', text, re.IGNORECASE):
        return (True, False)

    return (False, True)


# ---------------------------------------------------------------------------
# F4: Load-Trigger Alignment
# ---------------------------------------------------------------------------

def score_f4(rule: dict, source_file: dict) -> dict:
    """Score F4 (load-trigger alignment) using glob match and keyword overlap."""
    globs = source_file.get("globs", [])
    always_loaded = source_file.get("always_loaded", True)
    glob_match_count = source_file.get("glob_match_count")
    rule_text = rule["text"].lower()
    staleness = rule.get("staleness", {})

    # Check staleness first
    if staleness.get("gated", False):
        return {"value": 0.05, "method": "stale", "loading": "glob-scoped" if globs else "always-loaded", "trigger_match": None}

    # Dead glob
    if globs and glob_match_count == 0:
        return {"value": 0.05, "method": "dead_glob", "loading": "glob-scoped", "trigger_match": None}

    # Always-loaded with no globs
    if always_loaded and not globs:
        # Check for subsystem-specific trigger language
        trigger_keywords = _extract_trigger_scope(rule_text)
        if trigger_keywords:
            return {"value": 0.40, "method": "misaligned", "loading": "always-loaded", "trigger_match": "specific_trigger_in_universal_file"}
        return {"value": 0.95, "method": "always_universal", "loading": "always-loaded", "trigger_match": "universal"}

    # Glob-scoped file
    if globs:
        # Check for explicit trigger language matching glob
        trigger_keywords = _extract_trigger_scope(rule_text)
        glob_keywords = _extract_glob_keywords(globs)

        if trigger_keywords:
            # Explicit trigger — check if it matches the glob
            overlap = trigger_keywords & glob_keywords
            if overlap:
                return {"value": 0.95, "method": "glob_match", "loading": "glob-scoped", "trigger_match": "explicit_match"}
            else:
                return {"value": 0.25, "method": "wrong_scope", "loading": "glob-scoped", "trigger_match": "explicit_mismatch"}

        # No explicit trigger — try keyword overlap (semantic match)
        rule_keywords = _extract_rule_keywords(rule_text)
        overlap = rule_keywords & glob_keywords
        if overlap:
            return {"value": 0.90, "method": "keyword_overlap", "loading": "glob-scoped", "trigger_match": f"overlap:{','.join(sorted(overlap))}"}

        # No overlap — the rule has no explicit trigger text AND no keyword
        # overlap with the glob. Under the lens, this is a CORRECTLY LEAN rule:
        # the paths: frontmatter is doing the alignment work, and re-stating the
        # scope inside the rule text would be redundant padding. Score high.
        # See quality-model.md §F4 for the rationale.
        no_overlap_score = _WEIGHTS_DATA.get("F4_no_overlap_score", 0.85)
        return {"value": no_overlap_score, "method": "keyword_overlap", "loading": "glob-scoped", "trigger_match": "implicit_scope_trust"}

    # Fallback: reached when always_loaded=False AND globs=[] — truly ambiguous.
    # After Bug 6 fix this is mostly unreachable, but keep as safety net with
    # honest labels and a distinct (lower) score than the glob-scoped case.
    ambiguous_score = _WEIGHTS_DATA.get("F4_ambiguous_score", 0.65)
    return {"value": ambiguous_score, "method": "no_signal", "loading": "ambiguous", "trigger_match": "fallback"}


def _extract_trigger_scope(text: str) -> set[str]:
    """Extract subsystem-specific trigger keywords from rule text."""
    triggers = set()
    patterns = [
        r'\bwhen\s+(?:editing|working\s+(?:on|with)|modifying|creating)\s+(\w+)\s+files?\b',
        r'\bfor\s+(\w+)\s+files?\b',
        r'\bin\s+(?:the\s+)?(\w+)\s+(?:directory|folder|module)\b',
        r'\bduring\s+(\w+)\b',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            triggers.add(m.group(1).lower())
    return triggers


def _extract_glob_keywords(globs: list[str]) -> set[str]:
    """Extract meaningful keywords from glob patterns."""
    keywords = set()
    for g in globs:
        # Split on path separators and wildcards
        parts = re.split(r'[/\\*?.\[\]{}]+', g)
        for part in parts:
            part = part.lower().strip()
            if part and len(part) > 1 and part not in ("src", "lib", "test", "tests"):
                keywords.add(part)
    return keywords


def _extract_rule_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from rule text for semantic matching."""
    # Remove common stop words and extract domain-relevant terms
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    stop_words = {
        "the", "and", "for", "all", "new", "with", "not", "use", "when",
        "this", "that", "from", "into", "over", "than", "must", "should",
        "always", "never", "before", "after", "each", "every", "where",
        "only", "also", "just", "about", "more", "most", "some", "any",
    }
    return {w for w in words if w not in stop_words}


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    data = _lib.read_json_stdin()
    source_files = data.get("source_files", [])
    rules = data.get("rules", [])

    for rule in rules:
        file_idx = rule["file_index"]
        sf = source_files[file_idx] if file_idx < len(source_files) else {}

        # F1: Verb strength
        f1 = score_f1(rule["text"])
        rule["factors"]["F1"] = f1

        # F2: Framing polarity
        f2 = score_f2(rule["text"], f1)
        rule["factors"]["F2"] = f2

        # F4: Load-trigger alignment
        f4 = score_f4(rule, sf)
        rule["factors"]["F4"] = f4

        # Flag F1 extraction failures for judgment batch
        if f1["method"] == "extraction_failed":
            if "factor_confidence_low" not in rule:
                rule["factor_confidence_low"] = []
            if "F1" not in rule["factor_confidence_low"]:
                rule["factor_confidence_low"].append("F1")

    _lib.write_json_stdout(data)


if __name__ == "__main__":
    main()
