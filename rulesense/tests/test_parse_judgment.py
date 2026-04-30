"""Tests for parse_judgment.py — response parsing, validation, transformation."""

import json
import os
import tempfile

import pytest
from conftest import run_script, run_script_raw, PYTHON, SCRIPTS_DIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scored_semi(rule_ids: list[str]) -> dict:
    """Build a minimal scored_semi.json with the given rule IDs."""
    return {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_context": {"stack": [], "project_root": "/test"},
        "config": {},
        "source_files": [
            {"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
             "default_category": "mandate", "line_count": 50, "always_loaded": True},
        ],
        "rules": [
            {"id": rid, "file_index": 0, "text": f"Rule {rid}.",
             "line_start": i * 5, "line_end": i * 5, "category": "mandate",
             "referenced_entities": [], "staleness": {"gated": False, "missing_entities": []},
             "factors": {
                 "F1": {"value": 0.85, "method": "lookup"},
                 "F2": {"value": 0.85, "method": "classify"},
                 "F4": {"value": 0.95, "method": "glob_match"},
                 "F7": {"value": 0.80, "method": "count"},
             }}
            for i, rid in enumerate(rule_ids)
        ],
    }


def _make_entry(rule_id: str, f3_value: float = 0.80, f3_level: int = 3,
                f8_value: float = 0.65, f8_level: int = 2, **extra) -> dict:
    """Build a single judgment array entry."""
    entry = {
        "id": rule_id,
        "F3": {"value": f3_value, "level": f3_level, "reasoning": "test reasoning"},
        "F8": {"value": f8_value, "level": f8_level, "reasoning": "test reasoning"},
    }
    entry.update(extra)
    return entry


def _run_parse(scored_semi: dict, raw_input: str):
    """Write scored_semi to a temp file, run parse_judgment.py with raw_input on stdin."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(scored_semi, f)
        scored_path = f.name

    try:
        import subprocess
        result = subprocess.run(
            [PYTHON, str(SCRIPTS_DIR / "parse_judgment.py"), scored_path],
            input=raw_input,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result
    finally:
        os.unlink(scored_path)


def _run_parse_ok(scored_semi: dict, raw_input: str) -> dict:
    """Run parse_judgment.py and assert success, return parsed output."""
    result = _run_parse(scored_semi, raw_input)
    assert result.returncode == 0, f"parse_judgment.py failed:\nstderr: {result.stderr}\nstdout: {result.stdout}"
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------

class TestBasicParsing:
    def test_clean_json_array(self):
        """Valid JSON array with all IDs present."""
        scored = _make_scored_semi(["R001", "R002"])
        raw = json.dumps([
            _make_entry("R001"),
            _make_entry("R002", f3_value=0.50, f3_level=2, f8_value=0.90, f8_level=3),
        ])
        output = _run_parse_ok(scored, raw)

        assert output["schema_version"] == "0.1"
        assert "patches" in output
        assert "R001" in output["patches"]
        assert "R002" in output["patches"]
        assert output["patches"]["R001"]["F3"]["value"] == 0.80
        assert output["patches"]["R002"]["F8"]["value"] == 0.90

    def test_markdown_fences_stripped(self):
        """Input wrapped in ```json ... ``` fences."""
        scored = _make_scored_semi(["R001"])
        raw = '```json\n' + json.dumps([_make_entry("R001")]) + '\n```'
        output = _run_parse_ok(scored, raw)

        assert "R001" in output["patches"]
        assert output["patches"]["R001"]["F3"]["value"] == 0.80

    def test_prose_before_after(self):
        """Input has prose before [ and after ]."""
        scored = _make_scored_semi(["R001"])
        array = json.dumps([_make_entry("R001")])
        raw = f"Here are my scores:\n{array}\nLet me know if you need changes."
        output = _run_parse_ok(scored, raw)

        assert "R001" in output["patches"]

    def test_prose_with_brackets_before_and_after(self):
        """Prose containing [brackets] before and after the JSON array.

        Regression: find('[') used to match prose brackets, not the JSON array.
        The model routinely writes things like "scored against [State: SYNCED]"
        or "level 3 means [0.65, 0.85]" around the JSON output.
        """
        scored = _make_scored_semi(["R001"])
        array = json.dumps([_make_entry("R001")])
        raw = (
            'Some prose with [brackets] before the JSON.\n\n'
            f'{array}\n\n'
            'Trailing prose that mentions [State: SYNCED] which has brackets.'
        )
        output = _run_parse_ok(scored, raw)

        assert "R001" in output["patches"]
        assert output["patches"]["R001"]["F3"]["value"] == 0.80

    def test_reasoning_with_brackets_in_string(self):
        """Reasoning field containing brackets like [State: SYNCED].

        The JSON parser must handle brackets inside string literals correctly.
        """
        scored = _make_scored_semi(["R001"])
        entry = _make_entry("R001")
        entry["F3"]["reasoning"] = "contains [State: SYNCED] in description"
        raw = json.dumps([entry])
        output = _run_parse_ok(scored, raw)

        assert "R001" in output["patches"]
        assert "[State: SYNCED]" in output["patches"]["R001"]["F3"]["reasoning"]

    def test_markdown_fences_with_language_tag(self):
        """Input wrapped in ```python or other language-tagged fences."""
        scored = _make_scored_semi(["R001"])
        raw = '```python\n' + json.dumps([_make_entry("R001")]) + '\n```'
        output = _run_parse_ok(scored, raw)

        assert "R001" in output["patches"]

    def test_schema_version_present(self):
        """Output includes schema_version."""
        scored = _make_scored_semi(["R001"])
        raw = json.dumps([_make_entry("R001")])
        output = _run_parse_ok(scored, raw)

        assert output["schema_version"] == "0.1"
        assert output["model_version"] == "unknown"


# ---------------------------------------------------------------------------
# Missing IDs
# ---------------------------------------------------------------------------

class TestMissingIDs:
    def test_missing_rule_null_default(self):
        """Missing rule ID gets null entry with 'model_omitted' reasoning."""
        scored = _make_scored_semi(["R001", "R002", "R003"])
        raw = json.dumps([_make_entry("R001"), _make_entry("R002")])
        output = _run_parse_ok(scored, raw)

        # R003 should have null entries
        r003 = output["patches"]["R003"]
        assert r003["F3"]["value"] is None
        assert r003["F3"]["level"] is None
        assert r003["F3"]["reasoning"] == "model_omitted"
        assert r003["F8"]["value"] is None

    def test_missing_ids_above_tolerance_fatal(self):
        """Too many missing IDs causes fatal exit."""
        rule_ids = [f"R{i:03d}" for i in range(1, 51)]  # 50 rules
        scored = _make_scored_semi(rule_ids)
        # Only provide 10 of 50 — way above tolerance of max(2, 0.05*50)=3
        raw = json.dumps([_make_entry(f"R{i:03d}") for i in range(1, 11)])
        result = _run_parse(scored, raw)

        assert result.returncode != 0
        assert "FATAL" in result.stderr
        assert "missing" in result.stderr.lower()

    def test_few_missing_within_tolerance(self):
        """A few missing IDs within tolerance still succeeds.

        50 rules: tolerance = max(2, ceil(0.05 * 50)) = max(2, 3) = 3.
        2 missing is within tolerance of 3.
        """
        rule_ids = [f"R{i:03d}" for i in range(1, 51)]  # 50 rules
        scored = _make_scored_semi(rule_ids)
        # Provide 48 of 50 — 2 missing, within tolerance of 3
        raw = json.dumps([_make_entry(f"R{i:03d}") for i in range(1, 49)])
        output = _run_parse_ok(scored, raw)

        assert "R049" in output["patches"]
        assert output["patches"]["R049"]["F3"]["value"] is None
        assert "R050" in output["patches"]


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

class TestTruncation:
    def test_reasoning_truncation(self):
        """Reasoning longer than 80 chars gets truncated."""
        scored = _make_scored_semi(["R001"])
        long_reasoning = "x" * 200
        entry = _make_entry("R001")
        entry["F3"]["reasoning"] = long_reasoning
        raw = json.dumps([entry])
        output = _run_parse_ok(scored, raw)

        reasoning = output["patches"]["R001"]["F3"]["reasoning"]
        assert len(reasoning) <= 80
        assert reasoning.endswith("...")

    def test_short_reasoning_preserved(self):
        """Reasoning under 80 chars is kept intact."""
        scored = _make_scored_semi(["R001"])
        raw = json.dumps([_make_entry("R001")])
        output = _run_parse_ok(scored, raw)

        assert output["patches"]["R001"]["F3"]["reasoning"] == "test reasoning"


# ---------------------------------------------------------------------------
# Value-range validation
# ---------------------------------------------------------------------------

class TestValueRangeValidation:
    def test_value_within_level_range(self):
        """Value within the stated level's range passes unchanged."""
        scored = _make_scored_semi(["R001"])
        raw = json.dumps([_make_entry("R001", f3_value=0.75, f3_level=3)])
        output = _run_parse_ok(scored, raw)

        assert output["patches"]["R001"]["F3"]["value"] == 0.75
        assert output["patches"]["R001"]["F3"]["level"] == 3

    def test_value_outside_level_range_corrected(self):
        """F3 value=0.85 with level=2 (range 0.40-0.60) gets corrected to midpoint 0.50."""
        scored = _make_scored_semi(["R001"])
        # level 2 range is [0.40, 0.60], but value is 0.85 (resolves to level 3)
        raw = json.dumps([_make_entry("R001", f3_value=0.85, f3_level=2)])
        result = _run_parse(scored, raw)
        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["patches"]["R001"]["F3"]["value"] == 0.50  # midpoint of level 2
        assert output["patches"]["R001"]["F3"]["level"] == 2
        assert "WARNING" in result.stderr
        assert "Corrected" in result.stderr

    def test_value_at_level_boundary(self):
        """F3 value=0.87 in gap between level 3 (max 0.85) and level 4 (min 0.90).

        Resolved by >= lower_bound scan: 0.87 < 0.90 (not level 4), 0.87 >= 0.65 (level 3).
        If stated level is 3, value is in a gap but resolves to stated level — no correction.
        """
        scored = _make_scored_semi(["R001"])
        raw = json.dumps([_make_entry("R001", f3_value=0.87, f3_level=3)])
        output = _run_parse_ok(scored, raw)

        # Gap value resolves to level 3 which matches stated level — no correction
        assert output["patches"]["R001"]["F3"]["value"] == 0.87
        assert output["patches"]["R001"]["F3"]["level"] == 3

    def test_f8_value_range_validation(self):
        """F8 value-range validation works too."""
        scored = _make_scored_semi(["R001"])
        # F8 level 0 range is [0.10, 0.25], but value is 0.90 (resolves to level 3)
        raw = json.dumps([_make_entry("R001", f8_value=0.90, f8_level=0)])
        result = _run_parse(scored, raw)
        assert result.returncode == 0

        output = json.loads(result.stdout)
        # Corrected to midpoint of level 0: (0.10 + 0.25) / 2 = 0.175 ≈ 0.18
        assert output["patches"]["R001"]["F8"]["value"] == pytest.approx(0.18, abs=0.01)
        assert "WARNING" in result.stderr


# ---------------------------------------------------------------------------
# Partial / malformed entries
# ---------------------------------------------------------------------------

class TestPartialEntries:
    def test_entry_missing_f8(self):
        """Entry with F3 but no F8 gets null F8."""
        scored = _make_scored_semi(["R001"])
        entry = {"id": "R001", "F3": {"value": 0.80, "level": 3, "reasoning": "test"}}
        raw = json.dumps([entry])
        result = _run_parse(scored, raw)
        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["patches"]["R001"]["F8"]["value"] is None
        assert output["patches"]["R001"]["F8"]["reasoning"] == "model_omitted"
        assert "WARNING" in result.stderr

    def test_entry_missing_f3(self):
        """Entry with F8 but no F3 gets null F3."""
        scored = _make_scored_semi(["R001"])
        entry = {"id": "R001", "F8": {"value": 0.65, "level": 2, "reasoning": "test"}}
        raw = json.dumps([entry])
        result = _run_parse(scored, raw)
        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["patches"]["R001"]["F3"]["value"] is None
        assert output["patches"]["R001"]["F3"]["reasoning"] == "model_omitted"

    def test_null_values_explicit(self):
        """Model explicitly emits null value and level — legitimate 'could not score'."""
        scored = _make_scored_semi(["R001"])
        entry = {
            "id": "R001",
            "F3": {"value": None, "level": None, "reasoning": "Cannot score without more context"},
            "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
        }
        raw = json.dumps([entry])
        output = _run_parse_ok(scored, raw)

        assert output["patches"]["R001"]["F3"]["value"] is None
        assert output["patches"]["R001"]["F3"]["level"] is None
        assert "Cannot score" in output["patches"]["R001"]["F3"]["reasoning"]


# ---------------------------------------------------------------------------
# Optional patches
# ---------------------------------------------------------------------------

class TestOptionalPatches:
    def test_f7_patch_preserved(self):
        """F7_patch field passes through."""
        scored = _make_scored_semi(["R001"])
        entry = _make_entry("R001")
        entry["F7_patch"] = {"value": 0.30, "reasoning": "counterexample test: no violation constructible"}
        raw = json.dumps([entry])
        output = _run_parse_ok(scored, raw)

        assert "F7_patch" in output["patches"]["R001"]
        assert output["patches"]["R001"]["F7_patch"]["value"] == 0.30

    # F6 is absorbed into F7; the pipeline does not have a separate F6 factor.
    # The F6_patch test was removed because F6 does not exist as a factor.
    # F7_patch (above) covers the corresponding role because F7 absorbs
    # example density into the concreteness measurement.

    def test_patch_reasoning_truncated(self):
        """Reasoning in optional patches is also truncated."""
        scored = _make_scored_semi(["R001"])
        entry = _make_entry("R001")
        entry["F7_patch"] = {"value": 0.30, "reasoning": "a" * 200}
        raw = json.dumps([entry])
        output = _run_parse_ok(scored, raw)

        assert len(output["patches"]["R001"]["F7_patch"]["reasoning"]) <= 80


class TestMalformedPatchDrops:
    """Regression from Axo-folio dogfood (2026-04-17): the model emitted an
    F7_patch without a `value` key, which slipped past parse_judgment.py and
    crashed compose.py at `factor_data["value"]`. parse_judgment.py now drops
    malformed patches with a warning instead of passing them through."""

    def test_patch_missing_value_is_dropped(self):
        """F{N}_patch without a 'value' key → dropped with a warning, does not abort."""
        scored = _make_scored_semi(["R001"])
        entry = _make_entry("R001")
        entry["F7_patch"] = {"reasoning": "forgot to include value"}
        raw = json.dumps([entry])
        result = _run_parse(scored, raw)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        # F7_patch missing "value" is dropped, not passed through.
        assert "F7_patch" not in output["patches"]["R001"]
        assert "missing required 'value' key" in result.stderr

    def test_patch_non_dict_is_dropped(self):
        """F{N}_patch emitted as a bare number instead of an object → dropped."""
        scored = _make_scored_semi(["R001"])
        entry = _make_entry("R001")
        entry["F7_patch"] = 0.60
        raw = json.dumps([entry])
        result = _run_parse(scored, raw)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "F7_patch" not in output["patches"]["R001"]
        assert "must be an object" in result.stderr

    def test_patch_value_string_is_dropped(self):
        """F{N}_patch.value as a string instead of a number → dropped."""
        scored = _make_scored_semi(["R001"])
        entry = _make_entry("R001")
        entry["F7_patch"] = {"value": "0.60", "reasoning": "test"}
        raw = json.dumps([entry])
        result = _run_parse(scored, raw)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "F7_patch" not in output["patches"]["R001"]
        assert "must be a number or null" in result.stderr

    def test_patch_value_out_of_range_is_dropped(self):
        """F{N}_patch.value outside [0, 1] → dropped."""
        scored = _make_scored_semi(["R001"])
        entry = _make_entry("R001")
        entry["F7_patch"] = {"value": 1.5, "reasoning": "test"}
        raw = json.dumps([entry])
        result = _run_parse(scored, raw)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "F7_patch" not in output["patches"]["R001"]
        assert "must be in [0, 1]" in result.stderr

    def test_patch_null_value_is_allowed(self):
        """F{N}_patch.value == null is valid (means 'do not patch')."""
        scored = _make_scored_semi(["R001"])
        entry = _make_entry("R001")
        entry["F7_patch"] = {"value": None, "reasoning": "cannot judge"}
        raw = json.dumps([entry])
        output = _run_parse_ok(scored, raw)
        assert "F7_patch" in output["patches"]["R001"]
        assert output["patches"]["R001"]["F7_patch"]["value"] is None


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestErrors:
    def test_total_parse_failure_no_brackets(self):
        """Input with no [ ] brackets fails."""
        scored = _make_scored_semi(["R001"])
        result = _run_parse(scored, "I cannot score these rules because I need more context.")

        assert result.returncode != 0
        assert "FATAL" in result.stderr

    def test_empty_input(self):
        """Empty stdin fails."""
        scored = _make_scored_semi(["R001"])
        result = _run_parse(scored, "")

        assert result.returncode != 0
        assert "FATAL" in result.stderr

    def test_empty_array(self):
        """Empty array [] — all rules get null defaults."""
        scored = _make_scored_semi(["R001", "R002"])
        result = _run_parse(scored, "[]")
        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["patches"]["R001"]["F3"]["value"] is None
        assert output["patches"]["R002"]["F3"]["value"] is None

    def test_duplicate_ids_last_wins(self):
        """Duplicate rule IDs — last entry wins."""
        scored = _make_scored_semi(["R001"])
        entries = [
            _make_entry("R001", f3_value=0.50, f3_level=2),
            _make_entry("R001", f3_value=0.90, f3_level=4),
        ]
        raw = json.dumps(entries)
        result = _run_parse(scored, raw)
        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["patches"]["R001"]["F3"]["value"] == 0.90
        assert "WARNING" in result.stderr
        assert "duplicate" in result.stderr.lower()

    def test_invalid_json_in_brackets(self):
        """Malformed JSON between brackets."""
        scored = _make_scored_semi(["R001"])
        result = _run_parse(scored, "[{invalid json}]")

        assert result.returncode != 0
        assert "FATAL" in result.stderr

    def test_non_dict_entry_skipped(self):
        """Non-dict entries in the array are skipped with warning."""
        scored = _make_scored_semi(["R001"])
        raw = json.dumps(["not a dict", _make_entry("R001")])
        result = _run_parse(scored, raw)
        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert "R001" in output["patches"]
        assert "WARNING" in result.stderr

    def test_value_out_of_bounds_clamped(self):
        """Value outside [0, 1] gets clamped."""
        scored = _make_scored_semi(["R001"])
        entry = _make_entry("R001", f3_value=1.5, f3_level=4)
        raw = json.dumps([entry])
        result = _run_parse(scored, raw)
        assert result.returncode == 0

        output = json.loads(result.stdout)
        assert output["patches"]["R001"]["F3"]["value"] <= 1.0
        assert "WARNING" in result.stderr

    def test_scored_semi_wrong_schema_version_fatal(self):
        """scored_semi.json with wrong schema_version causes fatal exit."""
        scored = _make_scored_semi(["R001"])
        scored["schema_version"] = "2.0"
        raw = json.dumps([_make_entry("R001")])
        result = _run_parse(scored, raw)

        assert result.returncode != 0
        assert "FATAL" in result.stderr
        assert "schema_version" in result.stderr

    def test_scored_semi_missing_schema_version_warns(self):
        """scored_semi.json without schema_version warns but succeeds."""
        scored = _make_scored_semi(["R001"])
        del scored["schema_version"]
        raw = json.dumps([_make_entry("R001")])
        result = _run_parse(scored, raw)

        assert result.returncode == 0
        assert "WARNING" in result.stderr
        assert "schema_version" in result.stderr


# ---------------------------------------------------------------------------
# Rubric-parser compatibility (Phase 2a)
# ---------------------------------------------------------------------------

class TestRubricExamplesPassParser:
    """Every (level, value) pair in the rubric worked examples must be
    accepted by parse_judgment.py without correction. If this test fails,
    a rubric example teaches the model a pattern the parser will punish."""

    # Level ranges from parse_judgment.py (canonical from rubric docs)
    F3_LEVELS = {4: (0.90, 1.00), 3: (0.65, 0.85), 2: (0.40, 0.60), 1: (0.15, 0.35), 0: (0.00, 0.10)}
    F8_LEVELS = {3: (0.85, 1.00), 2: (0.55, 0.80), 1: (0.30, 0.50), 0: (0.10, 0.25)}

    def _extract_examples(self, rubric_path: str) -> list[tuple[int, float, str]]:
        """Extract (level, score, text_snippet) from a rubric file.

        Parses "Level N" headings and "Score: X.XX" in blockquotes.
        """
        import re
        from pathlib import Path

        rubric_text = (Path(__file__).parent.parent / "scripts" / "_data" / rubric_path).read_text(encoding="utf-8")
        examples = []
        current_level = None

        for line in rubric_text.split("\n"):
            # Match "Level N (X.XX–Y.YY):" at start of line
            level_match = re.match(r'^Level\s+(\d+)\s+\(', line)
            if level_match:
                current_level = int(level_match.group(1))
                continue

            # Match "Score: X.XX" — capture digits and exactly one decimal point
            score_match = re.search(r'Score:\s*(\d+\.\d{1,2})', line)
            if score_match and current_level is not None:
                score = float(score_match.group(1))
                snippet = line.strip()[:60]
                examples.append((current_level, score, snippet))

        return examples

    def test_f3_rubric_examples_in_range(self):
        """All F3 rubric worked examples have (level, value) pairs that
        parse_judgment.py will accept without correction."""
        examples = self._extract_examples("rubric_F3.md")
        assert len(examples) >= 6, f"Expected at least 6 F3 examples, found {len(examples)}"

        for level, value, snippet in examples:
            assert level in self.F3_LEVELS, f"Unknown F3 level {level} in: {snippet}"
            lo, hi = self.F3_LEVELS[level]
            # Value must be in range OR resolve to the stated level via >= scan
            in_range = lo <= value <= hi
            # Gap resolution: scan from highest level down
            resolved_level = None
            for lev in sorted(self.F3_LEVELS.keys(), reverse=True):
                if value >= self.F3_LEVELS[lev][0]:
                    resolved_level = lev
                    break
            assert in_range or resolved_level == level, \
                f"F3 example will be corrected by parser: level={level}, value={value}, " \
                f"range=[{lo}, {hi}], resolves_to_level={resolved_level}. Fix: {snippet}"

    def test_f8_rubric_examples_in_range(self):
        """All F8 rubric worked examples have (level, value) pairs that
        parse_judgment.py will accept without correction."""
        examples = self._extract_examples("rubric_F8.md")
        assert len(examples) >= 6, f"Expected at least 6 F8 examples, found {len(examples)}"

        for level, value, snippet in examples:
            assert level in self.F8_LEVELS, f"Unknown F8 level {level} in: {snippet}"
            lo, hi = self.F8_LEVELS[level]
            in_range = lo <= value <= hi
            resolved_level = None
            for lev in sorted(self.F8_LEVELS.keys(), reverse=True):
                if value >= self.F8_LEVELS[lev][0]:
                    resolved_level = lev
                    break
            assert in_range or resolved_level == level, \
                f"F8 example will be corrected by parser: level={level}, value={value}, " \
                f"range=[{lo}, {hi}], resolves_to_level={resolved_level}. Fix: {snippet}"
