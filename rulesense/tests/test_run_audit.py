"""Tests for run_audit.py orchestrator."""

import json
import os
import shutil
import subprocess

import pytest
from conftest import PYTHON, SCRIPTS_DIR, FIXTURES_DIR


RUN_AUDIT = str(SCRIPTS_DIR / "run_audit.py")


def _run_audit(args: list[str], cwd: str | None = None,
               timeout: int = 60) -> subprocess.CompletedProcess:
    """Run run_audit.py and return the CompletedProcess."""
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    return subprocess.run(
        [PYTHON, RUN_AUDIT] + args,
        capture_output=True, text=True, encoding='utf-8',
        env=env, timeout=timeout, cwd=cwd,
    )


def _make_rule(rule_id: str, file_index: int = 0, line_start: int = 5,
               score: float | None = None, category: str = "mandate") -> dict:
    """Build a minimal rule for testing."""
    return {
        "id": rule_id, "file_index": file_index,
        "text": f"Rule {rule_id} text.",
        "line_start": line_start, "line_end": line_start,
        "category": category,
        "referenced_entities": [],
        "staleness": {"gated": False, "missing_entities": []},
        "factors": {
            "F1": {"value": 0.85, "method": "lookup"},
            "F2": {"value": 0.85, "method": "classify"},
            "F4": {"value": 0.95, "method": "glob_match"},
            "F7": {"value": 0.80, "method": "count",
                   "concrete_count": 2, "abstract_count": 0},
        },
    }


def _make_scored_data(rules: list[dict],
                      source_files: list[dict] | None = None) -> dict:
    """Build a scored_semi.json structure."""
    return {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_context": {
            "stack": ["typescript"],
            "tooling": {"eslint": True, "prettier": False, "git_hooks": False,
                        "typescript": True, "ruff": False, "flake8": False,
                        "pre_commit": False},
            "always_loaded_files": ["CLAUDE.md"],
            "glob_scoped_files": [],
        },
        "config": {},
        "source_files": source_files or [
            {"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
             "default_category": "mandate", "line_count": 200,
             "always_loaded": True},
        ],
        "rules": rules,
    }


def _make_judgment_array(rule_ids: list[str],
                         f3: float = 0.70, f8: float = 0.60) -> list[dict]:
    """Build a flat judgment array for all_judgments.json."""
    return [
        {"id": rid,
         "F3": {"value": f3, "level": 3, "reasoning": "synthetic"},
         "F8": {"value": f8, "level": 2, "reasoning": "synthetic"}}
        for rid in rule_ids
    ]


def _make_audit_json(rules_with_scores: list[tuple[str, float]]) -> dict:
    """Build a minimal audit.json with rules having specified scores.

    rules_with_scores: list of (rule_id, score) tuples.
    """
    rules = []
    for rid, score in rules_with_scores:
        rules.append({
            "id": rid,
            "file_index": 0,
            "text": f"Rule {rid} text.",
            "line_start": 5,
            "line_end": 5,
            "category": "mandate",
            "score": score,
            "dominant_weakness": "F7" if score < 0.50 else None,
            "file": "CLAUDE.md",
            "factors": {
                "F1": {"value": 0.85},
                "F2": {"value": 0.85},
                "F3": {"value": 0.70},
                "F4": {"value": 0.95},
                "F7": {"value": 0.30 if score < 0.50 else 0.80},
                "F8": {"value": 0.60},
            },
        })
    return {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project": "",
        "files_scanned": 1,
        "rules_extracted": len(rules),
        "effective_corpus_quality": {"score": 0.60},
        "corpus_quality": {"rule_mean_score": 0.60},
        "guideline_quality": {"score": 0.55},
        "rules": rules,
        "files": [
            {"path": "CLAUDE.md", "file_score": 0.60, "line_count": 100,
             "rule_count": len(rules), "length_penalty": 0.0,
             "prohibition_ratio": 0.0, "trigger_scope_coherence": 0.0,
             "concreteness_coverage": 0.50, "dead_zone_count": 0},
        ],
        "positive_findings": [],
        "rewrite_candidates": [],
    }


# ---------------------------------------------------------------------------
# --prepare tests
# ---------------------------------------------------------------------------

class TestPrepare:
    def test_prepare_creates_tmp_and_outputs_metadata(self, tmp_path):
        """--prepare creates .rulesense-tmp/ and outputs valid metadata."""
        project = tmp_path / "sample_project"
        shutil.copytree(FIXTURES_DIR / "sample_project", project)

        result = _run_audit(
            ["--prepare", "--project-root", str(project)],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, f"--prepare failed: {result.stderr}"

        metadata = json.loads(result.stdout)
        assert "rule_count" in metadata
        assert "batch_mode" in metadata
        assert isinstance(metadata["rule_count"], int)
        assert metadata["rule_count"] > 0

        # Verify tmp dir was created
        tmp_dir = tmp_path / ".rulesense-tmp"
        assert tmp_dir.exists()
        assert (tmp_dir / ".gitignore").read_text() == "*\n"
        assert (tmp_dir / "scored_semi.json").exists()

    def test_prepare_small_corpus_single_prompt(self, tmp_path):
        """sample_project has <20 rules → single prompt mode."""
        project = tmp_path / "sample_project"
        shutil.copytree(FIXTURES_DIR / "sample_project", project)

        result = _run_audit(
            ["--prepare", "--project-root", str(project)],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, f"--prepare failed: {result.stderr}"

        metadata = json.loads(result.stdout)
        assert metadata["batch_mode"] is False
        assert metadata["batch_count"] == 0
        assert metadata["single_prompt"] is not None
        assert metadata["manifest"] is None
        assert metadata["prompt_files"] == []

        # Verify prompt file exists
        prompt_path = tmp_path / ".rulesense-tmp" / "prompt.md"
        assert prompt_path.exists()
        prompt_text = prompt_path.read_text(encoding="utf-8")
        assert "Quality Factor Scoring" in prompt_text

    def test_prepare_defaults_project_root_to_cwd(self, tmp_path):
        """--prepare without --project-root defaults to current directory."""
        project = tmp_path / "proj"
        shutil.copytree(FIXTURES_DIR / "sample_project", project)

        result = _run_audit(["--prepare"], cwd=str(project))
        # May succeed or fail depending on whether sample_project has
        # instruction files at its root. The key test is that it doesn't
        # crash with "missing --project-root".
        # discover.py will run with cwd as project root.
        assert result.returncode == 0 or "--project-root" not in result.stderr


# ---------------------------------------------------------------------------
# --finalize tests
# ---------------------------------------------------------------------------

class TestFinalize:
    def test_finalize_produces_report(self, tmp_path):
        """--finalize reads judgments, composes, and outputs markdown report."""
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()

        rule_ids = [f"R{i:03d}" for i in range(1, 6)]
        rules = [_make_rule(rid, line_start=i * 5)
                 for i, rid in enumerate(rule_ids)]
        scored = _make_scored_data(rules)

        # Write scored_semi.json
        with open(tmp_dir / "scored_semi.json", "w", encoding="utf-8") as f:
            json.dump(scored, f)

        # Write all_judgments.json (flat array)
        judgments = _make_judgment_array(rule_ids)
        with open(tmp_dir / "all_judgments.json", "w", encoding="utf-8") as f:
            json.dump(judgments, f)

        result = _run_audit(["--finalize"], cwd=str(tmp_path))
        assert result.returncode == 0, f"--finalize failed: {result.stderr}"

        # Stdout should be the markdown report
        assert "Grade" in result.stdout or "grade" in result.stdout.lower()

        # audit.json should have been created
        audit_path = tmp_dir / "audit.json"
        assert audit_path.exists()
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        assert audit["schema_version"] == "0.1"
        assert len(audit["rules"]) == 5

    def test_finalize_flattens_batched_judgments(self, tmp_path):
        """--finalize handles batched judgment format by flattening."""
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()

        rule_ids = [f"R{i:03d}" for i in range(1, 6)]
        rules = [_make_rule(rid, line_start=i * 5)
                 for i, rid in enumerate(rule_ids)]
        scored = _make_scored_data(rules)

        with open(tmp_dir / "scored_semi.json", "w", encoding="utf-8") as f:
            json.dump(scored, f)

        # Write batched format
        batched = {
            "batches": [
                {
                    "expected_ids": rule_ids[:3],
                    "judgments": _make_judgment_array(rule_ids[:3]),
                },
                {
                    "expected_ids": rule_ids[3:],
                    "judgments": _make_judgment_array(rule_ids[3:]),
                },
            ]
        }
        with open(tmp_dir / "all_judgments.json", "w", encoding="utf-8") as f:
            json.dump(batched, f)

        result = _run_audit(["--finalize"], cwd=str(tmp_path))
        assert result.returncode == 0, f"--finalize failed: {result.stderr}"

        audit = json.loads(
            (tmp_dir / "audit.json").read_text(encoding="utf-8"))
        assert len(audit["rules"]) == 5


# ---------------------------------------------------------------------------
# --prepare-fix tests
# ---------------------------------------------------------------------------

class TestPrepareFix:
    def test_selects_qualifying_rules(self, tmp_path):
        """--prepare-fix returns only mandate rules with score < 0.50."""
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()

        audit = _make_audit_json([
            ("R001", 0.35),  # below 0.50 → qualifies
            ("R002", 0.72),  # above 0.50 → excluded
            ("R003", 0.10),  # below 0.50 → qualifies
            ("R004", 0.50),  # exactly 0.50 → excluded (>= threshold)
            ("R005", 0.49),  # just below → qualifies
        ])

        with open(tmp_dir / "audit.json", "w", encoding="utf-8") as f:
            json.dump(audit, f)

        result = _run_audit(["--prepare-fix"], cwd=str(tmp_path))
        assert result.returncode == 0, f"--prepare-fix failed: {result.stderr}"

        output = json.loads(result.stdout)
        assert output["qualifying_count"] == 3
        qualifying_ids = {r["rule_id"] for r in output["rules"]}
        assert qualifying_ids == {"R001", "R003", "R005"}

        # Each qualifying rule has the expected fields
        for r in output["rules"]:
            assert "file" in r
            assert "text" in r
            assert "score" in r
            assert "dominant_weakness" in r
            assert "action" in r
            assert r["file"] == "CLAUDE.md"

    def test_no_qualifying_rules(self, tmp_path):
        """--prepare-fix with all rules above 0.50 returns empty list."""
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()

        audit = _make_audit_json([
            ("R001", 0.80),
            ("R002", 0.65),
        ])

        with open(tmp_dir / "audit.json", "w", encoding="utf-8") as f:
            json.dump(audit, f)

        result = _run_audit(["--prepare-fix"], cwd=str(tmp_path))
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["qualifying_count"] == 0
        assert output["rules"] == []


# ---------------------------------------------------------------------------
# --cleanup tests
# ---------------------------------------------------------------------------

class TestCleanup:
    def test_cleanup_removes_tmp(self, tmp_path):
        """--cleanup removes .rulesense-tmp/ directory."""
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()
        (tmp_dir / "some_file.json").write_text("{}", encoding="utf-8")

        result = _run_audit(["--cleanup"], cwd=str(tmp_path))
        assert result.returncode == 0
        assert not tmp_dir.exists()

    def test_cleanup_noop_when_no_tmp(self, tmp_path):
        """--cleanup succeeds even if .rulesense-tmp/ doesn't exist."""
        result = _run_audit(["--cleanup"], cwd=str(tmp_path))
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# --build-overview tests
# ---------------------------------------------------------------------------

class TestBuildOverview:
    def test_build_overview_produces_scaffold(self, tmp_path):
        """--build-overview with audit.json produces scaffold with all expected keys."""
        audit = _make_audit_json([("R001", 0.85), ("R002", 0.55)])
        # Add loading field (present in real audit.json, missing in _make_audit_json)
        for r in audit["rules"]:
            r["loading"] = "always-loaded"
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()
        (tmp_dir / "audit.json").write_text(
            json.dumps(audit), encoding="utf-8"
        )

        result = _run_audit(["--build-overview"], cwd=str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"

        scaffold = json.loads(result.stdout)
        assert "audit" in scaffold
        assert scaffold["audit"]["schema_version"] == "0.1"
        assert isinstance(scaffold["organization"], dict)
        assert scaffold["organization"]["claude_md_rules"] == 2
        assert scaffold["intentions"] == []
        assert scaffold["coverage_gaps"] == []
        assert scaffold["generated_at"] == ""

    def test_build_overview_organization_metrics(self, tmp_path):
        """Organization counts correctly distinguish CLAUDE.md, scoped, and always-loaded rules."""
        audit = _make_audit_json([("R001", 0.85), ("R002", 0.70), ("R003", 0.60)])
        # R001 in CLAUDE.md (always-loaded)
        audit["rules"][0]["file"] = "CLAUDE.md"
        audit["rules"][0]["loading"] = "always-loaded"
        # R002 in rules dir (glob-scoped)
        audit["rules"][1]["file"] = ".claude/rules/api.md"
        audit["rules"][1]["loading"] = "glob-scoped"
        # R003 in rules dir (always-loaded)
        audit["rules"][2]["file"] = ".claude/rules/general.md"
        audit["rules"][2]["loading"] = "always-loaded"
        # Add file entries for the rules dir files
        audit["files"].append({
            "path": ".claude/rules/api.md", "file_score": 0.70,
            "line_count": 50, "rule_count": 1, "length_penalty": 1.0,
            "prohibition_ratio": 0.0, "trigger_scope_coherence": 0.0,
            "concreteness_coverage": 0.50, "dead_zone_count": 0,
        })
        audit["files"].append({
            "path": ".claude/rules/general.md", "file_score": 0.60,
            "line_count": 30, "rule_count": 1, "length_penalty": 1.0,
            "prohibition_ratio": 0.0, "trigger_scope_coherence": 0.0,
            "concreteness_coverage": 0.50, "dead_zone_count": 0,
        })

        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()
        (tmp_dir / "audit.json").write_text(
            json.dumps(audit), encoding="utf-8"
        )

        result = _run_audit(["--build-overview"], cwd=str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"

        scaffold = json.loads(result.stdout)
        org = scaffold["organization"]
        assert org["claude_md_rules"] == 1
        assert org["scoped_rules"] == 1
        assert org["always_loaded_rules_in_rules_dir"] == 1
        assert org["claude_md_lines"] == 100  # from _make_audit_json files[0]


# ---------------------------------------------------------------------------
# --build-analysis tests
# ---------------------------------------------------------------------------

class TestBuildAnalysis:
    def test_build_analysis_produces_structured_data(self, tmp_path):
        """--build-analysis with audit.json produces all expected fields."""
        audit = _make_audit_json([("R001", 0.85), ("R002", 0.55), ("R003", 0.30)])
        for r in audit["rules"]:
            r["loading"] = "always-loaded"
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()
        (tmp_dir / "audit.json").write_text(
            json.dumps(audit), encoding="utf-8"
        )

        result = _run_audit(["--build-analysis"], cwd=str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"

        data = json.loads(result.stdout)
        assert data["grade"] in ("A", "B", "C", "D", "F")
        assert isinstance(data["score"], (int, float))
        assert data["rule_count"] == 3
        assert isinstance(data["good_count"], int)
        assert set(data["grade_counts"].keys()) == {"A", "B", "C", "D", "F"}
        assert isinstance(data["below_floor_count"], int)
        assert len(data["files"]) >= 1
        assert "organization" in data
        assert len(data["best_rules"]) <= 5
        assert len(data["worst_rules"]) <= 5
        assert len(data["rules_for_intention_map"]) == 3

    def test_build_analysis_uses_standard_grades(self, tmp_path):
        """Grade computation uses A/B/C/D/F only — no E or A+ tiers."""
        audit = _make_audit_json([
            ("R001", 0.80),  # A boundary
            ("R002", 0.65),  # B boundary
            ("R003", 0.50),  # C boundary
            ("R004", 0.35),  # D boundary
            ("R005", 0.34),  # F
        ])
        for r in audit["rules"]:
            r["loading"] = "always-loaded"
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()
        (tmp_dir / "audit.json").write_text(
            json.dumps(audit), encoding="utf-8"
        )

        result = _run_audit(["--build-analysis"], cwd=str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"

        data = json.loads(result.stdout)
        # Only A/B/C/D/F keys in grade_counts
        assert set(data["grade_counts"].keys()) == {"A", "B", "C", "D", "F"}
        assert data["grade_counts"]["A"] == 1
        assert data["grade_counts"]["B"] == 1
        assert data["grade_counts"]["C"] == 1
        assert data["grade_counts"]["D"] == 1
        assert data["grade_counts"]["F"] == 1
        # No E or A+ in any grade field
        output_str = json.dumps(data)
        assert '"E"' not in output_str or '"E"' in output_str.split('"text"')[0] is False
        for rule in data["rules_for_intention_map"]:
            assert rule["grade"] in ("A", "B", "C", "D", "F")

    def test_build_analysis_organization_metrics(self, tmp_path):
        """Organization metrics distinguish CLAUDE.md from .claude/rules/."""
        audit = _make_audit_json([("R001", 0.85), ("R002", 0.70), ("R003", 0.60)])
        audit["rules"][0]["file"] = "CLAUDE.md"
        audit["rules"][0]["loading"] = "always-loaded"
        audit["rules"][1]["file"] = ".claude/rules/api.md"
        audit["rules"][1]["loading"] = "glob-scoped"
        audit["rules"][2]["file"] = ".claude/rules/general.md"
        audit["rules"][2]["loading"] = "always-loaded"
        audit["files"].append({
            "path": ".claude/rules/api.md", "file_score": 0.70,
            "line_count": 50, "rule_count": 1, "length_penalty": 1.0,
            "prohibition_ratio": 0.0, "trigger_scope_coherence": 0.0,
            "concreteness_coverage": 0.50, "dead_zone_count": 0,
        })
        audit["files"].append({
            "path": ".claude/rules/general.md", "file_score": 0.60,
            "line_count": 30, "rule_count": 1, "length_penalty": 1.0,
            "prohibition_ratio": 0.0, "trigger_scope_coherence": 0.0,
            "concreteness_coverage": 0.50, "dead_zone_count": 0,
        })

        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()
        (tmp_dir / "audit.json").write_text(
            json.dumps(audit), encoding="utf-8"
        )

        result = _run_audit(["--build-analysis"], cwd=str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"

        data = json.loads(result.stdout)
        org = data["organization"]
        assert org["claude_md_rules"] == 1
        assert org["scoped_rules"] == 1
        assert org["always_loaded_rules_in_rules_dir"] == 1
        assert org["claude_md_lines"] == 100


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

class TestErrors:
    def test_no_mode_exits_nonzero(self):
        """Running with no arguments exits 1 with usage."""
        result = _run_audit([])
        assert result.returncode == 1
        assert "Usage" in result.stderr

    def test_unknown_mode_exits_nonzero(self):
        """Running with unknown mode exits 1."""
        result = _run_audit(["--bogus"])
        assert result.returncode == 1
        assert "Unknown mode" in result.stderr

    def test_prepare_bad_project_root(self, tmp_path):
        """--prepare with nonexistent project root fails."""
        result = _run_audit(
            ["--prepare", "--project-root", str(tmp_path / "nonexistent")],
            cwd=str(tmp_path),
        )
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# --score-draft tests
# ---------------------------------------------------------------------------

class TestScoreDraft:
    def test_score_draft_produces_mechanical_scores(self, tmp_path):
        """--score-draft with 2 rules produces F1/F2/F4/F7 scores."""
        draft = {
            "rules": [
                {"id": "T01", "text": "Use early returns over nested ifs."},
                {"id": "T02", "text": "Name booleans as questions: isReady, hasAccess."},
            ],
            "file": ".claude/rules/test.md",
            "category": "mandate",
        }
        draft_path = tmp_path / "draft.json"
        draft_path.write_text(json.dumps(draft), encoding="utf-8")

        result = _run_audit(
            ["--score-draft", str(draft_path)],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, f"--score-draft failed: {result.stderr}"

        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert len(data["rules"]) == 2
        assert "judgment_prompt" in data

        for rule in data["rules"]:
            factors = rule["factors"]
            for fn in ("F1", "F2", "F4", "F7"):
                assert fn in factors, f"Rule {rule['id']} missing {fn}"
            assert rule["needs_judgment"] is True

        # Verify tmp files were created (draft_ prefix avoids audit collision)
        assert (tmp_path / ".rulesense-tmp" / "draft_scored_semi.json").exists()
        assert (tmp_path / ".rulesense-tmp" / "draft_prompt.md").exists()

    def test_score_draft_flags_fragmenting_and_rule(self, tmp_path):
        """A draft rule with `, and` between two imperatives short-circuits
        with status=needs_revision before any scoring runs."""
        draft = {
            "rules": [
                {"id": "T01",
                 "text": "Use functional components for all new React files, "
                         "and run `npm test` before committing."},
            ],
            "file": ".claude/rules/test.md",
            "category": "mandate",
        }
        draft_path = tmp_path / "draft.json"
        draft_path.write_text(json.dumps(draft), encoding="utf-8")

        result = _run_audit(
            ["--score-draft", str(draft_path)],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, f"--score-draft failed: {result.stderr}"

        data = json.loads(result.stdout)
        assert data["status"] == "needs_revision"
        assert "fragmenting_rules" in data
        assert len(data["fragmenting_rules"]) == 1
        flagged = data["fragmenting_rules"][0]
        assert flagged["id"] == "T01"
        assert flagged["fragment_count"] >= 2
        assert len(flagged["fragments_preview"]) >= 2
        assert "splitter" in flagged["reason"].lower()

        # Critical: no scoring output produced — the pipeline short-circuited.
        assert "rules" not in data
        assert "judgment_prompt" not in data
        # The scored_semi / prompt artifacts must NOT exist yet — they would
        # only appear after a successful scoring pass.
        assert not (tmp_path / ".rulesense-tmp" / "draft_scored_semi.json").exists()
        assert not (tmp_path / ".rulesense-tmp" / "draft_prompt.md").exists()

    def test_score_draft_flags_semicolon_split(self, tmp_path):
        """A rule with `;` between two verb-bearing clauses fragments."""
        draft = {
            "rules": [
                {"id": "T01",
                 "text": "Use `expect` for all assertions; avoid `assert`."},
            ],
            "file": ".claude/rules/test.md",
            "category": "mandate",
        }
        draft_path = tmp_path / "draft.json"
        draft_path.write_text(json.dumps(draft), encoding="utf-8")

        result = _run_audit(
            ["--score-draft", str(draft_path)],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "needs_revision"
        assert data["fragmenting_rules"][0]["id"] == "T01"

    def test_score_draft_mixed_batch_flags_only_fragmenting(self, tmp_path):
        """A batch with one clean rule and one fragmenting rule reports only
        the fragmenting one; scoring still short-circuits globally."""
        draft = {
            "rules": [
                {"id": "T01", "text": "Use early returns over nested ifs."},
                {"id": "T02",
                 "text": "Name tests as sentences, and avoid mutating shared "
                         "fixtures across test cases."},
            ],
            "file": ".claude/rules/test.md",
            "category": "mandate",
        }
        draft_path = tmp_path / "draft.json"
        draft_path.write_text(json.dumps(draft), encoding="utf-8")

        result = _run_audit(
            ["--score-draft", str(draft_path)],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "needs_revision"
        flagged_ids = [r["id"] for r in data["fragmenting_rules"]]
        assert "T02" in flagged_ids
        assert "T01" not in flagged_ids

    def test_score_draft_missing_arg_exits_nonzero(self):
        """--score-draft with no file argument exits 1."""
        result = _run_audit(["--score-draft"])
        assert result.returncode == 1
        assert "Usage" in result.stderr

    def test_score_draft_bad_file_exits_nonzero(self, tmp_path):
        """--score-draft with nonexistent file exits nonzero."""
        result = _run_audit(
            ["--score-draft", str(tmp_path / "nonexistent.json")],
            cwd=str(tmp_path),
        )
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# --finalize-draft tests
# ---------------------------------------------------------------------------

class TestFinalizeDraft:
    def test_finalize_draft_produces_grades(self, tmp_path):
        """--finalize-draft reads scored + judgments and outputs grades."""
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()

        rule_ids = ["D01", "D02", "D03"]
        rules = [_make_rule(rid, line_start=5 + i)
                 for i, rid in enumerate(rule_ids)]
        scored = _make_scored_data(rules)

        with open(tmp_dir / "draft_scored_semi.json", "w", encoding="utf-8") as f:
            json.dump(scored, f)

        judgments = _make_judgment_array(rule_ids, f3=0.85, f8=0.90)
        with open(tmp_dir / "draft_judgments.json", "w", encoding="utf-8") as f:
            json.dump(judgments, f)

        result = _run_audit(["--finalize-draft"], cwd=str(tmp_path))
        assert result.returncode == 0, f"--finalize-draft failed: {result.stderr}"

        data = json.loads(result.stdout)
        assert "rules" in data
        assert "all_pass" in data
        assert "floor" in data
        assert len(data["rules"]) == 3

        for rule in data["rules"]:
            assert "score" in rule
            assert "grade" in rule
            assert "pass" in rule
            assert "friendly_summary" in rule
            assert "dominant_weakness" in rule
            assert rule["grade"] in ("A", "B", "C", "D", "F")

    def test_finalize_draft_detects_failing_rules(self, tmp_path):
        """--finalize-draft flags rules below the category floor."""
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()

        # One strong rule, one weak rule (low F7 drags score down).
        strong = _make_rule("D01", line_start=5)
        weak = _make_rule("D02", line_start=6)
        weak["factors"]["F7"] = {"value": 0.10, "method": "count",
                                 "concrete_count": 0, "abstract_count": 3}
        weak["factors"]["F1"] = {"value": 0.20, "method": "lookup"}
        scored = _make_scored_data([strong, weak])

        with open(tmp_dir / "draft_scored_semi.json", "w", encoding="utf-8") as f:
            json.dump(scored, f)

        judgments = _make_judgment_array(["D01", "D02"], f3=0.70, f8=0.60)
        with open(tmp_dir / "draft_judgments.json", "w", encoding="utf-8") as f:
            json.dump(judgments, f)

        result = _run_audit(["--finalize-draft"], cwd=str(tmp_path))
        assert result.returncode == 0, f"--finalize-draft failed: {result.stderr}"

        data = json.loads(result.stdout)
        assert data["all_pass"] is False

        failing = [r for r in data["rules"] if not r["pass"]]
        assert len(failing) >= 1
        assert failing[0]["id"] == "D02"


# ---------------------------------------------------------------------------
# Draft namespace isolation tests
# ---------------------------------------------------------------------------

class TestDraftNamespaceIsolation:
    def test_score_draft_does_not_overwrite_audit_state(self, tmp_path):
        """--score-draft writes to draft_scored_semi.json, not scored_semi.json."""
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()

        # Simulate existing audit state
        audit_scored = {"sentinel": "audit_data", "rules": [], "source_files": []}
        with open(tmp_dir / "scored_semi.json", "w", encoding="utf-8") as f:
            json.dump(audit_scored, f)

        # Run draft scoring
        draft = {
            "rules": [{"id": "T01", "text": "Use early returns over nested ifs."}],
            "file": ".claude/rules/test.md",
            "category": "mandate",
        }
        draft_path = tmp_path / "draft.json"
        draft_path.write_text(json.dumps(draft), encoding="utf-8")

        result = _run_audit(
            ["--score-draft", str(draft_path)],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

        # Audit state must be untouched
        with open(tmp_dir / "scored_semi.json", encoding="utf-8") as f:
            preserved = json.load(f)
        assert preserved["sentinel"] == "audit_data"

        # Draft state must exist separately
        assert (tmp_dir / "draft_scored_semi.json").exists()

    def test_finalize_draft_uses_draft_namespace(self, tmp_path):
        """--finalize-draft reads draft_* files, not audit files."""
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()

        rule_ids = ["D01", "D02"]
        rules = [_make_rule(rid, line_start=5 + i)
                 for i, rid in enumerate(rule_ids)]
        scored = _make_scored_data(rules)

        # Write to draft namespace
        with open(tmp_dir / "draft_scored_semi.json", "w", encoding="utf-8") as f:
            json.dump(scored, f)
        judgments = _make_judgment_array(rule_ids, f3=0.85, f8=0.90)
        with open(tmp_dir / "draft_judgments.json", "w", encoding="utf-8") as f:
            json.dump(judgments, f)

        # DO NOT write audit namespace files — finalize-draft must not need them
        assert not (tmp_dir / "scored_semi.json").exists()
        assert not (tmp_dir / "all_judgments.json").exists()

        result = _run_audit(["--finalize-draft"], cwd=str(tmp_path))
        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert len(data["rules"]) == 2

        # Draft output goes to draft_audit.json, not audit.json
        assert (tmp_dir / "draft_audit.json").exists()
        assert not (tmp_dir / "audit.json").exists()

    def test_audit_state_survives_draft_cycle(self, tmp_path):
        """Full audit→draft→audit cycle: audit state survives draft scoring."""
        tmp_dir = tmp_path / ".rulesense-tmp"
        tmp_dir.mkdir()

        # Simulate completed audit state (3 rules, one below floor)
        audit_rule_ids = ["R01", "R02", "R03"]
        audit_rules = [_make_rule(rid, line_start=10 + i)
                       for i, rid in enumerate(audit_rule_ids)]
        # Make R03 weak
        audit_rules[2]["factors"]["F7"] = {"value": 0.10, "method": "count",
                                           "concrete_count": 0, "abstract_count": 3}
        audit_rules[2]["factors"]["F1"] = {"value": 0.15, "method": "lookup"}
        audit_scored = _make_scored_data(audit_rules)

        with open(tmp_dir / "scored_semi.json", "w", encoding="utf-8") as f:
            json.dump(audit_scored, f)
        audit_judgments = _make_judgment_array(audit_rule_ids, f3=0.70, f8=0.80)
        with open(tmp_dir / "all_judgments.json", "w", encoding="utf-8") as f:
            json.dump(audit_judgments, f)

        # Finalize the audit
        result = _run_audit(["--finalize"], cwd=str(tmp_path))
        assert result.returncode == 0
        assert (tmp_dir / "audit.json").exists()

        # Now simulate the draft cycle (gap bridge)
        draft = {
            "rules": [{"id": "XX01", "text": "Use early returns."}],
            "file": ".claude/rules/new.md",
            "category": "mandate",
        }
        draft_path = tmp_path / "draft.json"
        draft_path.write_text(json.dumps(draft), encoding="utf-8")

        result = _run_audit(
            ["--score-draft", str(draft_path)],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

        # Write draft judgments
        draft_judgments = _make_judgment_array(["XX01"], f3=0.90, f8=0.85)
        with open(tmp_dir / "draft_judgments.json", "w", encoding="utf-8") as f:
            json.dump(draft_judgments, f)

        # Finalize draft
        result = _run_audit(["--finalize-draft"], cwd=str(tmp_path))
        assert result.returncode == 0

        # CRITICAL ASSERTION: audit state is INTACT
        with open(tmp_dir / "audit.json", encoding="utf-8") as f:
            audit = json.load(f)
        assert len(audit["rules"]) == 3  # original 3, not draft's 1
        assert any(r["id"] == "R03" for r in audit["rules"])

        # Prepare-fix should find qualifying rules from the ORIGINAL audit
        result = _run_audit(["--prepare-fix"], cwd=str(tmp_path))
        assert result.returncode == 0
        fix_data = json.loads(result.stdout)
        assert fix_data["qualifying_count"] >= 1  # R03 should qualify


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_prepare_pipeline_sample_project(self, tmp_path):
        """End-to-end --prepare on sample_project produces valid scored data."""
        project = tmp_path / "sample_project"
        shutil.copytree(FIXTURES_DIR / "sample_project", project)

        result = _run_audit(
            ["--prepare", "--project-root", str(project)],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, f"--prepare failed: {result.stderr}"

        # Verify scored_semi.json structure
        scored_path = tmp_path / ".rulesense-tmp" / "scored_semi.json"
        scored = json.loads(scored_path.read_text(encoding="utf-8"))
        assert scored["schema_version"] == "0.1"
        assert "rules" in scored
        assert "source_files" in scored
        assert len(scored["rules"]) > 0

        # Every rule should have F1, F2, F4, F7 factors
        for rule in scored["rules"]:
            factors = rule.get("factors", {})
            for fn in ("F1", "F2", "F4", "F7"):
                assert fn in factors, f"Rule {rule['id']} missing {fn}"
