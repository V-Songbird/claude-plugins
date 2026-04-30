"""Tests for Phase 2b: batch scoring (partition_rules, merge_batch_patches)."""

import json
import os
import subprocess
import tempfile

import pytest
from conftest import run_script, run_script_raw, PYTHON, SCRIPTS_DIR, FIXTURES_DIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rule(rule_id: str, file_index: int = 0, line_start: int = 5) -> dict:
    """Build a minimal rule for partition testing."""
    return {
        "id": rule_id, "file_index": file_index, "text": f"Rule {rule_id}.",
        "line_start": line_start, "line_end": line_start, "category": "mandate",
        "referenced_entities": [], "staleness": {"gated": False, "missing_entities": []},
        "factors": {
            "F1": {"value": 0.85, "method": "lookup"},
            "F2": {"value": 0.85, "method": "classify"},
            "F4": {"value": 0.95, "method": "glob_match"},
            "F7": {"value": 0.80, "method": "count", "concrete_count": 2, "abstract_count": 0},
        },
    }


def _make_scored_data(rules: list[dict], source_files: list[dict] | None = None) -> dict:
    """Build a scored_semi.json for batch testing."""
    return {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_context": {
            "stack": ["typescript"],
            "tooling": {"eslint": True, "prettier": False, "git_hooks": False,
                        "typescript": True, "ruff": False, "flake8": False, "pre_commit": False},
            "always_loaded_files": ["CLAUDE.md"],
            "glob_scoped_files": [],
        },
        "config": {},
        "source_files": source_files or [
            {"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
             "default_category": "mandate", "line_count": 200, "always_loaded": True},
        ],
        "rules": rules,
    }


def _run_build_prompt_batch(data: dict, batch_dir: str) -> dict:
    """Run build_prompt.py with --batch-dir and return the manifest."""
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    result = subprocess.run(
        [PYTHON, str(SCRIPTS_DIR / "build_prompt.py"), "--batch-dir", batch_dir],
        input=json.dumps(data), capture_output=True, text=True, timeout=30,
        encoding='utf-8', env=env
    )
    assert result.returncode == 0, f"build_prompt.py batch failed: {result.stderr}"

    manifest_path = os.path.join(batch_dir, "batch_manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Partition tests
# ---------------------------------------------------------------------------

class TestBatchPartition:
    def test_batch_partition_small_corpus(self):
        """10 rules → no batching (below threshold). Single prompt to stdout."""
        rules = [_make_rule(f"R{i:03d}", line_start=i * 5) for i in range(1, 11)]
        data = _make_scored_data(rules)

        # Without --batch-dir, single-prompt mode
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        result = subprocess.run(
            [PYTHON, str(SCRIPTS_DIR / "build_prompt.py")],
            input=json.dumps(data), capture_output=True, text=True, timeout=30,
            encoding='utf-8', env=env
        )
        assert result.returncode == 0
        assert "# Quality Factor Scoring" in result.stdout
        # All 10 rule IDs in the single prompt
        for i in range(1, 11):
            assert f"R{i:03d}" in result.stdout

    def test_batch_partition_large_corpus(self):
        """35 rules → 3 batches (with batch_size=12)."""
        rules = [_make_rule(f"R{i:03d}", line_start=i * 5) for i in range(1, 36)]
        data = _make_scored_data(rules)

        with tempfile.TemporaryDirectory() as batch_dir:
            manifest = _run_build_prompt_batch(data, batch_dir)

            assert manifest["batch_count"] == 3
            assert manifest["total_rules"] == 35

            # All rule IDs covered exactly once
            all_ids = []
            for batch in manifest["batches"]:
                all_ids.extend(batch["rule_ids"])
            assert len(all_ids) == 35
            assert len(set(all_ids)) == 35

            # Each prompt file exists
            for batch in manifest["batches"]:
                prompt_path = os.path.join(batch_dir, batch["file"])
                assert os.path.exists(prompt_path)

    def test_batch_same_file_cohesion(self):
        """Rules from the same file stay in the same batch when possible."""
        sf = [
            {"path": "a.md", "globs": [], "glob_match_count": None,
             "default_category": "mandate", "line_count": 50, "always_loaded": True},
            {"path": "b.md", "globs": [], "glob_match_count": None,
             "default_category": "mandate", "line_count": 50, "always_loaded": True},
        ]
        # 11 rules in file a, 12 in file b (23 total, above >20 threshold)
        rules = (
            [_make_rule(f"R{i:03d}", file_index=0, line_start=i * 5) for i in range(1, 12)] +
            [_make_rule(f"R{i:03d}", file_index=1, line_start=i * 5) for i in range(12, 24)]
        )
        data = _make_scored_data(rules, sf)

        with tempfile.TemporaryDirectory() as batch_dir:
            manifest = _run_build_prompt_batch(data, batch_dir)

            assert manifest["batch_count"] == 2
            batch1_ids = set(manifest["batches"][0]["rule_ids"])
            batch2_ids = set(manifest["batches"][1]["rule_ids"])
            file_a_ids = {f"R{i:03d}" for i in range(1, 12)}
            file_b_ids = {f"R{i:03d}" for i in range(12, 24)}
            # File cohesion: all file-a rules in one batch, file-b in the other
            assert file_a_ids <= batch1_ids or file_a_ids <= batch2_ids, \
                "File-a rules should be in the same batch"
            assert file_b_ids <= batch1_ids or file_b_ids <= batch2_ids, \
                "File-b rules should be in the same batch"

    def test_batch_partition_deterministic(self):
        """partition_rules is a pure function: identical input → identical output."""
        rules = [_make_rule(f"R{i:03d}", line_start=i * 5) for i in range(1, 36)]
        data = _make_scored_data(rules)

        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            m1 = _run_build_prompt_batch(data, d1)
            m2 = _run_build_prompt_batch(data, d2)

            assert m1["batch_count"] == m2["batch_count"]
            for b1, b2 in zip(m1["batches"], m2["batches"]):
                assert b1["rule_ids"] == b2["rule_ids"]

    def test_batch_partition_oversize_file(self):
        """30 rules in one file, batch_size=12 → 3 batches, contiguous, line-ordered."""
        rules = [_make_rule(f"R{i:03d}", file_index=0, line_start=i * 5) for i in range(1, 31)]
        data = _make_scored_data(rules)

        with tempfile.TemporaryDirectory() as batch_dir:
            manifest = _run_build_prompt_batch(data, batch_dir)

            assert manifest["batch_count"] == 3
            # First batch: R001-R012, second: R013-R024, third: R025-R030
            assert manifest["batches"][0]["rule_ids"] == [f"R{i:03d}" for i in range(1, 13)]
            assert manifest["batches"][1]["rule_ids"] == [f"R{i:03d}" for i in range(13, 25)]
            assert manifest["batches"][2]["rule_ids"] == [f"R{i:03d}" for i in range(25, 31)]

            # Continuation batches should have a note in the prompt
            prompt2_path = os.path.join(batch_dir, "prompt_002.md")
            with open(prompt2_path, encoding="utf-8") as f:
                prompt2 = f.read()
            assert "continue from" in prompt2.lower() or "Batch 2 of 3" in prompt2

    def test_batch_prompt_contains_full_rubrics(self):
        """Each batch prompt must contain the full F3+F8 rubrics and tooling context.

        This pins the Phase 2a+2b integration contract: enriched rubrics appear
        in every batch, not just the first one.
        """
        rules = [_make_rule(f"R{i:03d}", line_start=i * 5) for i in range(1, 36)]
        data = _make_scored_data(rules)

        with tempfile.TemporaryDirectory() as batch_dir:
            manifest = _run_build_prompt_batch(data, batch_dir)

            for batch_info in manifest["batches"]:
                prompt_path = os.path.join(batch_dir, batch_info["file"])
                with open(prompt_path, encoding="utf-8") as f:
                    prompt = f.read()

                # F3 rubric level headings
                assert "Level 4" in prompt, f"{batch_info['file']} missing F3 Level 4"
                assert "Level 0" in prompt, f"{batch_info['file']} missing F3 Level 0"
                assert "Trigger-Action Distance" in prompt

                # F8 rubric level headings
                assert "Enforceability Ceiling" in prompt
                assert "Not mechanically enforceable" in prompt

                # Tooling context
                assert "eslint" in prompt or "No enforcement tooling" in prompt


# ---------------------------------------------------------------------------
# Merge tests
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Integration: parse_judgment in batch mode
# ---------------------------------------------------------------------------

class TestBatchParseJudgment:
    """The critical integration test: raw batch output → parse_judgment.py
    with --expected-ids → patches file. This is the production path that
    SKILL.md documents. Without --expected-ids, parse_judgment fatals on
    every batch because it compares 12 rules against the full 46-rule corpus.
    """

    def test_batch_parse_judgment_handles_subset(self):
        """parse_judgment.py with --expected-ids for a batch subset must succeed."""
        # 46-rule corpus but only 12 in this batch
        all_rule_ids = [f"R{i:03d}" for i in range(1, 47)]
        batch_ids = all_rule_ids[:12]

        scored = _make_scored_data(
            [_make_rule(rid, line_start=i * 5) for i, rid in enumerate(all_rule_ids)]
        )

        # Write scored_semi
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(scored, f)
            scored_path = f.name

        try:
            # Simulate raw judgment for just the 12 batch rules
            raw_judgment = json.dumps([
                {"id": rid,
                 "F3": {"value": 0.70, "level": 3, "reasoning": "test"},
                 "F8": {"value": 0.60, "level": 2, "reasoning": "test"}}
                for rid in batch_ids
            ])

            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            # Without --expected-ids: should fatal (34 of 46 missing)
            result_no_flag = subprocess.run(
                [PYTHON, str(SCRIPTS_DIR / "parse_judgment.py"), scored_path],
                input=raw_judgment, capture_output=True, text=True, timeout=30,
                encoding='utf-8', env=env
            )
            assert result_no_flag.returncode != 0, \
                "parse_judgment should fatal without --expected-ids on a batch subset"
            assert "FATAL" in result_no_flag.stderr
            assert "missing" in result_no_flag.stderr.lower()

            # With --expected-ids: should succeed
            result_with_flag = subprocess.run(
                [PYTHON, str(SCRIPTS_DIR / "parse_judgment.py"), scored_path,
                 "--expected-ids", ",".join(batch_ids)],
                input=raw_judgment, capture_output=True, text=True, timeout=30,
                encoding='utf-8', env=env
            )
            assert result_with_flag.returncode == 0, \
                f"parse_judgment with --expected-ids should succeed: {result_with_flag.stderr[:200]}"

            patches = json.loads(result_with_flag.stdout)
            assert len(patches["patches"]) == 12
            for rid in batch_ids:
                assert rid in patches["patches"]
            assert patches["schema_version"] == "0.1"

        finally:
            os.unlink(scored_path)


class TestMergeBatchPatches:
    def _make_batch_patches(self, batch_dir: str, batch_num: int,
                            rule_ids: list[str], f3: float = 0.70, f8: float = 0.60) -> None:
        """Write a patches_NNN.json file to batch_dir."""
        patches = {}
        for rid in rule_ids:
            patches[rid] = {
                "F3": {"value": f3, "level": 3, "reasoning": "synthetic"},
                "F8": {"value": f8, "level": 2, "reasoning": "synthetic"},
            }
        data = {"schema_version": "0.1", "model_version": "test", "patches": patches}
        path = os.path.join(batch_dir, f"patches_{batch_num:03d}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def test_merge_two_batches(self):
        """Two patches files with disjoint rule IDs merge correctly."""
        rules = [_make_rule(f"R{i:03d}", line_start=i * 5) for i in range(1, 25)]
        scored = _make_scored_data(rules)

        with tempfile.TemporaryDirectory() as batch_dir:
            scored_path = os.path.join(batch_dir, "scored_semi.json")
            with open(scored_path, "w", encoding="utf-8") as f:
                json.dump(scored, f)

            # Two batches: R001-R012, R013-R024
            self._make_batch_patches(batch_dir, 1, [f"R{i:03d}" for i in range(1, 13)])
            self._make_batch_patches(batch_dir, 2, [f"R{i:03d}" for i in range(13, 25)])

            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            result = subprocess.run(
                [PYTHON, str(SCRIPTS_DIR / "merge_batch_patches.py"), batch_dir, scored_path],
                capture_output=True, text=True, timeout=30, encoding='utf-8', env=env
            )
            assert result.returncode == 0, f"merge failed: {result.stderr}"

            merged = json.loads(result.stdout)
            assert len(merged["patches"]) == 24
            for i in range(1, 25):
                assert f"R{i:03d}" in merged["patches"]

    def test_merge_schema_version(self):
        """Merged output has schema_version from the batch patches."""
        rules = [_make_rule("R001")]
        scored = _make_scored_data(rules)

        with tempfile.TemporaryDirectory() as batch_dir:
            scored_path = os.path.join(batch_dir, "scored_semi.json")
            with open(scored_path, "w", encoding="utf-8") as f:
                json.dump(scored, f)

            self._make_batch_patches(batch_dir, 1, ["R001"])

            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            result = subprocess.run(
                [PYTHON, str(SCRIPTS_DIR / "merge_batch_patches.py"), batch_dir, scored_path],
                capture_output=True, text=True, timeout=30, encoding='utf-8', env=env
            )
            assert result.returncode == 0

            merged = json.loads(result.stdout)
            assert merged["schema_version"] == "0.1"
