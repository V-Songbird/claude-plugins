"""Tests for generate_overview.py — HTML overview generation."""

import json
import os
import re
import subprocess

import pytest
from conftest import PYTHON, SCRIPTS_DIR


GENERATE_OVERVIEW = str(SCRIPTS_DIR / "generate_overview.py")


def _run(input_path: str, output_path: str,
         timeout: int = 30) -> subprocess.CompletedProcess:
    """Run generate_overview.py and return the CompletedProcess."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [PYTHON, GENERATE_OVERVIEW, "--input", input_path, "--output", output_path],
        capture_output=True, text=True, encoding="utf-8",
        env=env, timeout=timeout,
    )


def _make_rule(rule_id: str, score: float, category: str = "mandate",
               dominant_weakness: str | None = "F7",
               text: str | None = None) -> dict:
    """Build a minimal rule dict for overview testing."""
    return {
        "id": rule_id,
        "file_index": 0,
        "file": "CLAUDE.md",
        "text": text or f"Rule {rule_id} text.",
        "line_start": 5,
        "line_end": 5,
        "category": category,
        "score": score,
        "dominant_weakness": dominant_weakness if score < 0.65 else None,
        "factors": {
            "F1": {"value": 0.85, "method": "lookup"},
            "F2": {"value": 0.85, "method": "classify"},
            "F3": {"value": 0.70, "method": "judgment"},
            "F4": {"value": 0.95, "method": "glob_match"},
            "F7": {"value": 0.30 if score < 0.50 else 0.80, "method": "count"},
            "F8": {"value": 0.60, "method": "judgment"},
        },
    }


def _make_overview_data(
    rules: list[dict] | None = None,
    intentions: list[dict] | None = None,
    gaps: list[str] | None = None,
    org: dict | None = None,
    positive_findings: list[dict] | None = None,
    files: list[dict] | None = None,
    ecq_score: float = 0.72,
) -> dict:
    """Build a minimal overview_data.json for testing."""
    if rules is None:
        rules = [
            _make_rule("R001", 0.88),
            _make_rule("R002", 0.72),
            _make_rule("R003", 0.45, dominant_weakness="F7"),
        ]
    if positive_findings is None:
        positive_findings = [
            {"file": "CLAUDE.md", "line": 5,
             "text": r["text"][:100], "score": r["score"]}
            for r in rules if r.get("score", 0) >= 0.80
        ]
    if files is None:
        files = [
            {"path": "CLAUDE.md", "file_score": ecq_score, "line_count": 100,
             "rule_count": len(rules), "length_penalty": 1.0,
             "prohibition_ratio": 0.0, "trigger_scope_coherence": 0.0,
             "concreteness_coverage": 0.50, "dead_zone_count": 0},
        ]

    audit = {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project": "/test/project",
        "files_scanned": len(files),
        "rules_extracted": len(rules),
        "effective_corpus_quality": {"score": ecq_score},
        "corpus_quality": {"rule_mean_score": ecq_score},
        "guideline_quality": {"score": 0.55},
        "rules": rules,
        "files": files,
        "positive_findings": positive_findings,
        "rewrite_candidates": [],
    }

    return {
        "audit": audit,
        "intentions": intentions or [
            {"theme": "Code style", "count": 2, "rule_ids": ["R001", "R002"],
             "avg_grade": "B"},
            {"theme": "Testing", "count": 1, "rule_ids": ["R003"],
             "avg_grade": "D"},
        ],
        "coverage_gaps": gaps if gaps is not None else ["accessibility", "performance budgets"],
        "organization": org or {
            "claude_md_rules": 3,
            "scoped_rules": 0,
            "always_loaded_rules_in_rules_dir": 0,
            "claude_md_lines": 100,
        },
        "generated_at": "2026-04-14T12:00:00Z",
    }


def _write_and_run(tmp_path, data: dict) -> tuple[str, subprocess.CompletedProcess]:
    """Write overview data to tmp, run generate_overview.py, return (html_content, result)."""
    input_path = str(tmp_path / "overview_data.json")
    output_path = str(tmp_path / "overview.html")
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    result = _run(input_path, output_path)
    if result.returncode != 0:
        return "", result
    with open(output_path, encoding="utf-8") as f:
        return f.read(), result


class TestGenerateOverview:
    """Tests for generate_overview.py."""

    def test_produces_valid_html(self, tmp_path):
        """generate_overview.py with standard data produces valid HTML."""
        data = _make_overview_data()
        html_content, result = _write_and_run(tmp_path, data)

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert html_content.startswith("<!DOCTYPE html>")
        assert "<html" in html_content
        assert "</html>" in html_content
        # Grade should be B (ecq_score=0.72)
        assert "grade-b" in html_content

    def test_all_sections_present(self, tmp_path):
        """The generated HTML contains all expected section headings."""
        data = _make_overview_data()
        html_content, result = _write_and_run(tmp_path, data)

        assert result.returncode == 0
        for heading in [
            "Grade Distribution",
            "What Your Rules Cover",
            "Coverage Gaps",
            "How Rules Are Organized",
            "Per-File Breakdown",
            "Strongest Rules",
            "Rules That Need Work",
        ]:
            assert heading in html_content, f"Missing section: {heading}"

    def test_grade_colors_applied(self, tmp_path):
        """Grade badges have the correct CSS classes for their grade levels."""
        rules = [
            _make_rule("R001", 0.90),   # A
            _make_rule("R002", 0.70),   # B
            _make_rule("R003", 0.55),   # C
            _make_rule("R004", 0.40, dominant_weakness="F3"),  # D
            _make_rule("R005", 0.20, dominant_weakness="F7"),  # F
        ]
        data = _make_overview_data(rules=rules, ecq_score=0.55)
        html_content, result = _write_and_run(tmp_path, data)

        assert result.returncode == 0
        assert "grade-a" in html_content
        assert "grade-b" in html_content
        assert "grade-c" in html_content
        assert "grade-d" in html_content
        assert "grade-f" in html_content

    def test_no_external_dependencies(self, tmp_path):
        """HTML has no external script/link/img references."""
        data = _make_overview_data()
        html_content, result = _write_and_run(tmp_path, data)

        assert result.returncode == 0
        # No external URLs in src or href attributes
        assert not re.search(r'<script[^>]+src="https?://', html_content)
        assert not re.search(r'<link[^>]+href="https?://', html_content)
        assert not re.search(r'<img[^>]+src="https?://', html_content)

    def test_empty_rules_handled(self, tmp_path):
        """Overview with 0 rules produces valid HTML without crashing."""
        data = _make_overview_data(
            rules=[],
            positive_findings=[],
            files=[],
            intentions=[],
            gaps=[],
            ecq_score=0,
        )
        html_content, result = _write_and_run(tmp_path, data)

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert html_content.startswith("<!DOCTYPE html>")
        assert "0 of 0 rules" in html_content

    def test_timestamp_rendered(self, tmp_path):
        """The generated_at timestamp appears in the output."""
        data = _make_overview_data()
        html_content, result = _write_and_run(tmp_path, data)

        assert result.returncode == 0
        assert "2026-04-14T12:00:00Z" in html_content

    def test_html_escaping(self, tmp_path):
        """Rule text containing HTML special chars is escaped."""
        xss_text = '<script>alert("xss")</script> & "quotes"'
        rules = [_make_rule("R001", 0.30, text=xss_text, dominant_weakness="F7")]
        data = _make_overview_data(rules=rules, positive_findings=[], ecq_score=0.30)
        html_content, result = _write_and_run(tmp_path, data)

        assert result.returncode == 0
        # Raw script tag must not appear
        assert "<script>alert" not in html_content
        # Escaped versions should be present
        assert "&lt;script&gt;" in html_content
        assert "&amp;" in html_content

    def test_normalize_nonstandard_grades(self, tmp_path):
        """Intentions with non-standard grades (E, A+) render with valid CSS classes."""
        data = _make_overview_data(
            intentions=[
                {"theme": "Style", "count": 3, "rule_ids": ["R001"], "avg_grade": "E"},
                {"theme": "Testing", "count": 2, "rule_ids": ["R002"], "avg_grade": "A+"},
                {"theme": "Docs", "count": 1, "rule_ids": ["R003"], "avg_grade": "B"},
            ],
        )
        html_content, result = _write_and_run(tmp_path, data)

        assert result.returncode == 0
        # E should map to D
        assert "grade-d" in html_content
        # A+ should map to A
        assert "grade-a" in html_content
        # B stays B
        assert "grade-b" in html_content
        # No gray fallback badges — var(--muted) should not appear as a background
        assert 'background:var(--muted)' not in html_content
