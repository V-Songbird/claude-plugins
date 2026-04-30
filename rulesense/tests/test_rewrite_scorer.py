"""Tests for rewrite_scorer.py — the --fix mode helper script."""

import json
import os
import tempfile

import pytest
from conftest import run_script, FIXTURES_DIR, PYTHON, SCRIPTS_DIR

import subprocess


def _run_rewrite_scorer(mode: str, *args: str) -> dict | list:
    """Run rewrite_scorer.py with the given mode and args."""
    cmd = [PYTHON, str(SCRIPTS_DIR / "rewrite_scorer.py"), mode] + list(args)
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=60, encoding="utf-8",
    )
    assert result.returncode == 0, f"rewrite_scorer.py {mode} failed: {result.stderr}"
    return json.loads(result.stdout)


def _run_rewrite_scorer_raw(mode: str, *args: str):
    """Run rewrite_scorer.py and return the raw CompletedProcess (stderr inspectable)."""
    cmd = [PYTHON, str(SCRIPTS_DIR / "rewrite_scorer.py"), mode] + list(args)
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=60, encoding="utf-8",
    )


class TestScoreRewrites:
    """Phase 1: --score-rewrites produces mechanically scored output."""

    def test_score_single_rewrite(self, tmp_path):
        """A single rewrite should be mechanically scored with F1/F2/F4/F7."""
        # Build minimal audit.json
        audit = {
            "schema_version": "0.1",
            "rules": [
                {"id": "R001", "text": "Try to prefer functional components.",
                 "score": 0.30, "dominant_weakness": "F1",
                 "factors": {"F1": {"value": 0.20}}, "category": "mandate"},
            ],
            "source_files": [
                {"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
                 "default_category": "mandate", "line_count": 10, "always_loaded": True},
            ],
            "project_context": {"stack": []},
            "config": {},
        }
        audit_path = str(tmp_path / "audit.json")
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit, f)

        # Build rewrites input
        rewrites_input = [
            {"rule_id": "R001",
             "original_text": "Try to prefer functional components.",
             "suggested_rewrite": "Use functional components for all new React files.",
             "file": "CLAUDE.md", "line_start": 5,
             "old_score": 0.30, "old_dominant_weakness": "F1",
             "projected_score": 0.75},
        ]
        input_path = str(tmp_path / "rewrites_input.json")
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(rewrites_input, f)

        result = _run_rewrite_scorer("--score-rewrites", audit_path, input_path)

        assert "rules" in result
        assert len(result["rules"]) == 1
        rule = result["rules"][0]
        assert "factors" in rule
        assert "F1" in rule["factors"]
        assert "F4" in rule["factors"]
        # The rewrite should have a rewrite metadata attachment
        assert "_rewrite_meta" in rule
        assert rule["_rewrite_meta"]["rule_id"] == "R001"
        # F1 should score higher for "Use" (imperative) than "Try to prefer"
        assert rule["factors"]["F1"]["value"] >= 0.70

    def test_score_rewrites_with_output_file(self, tmp_path):
        """--output flag writes result to file instead of stdout."""
        audit = {
            "schema_version": "0.1",
            "rules": [{"id": "R001", "text": "Old rule.", "score": 0.30,
                        "dominant_weakness": "F1", "factors": {}, "category": "mandate"}],
            "source_files": [{"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
                              "default_category": "mandate", "line_count": 10,
                              "always_loaded": True}],
            "project_context": {"stack": []}, "config": {},
        }
        audit_path = str(tmp_path / "audit.json")
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit, f)

        rewrites_input = [
            {"rule_id": "R001", "original_text": "Old rule.",
             "suggested_rewrite": "Use new approach for all files.",
             "file": "CLAUDE.md", "line_start": 5, "old_score": 0.30,
             "old_dominant_weakness": "F1", "projected_score": 0.75},
        ]
        input_path = str(tmp_path / "rewrites_input.json")
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(rewrites_input, f)

        output_path = str(tmp_path / "rewrite_semi.json")
        cmd = [PYTHON, str(SCRIPTS_DIR / "rewrite_scorer.py"),
               "--score-rewrites", audit_path, input_path, "--output", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding="utf-8")
        assert result.returncode == 0, f"Failed: {result.stderr}"

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
        assert "rules" in data
        assert len(data["rules"]) == 1

    def test_empty_rewrites(self, tmp_path):
        """Empty rewrites input should produce empty rules."""
        audit = {"rules": [], "source_files": [], "project_context": {}, "config": {}}
        audit_path = str(tmp_path / "audit.json")
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit, f)

        input_path = str(tmp_path / "rewrites_input.json")
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump([], f)

        result = _run_rewrite_scorer("--score-rewrites", audit_path, input_path)
        assert result["rules"] == []


class TestFinalize:
    """Phase 2: --finalize applies safety gates and produces rewrites list."""

    def test_regression_gate_drops_worse_rewrite(self, tmp_path):
        """A rewrite that scores LOWER than the original should be dropped."""
        # Build scored rewrite data (as if from --score-rewrites + score_semi)
        rewrite_semi = {
            "schema_version": "0.1",
            "pipeline_version": "0.1.0",
            "project_context": {"stack": []},
            "config": {},
            "source_files": [{"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
                              "default_category": "mandate", "line_count": 10,
                              "always_loaded": True}],
            "rules": [{
                "id": "R001", "file_index": 0,
                "text": "A worse rewrite that scores lower.",
                "line_start": 5, "line_end": 5, "category": "mandate",
                "referenced_entities": [],
                "staleness": {"gated": False, "missing_entities": []},
                "factors": {
                    "F1": {"value": 0.20, "method": "lookup"},
                    "F2": {"value": 0.50, "method": "classify"},
                    "F4": {"value": 0.95, "method": "always_universal"},
                    "F7": {"value": 0.10, "method": "count"},
                },
                "_rewrite_meta": {
                    "rule_id": "R001",
                    "original_text": "Original rule text.",
                    "file": "CLAUDE.md", "line_start": 5,
                    "old_score": 0.60,  # original scored higher
                    "old_dominant_weakness": "F7",
                    "projected_score": 0.75,
                },
            }],
        }
        semi_path = str(tmp_path / "rewrite_semi.json")
        with open(semi_path, "w", encoding="utf-8") as f:
            json.dump(rewrite_semi, f)

        # Judgment patches
        patches = {"schema_version": "0.1", "model_version": "test", "patches": {
            "R001": {"F3": {"value": 0.70, "level": 3, "reasoning": "test"},
                     "F8": {"value": 0.60, "level": 2, "reasoning": "test"}},
        }}
        patches_path = str(tmp_path / "patches.json")
        with open(patches_path, "w", encoding="utf-8") as f:
            json.dump(patches, f)

        # Audit with original rule
        audit = {
            "schema_version": "0.1",
            "rules": [{"id": "R001", "score": 0.60, "dominant_weakness": "F7",
                        "factors": {"F1": {"value": 0.50}, "F3": {"value": 0.70},
                                    "F8": {"value": 0.60}},
                        "category": "mandate"}],
        }
        audit_path = str(tmp_path / "audit.json")
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit, f)

        rewrites = _run_rewrite_scorer("--finalize", semi_path, patches_path, audit_path)
        # Regression gate should drop the rewrite (new_score < old_score)
        assert len(rewrites) == 0, f"Expected 0 rewrites (regression), got {len(rewrites)}"

    def test_passing_rewrite_included(self, tmp_path):
        """A rewrite that scores HIGHER than the original should be included."""
        rewrite_semi = {
            "schema_version": "0.1",
            "pipeline_version": "0.1.0",
            "project_context": {"stack": []},
            "config": {},
            "source_files": [{"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
                              "default_category": "mandate", "line_count": 10,
                              "always_loaded": True}],
            "rules": [{
                "id": "R001", "file_index": 0,
                "text": "Use functional components for all new React files.",
                "line_start": 5, "line_end": 5, "category": "mandate",
                "referenced_entities": [],
                "staleness": {"gated": False, "missing_entities": []},
                "factors": {
                    "F1": {"value": 0.85, "method": "lookup"},
                    "F2": {"value": 0.85, "method": "classify"},
                    "F4": {"value": 0.95, "method": "always_universal"},
                    "F7": {"value": 0.80, "method": "count"},
                },
                "_rewrite_meta": {
                    "rule_id": "R001",
                    "original_text": "Try to prefer functional components.",
                    "file": "CLAUDE.md", "line_start": 5,
                    "old_score": 0.30,
                    "old_dominant_weakness": "F1",
                    "projected_score": 0.75,
                },
            }],
        }
        semi_path = str(tmp_path / "rewrite_semi.json")
        with open(semi_path, "w", encoding="utf-8") as f:
            json.dump(rewrite_semi, f)

        patches = {"schema_version": "0.1", "model_version": "test", "patches": {
            "R001": {"F3": {"value": 0.80, "level": 3, "reasoning": "test"},
                     "F8": {"value": 0.65, "level": 2, "reasoning": "test"}},
        }}
        patches_path = str(tmp_path / "patches.json")
        with open(patches_path, "w", encoding="utf-8") as f:
            json.dump(patches, f)

        audit = {
            "schema_version": "0.1",
            "rules": [{"id": "R001", "score": 0.30, "dominant_weakness": "F1",
                        "factors": {"F1": {"value": 0.20}, "F3": {"value": 0.70},
                                    "F8": {"value": 0.60}},
                        "category": "mandate"}],
        }
        audit_path = str(tmp_path / "audit.json")
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit, f)

        rewrites = _run_rewrite_scorer("--finalize", semi_path, patches_path, audit_path)
        assert len(rewrites) == 1
        rw = rewrites[0]
        assert rw["rule_id"] == "R001"
        assert rw["new_score"] > rw["old_score"]
        assert rw["old_grade"] == "F"  # 0.30
        assert rw["new_grade"] in ("A", "B")  # should score well
        assert rw["original_text"] == "Try to prefer functional components."
        assert "functional components" in rw["suggested_rewrite"]


class TestRewriteFragmentationDetection:
    """Regression from Axo-folio dogfood (2026-04-17): a rewrite that contains
    `, and` / `;` / independent-clause em-dashes fragments into orphan rules
    when the rewrite is applied and the next audit re-runs extract.py. Score
    step now flags these up-front so the user revises before applying."""

    def _write_audit_and_input(self, tmp_path, rewrite_text: str):
        audit = {
            "schema_version": "0.1",
            "rules": [{"id": "R001", "text": "Old.", "score": 0.30,
                        "dominant_weakness": "F1", "factors": {}, "category": "mandate"}],
            "source_files": [{"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
                              "default_category": "mandate", "line_count": 10,
                              "always_loaded": True}],
            "project_context": {"stack": []}, "config": {},
        }
        audit_path = str(tmp_path / "audit.json")
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit, f)
        rewrites_input = [{
            "rule_id": "R001", "original_text": "Old.",
            "suggested_rewrite": rewrite_text,
            "file": "CLAUDE.md", "line_start": 5, "old_score": 0.30,
            "old_dominant_weakness": "F1", "projected_score": 0.75,
        }]
        input_path = str(tmp_path / "rewrites_input.json")
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(rewrites_input, f)
        return audit_path, input_path

    def test_compound_and_rewrite_flagged_as_fragmenting(self, tmp_path):
        """A rewrite with `, and` joining two independent imperatives is flagged."""
        audit_path, input_path = self._write_audit_and_input(
            tmp_path,
            "Use functional components for all new React files, and run `npm test` before committing."
        )
        proc = _run_rewrite_scorer_raw("--score-rewrites", audit_path, input_path)
        assert proc.returncode == 0
        assert "would fragment" in proc.stderr
        result = json.loads(proc.stdout)
        meta = result["rules"][0]["_rewrite_meta"]
        assert meta.get("would_fragment") is True
        assert meta.get("fragment_count", 0) >= 2

    def test_clean_rewrite_not_flagged(self, tmp_path):
        """A single-directive rewrite passes without a fragmentation warning."""
        audit_path, input_path = self._write_audit_and_input(
            tmp_path,
            "Use functional components for all new React files."
        )
        proc = _run_rewrite_scorer_raw("--score-rewrites", audit_path, input_path)
        assert proc.returncode == 0
        assert "would fragment" not in proc.stderr
        result = json.loads(proc.stdout)
        meta = result["rules"][0]["_rewrite_meta"]
        assert meta.get("would_fragment") is not True
