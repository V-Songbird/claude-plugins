"""Tests for build_prompt.py — prompt assembly verification."""

import json
import subprocess

import pytest
from conftest import run_script_raw, PYTHON, SCRIPTS_DIR


def _build_prompt(data: dict) -> str:
    """Run build_prompt.py and return the prompt text."""
    result = subprocess.run(
        [PYTHON, str(SCRIPTS_DIR / "build_prompt.py")],
        input=json.dumps(data), capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"build_prompt.py failed: {result.stderr}"
    return result.stdout


def _make_scored_data(rules: list[dict] | None = None) -> dict:
    """Build minimal scored_semi.json for prompt testing."""
    if rules is None:
        rules = [
            {
                "id": "R001", "file_index": 0, "text": "ALWAYS validate input.",
                "line_start": 3, "line_end": 3, "category": "mandate",
                "referenced_entities": [], "staleness": {"gated": False, "missing_entities": []},
                "factors": {
                    "F1": {"value": 1.0, "method": "lookup"},
                    "F2": {"value": 0.85, "method": "classify"},
                    "F4": {"value": 0.95, "method": "glob_match"},
                    "F7": {"value": 0.80, "method": "count", "concrete_count": 1, "abstract_count": 0},
                },
            },
        ]
    return {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_context": {
            "stack": ["typescript", "react"],
            "always_loaded_files": ["CLAUDE.md"],
            "glob_scoped_files": [
                {"path": ".claude/rules/api.md", "globs": ["src/api/**/*.ts"], "glob_match_count": 5}
            ],
        },
        "config": {},
        "source_files": [
            {"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
             "default_category": "mandate", "line_count": 20, "always_loaded": True},
        ],
        "rules": rules,
    }


class TestRubricsPresent:
    def test_f3_rubric_present(self):
        prompt = _build_prompt(_make_scored_data())
        assert "Trigger-Action Distance" in prompt
        assert "Level 4" in prompt or "Immediate" in prompt
        assert "Level 0" in prompt or "No trigger" in prompt

    def test_f8_rubric_present(self):
        prompt = _build_prompt(_make_scored_data())
        assert "Enforceability Ceiling" in prompt
        assert "Not mechanically enforceable" in prompt or "Level 3" in prompt


class TestProjectContext:
    def test_project_context_included(self):
        prompt = _build_prompt(_make_scored_data())
        assert "Project Context" in prompt
        assert "typescript" in prompt
        assert "react" in prompt

    def test_glob_scoped_files_listed(self):
        prompt = _build_prompt(_make_scored_data())
        assert "src/api/**/*.ts" in prompt

    def test_trigger_note_present(self):
        prompt = _build_prompt(_make_scored_data())
        assert "trigger context" in prompt.lower() or "trigger anchored" in prompt.lower()


class TestToolingContext:
    def test_tooling_context_present(self):
        """When tooling data is in project_context, prompt includes it."""
        data = _make_scored_data()
        data["project_context"]["tooling"] = {
            "eslint": True, "prettier": True, "git_hooks": False,
            "typescript": True, "ruff": False, "flake8": False, "pre_commit": False,
        }
        prompt = _build_prompt(data)
        assert "Configured enforcement" in prompt
        assert "eslint" in prompt
        assert "prettier" in prompt

    def test_tooling_context_absent_graceful(self):
        """When no tooling data in project_context, prompt still renders."""
        data = _make_scored_data()
        # project_context has no "tooling" key
        prompt = _build_prompt(data)
        assert "No enforcement tooling detected" in prompt or "Not detected" in prompt


class TestFlaggedRules:
    def test_flagged_rules_annotated(self):
        rules = [
            {
                "id": "R001", "file_index": 0, "text": "Try to prefer functional components when possible.",
                "line_start": 5, "line_end": 5, "category": "mandate",
                "referenced_entities": [], "staleness": {"gated": False, "missing_entities": []},
                "factors": {
                    "F1": {"value": 0.20, "method": "lookup"},
                    "F2": {"value": 0.35, "method": "classify"},
                    "F4": {"value": 0.95, "method": "always_universal"},
                    "F7": {"value": 0.35, "method": "count", "concrete_count": 1, "abstract_count": 1},
                },
                "factor_confidence_low": ["F7"],
            },
        ]
        prompt = _build_prompt(_make_scored_data(rules))
        assert "F7:" in prompt
        assert "concrete:1" in prompt or "concrete_count" in prompt

    def test_f1_extraction_failures_flagged(self):
        rules = [
            {
                "id": "R001", "file_index": 0, "text": "Stack: generic, TypeScript",
                "line_start": 1, "line_end": 1, "category": "mandate",
                "referenced_entities": [], "staleness": {"gated": False, "missing_entities": []},
                "factors": {
                    "F1": {"value": None, "method": "extraction_failed"},
                    "F2": {"value": 0.85, "method": "classify"},
                    "F4": {"value": 0.95, "method": "always_universal"},
                    "F7": {"value": 0.05, "method": "count", "concrete_count": 0, "abstract_count": 0},
                },
                "factor_confidence_low": ["F1"],
            },
        ]
        prompt = _build_prompt(_make_scored_data(rules))
        assert "F1:" in prompt
        assert "extraction_failed" in prompt


class TestRulesTable:
    def test_ids_unique(self):
        rules = [
            {
                "id": f"R{i:03d}", "file_index": 0, "text": f"Rule {i}.",
                "line_start": i, "line_end": i, "category": "mandate",
                "referenced_entities": [], "staleness": {"gated": False, "missing_entities": []},
                "factors": {
                    "F1": {"value": 0.85}, "F2": {"value": 0.85},
                    "F4": {"value": 0.95}, "F7": {"value": 0.80},
                },
            }
            for i in range(1, 4)
        ]
        prompt = _build_prompt(_make_scored_data(rules))
        # Extract just the rules table (between "## Rules" and "## Response")
        table_start = prompt.find("## Rules")
        table_end = prompt.find("## Response")
        table = prompt[table_start:table_end] if table_start >= 0 and table_end >= 0 else prompt
        assert table.count("R001") == 1
        assert table.count("R002") == 1
        assert table.count("R003") == 1

    def test_response_format_specified(self):
        prompt = _build_prompt(_make_scored_data())
        assert "ONLY" in prompt
        assert "JSON array" in prompt
        assert "no markdown fences" in prompt.lower() or "no prose" in prompt.lower()
