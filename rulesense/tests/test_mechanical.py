"""Tests for score_mechanical.py — F1 (verb strength), F2 (framing polarity), F4 (load-trigger alignment)."""

import pytest
from conftest import run_script


def _score_rule(text: str, globs: list | None = None, always_loaded: bool = True,
                glob_match_count: int | None = None, staleness: dict | None = None,
                entity_index: dict | None = None) -> dict:
    """Run a single rule through extract + score_mechanical and return the scored rule."""
    rule = {
        "id": "R001",
        "file_index": 0,
        "text": text,
        "line_start": 1,
        "line_end": 1,
        "category": "mandate",
        "referenced_entities": [],
        "staleness": staleness or {"gated": False, "missing_entities": []},
        "factors": {},
    }
    data = {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_context": {"stack": [], "always_loaded_files": [], "glob_scoped_files": []},
        "config": {},
        "source_files": [{
            "path": "test.md",
            "globs": globs or [],
            "glob_match_count": glob_match_count,
            "default_category": "mandate",
            "line_count": 10,
            "always_loaded": always_loaded,
        }],
        "rules": [rule],
    }
    result = run_script("score_mechanical.py", stdin_data=data)
    return result["rules"][0]


# ---------------------------------------------------------------------------
# F1: Verb Strength
# ---------------------------------------------------------------------------

class TestF1WorkedExamples:
    """Test all 7 worked examples from factor-rubrics.md."""

    @pytest.mark.parametrize("text,expected_score", [
        ("ALWAYS use project-aware methods for command database access", 1.00),
        ("NEVER edit files in src/main/gen/ directly", 0.95),
        ("Use functional components for all new React files", 0.85),
        ("Each test file must import from the module it tests", 1.00),
        ("Prefer named exports over default exports", 0.50),
        ("Use good judgment about error handling", 0.85),
        ("Try to prefer functional components when possible", 0.20),
    ])
    def test_f1_worked_examples(self, text, expected_score):
        rule = _score_rule(text)
        assert rule["factors"]["F1"]["value"] == expected_score, \
            f"F1 for '{text[:50]}' expected {expected_score}, got {rule['factors']['F1']['value']}"

    def test_f1_compound_hedging(self):
        rule = _score_rule("Try to prefer functional components when possible")
        assert rule["factors"]["F1"]["value"] == 0.20
        assert rule["factors"]["F1"]["method"] == "lookup"

    def test_f1_implicit_verb(self):
        rule = _score_rule("Test files mirror source paths")
        assert rule["factors"]["F1"]["value"] == 0.70
        assert rule["factors"]["F1"]["method"] == "implicit_imperative_default"

    def test_f1_extraction_failure(self):
        # A string with no recognizable verb or statement form
        rule = _score_rule("Stack: generic, TypeScript")
        # This should either be implicit or extraction failure
        f1 = rule["factors"]["F1"]
        assert f1["method"] in ("implicit_imperative_default", "extraction_failed")


# ---------------------------------------------------------------------------
# F2: Framing Polarity
# ---------------------------------------------------------------------------

class TestF2WorkedExamples:
    """Test all 6 worked examples from factor-rubrics.md."""

    @pytest.mark.parametrize("text,expected_score", [
        ("ALWAYS use project-aware methods: `getProjectCommands(project)` not `.database.commands`", 0.95),
        ("Use CachedValuesManager for expensive computations", 0.85),
        ("NEVER edit files in src/main/gen/ directly. Edit the .bnf/.flex source and regenerate.", 0.70),
        ("NEVER edit files in src/main/gen/ directly.", 0.50),
        ("Prefer named exports over default exports", 0.35),
        ("Try to prefer functional components when possible", 0.35),
    ])
    def test_f2_worked_examples(self, text, expected_score):
        rule = _score_rule(text)
        assert rule["factors"]["F2"]["value"] == expected_score, \
            f"F2 for '{text[:50]}' expected {expected_score}, got {rule['factors']['F2']['value']}"

    def test_f2_prohibition_with_alternative(self):
        rule = _score_rule("NEVER edit files in src/main/gen/ directly. Edit the .bnf/.flex source and regenerate.")
        assert rule["factors"]["F2"]["value"] == 0.70
        assert rule["factors"]["F2"]["matched_category"] == "positive_with_negative_clarification"


# ---------------------------------------------------------------------------
# F4: Load-Trigger Alignment
# ---------------------------------------------------------------------------

class TestF4WorkedExamples:
    """Test worked examples from factor-rubrics.md."""

    def test_f4_glob_matches_trigger(self):
        rule = _score_rule(
            "Use Zod for API validation",
            globs=["src/api/**/*.ts"],
            always_loaded=False,
            glob_match_count=5,
        )
        # "api" appears in both glob and rule text
        assert rule["factors"]["F4"]["value"] >= 0.85

    def test_f4_always_loaded_universal(self):
        rule = _score_rule("Use TypeScript strict mode")
        assert rule["factors"]["F4"]["value"] >= 0.90
        assert rule["factors"]["F4"]["method"] == "always_universal"

    def test_f4_always_loaded_specific_trigger(self):
        rule = _score_rule("When editing API files, validate with Zod")
        assert rule["factors"]["F4"]["value"] <= 0.50
        assert rule["factors"]["F4"]["method"] == "misaligned"

    def test_f4_dead_glob(self):
        rule = _score_rule(
            "Use strict mode",
            globs=["src/nonexistent/**"],
            always_loaded=False,
            glob_match_count=0,
        )
        assert rule["factors"]["F4"]["value"] == 0.05

    def test_f4_keyword_overlap(self):
        """Rule about API + glob containing 'api' → semantic match."""
        rule = _score_rule(
            "Use Zod for API validation",
            globs=["src/api/**/*.ts"],
            always_loaded=False,
            glob_match_count=5,
        )
        assert rule["factors"]["F4"]["value"] >= 0.85

    def test_f4_no_overlap(self):
        """Glob-scoped rule with no explicit trigger and no keyword overlap with
        the glob — the paths: frontmatter IS the alignment, the rule correctly
        trusts the scope. Scores high (F4_no_overlap_score default 0.85)."""
        rule = _score_rule(
            "All public functions must be documented with TSDoc",
            globs=["src/api/**/*.ts"],
            always_loaded=False,
            glob_match_count=5,
        )
        f4 = rule["factors"]["F4"]
        assert f4["value"] >= 0.80  # implicit scope trust
        assert f4["method"] == "keyword_overlap"
        assert f4["loading"] == "glob-scoped"
        assert f4["trigger_match"] == "implicit_scope_trust"

    def test_f4_concise_rule_not_penalized_vs_redundant(self):
        """F-4 regression from dogfood: a rule that re-states its scope in text
        should not score higher than the same rule without the redundant text,
        when both are in the same glob-scoped file. The lens rewards concise rules."""
        source_file_spec = {
            "globs": ["packages/**/*.ts", "packages/**/*.tsx"],
            "always_loaded": False,
            "glob_match_count": 10,
        }
        redundant = _score_rule(
            "When writing TypeScript in packages/ui, add a single-line comment "
            "explaining the business reason when logic cannot be inferred.",
            **source_file_spec,
        )
        concise = _score_rule(
            "When business logic cannot be inferred from identifiers alone, "
            "add a single-line comment explaining the business reason.",
            **source_file_spec,
        )
        # Both rules should score in the same high tier. The concise one MUST NOT
        # score lower — before the v1.4.x F4 fix, concise = 0.65 vs redundant = 0.90.
        assert concise["factors"]["F4"]["value"] >= 0.80, (
            f"Concise rule was penalized: F4 = {concise['factors']['F4']['value']}"
        )
        assert redundant["factors"]["F4"]["value"] >= 0.80
        # They should be within 0.10 of each other (same tier).
        delta = abs(concise["factors"]["F4"]["value"] - redundant["factors"]["F4"]["value"])
        assert delta <= 0.10, f"Concise vs redundant F4 delta too large: {delta}"

    def test_f4_stale(self):
        rule = _score_rule(
            "Run tests for `src/legacy/auth.js`",
            staleness={"gated": True, "missing_entities": ["src/legacy/auth.js"]},
        )
        assert rule["factors"]["F4"]["value"] == 0.05


# ---------------------------------------------------------------------------
# Regression: Bug 2 — "always" dual-tier over-scoring
# ---------------------------------------------------------------------------

class TestF1AlwaysRegression:
    """Regression tests: 'always' without a bare imperative verb should score 0.70, not 1.00."""

    def test_always_without_imperative(self):
        """'Always be careful...' → 0.70 (advisory), NOT 1.00."""
        rule = _score_rule("Always be careful when refactoring")
        assert rule["factors"]["F1"]["value"] == 0.70
        assert rule["factors"]["F1"]["matched_verb"] == "always"

    def test_always_with_imperative(self):
        """'Always use X' → 1.00 via special case (always + bare_imperative)."""
        rule = _score_rule("Always use consistent naming conventions")
        assert rule["factors"]["F1"]["value"] == 1.00
        assert "always + use" in rule["factors"]["F1"]["matched_verb"]

    def test_always_alone(self):
        """'Always.' as fragment → 0.70."""
        rule = _score_rule("Always.")
        assert rule["factors"]["F1"]["value"] == 0.70


# ---------------------------------------------------------------------------
# F-3: Noun-verb ambiguity in F1
# ---------------------------------------------------------------------------

class TestF3NounVerbAmbiguity:
    """F-3: Words like 'document', 'format', 'log' at sentence start are often
    nouns, not imperative verbs. _looks_like_statement should catch these.
    """

    def test_document_noun_not_verb(self):
        """'Document headers must be at the top' — 'document' is a noun."""
        rule = _score_rule("Document headers must be at the top")
        f1 = rule["factors"]["F1"]
        # "must" should be the binding verb (1.00), not "document" (0.85)
        assert f1["value"] == 1.00
        assert f1["matched_verb"] == "must"

    def test_format_noun_not_verb(self):
        """'Format strings should use f-strings' — 'format' is a noun."""
        rule = _score_rule("Format strings should use f-strings")
        f1 = rule["factors"]["F1"]
        # "should" (0.70) should take precedence, or statement downgrades to implicit
        assert f1["value"] <= 0.70  # Not 0.85 from 'format' as verb

    def test_log_noun_not_verb(self):
        """'Log entries for failed requests' — 'log' is a noun."""
        rule = _score_rule("Log entries for failed requests")
        f1 = rule["factors"]["F1"]
        # Should be implicit/statement (0.70) not 'log' as verb (0.85)
        assert f1["value"] == 0.70
        assert f1["method"] == "implicit_imperative_default"

    def test_name_noun_not_verb(self):
        """'Name conventions for exported types' — 'name' is a noun."""
        rule = _score_rule("Name conventions for exported types")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.70
        assert f1["method"] == "implicit_imperative_default"

    def test_set_the_is_imperative(self):
        """'Set the timeout to 30 seconds' — 'set' is a verb (article 'the' = direct object)."""
        rule = _score_rule("Set the timeout to 30 seconds")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.85
        assert f1["matched_verb"] == "set"

    def test_document_the_is_imperative(self):
        """'Document the API endpoints' — 'document' is a verb (article 'the' = direct object)."""
        rule = _score_rule("Document the API endpoints")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.85
        assert f1["matched_verb"] == "document"

    def test_check_the_is_imperative(self):
        """'Check the logs before deploying' — real imperative."""
        rule = _score_rule("Check the logs before deploying")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.85
        assert f1["matched_verb"] == "check"

    def test_watch_for_is_imperative(self):
        """'Watch for changes in the file' — real imperative with preposition."""
        rule = _score_rule("Watch for changes in the file")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.85
        assert f1["matched_verb"] == "watch"

    def test_format_the_is_imperative(self):
        """'Format the output as JSON' — real imperative."""
        rule = _score_rule("Format the output as JSON with consistent indentation")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.85
        assert f1["matched_verb"] == "format"

    def test_test_the_is_imperative(self):
        """'Test the function with edge cases' — 'test' is a verb (article = direct object)."""
        rule = _score_rule("Test the function with edge cases")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.85
        assert f1["matched_verb"] == "test"

    def test_test_code_is_noun_phrase(self):
        """'Test code is reviewed regularly' — 'test' is a noun (compound 'test code')."""
        rule = _score_rule("Test code is reviewed regularly")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.70
        assert f1["method"] == "implicit_imperative_default"

    def test_test_coverage_is_noun_phrase(self):
        """'Test coverage should exceed 80%' — 'test' is a noun (compound 'test coverage')."""
        rule = _score_rule("Test coverage should exceed 80%")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.70

    def test_test_runs_is_noun_phrase(self):
        """'Test runs trigger CI builds' — 'test' is a noun (compound 'test runs')."""
        rule = _score_rule("Test runs trigger CI builds")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.70
        assert f1["method"] == "implicit_imperative_default"

    def test_matched_position_reported(self):
        """F1 output includes matched_position (character index of the match)."""
        rule = _score_rule("Use functional components for all new React files")
        f1 = rule["factors"]["F1"]
        assert "matched_position" in f1
        assert isinstance(f1["matched_position"], int)

    def test_matched_position_points_at_verb_not_whitespace(self):
        """P4.3: matched_position must point at the verb itself, not the
        leading whitespace. 'ALWAYS use X' → position of 'u' in 'use'."""
        rule = _score_rule("ALWAYS use consistent naming conventions")
        f1 = rule["factors"]["F1"]
        # "ALWAYS use" — the "use" starts at index 7
        text = "always use consistent naming conventions"
        expected_pos = text.index("use")
        assert f1["matched_position"] == expected_pos, \
            f"Expected position {expected_pos} (start of 'use'), got {f1['matched_position']}"
        assert f1["matched_position"] >= 0

    def test_matched_position_none_for_implicit(self):
        """matched_position is None for implicit/extraction_failed methods."""
        rule = _score_rule("Test files mirror source paths")
        f1 = rule["factors"]["F1"]
        assert f1["matched_position"] is None


# ---------------------------------------------------------------------------
# Verb-list expansion (Guide D): new imperative verbs recognized
# ---------------------------------------------------------------------------

class TestVerbListExpansion:
    """Characterization tests for verbs added in the verb-list expansion.

    Each verb was missing from verbs.json and caused rules starting with it
    to score F1=None (extraction_failed). These tests verify the fix.
    """

    @pytest.mark.parametrize("text,verb", [
        ("Reset all state on 401 responses.", "reset"),
        ("Revert changes if validation fails.", "revert"),
        ("Avoid circular dependencies.", "avoid"),
        ("Enforce strict mode in all modules.", "enforce"),
        ("Restrict admin endpoints to internal network.", "restrict"),
        ("Sanitize all user input before processing.", "sanitize"),
        ("Normalize paths before comparison.", "normalize"),
        ("Optimize images before deployment.", "optimize"),
        ("Lint all files before committing.", "lint"),
        ("Encrypt sensitive data at rest.", "encrypt"),
        ("Decrypt tokens on the server side only.", "decrypt"),
        ("Retry failed requests up to 3 times.", "retry"),
        ("Abort requests after 30 seconds.", "abort"),
        ("Throttle API requests to 100/s.", "throttle"),
        ("Debounce search input by 300ms.", "debounce"),
        ("Generate API docs from annotations.", "generate"),
        ("Execute migrations in a transaction.", "execute"),
        ("Invoke callbacks asynchronously.", "invoke"),
        ("Scaffold new services with the template.", "scaffold"),
        ("Bootstrap the app with environment config.", "bootstrap"),
        ("Authenticate users via OAuth2.", "authenticate"),
        ("Authorize access with role-based permissions.", "authorize"),
    ])
    def test_new_verb_recognized(self, text, verb):
        """Newly added verb scores 0.85 (bare_imperative), not extraction_failed."""
        rule = _score_rule(text)
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.85, \
            f"'{verb}' should score 0.85 but got {f1['value']} (method={f1['method']})"
        assert f1["matched_verb"] == verb

    @pytest.mark.parametrize("text,verb", [
        ("Specify the node version in .nvmrc.", "specify"),
        ("Maintain backward compatibility for 2 major versions.", "maintain"),
        ("Expose only public API methods.", "expose"),
        ("Guard against null pointer exceptions.", "guard"),
        ("Preserve insertion order in maps.", "preserve"),
        ("Notify stakeholders on deployment.", "notify"),
        ("Compose middleware in order of priority.", "compose"),
        ("Bind event handlers in the constructor.", "bind"),
        ("Defer non-critical loading.", "defer"),
        ("Flush stale data after deployments.", "flush"),
        ("Suppress warnings only with documented reasons.", "suppress"),
        ("Freeze the API surface before v2.", "freeze"),
        ("Truncate logs older than 30 days.", "truncate"),
        ("Rotate secrets every 90 days.", "rotate"),
        ("Minimize bundle size by tree-shaking.", "minimize"),
        ("Preload critical assets.", "preload"),
        ("Paginate results over 100 items.", "paginate"),
    ])
    def test_more_new_verbs_recognized(self, text, verb):
        """Additional expanded verbs score correctly."""
        rule = _score_rule(text)
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.85, \
            f"'{verb}' should score 0.85 but got {f1['value']} (method={f1['method']})"
        assert f1["matched_verb"] == verb

    def test_cache_as_verb(self):
        """'Cache responses for 5 minutes' — 'cache' is a verb (not followed by noun-follower)."""
        rule = _score_rule("Cache responses for 5 minutes.")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.85
        assert f1["matched_verb"] == "cache"

    def test_cache_as_noun(self):
        """'Cache entries must be...' — 'cache' is a noun (followed by noun-follower 'entries')."""
        rule = _score_rule("Cache entries must be invalidated after writes.")
        f1 = rule["factors"]["F1"]
        # "must" (1.00) is the strongest verb; cache+entries triggers noun-verb ambiguity
        # but best_match_score > 0.85 so the strong verb wins
        assert f1["value"] == 1.00
        assert f1["matched_verb"] == "must"

    def test_scope_as_verb(self):
        """'Scope CSS to component boundaries' — 'scope' is a verb."""
        rule = _score_rule("Scope CSS to component boundaries.")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.85
        assert f1["matched_verb"] == "scope"

    def test_scope_as_noun(self):
        """'Scope variables should be minimized' — 'scope' is a noun."""
        rule = _score_rule("Scope variables should be minimized.")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.70
        assert f1["method"] == "implicit_imperative_default"

    def test_batch_as_noun(self):
        """'Batch operations should be atomic' — 'batch' is a noun."""
        rule = _score_rule("Batch operations should be atomic.")
        f1 = rule["factors"]["F1"]
        assert f1["value"] == 0.70
        assert f1["method"] == "implicit_imperative_default"


# ---------------------------------------------------------------------------
# Regression: Bug 1 — F2 "not " pattern false positives
# ---------------------------------------------------------------------------

class TestF2ContrastNotRegression:
    """Regression tests: contrast-not vs negation-not disambiguation."""

    def test_negation_not_gerund(self):
        """'not depending on' is negation, NOT contrast → 0.85 (positive imperative)."""
        rule = _score_rule("Functions should be pure, not depending on global state")
        assert rule["factors"]["F2"]["value"] == 0.85
        assert rule["factors"]["F2"]["matched_category"] == "positive_imperative"

    def test_contrast_not_nouns(self):
        """'Use lists, not tuples' → positive_with_alternative (0.95)."""
        rule = _score_rule("Use lists, not tuples")
        assert rule["factors"]["F2"]["value"] == 0.95

    def test_contrast_not_backticks(self):
        """Backtick contrast `X` not `Y` → 0.95."""
        rule = _score_rule("Use `getProjectCommands` not `.database`")
        assert rule["factors"]["F2"]["value"] == 0.95

    def test_contrast_not_adjectives(self):
        """'pure, not stateful' → adjective contrast → 0.95."""
        rule = _score_rule("Functions should be pure, not stateful")
        assert rule["factors"]["F2"]["value"] == 0.95

    def test_predicate_negation(self):
        """'is not optional' → predicate negation → falls to default 0.85."""
        rule = _score_rule("This rule is not optional")
        assert rule["factors"]["F2"]["value"] == 0.85

    def test_contrast_not_nouns_verb_context(self):
        """'verify behavior, not implementation' → noun contrast → 0.95."""
        rule = _score_rule("Tests must verify behavior, not implementation")
        assert rule["factors"]["F2"]["value"] == 0.95

    def test_instead_of_unchanged(self):
        """'instead of' pattern still works."""
        rule = _score_rule("Use forEach instead of for loops")
        assert rule["factors"]["F2"]["value"] == 0.95

    def test_rather_than_unchanged(self):
        """' rather than ' pattern still works."""
        rule = _score_rule("Use async/await rather than raw promises")
        assert rule["factors"]["F2"]["value"] == 0.95


# ---------------------------------------------------------------------------
# Regression: Bug 7 — F4 fallback labels
# ---------------------------------------------------------------------------

class TestF4FallbackRegression:
    """Regression test: F4 fallback uses honest method/loading labels."""

    def test_f4_fallback_labels(self):
        """True ambiguous fallback (no globs, not always-loaded) uses the
        distinct F4_ambiguous_score — still 0.65, since the alignment is
        genuinely unknowable here, unlike the glob-scoped-no-overlap case."""
        rule = _score_rule(
            "Some rule text",
            globs=[],
            always_loaded=False,
            glob_match_count=None,
        )
        f4 = rule["factors"]["F4"]
        assert f4["method"] == "no_signal"
        assert f4["loading"] == "ambiguous"
        assert f4["value"] == 0.65
