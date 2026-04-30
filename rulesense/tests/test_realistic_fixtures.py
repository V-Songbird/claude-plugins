"""Smoke tests against real-world CLAUDE.md patterns.

These are the 'audit the audit' regression layer — they catch upstream
regressions that fixture-based unit tests miss. Use ranges not exact numbers.
"""

import json
import os
import subprocess
import tempfile

import pytest
from conftest import run_script, run_script_raw, PYTHON, SCRIPTS_DIR, FIXTURES_DIR


def _run_pipeline(project_root: str) -> dict:
    """Run discover -> extract -> score_mechanical -> score_semi on a project."""
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    result = subprocess.run(
        [PYTHON, str(SCRIPTS_DIR / "discover.py"), "--project-root", project_root],
        capture_output=True, text=True, timeout=30, encoding='utf-8', env=env
    )
    assert result.returncode == 0, f"discover failed: {result.stderr[:300]}"

    for script in ["extract.py", "score_mechanical.py", "score_semi.py"]:
        result = subprocess.run(
            [PYTHON, str(SCRIPTS_DIR / script)],
            input=result.stdout, capture_output=True, text=True, timeout=30,
            encoding='utf-8', env=env
        )
        assert result.returncode == 0, f"{script} failed: {result.stderr[:300]}"

    return json.loads(result.stdout)


def _run_full_pipeline(project_root: str, output_dir: str) -> dict:
    """Run full pipeline including compose with synthetic judgment patches."""
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    scored_data = _run_pipeline(project_root)
    rules = scored_data.get("rules", [])

    # Write scored_semi to temp file
    scored_path = os.path.join(output_dir, "_scored_semi.json")
    with open(scored_path, "w", encoding="utf-8") as f:
        json.dump(scored_data, f)

    # Synthetic judgment patches (F3=0.70, F8=0.60 for all rules)
    patches = {"schema_version": "0.1", "model_version": "synthetic", "patches": {}}
    for r in rules:
        patches["patches"][r["id"]] = {
            "F3": {"value": 0.70, "level": 3, "reasoning": "synthetic"},
            "F8": {"value": 0.60, "level": 2, "reasoning": "synthetic"},
        }
    patches_path = os.path.join(output_dir, "_patches.json")
    with open(patches_path, "w", encoding="utf-8") as f:
        json.dump(patches, f)

    # Compose
    result = subprocess.run(
        [PYTHON, str(SCRIPTS_DIR / "compose.py"), scored_path, patches_path],
        capture_output=True, text=True, timeout=30, encoding='utf-8', env=env
    )
    assert result.returncode == 0, f"compose failed: {result.stderr[:300]}"

    return json.loads(result.stdout)


class TestDesignSystemFixture:
    """Smoke tests for the design-system CLAUDE.md (axo-folio-derived)."""

    def test_extraction_count(self):
        """Should extract a reasonable number of rules (not 73, not 5)."""
        project = str(FIXTURES_DIR / "realistic_design_system")
        data = _run_pipeline(project)
        rules = data.get("rules", [])
        rule_count = len(rules)
        assert 5 < rule_count < 40, f"Rule count {rule_count} outside expected range"

        # Table content must not be in rules
        texts = " ".join(r["text"] for r in rules)
        assert "PascalCase.tsx" not in texts, "Table content leaked into rules"
        assert "useCamelCase.ts" not in texts, "Table content leaked into rules"

        # Code fence content must not be in rules
        assert "defineConfig" not in texts, "Code fence content leaked into rules"

        # Bare links must not be in rules
        assert "DESIGN_SYSTEM.md](./" not in texts, "Bare link leaked into rules"

    def test_real_directives_preserved(self):
        """Real behavioral directives must survive extraction."""
        project = str(FIXTURES_DIR / "realistic_design_system")
        data = _run_pipeline(project)
        texts = [r["text"] for r in data.get("rules", [])]
        assert any("WCAG" in t for t in texts), "WCAG directive missing"
        assert any("functional components" in t for t in texts), "Component rule missing"

    def test_full_pipeline_smoke(self, tmp_path):
        """Full pipeline with synthetic patches produces sane quality score."""
        project = str(FIXTURES_DIR / "realistic_design_system")
        audit = _run_full_pipeline(project, str(tmp_path))
        ecq = audit.get("effective_corpus_quality", {}).get("score", 0)
        assert 0.10 < ecq < 0.90, f"Effective corpus quality {ecq} outside sane range"
        # Rule count matches between extract and compose
        assert audit.get("rules_extracted", 0) == len(audit.get("rules", []))


class TestReduxAppFixture:
    """Smoke tests for the Redux-app CLAUDE.md (UPP-derived, .claude/ location)."""

    def test_extraction_count(self):
        """Should extract a reasonable number of rules."""
        project = str(FIXTURES_DIR / "realistic_redux_app")
        data = _run_pipeline(project)
        rules = data.get("rules", [])
        rule_count = len(rules)
        assert 5 < rule_count < 40, f"Rule count {rule_count} outside expected range"

        # Table content excluded
        texts = " ".join(r["text"] for r in rules)
        assert "FeesPage.tsx" not in texts, "Table content leaked into rules"

        # Code fence content excluded (multi-line code patterns, not inline refs)
        assert "providesTags" not in texts, "Code fence content leaked into rules"
        assert "toMatchSnapshot" not in texts, "Code fence content leaked into rules"

    def test_dot_claude_location_discovered(self):
        """The .claude/CLAUDE.md location should be discovered correctly."""
        project = str(FIXTURES_DIR / "realistic_redux_app")
        data = _run_pipeline(project)
        source_files = data.get("source_files", [])
        paths = [sf["path"] for sf in source_files]
        assert ".claude/CLAUDE.md" in paths, "Alternate CLAUDE.md location not discovered"

    def test_real_directives_preserved(self):
        """Hard rules from the original must survive."""
        project = str(FIXTURES_DIR / "realistic_redux_app")
        data = _run_pipeline(project)
        texts = [r["text"] for r in data.get("rules", [])]
        assert any("NEVER install new packages" in t for t in texts), "Hard rule 1 missing"
        assert any("functional" in t and "hooks" in t for t in texts), "Hard rule 2 missing"

    def test_full_pipeline_smoke(self, tmp_path):
        """Full pipeline with synthetic patches produces sane quality score."""
        project = str(FIXTURES_DIR / "realistic_redux_app")
        audit = _run_full_pipeline(project, str(tmp_path))
        ecq = audit.get("effective_corpus_quality", {}).get("score", 0)
        assert 0.10 < ecq < 0.90, f"Effective corpus quality {ecq} outside sane range"
        assert audit.get("rules_extracted", 0) == len(audit.get("rules", []))


# ---------------------------------------------------------------------------
# F-28: Non-BMP / surrogate character handling
# ---------------------------------------------------------------------------

class TestNonBMPContent:
    """F-28: Pipeline must not crash on CLAUDE.md with non-BMP unicode.
    The stdout reconfigure handles output; the input-decode fix handles the input
    side — stdin reconfigure + discover.py errors='replace'.

    NOTE: This test has teeth only on Windows. On Linux/macOS the default
    encoding is already UTF-8, so the test passes even if someone removes the
    stdin reconfigure. The Windows-specific regression path is: cp1252 stdin
    produces surrogates from non-ASCII piped content, json.dump crashes.
    """

    def test_full_pipeline_handles_non_bmp(self):
        """Full pipeline (discover -> extract -> score_mech -> score_semi) must
        not crash on source files with emoji, arrows, or math symbols."""
        project = str(FIXTURES_DIR / "non_bmp_content")
        data = _run_pipeline(project)
        rules = data.get("rules", [])
        assert len(rules) >= 3, f"Expected at least 3 rules, got {len(rules)}"
        # Confirm non-BMP content is preserved through the pipeline
        texts = " ".join(r["text"] for r in rules)
        assert "→" in texts or "🦎" in texts or "∀" in texts, \
            "Non-BMP characters were stripped — encoding may be lossy"
