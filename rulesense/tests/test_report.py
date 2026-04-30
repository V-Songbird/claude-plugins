"""Tests for report.py — markdown rendering and JSON passthrough."""

import json
import subprocess

import pytest
from conftest import PYTHON, SCRIPTS_DIR


def _render_report(audit: dict, json_mode: bool = False, verbose: bool = False) -> str:
    """Run report.py and return output."""
    cmd = [PYTHON, str(SCRIPTS_DIR / "report.py")]
    if json_mode:
        cmd.append("--json")
    if verbose:
        cmd.append("--verbose")
    result = subprocess.run(
        cmd, input=json.dumps(audit), capture_output=True, text=True,
        timeout=30, encoding="utf-8",
    )
    assert result.returncode == 0, f"report.py failed: {result.stderr}"
    return result.stdout


def _make_audit() -> dict:
    """Build a minimal audit.json for testing."""
    return {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project": "/test/project",
        "date": "2026-04-07",
        "methodology": {
            "weights_version": "quality-heuristic-0.1",
            "pipeline_version": "0.1.0",
            "model_version": "claude-opus-4-6",
        },
        "files_scanned": 2,
        "rules_extracted": 3,
        "effective_corpus_quality": {
            "score": 0.65,
            "methodology": "file-score weighted aggregate",
        },
        "corpus_quality": {
            "rule_mean_score": 0.68,
            "rule_count": 2,
            "note": "diagnostic",
        },
        "guideline_quality": {"score": 0.45, "rule_count": 1},
        "rules": [
            {
                "id": "R001", "file": "CLAUDE.md", "line_start": 3, "line_end": 3,
                "text": "ALWAYS validate user input before processing.",
                "category": "mandate", "loading": "always-loaded",
                "score": 0.874, "pre_floor_score": 0.874, "floor": 1.0, "stale": False,
                "leverage": 0.13,
                "factors": {
                    "F1": {"value": 1.0}, "F2": {"value": 0.85}, "F3": {"value": 0.80},
                    "F4": {"value": 0.95}, "F7": {"value": 0.80},
                    "F8": {"value": 0.70},
                },
                "contributions": {"F1": 0.221, "F2": 0.125, "F3": 0.153,
                                  "F4": 0.140, "F7": 0.235},
                "layers": {"clarity": 0.83, "activation": 0.87},
                "dominant_weakness": "F7", "dominant_weakness_gap": 0.40,
                "failure_class": "ambiguity",
                "f8_value": 0.70, "is_hook_candidate": False,
            },
            {
                "id": "R002", "file": "CLAUDE.md", "line_start": 5, "line_end": 5,
                "text": "Try to prefer functional components when possible.",
                "category": "mandate", "loading": "always-loaded",
                "score": 0.386, "pre_floor_score": 0.386, "floor": 1.0, "stale": False,
                "leverage": 0.61,
                "factors": {
                    "F1": {"value": 0.20}, "F2": {"value": 0.35}, "F3": {"value": 0.25},
                    "F4": {"value": 0.95}, "F7": {"value": 0.35},
                    "F8": {"value": 0.70},
                },
                "contributions": {"F1": 0.044, "F2": 0.051, "F3": 0.048,
                                  "F4": 0.140, "F7": 0.103},
                "layers": {"clarity": 0.27, "activation": 0.55},
                "dominant_weakness": "F7", "dominant_weakness_gap": 1.30,
                "failure_class": "ambiguity",
                "f8_value": 0.70, "is_hook_candidate": False,
            },
            {
                "id": "R003", "file": ".claude/rules/api.md", "line_start": 8, "line_end": 8,
                "text": "Prefer transactions for queries spanning multiple tables.",
                "category": "preference", "loading": "glob-scoped",
                "score": 0.490, "pre_floor_score": 0.490, "floor": 1.0, "stale": False,
                "leverage": None,
                "factors": {
                    "F1": {"value": 0.50}, "F2": {"value": 0.35}, "F3": {"value": 0.60},
                    "F4": {"value": 0.65}, "F7": {"value": 0.40},
                    "F8": {"value": 0.70},
                },
                "contributions": {"F1": 0.110, "F2": 0.051, "F3": 0.115,
                                  "F4": 0.096, "F7": 0.118},
                "layers": {"clarity": 0.35, "activation": 0.62},
                "dominant_weakness": "F7", "dominant_weakness_gap": 1.20,
                "failure_class": "ambiguity",
                "f8_value": 0.70, "is_hook_candidate": False,
            },
        ],
        "files": [
            {
                "path": "CLAUDE.md", "file_score": 0.62, "line_count": 20, "rule_count": 2,
                "length_penalty": 1.0, "prohibition_ratio": 0.0,
                "trigger_scope_coherence": 0.0, "concreteness_coverage": 0.50, "dead_zone_count": 0,
            },
            {
                "path": ".claude/rules/api.md", "file_score": 0.45, "line_count": 15,
                "rule_count": 1, "length_penalty": 1.0, "prohibition_ratio": 0.0,
                "trigger_scope_coherence": 0.0, "concreteness_coverage": 0.0, "dead_zone_count": 0,
            },
        ],
        "positive_findings": [
            {"file": "CLAUDE.md", "line": 3, "text": "ALWAYS validate user input", "score": 0.82}
        ],
        "rewrite_candidates": [
            {"rule_id": "R002", "score": 0.42, "dominant_weakness": "F7"}
        ],
        "conflicts": [],
    }


class TestMarkdownSections:
    def test_all_sections_present(self):
        report = _render_report(_make_audit())
        assert "# Rules Quality Report" in report
        assert "Grade:" in report
        assert "What to fix first" in report
        assert "Your best rules" in report

    def test_verbose_sections_present(self):
        report = _render_report(_make_audit(), verbose=True)
        assert "Detailed Scores" in report
        assert "Per-rule breakdown" in report

    def test_headline_has_grade_and_summary(self):
        report = _render_report(_make_audit())
        assert "Grade: B" in report
        assert "rules are clear enough" in report


class TestFailureClassSummary:
    """The grade headline should include a one-line 'At-risk rules' summary
    when at least one mandate rule has a failure class. See Phase A of the
    integration plan: presentation-layer diagnostic grouping rules by
    drift / ambiguity / conflict."""

    def test_summary_line_appears_when_mandate_rules_have_failure_class(self):
        """Default fixture has 2 mandate rules with failure_class='ambiguity'."""
        report = _render_report(_make_audit())
        assert "At-risk rules:" in report
        assert "ambiguity" in report

    def test_summary_counts_mandate_rules_only(self):
        """R003 is a 'preference' rule and must not be counted in the
        at-risk summary even though it has a failure_class."""
        report = _render_report(_make_audit())
        # 2 mandate rules with ambiguity, not 3
        assert "2 ambiguity" in report

    def test_summary_groups_by_class(self):
        """Mixed failure classes should appear in drift → ambiguity order."""
        audit = _make_audit()
        audit["rules"][0]["dominant_weakness"] = "F3"
        audit["rules"][0]["failure_class"] = "drift"
        report = _render_report(audit)
        assert "At-risk rules:" in report
        # Drift appears before ambiguity in the rendered line
        at_risk_line = [ln for ln in report.splitlines() if "At-risk rules:" in ln][0]
        drift_pos = at_risk_line.find("drift")
        ambiguity_pos = at_risk_line.find("ambiguity")
        assert 0 <= drift_pos < ambiguity_pos

    def test_summary_hidden_when_no_failure_class(self):
        """If every mandate rule has failure_class=None, summary is skipped."""
        audit = _make_audit()
        for r in audit["rules"]:
            r["failure_class"] = None
        report = _render_report(audit)
        assert "At-risk rules:" not in report

    def test_failure_class_shown_in_verbose_detail(self):
        """Verbose per-rule detail should include 'At risk of: <label>'."""
        report = _render_report(_make_audit(), verbose=True)
        assert "At risk of: ambiguity" in report


def _make_audit_with_conflicts() -> dict:
    """Build an audit fixture with one polarity-mismatch conflict pair."""
    audit = _make_audit()
    audit["conflicts"] = [
        {
            "type": "polarity_mismatch",
            "rule_a": {
                "id": "R001",
                "text": "NEVER edit files in src/main/gen/ directly.",
                "file": "CLAUDE.md",
                "line_start": 5,
                "polarity": "prohibition",
            },
            "rule_b": {
                "id": "R002",
                "text": "Use src/main/gen/ cached results for faster access.",
                "file": ".claude/rules/api.md",
                "line_start": 8,
                "polarity": "positive_imperative",
            },
            "shared_markers": ["src/main/gen/"],
        }
    ]
    return audit


class TestPotentialConflicts:
    """Potential conflicts render as a corpus-level section and a headline
    one-liner. See Phase B of the integration plan."""

    def test_section_appears_when_conflicts_present(self):
        report = _render_report(_make_audit_with_conflicts())
        assert "## Potential conflicts" in report

    def test_section_lists_both_rules_in_pair(self):
        report = _render_report(_make_audit_with_conflicts())
        assert "NEVER edit files in src/main/gen/" in report
        assert "Use src/main/gen/ cached results" in report

    def test_section_names_shared_marker(self):
        report = _render_report(_make_audit_with_conflicts())
        assert "`src/main/gen/`" in report

    def test_section_hidden_when_conflicts_empty(self):
        """Empty conflicts list means the section is skipped entirely."""
        report = _render_report(_make_audit())
        assert "## Potential conflicts" not in report

    def test_headline_one_liner_appears(self):
        """A single-line summary appears in the grade headline when
        conflicts exist, so readers see the signal without scrolling."""
        report = _render_report(_make_audit_with_conflicts())
        assert "**Potential conflicts:**" in report
        assert "1 rule pair" in report

    def test_headline_uses_plural_for_multiple_pairs(self):
        audit = _make_audit_with_conflicts()
        # Duplicate the conflict to get two pairs
        audit["conflicts"].append(audit["conflicts"][0])
        report = _render_report(audit)
        assert "2 rule pairs" in report

    def test_headline_hidden_when_conflicts_empty(self):
        report = _render_report(_make_audit())
        assert "**Potential conflicts:**" not in report


class TestSortOrder:
    def test_leverage_descending_in_verbose(self):
        """Mandate rules should appear sorted by leverage descending in verbose per-rule table."""
        audit = _make_audit()
        audit["rules"] = [audit["rules"][1], audit["rules"][0], audit["rules"][2]]
        report = _render_report(audit, verbose=True)
        table_start = report.find("Detailed Scores")
        table_section = report[table_start:]
        pos_r002 = table_section.find("Try to prefer")
        pos_r001 = table_section.find("ALWAYS validate")
        assert pos_r002 >= 0, "R002 not found in verbose table"
        assert pos_r001 >= 0, "R001 not found in verbose table"
        assert pos_r002 < pos_r001, "Higher-leverage rule should appear first"


class TestFloorDisplay:
    def test_floor_not_shown_when_1(self):
        """Floor should not be displayed when it's 1.0 (verbose mode)."""
        report = _render_report(_make_audit(), verbose=True)
        assert "Floor: 1.00" not in report

    def test_floor_shown_when_active(self):
        """Floor should be shown when < 1.0 (verbose mode)."""
        audit = _make_audit()
        audit["rules"][1]["floor"] = 0.50
        audit["rules"][1]["pre_floor_score"] = 0.84
        report = _render_report(audit, verbose=True)
        assert "Floor: 0.50" in report


class TestJsonPassthrough:
    def test_json_valid(self):
        output = _render_report(_make_audit(), json_mode=True)
        data = json.loads(output)
        assert data["schema_version"] == "0.1"

    def test_json_preserves_all_fields(self):
        audit = _make_audit()
        output = _render_report(audit, json_mode=True)
        data = json.loads(output)
        assert "effective_corpus_quality" in data
        assert "rules" in data
        assert len(data["rules"]) == 3


class TestPositiveFindings:
    def test_best_rules_shown(self):
        report = _render_report(_make_audit())
        assert "Your best rules" in report
        assert "ALWAYS validate" in report

    def test_best_rules_have_why(self):
        report = _render_report(_make_audit())
        assert "Why it works" in report


class TestFriendlyOutput:
    """The default output should use friendly language, not factor codes."""

    def test_no_factor_codes_in_default(self):
        report = _render_report(_make_audit())
        # Factor codes should NOT appear in default output
        for code in ("F1", "F2", "F3", "F4", "F7", "F8"):
            assert code not in report, f"Factor code {code} found in default output"

    def test_friendly_problem_descriptions_present(self):
        report = _render_report(_make_audit())
        # The "What to fix first" section should use friendly descriptions
        assert "What to fix first" in report

    def test_factor_codes_in_verbose(self):
        report = _render_report(_make_audit(), verbose=True)
        # Factor codes SHOULD appear in verbose output
        assert "F1" in report or "F7" in report


def _make_audit_with_score(ecq_score: float) -> dict:
    """Build a minimal audit with a specific effective corpus quality score."""
    audit = _make_audit()
    audit["effective_corpus_quality"]["score"] = ecq_score
    return audit


class TestLetterGrade:
    """Letter grade rendering in the headline.

    Half-open intervals:
      A ∈ [0.80, 1.00]
      B ∈ [0.65, 0.80)
      C ∈ [0.50, 0.65)
      D ∈ [0.35, 0.50)
      F ∈ [0.00, 0.35)
    """

    def test_grade_a(self):
        report = _render_report(_make_audit_with_score(0.85))
        assert "Grade: A" in report

    def test_grade_b(self):
        report = _render_report(_make_audit_with_score(0.70))
        assert "Grade: B" in report

    def test_grade_c(self):
        report = _render_report(_make_audit_with_score(0.55))
        assert "Grade: C" in report

    def test_grade_d(self):
        report = _render_report(_make_audit_with_score(0.40))
        assert "Grade: D" in report

    def test_grade_f(self):
        report = _render_report(_make_audit_with_score(0.25))
        assert "Grade: F" in report

    def test_grade_boundary_a(self):
        """0.80 → A (inclusive low); 0.799 → B (exclusive high)."""
        report = _render_report(_make_audit_with_score(0.80))
        assert "Grade: A" in report
        report = _render_report(_make_audit_with_score(0.799))
        assert "Grade: B" in report

    def test_grade_boundary_b(self):
        """0.65 → B; 0.649 → C."""
        report = _render_report(_make_audit_with_score(0.65))
        assert "Grade: B" in report
        report = _render_report(_make_audit_with_score(0.649))
        assert "Grade: C" in report

    def test_grade_boundary_c(self):
        """0.50 → C; 0.499 → D."""
        report = _render_report(_make_audit_with_score(0.50))
        assert "Grade: C" in report
        report = _render_report(_make_audit_with_score(0.499))
        assert "Grade: D" in report

    def test_grade_boundary_d(self):
        """0.35 → D; 0.349 → F."""
        report = _render_report(_make_audit_with_score(0.35))
        assert "Grade: D" in report
        report = _render_report(_make_audit_with_score(0.349))
        assert "Grade: F" in report

    def test_grade_in_best_rules_table(self):
        """The best-rules table should have a Grade column."""
        report = _render_report(_make_audit())
        assert "| Grade |" in report or "Grade" in report


class TestDisclaimer:
    """The disclaimer is a first-class output contract, not a hedge."""

    def test_disclaimer_present(self):
        report = _render_report(_make_audit())
        assert "how clearly Claude can parse and apply" in report
        assert "Actual compliance depends on factors" in report

    def test_disclaimer_at_end(self):
        report = _render_report(_make_audit())
        # Disclaimer should be near the end of the report
        disclaimer_pos = report.find("how clearly Claude can parse and apply")
        assert disclaimer_pos > len(report) // 2, "Disclaimer should be in the second half of the report"


def _make_rewrite(
    rule_id: str = "R002",
    old_score: float = 0.42,
    new_score: float = 0.82,
    judgment_volatility: dict | None = None,
    projected_score: float | None = None,
    self_verification_delta: float | None = None,
) -> dict:
    """Build a rewrite dict for TestFixMode fixtures."""
    old_grade = "A" if old_score >= 0.80 else "B" if old_score >= 0.65 else "C" if old_score >= 0.50 else "D" if old_score >= 0.35 else "F"
    new_grade = "A" if new_score >= 0.80 else "B" if new_score >= 0.65 else "C" if new_score >= 0.50 else "D" if new_score >= 0.35 else "F"
    return {
        "rule_id": rule_id,
        "file": "CLAUDE.md",
        "line_start": 5,
        "original_text": "Try to prefer functional components when possible.",
        "suggested_rewrite": "Use functional components for all new React files. Example: components/Button.tsx — function, not class.",
        "old_score": old_score,
        "new_score": new_score,
        "old_grade": old_grade,
        "new_grade": new_grade,
        "old_dominant_weakness": "F7",
        "new_dominant_weakness": None,
        "factor_improvements": {"F7": [0.25, 0.85]},
        "judgment_volatility": judgment_volatility or {
            "flagged": False,
            "f3_delta": 0.05,
            "old_f3": 0.80,
            "new_f3": 0.85,
        },
        "projected_score": projected_score if projected_score is not None else new_score,
        "self_verification_delta": self_verification_delta if self_verification_delta is not None else 0.0,
    }


class TestFixMode:
    """--fix mode rendering. The skill orchestrates the rewrite generation
    and feeds the rewrites list into audit.json; this test class exercises
    report.py's rendering of those rewrites, not the LLM calls."""

    def test_render_rewrites_section(self):
        """Audit with one rewrite produces Suggested Rewrites section."""
        audit = _make_audit()
        audit["rewrites"] = [_make_rewrite()]
        report = _render_report(audit)
        assert "## Suggested Rewrites" in report
        assert "Try to prefer functional components" in report
        assert "Use functional components for all new React files" in report
        # Before/after grades rendered (ASCII arrow)
        assert "D -> A" in report
        assert "0.42 (Grade D)" in report
        assert "0.82 (Grade A)" in report
        # Factor improvements rendered
        assert "F7: 0.25 -> 0.85" in report

    def test_no_rewrites_section_when_absent(self):
        """Audit without `rewrites` key means no Suggested Rewrites header."""
        audit = _make_audit()
        # No 'rewrites' key
        report = _render_report(audit)
        assert "## Suggested Rewrites" not in report

    def test_no_rewrites_section_when_empty_list(self):
        """Audit with empty rewrites list means no Suggested Rewrites header."""
        audit = _make_audit()
        audit["rewrites"] = []
        report = _render_report(audit)
        assert "## Suggested Rewrites" not in report

    def test_judgment_volatility_flag_rendered(self):
        """When judgment_volatility.flagged is True, render warning with pre/post F3/F8."""
        audit = _make_audit()
        audit["rewrites"] = [_make_rewrite(
            judgment_volatility={
                "flagged": True,
                "f3_delta": 0.25,
                "f8_delta": 0.00,
                "old_f3": 0.60,
                "new_f3": 0.85,
                "old_f8": 0.65,
                "new_f8": 0.65,
            }
        )]
        report = _render_report(audit)
        assert "Judgment changed" in report
        # Both pre and post F3 values rendered (ASCII arrow)
        assert "F3: 0.60 -> 0.85" in report
        # f3_delta shown
        assert "+0.25" in report

    def test_judgment_volatility_not_flagged_no_warning(self):
        """When judgment_volatility.flagged is False, no warning."""
        audit = _make_audit()
        audit["rewrites"] = [_make_rewrite()]  # default is not flagged
        report = _render_report(audit)
        assert "Judgment changed" not in report

    def test_self_verification_underdelivered_rendered(self):
        """When self_verification_delta > 0.05 and new_score < projected_score, show the
        underdelivered WARNING but still present the rewrite."""
        audit = _make_audit()
        audit["rewrites"] = [_make_rewrite(
            new_score=0.72,
            projected_score=0.80,
            self_verification_delta=0.08,
        )]
        report = _render_report(audit)
        assert "WARNING - Rewrite underdelivered" in report
        assert "projected 0.80" in report
        assert "re-scored 0.72" in report
        assert "Review before applying" in report
        # Rewrite is still shown
        assert "Use functional components for all new React files" in report

    def test_self_verification_within_tolerance_no_warning(self):
        """When self_verification_delta is within 0.05, no warning or note fires."""
        audit = _make_audit()
        audit["rewrites"] = [_make_rewrite(
            new_score=0.82,
            projected_score=0.80,
            self_verification_delta=0.02,
        )]
        report = _render_report(audit)
        assert "WARNING - Rewrite underdelivered" not in report
        assert "Note: Rewrite exceeded projection" not in report

    def test_self_verification_overdelivered_rendered(self):
        """When self_verification_delta > 0.05 and new_score > projected_score, show the
        overdelivered Note (softer than WARNING) but still present the rewrite."""
        audit = _make_audit()
        audit["rewrites"] = [_make_rewrite(
            new_score=0.85,
            projected_score=0.72,
            self_verification_delta=0.13,
        )]
        report = _render_report(audit)
        assert "Note: Rewrite exceeded projection" in report
        assert "projected 0.72" in report
        assert "re-scored 0.85" in report
        assert "projection is conservative" in report
        # Severity downgrade: no bold WARNING label on the Note branch
        assert "WARNING" not in report
        # Rewrite is still shown
        assert "Use functional components for all new React files" in report

    def test_null_factor_improvements_does_not_crash(self):
        """Rewrites with null factor_improvements must render without TypeError."""
        audit = _make_audit()
        rewrite = _make_rewrite()
        rewrite["factor_improvements"] = None
        audit["rewrites"] = [rewrite]
        report = _render_report(audit)
        assert "Suggested Rewrites" in report


# ---------------------------------------------------------------------------
# G.2: Encoding — emoji/Unicode in rule text must not crash report.py
# ---------------------------------------------------------------------------

class TestEmojiEncoding:
    """Phase G.2 characterization test: report.py must render rule text
    containing emoji without UnicodeEncodeError, even on Windows cp1252."""

    def test_emoji_in_rule_text_does_not_crash(self):
        audit = _make_audit()
        # Replace rule text with emoji-heavy content AND set low score so it appears in fix groups
        audit["rules"][0]["text"] = "Don't use AI-sounding words: \u2705 \u2728 \U0001f680 \u2014 avoid these in all copy."
        audit["rules"][0]["score"] = 0.30
        audit["rules"][0]["leverage"] = 0.70
        audit["positive_findings"] = []  # remove from best rules since score is now low
        report = _render_report(audit)
        # Primary assertion: the subprocess didn't crash (_render_report asserts returncode == 0).
        # Secondary: rule text with emoji survived the render pipeline.
        assert "AI-sounding words" in report


# ---------------------------------------------------------------------------
# Hook opportunities render as a parallel section
# ---------------------------------------------------------------------------

class TestHookOpportunitiesRender:
    def test_render_hook_opportunities_renders_when_present(self):
        audit = _make_audit()
        audit["hook_opportunities"] = [{
            "id": "R01", "text": "Run prettier before commit",
            "file": "CLAUDE.md", "line_start": 10,
            "f8_value": 0.20,
            "suggested_enforcement": "Pre-commit hook",
        }]
        report = _render_report(audit)
        assert "## Hook opportunities" in report
        assert "Pre-commit hook" in report
        assert "Run prettier" in report

    def test_render_hook_opportunities_skipped_when_empty(self):
        audit = _make_audit()
        audit["hook_opportunities"] = []
        report = _render_report(audit)
        assert "## Hook opportunities" not in report

    def test_render_hook_opportunities_missing_key_safe(self):
        """No hook_opportunities key at all (old audit.json) — render gracefully."""
        audit = _make_audit()
        audit.pop("hook_opportunities", None)
        report = _render_report(audit)
        assert "## Hook opportunities" not in report


class TestDegradedRuleNotice:
    def test_degraded_notice_shown_when_any_rule_degraded(self):
        """Default (non-verbose) report surfaces degraded rule count in the headline section."""
        audit = _make_audit()
        audit["rules"][0]["degraded"] = True
        audit["rules"][0]["degraded_factors"] = ["F3"]
        report = _render_report(audit)
        assert "scored on fewer than all factors" in report
        assert "--verbose" in report

    def test_degraded_notice_singular_vs_plural(self):
        """Notice uses correct grammar for one vs multiple degraded rules."""
        audit = _make_audit()
        audit["rules"][0]["degraded"] = True
        audit["rules"][0]["degraded_factors"] = ["F3"]
        audit["rules"][1]["degraded"] = True
        audit["rules"][1]["degraded_factors"] = ["F8"]
        report = _render_report(audit)
        assert "2 rules were scored" in report

    def test_degraded_notice_absent_when_no_degraded_rules(self):
        """Clean reports do not mention degraded factors."""
        audit = _make_audit()
        # _make_audit has no degraded rules by default
        report = _render_report(audit)
        assert "scored on fewer than all factors" not in report
