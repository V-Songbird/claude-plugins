"""End-to-end tests for the placement-analyzer orchestrator integration.

Covers:
- run_audit.py --prepare-placement reads audit.json from .rulesense-tmp/
  and emits a valid candidates report.
- run_audit.py --write-promotions accepts a moves payload on stdin, writes
  .rulesense/PROMOTIONS.md, and removes moved rules from source files
  atomically.
- discover.py leaves .rulesense/PROMOTIONS.md out of the extraction pass
  on subsequent audits (the nag-until-promoted semantics require that
  moved rules stay gone, and that means discover must not re-read them
  from the promotions doc).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
PYTHON = sys.executable


def _run(cmd: list[str], *, cwd: Path, stdin: str | None = None, timeout: int = 60):
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        input=stdin,
        timeout=timeout,
    )


def _write_audit_json(project_root: Path, audit: dict) -> Path:
    tmp_dir = project_root / ".rulesense-tmp"
    tmp_dir.mkdir(exist_ok=True)
    path = tmp_dir / "audit.json"
    path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# --prepare-placement mode
# ---------------------------------------------------------------------------

class TestPreparePlacementMode:
    """The orchestrator reads audit.json and produces candidates JSON."""

    def test_emits_candidates_report(self, tmp_path):
        audit = {
            "project": "e2e-test",
            "effective_corpus_quality": {"score": 0.55},
            "rules": [
                {"id": "R1", "text": "Never run git commit or git push for the user.",
                 "file": "CLAUDE.md", "line_start": 3, "line_end": 3,
                 "factors": {"F8": {"value": 0.15}}, "category": "mandate"},
                {"id": "R2", "text": "Use functional components for all new React files.",
                 "file": "CLAUDE.md", "line_start": 5, "line_end": 5,
                 "factors": {"F8": {"value": 0.85}}, "category": "mandate"},
                {"id": "R3", "text": "When styling v2 components, follow the style guide at docs/tokens.md.",
                 "file": "CLAUDE.md", "line_start": 7, "line_end": 7,
                 "factors": {}, "category": "mandate"},
            ],
        }
        _write_audit_json(tmp_path, audit)

        result = _run(
            [PYTHON, str(SCRIPTS_DIR / "run_audit.py"), "--prepare-placement"],
            cwd=tmp_path,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = json.loads(result.stdout)
        assert output["summary"]["hook_candidates"] == 1
        assert output["summary"]["skill_candidates"] == 1
        assert output["summary"]["total_candidates"] == 2
        ids = [c["rule_id"] for c in output["candidates"]]
        assert "R1" in ids
        assert "R3" in ids
        assert "R2" not in ids  # non-candidate

    def test_empty_corpus_emits_empty_report(self, tmp_path):
        audit = {"rules": [], "effective_corpus_quality": {"score": 0.5}}
        _write_audit_json(tmp_path, audit)

        result = _run(
            [PYTHON, str(SCRIPTS_DIR / "run_audit.py"), "--prepare-placement"],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["summary"]["total_candidates"] == 0
        assert output["candidates"] == []


# ---------------------------------------------------------------------------
# --write-promotions mode
# ---------------------------------------------------------------------------

class TestWritePromotionsMode:
    """End-to-end: moves payload in, atomic file surgery out."""

    def test_full_transaction_writes_doc_and_removes_rule(self, tmp_path):
        # Set up a project with a CLAUDE.md containing a hook-candidate rule.
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Guide\n"
            "\n"
            "- Never run git commit or git push.\n"
            "- Use functional components.\n",
            encoding="utf-8",
        )
        payload = {
            "schema_version": "0.1",
            "project": "e2e",
            "audit_grade": "C (0.550)",
            "generated_at": "2026-04-17T18:00:00Z",
            "moves": [
                {
                    "rule_id": "R1",
                    "primitive": "hook",
                    "sub_type": "deterministic-gate",
                    "rule_text": "Never run git commit or git push.",
                    "file": "CLAUDE.md",
                    "line_start": 3,
                    "line_end": 3,
                    "judgment": {
                        "why": "Mechanically detectable git tool invocation.",
                        "suggested_shape": "PreToolUse on Bash matching ^git (commit|push)",
                        "next_step": "Add to .claude/settings.json",
                        "tradeoff": None,
                    },
                }
            ],
        }
        result = _run(
            [PYTHON, str(SCRIPTS_DIR / "run_audit.py"),
             "--write-promotions", "--project-root", str(tmp_path)],
            cwd=tmp_path,
            stdin=json.dumps(payload),
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert output["rules_removed"] == 1
        assert output["entries_written"] == 1

        # The rule is gone from CLAUDE.md.
        new_md = claude_md.read_text(encoding="utf-8")
        assert "Never run git commit" not in new_md
        assert "Use functional components" in new_md

        # PROMOTIONS.md was created with the entry.
        promo = tmp_path / ".rulesense" / "PROMOTIONS.md"
        assert promo.exists()
        content = promo.read_text(encoding="utf-8")
        assert "## Hooks" in content
        assert "Never run git commit" in content
        assert "PreToolUse on Bash" in content

    def test_drift_aborts_with_no_changes(self, tmp_path):
        """When the source file doesn't match rule_text, nothing is written."""
        claude_md = tmp_path / "CLAUDE.md"
        original = "- A rule that disagrees with the moves payload.\n"
        claude_md.write_text(original, encoding="utf-8")
        payload = {
            "schema_version": "0.1",
            "project": "e2e",
            "audit_grade": "C",
            "moves": [
                {
                    "rule_id": "R1",
                    "primitive": "hook",
                    "rule_text": "The rule we think is there.",
                    "file": "CLAUDE.md",
                    "line_start": 1,
                    "line_end": 1,
                    "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n"},
                }
            ],
        }
        result = _run(
            [PYTHON, str(SCRIPTS_DIR / "run_audit.py"),
             "--write-promotions", "--project-root", str(tmp_path)],
            cwd=tmp_path,
            stdin=json.dumps(payload),
        )
        assert result.returncode != 0
        output = json.loads(result.stdout)
        assert output["status"] == "failed"
        assert "drift" in output["reason"]
        # Source file is untouched.
        assert claude_md.read_text(encoding="utf-8") == original
        # No .rulesense/ dir was created.
        assert not (tmp_path / ".rulesense").exists()


# ---------------------------------------------------------------------------
# Discover ignores .rulesense/ on re-audit
# ---------------------------------------------------------------------------

class TestDiscoverIgnoresPromotionsDoc:
    """After a rule is moved to .rulesense/PROMOTIONS.md, a subsequent audit
    must NOT re-extract it from the promotions doc. This test pins the nag-
    until-promoted semantics: moved rules stay gone from the audit corpus
    unless the user explicitly restores them to a real rule file."""

    def test_discover_does_not_walk_into_rulesense_dir(self, tmp_path):
        """Running discover on a project with .rulesense/PROMOTIONS.md present
        should not list the promotions file among the discovered sources."""
        # Minimal project: one CLAUDE.md + a populated .rulesense/PROMOTIONS.md
        (tmp_path / "CLAUDE.md").write_text("- Use functional components.\n", encoding="utf-8")
        (tmp_path / ".rulesense").mkdir()
        (tmp_path / ".rulesense" / "PROMOTIONS.md").write_text(
            "# Rulesense promotion candidates\n\n"
            "## Hooks\n\n"
            "### `CLAUDE.md:3` — \"Never run git commit.\"\n"
            "- Why a hook: this rule text should NOT be re-extracted as a rule.\n",
            encoding="utf-8",
        )

        result = _run(
            [PYTHON, str(SCRIPTS_DIR / "discover.py"),
             "--project-root", str(tmp_path)],
            cwd=tmp_path,
        )
        assert result.returncode == 0, f"discover failed: {result.stderr}"
        output = json.loads(result.stdout)
        source_paths = [sf["path"] for sf in output.get("source_files", [])]
        # CLAUDE.md is discovered
        assert "CLAUDE.md" in source_paths
        # PROMOTIONS.md is NOT
        assert not any(".rulesense" in p for p in source_paths), (
            f"Placement-analyzer leak: discover surfaced a .rulesense/ path: {source_paths}"
        )

    def test_moved_rule_does_not_reappear_on_reaudit(self, tmp_path):
        """End-to-end: write-promotions removes a rule from source + writes
        it to PROMOTIONS.md. Running extract on the updated project must not
        re-extract the moved rule."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Guide\n"
            "\n"
            "- Never run git commit or git push.\n"
            "- Use functional components.\n",
            encoding="utf-8",
        )
        payload = {
            "schema_version": "0.1",
            "project": "e2e",
            "audit_grade": "C",
            "moves": [{
                "rule_id": "R1", "primitive": "hook",
                "rule_text": "Never run git commit or git push.",
                "file": "CLAUDE.md", "line_start": 3, "line_end": 3,
                "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n"},
            }],
        }
        r1 = _run(
            [PYTHON, str(SCRIPTS_DIR / "run_audit.py"),
             "--write-promotions", "--project-root", str(tmp_path)],
            cwd=tmp_path,
            stdin=json.dumps(payload),
        )
        assert r1.returncode == 0, f"write-promotions failed: {r1.stderr}"

        # Now the promotions doc exists. Run discover — it must not list
        # .rulesense/PROMOTIONS.md among source files.
        r2 = _run(
            [PYTHON, str(SCRIPTS_DIR / "discover.py"),
             "--project-root", str(tmp_path)],
            cwd=tmp_path,
        )
        assert r2.returncode == 0, f"discover failed: {r2.stderr}"
        output = json.loads(r2.stdout)
        source_paths = [sf["path"] for sf in output.get("source_files", [])]
        assert "CLAUDE.md" in source_paths
        for path in source_paths:
            assert not path.startswith(".rulesense/"), (
                f"discover leaked .rulesense path: {path}"
            )
