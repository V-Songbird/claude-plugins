"""Tests for discover.py — filesystem discovery and project context."""

import json
import os
from pathlib import Path

import pytest
from conftest import run_script, run_script_raw, FIXTURES_DIR


class TestFileDiscovery:
    def test_finds_instruction_files(self, sample_project):
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        paths = [sf["path"] for sf in result["source_files"]]
        assert "CLAUDE.md" in paths
        assert ".claude/rules/api.md" in paths

    def test_reads_file_content(self, sample_project):
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        claude_md = next(sf for sf in result["source_files"] if sf["path"] == "CLAUDE.md")
        assert "ALWAYS validate user input" in claude_md["content"]

    def test_glob_resolution(self, sample_project):
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        api_md = next(sf for sf in result["source_files"] if sf["path"] == ".claude/rules/api.md")
        assert api_md["glob_match_count"] >= 1  # handler.ts matches

    def test_primary_file_fatal(self, tmp_path):
        """Missing CLAUDE.md with no .claude/rules/ → fatal exit."""
        proc = run_script_raw("discover.py", args=["--project-root", str(tmp_path)])
        assert proc.returncode != 0
        assert "FATAL" in proc.stderr

    def test_peripheral_file_skip(self, sample_project):
        """Bad .claude/rules/ file → skip + warn, other files still discovered."""
        bad_file = sample_project / ".claude" / "rules" / "broken.md"
        bad_file.write_text("\x00\x01\x02 invalid utf-8-ish content but valid bytes", encoding="utf-8")
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        paths = [sf["path"] for sf in result["source_files"]]
        assert "CLAUDE.md" in paths
        assert ".claude/rules/api.md" in paths


class TestStackDetection:
    def test_project_context_react(self, sample_project):
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        assert "react" in result["project_context"]["stack"]

    def test_project_context_typescript(self, sample_project):
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        assert "typescript" in result["project_context"]["stack"]

    def test_project_context_unknown(self, tmp_path):
        """No manifest files → empty stack, no crash."""
        (tmp_path / "CLAUDE.md").write_text("- Use consistent naming.\n")
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        assert result["project_context"]["stack"] == []

    def test_project_context_python(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("- Use type hints.\n")
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        assert "python" in result["project_context"]["stack"]


class TestConfigDiscovery:
    def test_config_loading(self, sample_project):
        (sample_project / ".rulesense.config").write_text(
            '# load_prob overrides\n".claude/rules/api.md": 0.8\n'
        )
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        assert ".claude/rules/api.md" in result["config"]["load_prob_overrides"]

    def test_ignore_loading(self, sample_project):
        (sample_project / ".rulesense-ignore").write_text(
            "# Ignored rules\nCLAUDE.md: \"Try to prefer\"\n"
        )
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        assert len(result["config"]["ignore_patterns"]) == 1

    def test_no_walk_up(self, sample_project):
        """Config files in parent directory should NOT be discovered."""
        parent = sample_project.parent
        (parent / ".rulesense.config").write_text('"some-file.md": 0.9\n')
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        # Parent config should not be loaded
        assert "some-file.md" not in result["config"]["load_prob_overrides"]


class TestSchemaStructure:
    def test_schema_fields(self, sample_project):
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        assert result["schema_version"] == "0.1"
        assert result["pipeline_version"] == "0.1.0"
        assert "project_context" in result
        assert "config" in result
        assert "source_files" in result
        assert "entity_index" in result

    def test_always_loaded_classification(self, sample_project):
        result = run_script("discover.py", args=["--project-root", str(sample_project)])
        claude_md = next(sf for sf in result["source_files"] if sf["path"] == "CLAUDE.md")
        api_md = next(sf for sf in result["source_files"] if sf["path"] == ".claude/rules/api.md")
        assert claude_md["always_loaded"] is True
        assert api_md["always_loaded"] is False


# ---------------------------------------------------------------------------
# Phase 2a: Tooling detection
# ---------------------------------------------------------------------------

class TestToolingDetection:
    """Phase 2a: detect_tooling() identifies configured enforcement tools."""

    def test_detect_eslint(self, tmp_path):
        """ESLint config file → eslint: True."""
        (tmp_path / "CLAUDE.md").write_text("- Always validate input.\n")
        (tmp_path / ".eslintrc.json").write_text("{}")
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        tooling = result["project_context"]["tooling"]
        assert tooling["eslint"] is True

    def test_detect_prettier(self, tmp_path):
        """Prettier config file → prettier: True."""
        (tmp_path / "CLAUDE.md").write_text("- Always validate input.\n")
        (tmp_path / ".prettierrc").write_text("{}")
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        tooling = result["project_context"]["tooling"]
        assert tooling["prettier"] is True

    def test_detect_nothing(self, tmp_path):
        """No tooling files → all False."""
        (tmp_path / "CLAUDE.md").write_text("- Always validate input.\n")
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        tooling = result["project_context"]["tooling"]
        assert tooling["eslint"] is False
        assert tooling["prettier"] is False
        assert tooling["git_hooks"] is False

    def test_tooling_in_project_context(self, tmp_path):
        """Tooling field is present in project_context output."""
        (tmp_path / "CLAUDE.md").write_text("- Always validate input.\n")
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        assert "tooling" in result["project_context"]

    def test_undetected_tool_not_in_output(self, tmp_path):
        """Tools not in the detector list (e.g., biome) are not detected.
        This test documents the boundary — it pins which tools we DO detect."""
        (tmp_path / "CLAUDE.md").write_text("- Always validate input.\n")
        (tmp_path / "biome.json").write_text("{}")  # biome is not in our detector list
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        tooling = result["project_context"]["tooling"]
        assert "biome" not in tooling  # We don't detect biome yet


# ---------------------------------------------------------------------------
# Regression: Bug 3 — YAML list-form globs
# ---------------------------------------------------------------------------

class TestGlobParsingRegression:
    """Regression tests: YAML inline list-form globs must be parsed correctly."""

    def test_yaml_list_single(self, tmp_path):
        """globs: ["src/api/**/*.ts"] → parsed without brackets/quotes."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\nglobs: ["src/api/**/*.ts"]\n---\n\n- A rule.\n'
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**/*.ts"]

    def test_yaml_list_multiple(self, tmp_path):
        """globs: ["src/api/**", "src/lib/**"] → two clean patterns."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\nglobs: ["src/api/**", "src/lib/**"]\n---\n\n- A rule.\n'
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**", "src/lib/**"]

    def test_yaml_list_single_quotes(self, tmp_path):
        """globs: ['src/api/**'] → handles single quotes."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            "---\nglobs: ['src/api/**']\n---\n\n- A rule.\n"
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**"]

    def test_plain_globs_still_work(self, tmp_path):
        """globs: src/api/**/*.ts (no brackets) → still works."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\nglobs: src/api/**/*.ts\n---\n\n- A rule.\n'
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**/*.ts"]

    def test_block_list_globs_parsed(self, tmp_path):
        """Block-list YAML for globs: is now parsed correctly."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            "---\nglobs:\n  - src/api/**/*.ts\n  - src/lib/**/*.ts\n---\n\n- A rule.\n"
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**/*.ts", "src/lib/**/*.ts"]
        assert api_md["always_loaded"] is False


# ---------------------------------------------------------------------------
# F-25: .claude/CLAUDE.md alternate location
# ---------------------------------------------------------------------------

class TestClaudeMdDiscovery:
    """F-25: discover.py should find CLAUDE.md at both root and .claude/ locations."""

    def test_root_claude_md_discovered(self, tmp_path):
        """Only root-level CLAUDE.md → discovered, always_loaded=True."""
        (tmp_path / "CLAUDE.md").write_text("- Always validate input.\n")
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        paths = [sf["path"] for sf in result["source_files"]]
        assert "CLAUDE.md" in paths
        claude = next(sf for sf in result["source_files"] if sf["path"] == "CLAUDE.md")
        assert claude["always_loaded"] is True

    def test_dot_claude_claude_md_discovered(self, tmp_path):
        """Only .claude/CLAUDE.md → discovered, always_loaded=True."""
        dot_claude = tmp_path / ".claude"
        dot_claude.mkdir()
        (dot_claude / "CLAUDE.md").write_text("- Always validate input.\n")
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        paths = [sf["path"] for sf in result["source_files"]]
        assert ".claude/CLAUDE.md" in paths
        claude = next(sf for sf in result["source_files"] if sf["path"] == ".claude/CLAUDE.md")
        assert claude["always_loaded"] is True

    def test_both_locations_root_wins(self, tmp_path):
        """Both CLAUDE.md and .claude/CLAUDE.md → root used, warning on stderr."""
        (tmp_path / "CLAUDE.md").write_text("- Root rule.\n")
        dot_claude = tmp_path / ".claude"
        dot_claude.mkdir()
        (dot_claude / "CLAUDE.md").write_text("- Alt rule.\n")
        proc = run_script_raw("discover.py", args=["--project-root", str(tmp_path)])
        assert proc.returncode == 0
        assert ("WARNING: Found both CLAUDE.md and .claude/CLAUDE.md. "
                "Using CLAUDE.md (root). The .claude/CLAUDE.md file will be ignored.") in proc.stderr
        result = json.loads(proc.stdout)
        paths = [sf["path"] for sf in result["source_files"]]
        assert "CLAUDE.md" in paths
        assert ".claude/CLAUDE.md" not in paths

    def test_neither_location_fatals(self, tmp_path):
        """No CLAUDE.md anywhere and no .claude/rules/ → fatal."""
        proc = run_script_raw("discover.py", args=["--project-root", str(tmp_path)])
        assert proc.returncode != 0
        assert "FATAL" in proc.stderr


# ---------------------------------------------------------------------------
# F-26: build_entity_index fence-safety
# ---------------------------------------------------------------------------

class TestF26EntityIndexFenceSafety:
    """F-26: build_entity_index regex must not greedy-match across code fences."""

    def test_build_entity_index_does_not_match_across_fences(self, tmp_path):
        """Content like ```javascript\\nimport x from 'foo/bar';\\n```
        must not produce a multi-hundred-char phantom path entity."""
        (tmp_path / "CLAUDE.md").write_text(
            "Use the config:\n\n"
            "```javascript\n"
            "import x from 'foo/bar';\n"
            "import y from 'baz/qux';\n"
            "```\n\n"
            "- Always validate input.\n"
        )
        proc = run_script_raw("discover.py", args=["--project-root", str(tmp_path)])
        assert proc.returncode == 0, f"discover crashed: {proc.stderr[:200]}"
        result = json.loads(proc.stdout)
        for entity_name in result.get("entity_index", {}):
            assert len(entity_name) < 250, f"Phantom long entity: {entity_name[:80]}..."


class TestF14PackageIndex:
    """F-14 (partial): entity index tracks packages from manifests as known entities."""

    def test_known_package_indexed_as_existing(self, tmp_path):
        """A backtick-wrapped package name present in package.json deps → indexed with exists=True."""
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"axios": "^1.0.0", "zod": "^3.0.0"}})
        )
        (tmp_path / "CLAUDE.md").write_text(
            "- Use `axios` for HTTP calls.\n"
            "- Validate request bodies with `zod`.\n"
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        index = result.get("entity_index", {})
        assert "axios" in index
        assert index["axios"] == {"kind": "package", "exists": True}
        assert "zod" in index
        assert index["zod"] == {"kind": "package", "exists": True}

    def test_unknown_identifier_not_indexed(self, tmp_path):
        """Backtick identifiers not in any manifest are NOT added to the index
        (F-14 partial scope — missing-package detection is out of scope)."""
        (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"react": "^18.0.0"}}))
        (tmp_path / "CLAUDE.md").write_text(
            "- Use `SomeArbitraryThing` for prose.\n"
            "- Use `react` for UI.\n"
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        index = result.get("entity_index", {})
        assert "react" in index
        assert "SomeArbitraryThing" not in index

    def test_package_index_works_with_pyproject_toml(self, tmp_path):
        """Python projects: pyproject.toml [project.dependencies] names are indexed."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "myproj"\n'
            'dependencies = ["requests>=2.0", "pydantic"]\n'
        )
        (tmp_path / "CLAUDE.md").write_text(
            "- Use `requests` for HTTP.\n"
            "- Use `pydantic` for validation.\n"
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        index = result.get("entity_index", {})
        assert "requests" in index
        assert index["requests"]["kind"] == "package"
        assert "pydantic" in index


class TestPathsFieldSupport:
    """paths: is the canonical frontmatter field per Claude Code docs.
    globs: is accepted as backward-compat fallback.
    """

    def test_paths_block_list(self, tmp_path):
        """paths: with YAML block list (the documented format)."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\npaths:\n  - "src/api/**/*.ts"\n  - "lib/**/*.ts"\n---\n\n- A rule.\n'
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**/*.ts", "lib/**/*.ts"]
        assert api_md["always_loaded"] is False

    def test_paths_inline_list(self, tmp_path):
        """paths: ["src/api/**"] inline format."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\npaths: ["src/api/**/*.ts"]\n---\n\n- A rule.\n'
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**/*.ts"]
        assert api_md["always_loaded"] is False

    def test_paths_plain_string(self, tmp_path):
        """paths: src/api/** plain string (undocumented but accepted)."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\npaths: src/api/**\n---\n\n- A rule.\n'
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**"]

    def test_paths_takes_precedence_over_globs(self, tmp_path):
        """When both paths: and globs: present, paths: wins."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\npaths: src/api/**\nglobs: src/lib/**\n---\n\n- A rule.\n'
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**"]

    def test_globs_backward_compat(self, tmp_path):
        """globs: still works as backward-compat fallback."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\nglobs: src/api/**\n---\n\n- API rule.\n'
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**"]
        assert api_md["always_loaded"] is False

    def test_no_paths_no_globs_always_loaded(self, tmp_path):
        """No scoping frontmatter → always_loaded=True per Claude Code docs."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "general.md").write_text("# General\n\n- A rule.\n")
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        gen_md = next(sf for sf in result["source_files"] if "general.md" in sf["path"])
        assert gen_md["always_loaded"] is True

    def test_empty_paths_falls_through_to_globs(self, tmp_path):
        """Empty paths: field with real globs: below → globs: wins.

        Regression for P2.4: mid-migration state where user adds empty paths:
        before filling in values. Must not silently suppress globs: fallback.
        """
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            "---\npaths:\nglobs: src/api/**\n---\n\n- A rule.\n"
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**"]
        assert api_md["always_loaded"] is False

    def test_paths_wrong_type_integer(self, tmp_path):
        """paths: 42 (integer) — characterization test for malformed input.

        Documents discover.py's actual behavior: the YAML-lite parser reads
        the integer as a bare string "42" and the downstream glob handler
        treats it as a single-item glob pattern. Not a crash, but a
        degenerate fallback (the literal path "42" will match no files in
        practice). If discover.py ever adds strict type validation for
        paths:, this test will fail and force an explicit spec decision.
        """
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            "---\npaths: 42\n---\n\n- A rule.\n"
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        # Integer coerced to string glob — documents current behavior.
        assert api_md["globs"] == ["42"]
        assert api_md["always_loaded"] is False
        assert api_md["glob_match_count"] == 0

    def test_paths_with_default_category(self, tmp_path):
        """paths: block list + default-category: both fields coexist cleanly.

        Regression guard: the parse_frontmatter block-list handler uses a
        continue statement that could accidentally consume subsequent
        frontmatter keys. This test pins the intended behavior — both
        fields survive parsing and appear in the source_file output.
        """
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\npaths:\n  - "src/api/**/*.ts"\ndefault-category: recommendation\n---\n\n- A rule.\n'
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["globs"] == ["src/api/**/*.ts"]
        assert api_md["default_category"] == "recommendation"
        assert api_md["always_loaded"] is False


# ---------------------------------------------------------------------------
# Regression: Bug 6 — always_loaded shadowing
# ---------------------------------------------------------------------------

class TestAlwaysLoadedRegression:
    """Regression tests: .claude/rules/ files without globs should be always-loaded."""

    def test_rules_file_no_globs_is_always_loaded(self, tmp_path):
        """.claude/rules/foo.md without globs → always_loaded=True."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "foo.md").write_text("# General rules\n\n- A rule.\n")
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        foo_md = next(sf for sf in result["source_files"] if "foo.md" in sf["path"])
        assert foo_md["always_loaded"] is True

    def test_rules_file_with_globs_is_not_always_loaded(self, tmp_path):
        """.claude/rules/api.md WITH globs → always_loaded=False."""
        (tmp_path / "CLAUDE.md").write_text("- Global rule.\n")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text(
            '---\nglobs: src/api/**\n---\n\n- API rule.\n'
        )
        result = run_script("discover.py", args=["--project-root", str(tmp_path)])
        api_md = next(sf for sf in result["source_files"] if "api.md" in sf["path"])
        assert api_md["always_loaded"] is False
