"""Tests for score_semi.py — F7 (concreteness; absorbs example density).

F6 (example density) is absorbed into F7 — not a separate factor.
F7 (concreteness) takes both roles. The TestF6WorkedExamples class was
removed; F7 has its own tests below.
"""

import re

import pytest
from conftest import run_script


def _score_rule(text: str) -> dict:
    """Run a single rule through score_semi and return it."""
    data = {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_context": {"stack": [], "always_loaded_files": [], "glob_scoped_files": []},
        "config": {},
        "source_files": [{"path": "test.md", "globs": [], "glob_match_count": None,
                          "default_category": "mandate", "line_count": 10, "always_loaded": True}],
        "rules": [{
            "id": "R001", "file_index": 0, "text": text,
            "line_start": 1, "line_end": 1, "category": "mandate",
            "referenced_entities": [], "staleness": {"gated": False, "missing_entities": []},
            "factors": {
                "F1": {"value": 0.85, "method": "lookup"},
                "F2": {"value": 0.85, "method": "classify"},
                "F4": {"value": 0.95, "method": "glob_match"},
            },
        }],
    }
    result = run_script("score_semi.py", stdin_data=data)
    return result["rules"][0]


# ---------------------------------------------------------------------------
# F7: Concreteness (absorbs example density — F6 is not a separate factor)
# ---------------------------------------------------------------------------

class TestF7WorkedExamples:
    """Test F7 scoring from factor-rubrics.md worked examples.

    F7 is semi-mechanical — the mechanical counting gets close but
    borderline cases need the LLM counterexample test fallback.
    Tolerance is ±0.15 for tests that the mechanical scorer can handle.
    Cases requiring the LLM fallback are tested separately with wider tolerance.
    """

    @pytest.mark.parametrize("text,expected_score,tolerance", [
        # 4 concrete, 0 abstract -> 0.95 (all concrete)
        ("ALWAYS use `getProjectCommands(project)` not `.database.commands`", 0.95, 0.15),
        # 2 concrete (func components, React), 0 abstract -> 0.85
        ("Use functional components for all new React files", 0.85, 0.15),
        # 1 concrete (path), 0 abstract -> 0.85
        ("NEVER edit files in src/main/gen/ directly", 0.85, 0.15),
        # 2 concrete, 1 abstract (expensive) -> ~0.70
        ("Use CachedValuesManager for expensive computations over PSI trees", 0.70, 0.15),
        # 0 concrete, 3 abstract -> ~0.05
        ("Use good judgment about error handling", 0.05, 0.15),
    ])
    def test_f7_worked_examples(self, text, expected_score, tolerance):
        rule = _score_rule(text)
        f7 = rule["factors"]["F7"]
        assert abs(f7["value"] - expected_score) <= tolerance, \
            f"F7 for '{text[:50]}' expected ~{expected_score}, got {f7['value']} (C={f7['concrete_count']},A={f7['abstract_count']})"

    def test_f7_marker_counting_concrete(self):
        """Verify concrete markers are detected."""
        rule = _score_rule("Use `getProjectCommands(project)` not `.database.commands`")
        f7 = rule["factors"]["F7"]
        assert f7["concrete_count"] >= 2

    def test_f7_marker_counting_abstract(self):
        """Verify abstract markers are detected."""
        rule = _score_rule("Use good judgment about error handling")
        f7 = rule["factors"]["F7"]
        assert f7["abstract_count"] >= 2
        assert "good" in f7["abstract_markers"] or "error handling" in f7["abstract_markers"]

    def test_f7_domain_terms_detected(self):
        """Domain terms like 'functional components' should count as concrete."""
        rule = _score_rule("Use functional components for all new React files")
        f7 = rule["factors"]["F7"]
        concrete_names = [m.lower() for m in f7["concrete_markers"]]
        assert any("functional component" in n for n in concrete_names)

    def test_f7_confidence_flag_mixed(self):
        """Rules with both concrete and abstract markers should be flagged."""
        rule = _score_rule("Try to prefer functional components when possible")
        f7 = rule["factors"]["F7"]
        assert f7["concrete_count"] >= 1
        assert f7["abstract_count"] >= 1
        flags = rule.get("factor_confidence_low", [])
        assert "F7" in flags, "Mixed concrete/abstract should flag F7 for judgment"

    def test_f7_no_markers(self):
        """Rule with no recognizable markers scores very low."""
        rule = _score_rule("Do the right thing here.")
        f7 = rule["factors"]["F7"]
        assert f7["value"] <= 0.20


class TestF7NumericThresholds:
    """Bright-line numeric thresholds count as concrete markers.

    A rule with 'fewer than 15 words' has converted an adjectival standard
    into something Claude can mechanically check. These lift F7 above what
    the same rule would score with just 'short'. See claude.ai system-prompt
    patterns analysis, pattern 5.
    """

    @pytest.mark.parametrize("text,expected_phrase", [
        ("Keep PR titles under 70 characters.", "under 70 characters"),
        ("Summaries must be fewer than 15 words.", "fewer than 15 words"),
        ("Include at least 3 examples per rule.", "at least 3 examples"),
        ("Allow no more than 20 entries in a list.", "no more than 20 entries"),
        ("Response time budget: 100ms.", "100ms"),
        ("Stall warnings fire after 5 seconds.", "5 seconds"),
        ("Coverage must be at least 80%.", "at least 80%"),
        ("Batch size must be between 1 and 10.", "between 1 and 10"),
    ])
    def test_numeric_phrases_detected(self, text, expected_phrase):
        rule = _score_rule(text)
        f7 = rule["factors"]["F7"]
        markers_lower = [m.lower() for m in f7["concrete_markers"]]
        assert any(expected_phrase.lower() in m for m in markers_lower), \
            f"Expected '{expected_phrase}' among markers, got {f7['concrete_markers']}"

    def test_case_insensitive_match(self):
        rule = _score_rule("Keep titles Under 70 Characters.")
        f7 = rule["factors"]["F7"]
        markers_lower = [m.lower() for m in f7["concrete_markers"]]
        assert any("70 characters" in m for m in markers_lower)

    def test_version_number_is_not_a_threshold(self):
        """'Node 18' has a number but no unit — should not match as a
        threshold. (It may still match other concrete patterns, but not
        this one.)"""
        rule = _score_rule("Use Node 18 for production.")
        f7 = rule["factors"]["F7"]
        # No numeric-threshold marker should appear
        markers = f7["concrete_markers"]
        has_threshold = any(
            re.fullmatch(r"(?i).*\d+.*(ms|seconds?|minutes?|hours?|days?|"
                         r"weeks?|months?|years?|%|kb|mb|gb|bytes?|chars?|"
                         r"characters?|words?|lines?|items?|entries|rows?).*",
                         m) for m in markers
        )
        assert not has_threshold, \
            f"Version number incorrectly matched threshold: {markers}"

    def test_http_status_is_not_a_threshold(self):
        """'HTTP 200' — no unit, no match."""
        rule = _score_rule("Return HTTP 200 on success.")
        f7 = rule["factors"]["F7"]
        markers_lower = [m.lower() for m in f7["concrete_markers"]]
        # No marker should literally be '200' alone
        assert "200" not in markers_lower

    def test_numeric_threshold_lifts_f7_over_adjective(self):
        """Bright-line rule scores higher than the adjective equivalent."""
        sharp = _score_rule("Keep PR titles under 70 characters.")
        fuzzy = _score_rule("Keep PR titles short.")
        assert sharp["factors"]["F7"]["value"] > fuzzy["factors"]["F7"]["value"], (
            f"Bright-line threshold should lift F7 above adjectival equivalent. "
            f"Sharp={sharp['factors']['F7']['value']}, "
            f"Fuzzy={fuzzy['factors']['F7']['value']}"
        )


# ---------------------------------------------------------------------------
# Pipeline integration
# ---------------------------------------------------------------------------

class TestPipelineIntegration:
    def test_factors_added(self):
        rule = _score_rule("Use `React.memo` for expensive components")
        assert "F7" in rule["factors"]
        # F6 is absorbed into F7; the pipeline does not add a separate F6
        assert "F6" not in rule["factors"]

    def test_prior_factors_preserved(self):
        rule = _score_rule("ALWAYS validate input")
        assert "F1" in rule["factors"]
        assert "F2" in rule["factors"]
        assert "F4" in rule["factors"]

    def test_schema_carried_forward(self):
        data = {
            "schema_version": "0.1", "pipeline_version": "0.1.0",
            "project_context": {"stack": ["react"]},
            "config": {}, "source_files": [],
            "rules": [{
                "id": "R001", "file_index": 0, "text": "Always test",
                "line_start": 1, "line_end": 1, "category": "mandate",
                "referenced_entities": [], "staleness": {"gated": False, "missing_entities": []},
                "factors": {"F1": {"value": 0.85}, "F2": {"value": 0.85}, "F4": {"value": 0.95}},
            }],
        }
        result = run_script("score_semi.py", stdin_data=data)
        assert result["schema_version"] == "0.1"
        assert result["project_context"]["stack"] == ["react"]
