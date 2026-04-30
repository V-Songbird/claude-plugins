"""Tests for extract.py — instruction parser (pure JSON fixtures, no sample_project needed)."""

import json
from pathlib import Path

import pytest
from conftest import run_script, run_script_raw, FIXTURES_DIR


def _make_context(content: str, path: str = "CLAUDE.md", globs: list | None = None,
                  default_category: str = "mandate", entity_index: dict | None = None) -> dict:
    """Build a minimal project_context.json for testing extract.py."""
    return {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_context": {"stack": [], "always_loaded_files": [path], "glob_scoped_files": []},
        "config": {"load_prob_overrides": {}, "severity_overrides": {}, "ignore_patterns": []},
        "source_files": [{
            "path": path,
            "globs": globs or [],
            "glob_match_count": None,
            "default_category": default_category,
            "line_count": content.count("\n") + 1,
            "always_loaded": not bool(globs),
            "content": content,
        }],
        "entity_index": entity_index or {},
    }


class TestWorkedExample:
    """Test against the exact worked example from instruction-parser.md."""

    WORKED_EXAMPLE = (
        "---\n"
        'globs: "src/api/**/*.ts"\n'
        "default-category: mandate\n"
        "---\n"
        "\n"
        "# API Rules\n"
        "\n"
        "- Validate all request bodies at the handler boundary.\n"
        "- Return consistent error shapes: `{ error: string, code: number }`.\n"
        "  This ensures clients can parse errors uniformly.\n"
        "- Use middleware for cross-cutting concerns (auth, logging) — not inline checks.\n"
        "\n"
        "## Database Access\n"
        "\n"
        "<!-- category: preference -->\n"
        "- Prefer transactions for queries spanning multiple tables.\n"
        "- Consider using read replicas for heavy read operations where latency is acceptable.\n"
        "\n"
        "The API layer uses Express with TypeScript strict mode enabled.\n"
    )

    def test_worked_example_rule_count(self):
        ctx = _make_context(self.WORKED_EXAMPLE, path=".claude/rules/api.md",
                            globs=["src/api/**/*.ts"])
        result = run_script("extract.py", stdin_data=ctx)
        assert len(result["rules"]) == 5

    def test_worked_example_rule_texts(self):
        ctx = _make_context(self.WORKED_EXAMPLE, path=".claude/rules/api.md",
                            globs=["src/api/**/*.ts"])
        result = run_script("extract.py", stdin_data=ctx)
        texts = [r["text"] for r in result["rules"]]

        assert "Validate all request bodies at the handler boundary." in texts
        # Rule 2 should merge with clarification
        assert any("Return consistent error shapes" in t and "clients can parse" in t for t in texts)
        assert any("Use middleware" in t for t in texts)
        assert any("Prefer transactions" in t for t in texts)
        assert any("Consider using read replicas" in t for t in texts)

    def test_worked_example_categories(self):
        ctx = _make_context(self.WORKED_EXAMPLE, path=".claude/rules/api.md",
                            globs=["src/api/**/*.ts"])
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]

        # First 3 rules: mandate (from default-category)
        for r in rules[:3]:
            assert r["category"] == "mandate", f"Rule '{r['text'][:40]}' should be mandate"

        # Last 2 rules: preference (from annotation)
        for r in rules[3:]:
            assert r["category"] == "preference", f"Rule '{r['text'][:40]}' should be preference"

    def test_worked_example_prose_excluded(self):
        ctx = _make_context(self.WORKED_EXAMPLE, path=".claude/rules/api.md",
                            globs=["src/api/**/*.ts"])
        result = run_script("extract.py", stdin_data=ctx)
        texts = [r["text"] for r in result["rules"]]
        # "The API layer uses Express..." is prose, should not appear
        assert not any("The API layer uses Express" in t for t in texts)


class TestExtractionDeterminism:
    def test_extraction_determinism(self):
        ctx = _make_context("- ALWAYS use strict mode.\n- Prefer named exports.\n")
        result1 = run_script("extract.py", stdin_data=ctx)
        result2 = run_script("extract.py", stdin_data=ctx)
        assert result1["rules"] == result2["rules"]


class TestMetadataStripping:
    def test_frontmatter_stripped(self):
        ctx = _make_context("---\nglobs: \"src/**\"\n---\n\n- Use strict mode.\n",
                            globs=["src/**"])
        result = run_script("extract.py", stdin_data=ctx)
        assert len(result["rules"]) == 1
        assert "globs" not in result["rules"][0]["text"]

    def test_headings_stripped(self):
        ctx = _make_context("# Rules\n\n- Use strict mode.\n\n## More\n\n- Always test.\n")
        result = run_script("extract.py", stdin_data=ctx)
        assert not any("# Rules" in r["text"] for r in result["rules"])
        assert not any("## More" in r["text"] for r in result["rules"])


class TestCompoundSplit:
    def test_compound_split(self):
        ctx = _make_context("- Run tests before committing and ensure no warnings remain.\n")
        result = run_script("extract.py", stdin_data=ctx)
        assert len(result["rules"]) == 2

    def test_compound_nosplit(self):
        ctx = _make_context("- Edit the .bnf source and regenerate.\n")
        result = run_script("extract.py", stdin_data=ctx)
        assert len(result["rules"]) == 1


class TestClarificationMerge:
    def test_clarification_merge(self):
        ctx = _make_context(
            "- Use TypeScript strict mode for all new files.\n"
            "  This ensures type safety across the codebase.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        assert len(result["rules"]) == 1
        assert "type safety" in result["rules"][0]["text"]


# ---------------------------------------------------------------------------
# Phase H: Orphaned list items under parent directives
# ---------------------------------------------------------------------------

class TestDirectiveBulletMerge:
    """Verbless bullet items under a directive paragraph should merge into
    the parent rather than being extracted as standalone F-grade rules."""

    def test_verbless_bullets_merged_into_parent_directive(self):
        """Directive paragraph followed by verbless bullet list items should
        be extracted as ONE rule, not N+1 rules.

        Reproduces the Dallas-Digital 'forbidden phrases' pattern:
        directive paragraph with 'Don't use' + single-word bullet items.
        """
        ctx = _make_context(
            "These scream AI. Don't use them anywhere:\n"
            "- Synergy\n"
            "- Leverage\n"
            "- Innovative\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        # Should be 1 merged rule, not 4 separate rules
        assert len(rules) == 1, (
            f"Expected 1 merged rule, got {len(rules)}: "
            f"{[r['text'][:50] for r in rules]}"
        )
        # The merged text should contain both the directive and the items
        assert "Don't use" in rules[0]["text"]
        assert "Synergy" in rules[0]["text"]

    def test_verb_bearing_bullets_stay_standalone(self):
        """Bullets with their own imperative verbs should NOT be merged
        into a preceding paragraph, even if the paragraph is also a rule."""
        ctx = _make_context(
            "Write clean, readable code.\n"
            "- Use early returns over nested ifs.\n"
            "- Prefer flat objects over deep nesting.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        # Each bullet should stay standalone because they have their own verbs
        assert len(rules) >= 3, (
            f"Expected at least 3 standalone rules, got {len(rules)}: "
            f"{[r['text'][:50] for r in rules]}"
        )

class TestCategories:
    def test_category_annotation(self):
        ctx = _make_context(
            "<!-- category: preference -->\n"
            "- Prefer named exports over default exports.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        assert result["rules"][0]["category"] == "preference"

    def test_default_category(self):
        ctx = _make_context("- Always validate input.\n", default_category="override")
        result = run_script("extract.py", stdin_data=ctx)
        assert result["rules"][0]["category"] == "override"


# ---------------------------------------------------------------------------
# F-23: Content filtering (fenced code blocks, tables, bare links)
# ---------------------------------------------------------------------------

class TestF23ContentFiltering:
    """F-23: Non-directive content should be excluded from extraction."""

    def test_fenced_code_block_excluded(self):
        """Lines inside ``` fences are not extracted as rules.
        The line immediately preceding the fence (e.g., 'Use this RTK Query pattern:')
        IS still extracted — only the fence content itself is excluded.
        """
        ctx = _make_context(
            "- Use this RTK Query pattern:\n\n"
            "```typescript\n"
            "export const userApi = createApi({\n"
            "  reducerPath: 'userApi',\n"
            "});\n"
            "```\n\n"
            "- Always validate input.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        texts = [r["text"] for r in result["rules"]]
        # Intro line before fence IS extracted
        assert any("RTK Query pattern" in t for t in texts)
        # Post-fence rule IS extracted
        assert any("validate input" in t for t in texts)
        # Fence content is NOT extracted
        assert not any("createApi" in t for t in texts)
        assert not any("reducerPath" in t for t in texts)

    def test_indented_code_block_not_excluded(self):
        """The extractor only handles fenced code blocks. Indented code is still extracted.
        Bookmarked for v1.2; this test pins the current boundary."""
        ctx = _make_context(
            "- Use this pattern:\n\n"
            "    const x = 5;\n"
            "    return x;\n\n"
            "- Always validate input.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        texts = [r["text"] for r in result["rules"]]
        # Indented code is NOT excluded — boundary pin
        assert any("validate input" in t for t in texts)

    def test_markdown_table_rows_excluded(self):
        """Lines that are part of a markdown table are not extracted as rules."""
        ctx = _make_context(
            "## File naming\n\n"
            "| Type | Convention |\n"
            "|------|------------|\n"
            "| Components | PascalCase.tsx |\n"
            "| Hooks | useCamelCase.ts |\n\n"
            "- Always validate user input.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        texts = [r["text"] for r in result["rules"]]
        assert any("validate user input" in t for t in texts)
        assert not any("PascalCase" in t for t in texts)
        assert not any("useCamelCase" in t for t in texts)
        assert not any("Convention" in t for t in texts)

    def test_pipe_in_prose_not_excluded(self):
        """Prose containing pipe characters is NOT treated as a table row.
        The state machine requires a separator line (|---|) to enter table state."""
        ctx = _make_context(
            "- Use the pipe operator: `cat file.txt | grep foo`\n"
            "- Always validate input.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        texts = [r["text"] for r in result["rules"]]
        assert any("pipe operator" in t for t in texts)
        assert any("validate input" in t for t in texts)

    def test_bare_reference_link_excluded(self):
        """List items containing only a markdown link are not extracted."""
        ctx = _make_context(
            "## References\n\n"
            "- [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)\n"
            "- [WCAG 2.2](https://www.w3.org/WAI/WCAG22/)\n"
            "- Always check [the docs](./docs.md) before modifying the API.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        texts = [r["text"] for r in result["rules"]]
        # Bare links are excluded
        assert not any("DESIGN_SYSTEM.md](./" in t for t in texts)
        assert not any("WCAG 2.2](" in t for t in texts)
        # Link with directive prose around it stays (has "Always check")
        assert any("check" in t and "docs" in t for t in texts)

    def test_fenced_block_inside_table_not_double_excluded(self):
        """Edge case: a code fence inside a table region doesn't break state tracking."""
        ctx = _make_context(
            "| Col A | Col B |\n"
            "|-------|-------|\n"
            "| val   | val   |\n\n"
            "```bash\n"
            "echo hello\n"
            "```\n\n"
            "- Always validate input.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        texts = [r["text"] for r in result["rules"]]
        assert any("validate input" in t for t in texts)
        assert not any("echo hello" in t for t in texts)
        assert not any("Col A" in t for t in texts)


class TestEntityExtraction:
    def test_entity_extraction(self):
        ctx = _make_context("- Use `getProjectCommands(project)` not `.database.commands`.\n")
        result = run_script("extract.py", stdin_data=ctx)
        entities = result["rules"][0]["referenced_entities"]
        names = [e["name"] for e in entities]
        assert "getProjectCommands(project)" in names

    def test_staleness_crossref(self):
        ctx = _make_context(
            "- NEVER edit files in `src/main/gen/` directly.\n",
            entity_index={"src/main/gen/": {"kind": "path", "exists": False}},
        )
        result = run_script("extract.py", stdin_data=ctx)
        rule = result["rules"][0]
        assert rule["staleness"]["gated"] is True
        assert "src/main/gen/" in rule["staleness"]["missing_entities"]


# ---------------------------------------------------------------------------
# F-14: Path-kind entities not in entity_index
# ---------------------------------------------------------------------------

class TestF14StalenessGating:
    def test_path_entity_with_slash_not_in_index_is_stale(self):
        """Slashed path not in entity_index → exists=False, staleness gated."""
        ctx = _make_context(
            "- Always update `src/foo/missing.ts` after changes.\n",
            entity_index={},  # empty — no paths discovered
        )
        result = run_script("extract.py", stdin_data=ctx)
        rule = result["rules"][0]
        entity = next(e for e in rule["referenced_entities"] if e["name"] == "src/foo/missing.ts")
        assert entity["exists"] is False
        assert entity["kind"] == "path"
        assert rule["staleness"]["gated"] is True

    def test_path_entity_without_slash_not_falsely_stale(self):
        """Slash-less filename like `Button.tsx` should NOT be falsely stale.

        Regression test for P2.1: entity_index only indexes paths with slashes.
        Slash-less filenames classified as kind='path' by extract.py stay
        exists=None (genuinely unknown) and must NOT trigger staleness gating.
        """
        ctx = _make_context(
            "- Use `Button.tsx` for new buttons.\n",
            entity_index={},
        )
        result = run_script("extract.py", stdin_data=ctx)
        rule = result["rules"][0]
        entity = next(e for e in rule["referenced_entities"] if e["name"] == "Button.tsx")
        assert entity["exists"] is None  # NOT False
        assert rule["staleness"]["gated"] is False

    def test_api_entity_remains_none(self):
        """API-kind entity (uppercase, no slash) stays exists=None."""
        ctx = _make_context(
            "- Always use `SomeAPIClient` for requests.\n",
            entity_index={},
        )
        result = run_script("extract.py", stdin_data=ctx)
        rule = result["rules"][0]
        entity = next(e for e in rule["referenced_entities"] if e["name"] == "SomeAPIClient")
        assert entity["exists"] is None
        assert entity["kind"] == "api"
        assert rule["staleness"]["gated"] is False

    def test_common_config_files_not_falsely_stale(self):
        """Common config filenames (package.json, tsconfig.json) must not trigger staleness."""
        ctx = _make_context(
            "- Configure via `package.json` and `tsconfig.json`.\n",
            entity_index={},
        )
        result = run_script("extract.py", stdin_data=ctx)
        rule = result["rules"][0]
        assert rule["staleness"]["gated"] is False
        for entity in rule["referenced_entities"]:
            if entity["name"] in ("package.json", "tsconfig.json"):
                assert entity["exists"] is None

    def test_jsx_literal_not_falsely_stale(self):
        """JSX/HTML tag literals in backticks must NOT be classified as file paths.

        Regression for Phase C staleness gate root-cause fix: `<FormattedMessage id="..." />`
        was misclassified as kind="path" because of the `/>` slash, then promoted to
        exists=False by the F-14 guard, gating the rule.
        """
        ctx = _make_context(
            "- **All user-facing strings** use react-intl: `<FormattedMessage id=\"...\" />`.\n",
            entity_index={},  # empty — no paths discovered by discover.py
        )
        result = run_script("extract.py", stdin_data=ctx)
        rule = result["rules"][0]
        # The JSX literal should NOT be treated as a missing path
        assert rule["staleness"]["gated"] is False, (
            f"JSX literal was misclassified; staleness: {rule['staleness']}"
        )
        # If the JSX shows up in referenced_entities at all, it must not be exists=False
        for entity in rule["referenced_entities"]:
            if "<FormattedMessage" in entity["name"]:
                assert entity["exists"] is not False, (
                    f"JSX literal promoted to exists=False; entity: {entity}"
                )


class TestIgnoreFilter:
    def test_ignore_filter(self):
        ctx = _make_context("- Always validate input.\n- Try to prefer functional components.\n")
        ctx["config"]["ignore_patterns"] = ['CLAUDE.md: "Try to prefer"']
        result = run_script("extract.py", stdin_data=ctx)
        texts = [r["text"] for r in result["rules"]]
        assert not any("Try to prefer" in t for t in texts)
        assert any("validate input" in t for t in texts)


class TestSchemaOutput:
    def test_content_stripped(self):
        ctx = _make_context("- Always test.\n")
        result = run_script("extract.py", stdin_data=ctx)
        # Source files should not have content field in output
        for sf in result["source_files"]:
            assert "content" not in sf

    def test_schema_fields_carried_forward(self):
        ctx = _make_context("- Always test.\n")
        result = run_script("extract.py", stdin_data=ctx)
        assert result["schema_version"] == "0.1"
        assert result["pipeline_version"] == "0.1.0"
        assert "project_context" in result
        assert "config" in result


# ---------------------------------------------------------------------------
# Phase C root-cause regression: R003 in realistic_redux_app fixture
# ---------------------------------------------------------------------------

class TestJsxRegressionRealFixture:
    """End-to-end regression: the realistic_redux_app fixture's R003 rule
    (`**All user-facing strings** must use react-intl: `<FormattedMessage id="..." />`.`)
    must NOT be staleness-gated due to JSX misclassification.

    Runs discover.py + extract.py on the fixture directory, exactly as the
    real pipeline would, and asserts R003 comes out ungated.
    """

    def test_r003_realistic_redux_app_jsx_not_gated(self):
        fixture_root = Path(__file__).parent / "fixtures" / "realistic_redux_app"
        assert fixture_root.is_dir(), f"Fixture missing: {fixture_root}"

        # Run discover.py on the fixture root
        project_context = run_script(
            "discover.py",
            args=["--project-root", str(fixture_root)],
        )

        # Run extract.py on the discover output
        extracted = run_script("extract.py", stdin_data=project_context)

        # Find R003 by its distinctive text prefix (not by id — the R00X ids
        # depend on extraction order and could shift if extract.py changes)
        r003 = next(
            (r for r in extracted["rules"]
             if r["text"].startswith("**All user-facing strings**")),
            None,
        )
        assert r003 is not None, (
            f"R003 (react-intl rule) not found in extracted rules. "
            f"Found rule texts: {[r['text'][:60] for r in extracted['rules']]}"
        )

        # Primary assertion: no staleness gating
        assert r003["staleness"]["gated"] is False, (
            f"R003 JSX example triggered staleness gate. "
            f"staleness: {r003['staleness']}, "
            f"referenced_entities: {r003['referenced_entities']}"
        )

        # Secondary assertion: the JSX literal, if extracted at all,
        # must not be marked as a missing entity
        missing = r003["staleness"]["missing_entities"]
        assert not any("<FormattedMessage" in m for m in missing), (
            f"JSX literal classified as missing path: {missing}"
        )


# ---------------------------------------------------------------------------
# Phase I: Context vs directive classifier — description-bullet pattern
# ---------------------------------------------------------------------------

class TestDescriptionBulletFilter:
    """Architecture description bullets (**bold** — description) should be
    classified as prose and NOT extracted as rule candidates."""

    def test_architecture_description_bullets_not_extracted(self):
        """Bullets with **bold term** + separator (—/:/--) + descriptive text
        and NO imperative verb should be classified as prose, not rules.

        Reproduces the Dallas-Digital architecture section pattern.
        """
        ctx = _make_context(
            "## Architecture\n"
            "\n"
            "- **src/primitives/** — Headless behavior hooks and state management\n"
            "- **src/components/** — Visual components with Radix UI integration\n"
            "- **src/tokens/** — Design tokens and theming\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        rule_texts = [r["text"] for r in rules]
        # Architecture descriptions should NOT be extracted as rules
        assert not any("primitives" in t for t in rule_texts), (
            f"Architecture description 'primitives' extracted as rule: {rule_texts}"
        )
        assert not any("tokens" in t for t in rule_texts), (
            f"Architecture description 'tokens' extracted as rule: {rule_texts}"
        )
        assert len(rules) == 0, (
            f"Expected 0 rules from pure architecture section, got {len(rules)}: {rule_texts}"
        )

    def test_directive_bullets_still_extracted(self):
        """Directive bullets with imperative verbs must still be extracted,
        even if they appear after architecture descriptions."""
        ctx = _make_context(
            "## Architecture\n"
            "\n"
            "- **src/primitives/** — Headless behavior hooks\n"
            "\n"
            "## Rules\n"
            "\n"
            "- Use early returns over nested ifs.\n"
            "- Never mutate props directly.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        rule_texts = [r["text"] for r in rules]
        # Directive bullets should still be extracted
        assert any("early returns" in t for t in rule_texts), (
            f"Directive 'early returns' missing: {rule_texts}"
        )
        assert any("mutate props" in t for t in rule_texts), (
            f"Directive 'mutate props' missing: {rule_texts}"
        )
        # Architecture description should NOT be extracted
        assert not any("primitives" in t for t in rule_texts), (
            f"Architecture description leaked: {rule_texts}"
        )

    def test_bold_description_with_verb_stays_rule(self):
        """A bullet with bold formatting AND an imperative verb should
        still be classified as a rule (verb check fires before fallback)."""
        ctx = _make_context(
            "- **Auth**: Always use `getAccessToken()` for silent refresh. Reset all state on 401.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        assert len(rules) >= 1, "Verbed bold-description bullet should be a rule"
        assert any("Auth" in r["text"] for r in rules)

    def test_terse_directive_without_bold_preserved(self):
        """Terse directives without bold formatting should keep the bullet
        fallback — they don't match the description pattern."""
        ctx = _make_context(
            "- Error messages sound like a person wrote them.\n"
            "- TypeScript strict mode for all new files.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        assert len(rules) == 2, (
            f"Terse directives should be preserved: {[r['text'] for r in rules]}"
        )


class TestNavigationPointerAndReaderProse:
    """Regression from Dallas-Digital / Axo-folio / guess-who dogfood runs
    (2026-04-16..17): CLAUDE.md scoped-file pointers and reader-addressing
    section headers were being extracted as rules, polluting the audit with
    low-score non-directives. Reader prose and navigation bullets are prose,
    not rules."""

    def test_reader_addressing_paragraphs_not_extracted(self):
        """Paragraphs opening with 'These rules...', 'This file...', 'The following...'
        describe file behavior for a human reader; they must be classified prose."""
        ctx = _make_context(
            "# Game-logic rules\n"
            "\n"
            "These rules load when you're editing pure game logic or the DiceBear avatar renderer.\n"
            "\n"
            "This file provides guidance to Claude Code when working with code in this repository.\n"
            "\n"
            "The following rules apply to every test file in tests/.\n"
            "\n"
            "- Always run `npm test` before committing.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        rule_texts = [r["text"] for r in rules]
        assert not any("These rules load when" in t for t in rule_texts), (
            f"'These rules load when...' leaked: {rule_texts}"
        )
        assert not any("This file provides guidance" in t for t in rule_texts), (
            f"'This file provides guidance' leaked: {rule_texts}"
        )
        assert not any("The following rules apply" in t for t in rule_texts), (
            f"'The following rules' leaked: {rule_texts}"
        )
        # The real directive is still extracted.
        assert any("npm test" in t for t in rule_texts)

    def test_navigation_pointer_backtick_md_not_extracted(self):
        """Bullet opening with a backtick-wrapped .md path followed by a
        description separator is a pointer, not a rule."""
        ctx = _make_context(
            "## Scoped rules\n"
            "\n"
            "- `.claude/rules/comments.md` \u2014 when to write comments and what belongs in them\n"
            "- `.claude/rules/naming.md` \u2014 function, boolean, and domain-term naming\n"
            "- Always run `npm test` before committing.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        rule_texts = [r["text"] for r in rules]
        assert not any("comments.md" in t for t in rule_texts), (
            f"Navigation pointer 'comments.md' leaked as rule: {rule_texts}"
        )
        assert not any("naming.md" in t for t in rule_texts), (
            f"Navigation pointer 'naming.md' leaked as rule: {rule_texts}"
        )
        assert any("npm test" in t for t in rule_texts)

    def test_navigation_pointer_bold_arrow_link_not_extracted(self):
        """Bullet with **bold path** -> [linked.md](path) pattern is a pointer."""
        ctx = _make_context(
            "## Scoped rules\n"
            "\n"
            "- **src/game/** \u2192 [`.claude/rules/game-logic.md`](.claude/rules/game-logic.md) \u2014 purity, attribute coupling\n"
            "- **tests/** \u2192 [`.claude/rules/testing.md`](.claude/rules/testing.md) \u2014 test file placement\n"
            "- Never mutate input state in a state-transition function.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        rule_texts = [r["text"] for r in rules]
        assert not any("game-logic.md" in t for t in rule_texts), (
            f"Bold-arrow-link pointer leaked as rule: {rule_texts}"
        )
        assert not any("testing.md" in t for t in rule_texts), (
            f"Bold-arrow-link pointer leaked as rule: {rule_texts}"
        )
        assert any("mutate input state" in t for t in rule_texts)

    def test_directive_that_mentions_md_file_still_a_rule(self):
        """A real rule that HAPPENS to mention a .md file in its body stays a rule."""
        ctx = _make_context(
            "- When adding a new scoped rule file, update `CLAUDE.md` to include a pointer "
            "to it, because CLAUDE.md is the discovery surface for scoped conventions.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        assert len(rules) == 1, (
            f"Directive mentioning .md in body should still be a rule: {[r['text'] for r in rules]}"
        )


# ---------------------------------------------------------------------------
# Guide C: Heading-context propagation for orphaned bullets
# ---------------------------------------------------------------------------

class TestHeadingBulletMerge:
    """Verbless bullet items under a directive heading should merge into
    a single rule that includes the heading's context, rather than being
    extracted as orphaned F-grade rules."""

    def test_heading_bullet_list_merged(self):
        """Bullets under a directive heading should inherit the heading's context."""
        ctx = _make_context(
            "## When comments are NOT allowed\n"
            "\n"
            "- Restating the code\n"
            "- Narrating sections\n"
            "- Decorative banners\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        # Should be 1 merged rule with the heading's directive context,
        # not 3 orphaned bullets
        assert len(rules) <= 1, (
            f"Expected heading + bullets to merge, got {len(rules)}: "
            f"{[r['text'][:50] for r in rules]}"
        )

    def test_heading_with_verb_bullets_stay_standalone(self):
        """Bullets with their own verbs should NOT merge into the heading."""
        ctx = _make_context(
            "## Code style\n"
            "\n"
            "- Use early returns over nested ifs.\n"
            "- Match the file's existing style.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        # Each bullet has its own verb — should stay standalone
        assert len(rules) >= 2

    def test_merged_text_includes_heading_context(self):
        """The merged rule's text should include the heading for context."""
        ctx = _make_context(
            "## When comments are NOT allowed\n"
            "\n"
            "- Restating the code\n"
            "- Narrating sections\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        assert len(rules) == 1
        # Heading text should be present in the merged rule
        assert "When comments are NOT allowed" in rules[0]["text"]
        # Bullet texts should also be present
        assert "Restating the code" in rules[0]["text"]
        assert "Narrating sections" in rules[0]["text"]

    def test_mixed_verb_and_verbless_under_heading(self):
        """Only verbless bullets merge; verb-bearing bullets stay standalone."""
        ctx = _make_context(
            "## Error handling\n"
            "\n"
            "- Error messages sound like a person wrote them\n"
            "- No catch-rethrow unless adding context\n"
            "- Always log the original error before wrapping.\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        # The verb-bearing bullet ("Always log...") should be standalone.
        # The verbless bullets should merge under the heading.
        verb_rules = [r for r in rules if "Always log" in r["text"]]
        assert len(verb_rules) == 1, "Verb-bearing bullet should stay standalone"
        # Total: 1 merged heading+verbless + 1 standalone verb bullet = 2
        assert len(rules) == 2, (
            f"Expected 2 rules (1 merged + 1 standalone), got {len(rules)}: "
            f"{[r['text'][:50] for r in rules]}"
        )

    def test_different_headings_stay_separate(self):
        """Bullets under different headings should not merge together."""
        ctx = _make_context(
            "## Section A\n"
            "\n"
            "- Alpha item\n"
            "- Beta item\n"
            "\n"
            "## Section B\n"
            "\n"
            "- Gamma item\n"
            "- Delta item\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        # Should be 2 merged rules (one per heading), not 4 orphaned bullets
        assert len(rules) == 2, (
            f"Expected 2 rules (one per heading), got {len(rules)}: "
            f"{[r['text'][:50] for r in rules]}"
        )
        # Each merged rule should contain its heading
        texts = [r["text"] for r in rules]
        assert any("Section A" in t and "Alpha" in t for t in texts)
        assert any("Section B" in t and "Gamma" in t for t in texts)

    def test_phase_h_still_works_with_paragraph_directive(self):
        """Phase H merge (paragraph + verbless bullets) should still work
        when heading annotation is present — no regression."""
        ctx = _make_context(
            "## Writing style\n"
            "\n"
            "These scream AI. Don't use them anywhere:\n"
            "- Synergy\n"
            "- Leverage\n"
            "- Innovative\n"
        )
        result = run_script("extract.py", stdin_data=ctx)
        rules = result["rules"]
        # Phase H: paragraph directive + verbless bullets → 1 merged rule
        assert len(rules) == 1, (
            f"Phase H should still merge paragraph+bullets, got {len(rules)}: "
            f"{[r['text'][:50] for r in rules]}"
        )
        assert "Don't use" in rules[0]["text"]
