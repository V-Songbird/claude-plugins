"""Tests for compose.py — formula verification, regressions, edge cases."""

import json
import math
import os
import tempfile

import pytest
from conftest import run_script, run_script_raw, PYTHON, SCRIPTS_DIR


def _run_compose(scored_data: dict, patches_data: dict) -> dict:
    """Write temp files and run compose.py with two file args."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as sf:
        json.dump(scored_data, sf)
        scored_path = sf.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as pf:
        json.dump(patches_data, pf)
        patches_path = pf.name

    try:
        import subprocess
        result = subprocess.run(
            [PYTHON, str(SCRIPTS_DIR / "compose.py"), scored_path, patches_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, "compose.py", result.stdout, result.stderr)
        return json.loads(result.stdout)
    finally:
        os.unlink(scored_path)
        os.unlink(patches_path)


def _run_compose_raw(scored_data: dict, patches_data: dict):
    """Run compose.py and return raw CompletedProcess."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as sf:
        json.dump(scored_data, sf)
        scored_path = sf.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as pf:
        json.dump(patches_data, pf)
        patches_path = pf.name

    try:
        import subprocess
        return subprocess.run(
            [PYTHON, str(SCRIPTS_DIR / "compose.py"), scored_path, patches_path],
            capture_output=True, text=True, timeout=30,
        )
    finally:
        os.unlink(scored_path)
        os.unlink(patches_path)


def _make_scored(rules: list[dict], source_files: list[dict] | None = None) -> dict:
    """Build a minimal scored_semi.json."""
    return {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_context": {"stack": [], "project_root": "/test"},
        "config": {"load_prob_overrides": {}, "severity_overrides": {}, "ignore_patterns": []},
        "source_files": source_files or [
            {"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
             "default_category": "mandate", "line_count": 50, "always_loaded": True},
        ],
        "rules": rules,
    }


def _make_rule(rule_id: str = "R001", factors: dict | None = None, category: str = "mandate",
               file_index: int = 0, line_start: int = 5, staleness: dict | None = None) -> dict:
    """Build a minimal rule with all 4 script-scored factors."""
    default_factors = {
        "F1": {"value": 0.85, "method": "lookup"},
        "F2": {"value": 0.85, "method": "classify"},
        "F4": {"value": 0.95, "method": "glob_match"},
        "F7": {"value": 0.80, "method": "count"},
    }
    if factors:
        default_factors.update(factors)
    return {
        "id": rule_id, "file_index": file_index, "text": "Test rule.",
        "line_start": line_start, "line_end": line_start, "category": category,
        "referenced_entities": [],
        "staleness": staleness or {"gated": False, "missing_entities": []},
        "factors": default_factors,
    }


def _make_patches(patches: dict, model_version: str = "test") -> dict:
    """Build judgment_patches.json."""
    return {"schema_version": "0.1", "model_version": model_version, "patches": patches}


def _patches_for(rule_id: str, f3: float = 0.80, f8: float = 0.65) -> dict:
    """Quick patch dict for one rule."""
    return {
        rule_id: {
            "F3": {"value": f3, "level": 3, "reasoning": "test"},
            "F8": {"value": f8, "level": 2, "reasoning": "test"},
        }
    }


# ---------------------------------------------------------------------------
# Per-rule formula tests
# ---------------------------------------------------------------------------

class TestPerRuleFormula:
    def test_worked_example(self):
        """Worked example from quality-model.md: score = 0.84 with F8 as a parallel signal."""
        rule = _make_rule(factors={
            "F1": {"value": 0.85}, "F2": {"value": 0.85},
            "F4": {"value": 0.95}, "F7": {"value": 0.80},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=0.80, f8=0.65))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        # F8 is a parallel signal, not in composite: expected = (1.5*0.85 + 1.0*0.85 + 1.3*0.80 + 1.0*0.95 + 2.0*0.80) / 6.8
        #                                             = (1.275 + 0.850 + 1.040 + 0.950 + 1.600) / 6.8 = 5.715/6.8 = 0.840
        assert abs(r["score"] - 0.840) <= 0.02, f"Expected ~0.840, got {r['score']}"
        assert abs(r["pre_floor_score"] - 0.840) <= 0.02
        assert r["floor"] == 1.0
        # F8 is still reported as a parallel signal
        assert r["f8_value"] == 0.65
        assert r["is_hook_candidate"] is False  # 0.65 > 0.40 threshold

    def test_contributions_sum(self):
        """Contributions should sum to approximately pre_floor_score."""
        rule = _make_rule()
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        contrib_sum = sum(r["contributions"].values())
        assert abs(contrib_sum - r["pre_floor_score"]) < 0.01


class TestSoftFloors:
    def test_soft_floor_f7(self):
        """F7=0.10 → floor = 0.50 (= 0.10 / 0.2)."""
        rule = _make_rule(factors={"F7": {"value": 0.10}})
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        result = _run_compose(scored, patches)
        assert result["rules"][0]["floor"] == 0.5

    def test_soft_floor_f4(self):
        """F4=0.05 → floor = 0.25 (= 0.05 / 0.2)."""
        rule = _make_rule(factors={"F4": {"value": 0.05}})
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        result = _run_compose(scored, patches)
        assert result["rules"][0]["floor"] == 0.25

    def test_staleness_gate(self):
        """Stale entities → floor multiplied by 0.05."""
        rule = _make_rule(staleness={"gated": True, "missing_entities": ["src/old/"]})
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        result = _run_compose(scored, patches)
        assert result["rules"][0]["floor"] == 0.05

    def test_floor_smooth_zero(self):
        """F7=0.0 → floor = 0.0, no NaN."""
        rule = _make_rule(factors={"F7": {"value": 0.0}})
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["floor"] == 0.0
        assert r["score"] == 0.0
        assert not math.isnan(r["score"])


class TestLayerOverlay:
    def test_layer_overlay_worked_example(self):
        """Worked example from quality-model.md: clarity layer is F1/F2/F7 (F6 is absorbed into F7)."""
        rule = _make_rule(factors={
            "F1": {"value": 0.85}, "F2": {"value": 0.85},
            "F4": {"value": 0.95}, "F7": {"value": 0.80},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=0.80, f8=0.65))
        result = _run_compose(scored, patches)
        layers = result["rules"][0]["layers"]
        # clarity = (1.5*0.85 + 1.0*0.85 + 2.0*0.80) / 4.5 = 3.725/4.5 = 0.828
        assert abs(layers["clarity"] - 0.828) <= 0.02
        assert abs(layers["activation"] - 0.87) <= 0.02
        # Mechanism layer is removed — F8 is a parallel signal, not a composite factor
        assert "mechanism" not in layers

    def test_layer_overlay_division_safety(self):
        """All Clarity inputs at 0.0 → Clarity = 0.0, no NaN."""
        rule = _make_rule(factors={
            "F1": {"value": 0.0}, "F2": {"value": 0.0},
            "F7": {"value": 0.0},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=0.0, f8=0.0))
        result = _run_compose(scored, patches)
        layers = result["rules"][0]["layers"]
        assert layers["clarity"] == 0.0
        assert not math.isnan(layers["clarity"])


class TestDominantWeakness:
    def test_dominant_weakness(self):
        """F7 is dominant for the worked example.
        Gap = w_F7 * (1 - F7) = 2.0 * (1 - 0.80) = 0.40.
        F8 is a parallel signal, not a composite factor, so it cannot be the dominant weakness.
        """
        rule = _make_rule(factors={
            "F1": {"value": 0.85}, "F2": {"value": 0.85},
            "F4": {"value": 0.95}, "F7": {"value": 0.80},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=0.80, f8=0.65))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["dominant_weakness"] == "F7"
        assert abs(r["dominant_weakness_gap"] - 0.40) <= 0.01

    def test_dominant_weakness_perfect_rule(self):
        """All factors at 1.0 → dominant_weakness is null."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=1.0))
        result = _run_compose(scored, patches)
        assert result["rules"][0]["dominant_weakness"] is None


class TestFailureClass:
    """failure_class is a presentation-layer label derived from dominant_weakness.

    F3/F4 map to "drift" (rule not in attention when it fires).
    F1/F2/F7 map to "ambiguity" (rule reads multiple ways).
    Conflict is unmeasured in the composite and never appears here.
    """

    def test_f7_weakness_maps_to_ambiguity(self):
        rule = _make_rule(factors={
            "F1": {"value": 0.85}, "F2": {"value": 0.85},
            "F4": {"value": 0.95}, "F7": {"value": 0.50},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=0.80, f8=0.65))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["dominant_weakness"] == "F7"
        assert r["failure_class"] == "ambiguity"

    def test_f3_weakness_maps_to_drift(self):
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        scored = _make_scored([rule])
        # F3 is the judgment factor; low F3 = distant trigger-action
        patches = _make_patches(_patches_for("R001", f3=0.30, f8=1.0))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["dominant_weakness"] == "F3"
        assert r["failure_class"] == "drift"

    def test_f4_weakness_maps_to_drift(self):
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 0.30}, "F7": {"value": 1.0},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=1.0))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["dominant_weakness"] == "F4"
        assert r["failure_class"] == "drift"

    def test_f1_weakness_maps_to_ambiguity(self):
        rule = _make_rule(factors={
            "F1": {"value": 0.30}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=1.0))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["dominant_weakness"] == "F1"
        assert r["failure_class"] == "ambiguity"

    def test_perfect_rule_has_null_failure_class(self):
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=1.0))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["dominant_weakness"] is None
        assert r["failure_class"] is None


# ---------------------------------------------------------------------------
# Conflict detection (corpus-level)
# ---------------------------------------------------------------------------


def _make_conflict_rule(rule_id: str, polarity: str, markers: list[str],
                       text: str = "Test rule.", line_start: int = 5) -> dict:
    """Build a rule with explicit F2 polarity and F7 concrete_markers for
    conflict-detection tests."""
    return _make_rule(
        rule_id=rule_id,
        line_start=line_start,
        factors={
            "F1": {"value": 0.85, "method": "lookup"},
            "F2": {"value": 0.85, "method": "classify", "matched_category": polarity},
            "F4": {"value": 0.95, "method": "glob_match"},
            "F7": {"value": 0.80, "method": "count",
                   "concrete_markers": markers,
                   "concrete_count": len(markers),
                   "abstract_count": 0},
        },
    ) | {"text": text}


class TestConflictDetection:
    """Polarity mismatch on a shared concrete marker flags a conflict pair."""

    def test_prohibit_plus_assert_on_shared_marker_flags_conflict(self):
        rules = [
            _make_conflict_rule("R001", "prohibition", ["src/main/gen/"],
                                text="NEVER edit files in src/main/gen/ directly."),
            _make_conflict_rule("R002", "positive_imperative", ["src/main/gen/"],
                                text="Use src/main/gen/ cached results for speed."),
        ]
        scored = _make_scored(rules)
        patches = _make_patches({
            "R001": _patches_for("R001")["R001"],
            "R002": _patches_for("R002")["R002"],
        })
        result = _run_compose(scored, patches)

        conflicts = result["conflicts"]
        assert len(conflicts) == 1
        c = conflicts[0]
        assert c["type"] == "polarity_mismatch"
        # rule_a is always the prohibitive side
        assert c["rule_a"]["id"] == "R001"
        assert c["rule_a"]["polarity"] == "prohibition"
        assert c["rule_b"]["id"] == "R002"
        assert c["rule_b"]["polarity"] == "positive_imperative"
        assert c["shared_markers"] == ["src/main/gen/"]

    def test_two_positives_do_not_conflict(self):
        rules = [
            _make_conflict_rule("R001", "positive_imperative", ["src/main/gen/"]),
            _make_conflict_rule("R002", "positive_imperative", ["src/main/gen/"]),
        ]
        scored = _make_scored(rules)
        patches = _make_patches({
            "R001": _patches_for("R001")["R001"],
            "R002": _patches_for("R002")["R002"],
        })
        result = _run_compose(scored, patches)
        assert result["conflicts"] == []

    def test_two_prohibitions_do_not_conflict(self):
        rules = [
            _make_conflict_rule("R001", "prohibition", ["src/main/gen/"]),
            _make_conflict_rule("R002", "prohibition", ["src/main/gen/"]),
        ]
        scored = _make_scored(rules)
        patches = _make_patches({
            "R001": _patches_for("R001")["R001"],
            "R002": _patches_for("R002")["R002"],
        })
        result = _run_compose(scored, patches)
        assert result["conflicts"] == []

    def test_no_shared_marker_means_no_conflict(self):
        rules = [
            _make_conflict_rule("R001", "prohibition", ["src/main/gen/"]),
            _make_conflict_rule("R002", "positive_imperative", ["src/test/utils/"]),
        ]
        scored = _make_scored(rules)
        patches = _make_patches({
            "R001": _patches_for("R001")["R001"],
            "R002": _patches_for("R002")["R002"],
        })
        result = _run_compose(scored, patches)
        assert result["conflicts"] == []

    def test_stoplist_markers_do_not_trigger_conflicts(self):
        """Generic words like 'use' or 'code' are filtered — sharing them
        between a prohibition and a positive is not a conflict signal."""
        rules = [
            _make_conflict_rule("R001", "prohibition", ["use", "code"]),
            _make_conflict_rule("R002", "positive_imperative", ["use", "code"]),
        ]
        scored = _make_scored(rules)
        patches = _make_patches({
            "R001": _patches_for("R001")["R001"],
            "R002": _patches_for("R002")["R002"],
        })
        result = _run_compose(scored, patches)
        assert result["conflicts"] == []

    def test_short_markers_do_not_trigger_conflicts(self):
        """Markers shorter than 3 characters are too generic."""
        rules = [
            _make_conflict_rule("R001", "prohibition", ["x", "io"]),
            _make_conflict_rule("R002", "positive_imperative", ["x", "io"]),
        ]
        scored = _make_scored(rules)
        patches = _make_patches({
            "R001": _patches_for("R001")["R001"],
            "R002": _patches_for("R002")["R002"],
        })
        result = _run_compose(scored, patches)
        assert result["conflicts"] == []

    def test_non_mandate_rules_excluded(self):
        """Override and preference rules do not participate in conflict
        detection — they are expected to relax or refine mandates."""
        rules = [
            _make_conflict_rule("R001", "prohibition", ["src/main/gen/"]),
            _make_conflict_rule("R002", "positive_imperative", ["src/main/gen/"]),
        ]
        # Second rule is an override, not a mandate
        rules[1]["category"] = "override"
        scored = _make_scored(rules)
        patches = _make_patches({
            "R001": _patches_for("R001")["R001"],
            "R002": _patches_for("R002")["R002"],
        })
        result = _run_compose(scored, patches)
        assert result["conflicts"] == []

    def test_positive_with_alternative_counts_as_assertive(self):
        """F2 category 'positive_with_alternative' is an assertive polarity."""
        rules = [
            _make_conflict_rule("R001", "prohibition", ["CachedValuesManager"]),
            _make_conflict_rule("R002", "positive_with_alternative",
                                ["CachedValuesManager"]),
        ]
        scored = _make_scored(rules)
        patches = _make_patches({
            "R001": _patches_for("R001")["R001"],
            "R002": _patches_for("R002")["R002"],
        })
        result = _run_compose(scored, patches)
        assert len(result["conflicts"]) == 1
        assert result["conflicts"][0]["rule_b"]["polarity"] == "positive_with_alternative"

    def test_conflicts_sorted_by_rule_ids(self):
        """Conflict pairs are emitted in a deterministic order."""
        rules = [
            _make_conflict_rule("R003", "positive_imperative", ["apiClient"]),
            _make_conflict_rule("R001", "prohibition", ["apiClient"]),
            _make_conflict_rule("R002", "positive_imperative", ["apiClient"]),
        ]
        scored = _make_scored(rules)
        patches = _make_patches({
            "R001": _patches_for("R001")["R001"],
            "R002": _patches_for("R002")["R002"],
            "R003": _patches_for("R003")["R003"],
        })
        result = _run_compose(scored, patches)
        conflicts = result["conflicts"]
        # R001 prohibits; R002 and R003 are positive → two pairs
        assert len(conflicts) == 2
        ids = [(c["rule_a"]["id"], c["rule_b"]["id"]) for c in conflicts]
        assert ids == sorted(ids)

    def test_empty_conflicts_when_no_rules_share_markers(self):
        """Emitting `conflicts: []` for a clean corpus is the contract."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0, "matched_category": "positive_imperative"},
            "F4": {"value": 1.0}, "F7": {"value": 1.0, "concrete_markers": ["fooBar"],
                                          "concrete_count": 1, "abstract_count": 0},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        result = _run_compose(scored, patches)
        assert result["conflicts"] == []


# ---------------------------------------------------------------------------
# F-20: Position weight smoothing
# ---------------------------------------------------------------------------

class TestPositionWeightSmooth:
    """F-20: smooth triangular position weight, no cliff at 0.20/0.80."""

    def test_smooth_no_cliff(self):
        """Positions 0.19 and 0.21 should differ by less than 0.02.

        Old step function: 0.19→1.0, 0.21→0.80 (diff=0.20).
        New smooth: both near 0.92 (diff<0.02).
        """
        rule_19 = _make_rule("R001", line_start=19)
        rule_21 = _make_rule("R002", line_start=21)
        scored = _make_scored(
            [rule_19, rule_21],
            source_files=[{
                "path": "CLAUDE.md", "globs": [], "glob_match_count": None,
                "default_category": "mandate", "line_count": 100, "always_loaded": True,
            }],
        )
        patches = _make_patches({
            **_patches_for("R001"),
            **_patches_for("R002"),
        })
        result = _run_compose(scored, patches)
        scores = {r["id"]: r["score"] for r in result["rules"]}
        # With the same factor values, the only difference is position weight
        assert abs(scores["R001"] - scores["R002"]) < 0.02, \
            f"Position cliff: R001={scores['R001']}, R002={scores['R002']}"

    def test_symmetry(self):
        """Position 0.10 and 0.90 should produce identical scores.
        Position 0.30 and 0.70 should produce identical scores.
        """
        rule_10 = _make_rule("R001", line_start=10)
        rule_90 = _make_rule("R002", line_start=90)
        rule_30 = _make_rule("R003", line_start=30)
        rule_70 = _make_rule("R004", line_start=70)
        scored = _make_scored(
            [rule_10, rule_90, rule_30, rule_70],
            source_files=[{
                "path": "CLAUDE.md", "globs": [], "glob_match_count": None,
                "default_category": "mandate", "line_count": 100, "always_loaded": True,
            }],
        )
        patches = _make_patches({
            **_patches_for("R001"),
            **_patches_for("R002"),
            **_patches_for("R003"),
            **_patches_for("R004"),
        })
        result = _run_compose(scored, patches)
        scores = {r["id"]: r["score"] for r in result["rules"]}
        assert scores["R001"] == scores["R002"], \
            f"Asymmetric: pos 0.10 → {scores['R001']}, pos 0.90 → {scores['R002']}"
        assert scores["R003"] == scores["R004"], \
            f"Asymmetric: pos 0.30 → {scores['R003']}, pos 0.70 → {scores['R004']}"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_all_factors_perfect(self):
        """All factors 1.0 → score=1.0, floor=1.0, no NaN."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=1.0))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["score"] == 1.0
        assert r["floor"] == 1.0
        assert r["dominant_weakness"] is None

    def test_all_factors_zero(self):
        """All factors 0.0 → score=0.0, floor=0.0, no NaN."""
        rule = _make_rule(factors={
            "F1": {"value": 0.0}, "F2": {"value": 0.0},
            "F4": {"value": 0.0}, "F7": {"value": 0.0},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=0.0, f8=0.0))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["score"] == 0.0
        assert r["floor"] == 0.0
        assert not math.isnan(r["score"])
        assert r["leverage"] == 1.0  # 1.0 * 1.0 * (1 - 0) = 1.0

    def test_length_penalty_boundary(self):
        """lines=120 → penalty=1.0; lines=121 → penalty=0.995."""
        sf_120 = [{"path": "a.md", "globs": [], "glob_match_count": None,
                   "default_category": "mandate", "line_count": 120, "always_loaded": True}]
        sf_121 = [{"path": "a.md", "globs": [], "glob_match_count": None,
                   "default_category": "mandate", "line_count": 121, "always_loaded": True}]

        rule = _make_rule()
        patches = _make_patches(_patches_for("R001"))

        r120 = _run_compose(_make_scored([rule], sf_120), patches)
        r121 = _run_compose(_make_scored([rule], sf_121), patches)

        f120 = next(f for f in r120["files"] if f["path"] == "a.md")
        f121 = next(f for f in r121["files"] if f["path"] == "a.md")

        assert f120["length_penalty"] == 1.0
        assert f121["length_penalty"] == 0.995

    def test_length_penalty_floor(self):
        """lines=200 → penalty=0.6; lines=1000 → still 0.6 (floor)."""
        sf_200 = [{"path": "a.md", "globs": [], "glob_match_count": None,
                   "default_category": "mandate", "line_count": 200, "always_loaded": True}]
        sf_1000 = [{"path": "a.md", "globs": [], "glob_match_count": None,
                    "default_category": "mandate", "line_count": 1000, "always_loaded": True}]

        rule = _make_rule()
        patches = _make_patches(_patches_for("R001"))

        r200 = _run_compose(_make_scored([rule], sf_200), patches)
        r1000 = _run_compose(_make_scored([rule], sf_1000), patches)

        f200 = next(f for f in r200["files"] if f["path"] == "a.md")
        f1000 = next(f for f in r1000["files"] if f["path"] == "a.md")

        assert f200["length_penalty"] == 0.6
        assert f1000["length_penalty"] == 0.6


# ---------------------------------------------------------------------------
# Regression tests
# ---------------------------------------------------------------------------

class TestV101Regressions:
    def test_leverage_sort_monotonic(self):
        """Rules must be sorted by leverage descending."""
        rules = [
            _make_rule("R001", factors={"F1": {"value": 0.85}, "F7": {"value": 0.80}}, line_start=5),
            _make_rule("R002", factors={"F1": {"value": 0.20}, "F7": {"value": 0.30}}, line_start=10),
            _make_rule("R003", factors={"F1": {"value": 0.50}, "F7": {"value": 0.60}}, line_start=15),
        ]
        patches = _make_patches({
            **_patches_for("R001"), **_patches_for("R002"), **_patches_for("R003"),
        })
        result = _run_compose(_make_scored(rules), patches)
        mandate_rules = [r for r in result["rules"] if r["category"] == "mandate"]
        leverages = [r["leverage"] for r in mandate_rules]
        assert leverages == sorted(leverages, reverse=True), \
            f"Leverage not monotonic descending: {leverages}"

    def test_headline_pulls_effective(self):
        """Headline must be effective_corpus_quality, not corpus_quality."""
        rule = _make_rule()
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        result = _run_compose(scored, patches)
        assert "effective_corpus_quality" in result
        assert "score" in result["effective_corpus_quality"]
        # corpus_quality should be diagnostic, not headline
        assert "rule_mean_score" in result["corpus_quality"]
        assert "note" in result["corpus_quality"]

    def test_category_floors(self):
        """Mandate floor=0.50, override=0.25, preference=0.25 (in the spec, not enforced in compose)."""
        # compose.py computes scores; floors are about reporting thresholds
        # Just verify the score computes correctly for each category
        for cat in ("mandate", "override", "preference"):
            rule = _make_rule(category=cat)
            scored = _make_scored([rule])
            patches = _make_patches(_patches_for("R001"))
            result = _run_compose(scored, patches)
            assert result["rules"][0]["score"] > 0  # Score computes for all categories


# ---------------------------------------------------------------------------
# Patch merge logic
# ---------------------------------------------------------------------------

class TestPatchMerge:
    def test_judgment_patch_merge(self):
        """Patches should add F3 and F8 to rules."""
        rule = _make_rule()
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=0.80, f8=0.65))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["factors"]["F3"]["value"] == 0.80
        assert r["factors"]["F8"]["value"] == 0.65

    def test_missing_factor_fatal(self):
        """Rule without F3/F8 patch → fatal error naming upstream stage."""
        rule = _make_rule()
        scored = _make_scored([rule])
        patches = _make_patches({})  # No patches at all
        proc = _run_compose_raw(scored, patches)
        assert proc.returncode != 0
        assert "FATAL" in proc.stderr
        assert "F3" in proc.stderr or "judgment patches" in proc.stderr

    def test_patch_nonexistent_rule(self):
        """Patch for rule that doesn't exist → warning, no crash."""
        rule = _make_rule("R001")
        scored = _make_scored([rule])
        patches = _make_patches({
            **_patches_for("R001"),
            "R999": {"F3": {"value": 0.5}, "F8": {"value": 0.5}},
        })
        result = _run_compose(scored, patches)  # Should not crash

    def test_unknown_factor_in_patch(self):
        """Unknown factor F9 → ignored with warning."""
        rule = _make_rule("R001")
        scored = _make_scored([rule])
        patches = _make_patches({
            "R001": {
                "F3": {"value": 0.80, "level": 3, "reasoning": "test"},
                "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
                "F9": {"value": 0.50},
            }
        })
        result = _run_compose(scored, patches)
        assert "F9" not in result["rules"][0]["factors"]

    def test_factor_confidence_low_preserved(self):
        """factor_confidence_low should carry through to audit.json."""
        rule = _make_rule()
        rule["factor_confidence_low"] = ["F7"]
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        result = _run_compose(scored, patches)
        assert "factor_confidence_low" in result["rules"][0]
        assert "F7" in result["rules"][0]["factor_confidence_low"]


# ---------------------------------------------------------------------------
# F-16: Partial patch validation
# ---------------------------------------------------------------------------

class TestF16PartialPatchValidation:
    """F-16: After patching, every rule must have F3 AND F8 as keys in factors.
    The check is key presence (f not in factors), NOT truthy value check.
    Null-valued factors like {"value": null} are present keys and must pass.
    """

    def test_partial_patch_f3_only_fatal(self):
        """Patch with F3 but no F8 key → fatal exit."""
        rule = _make_rule("R001")
        scored = _make_scored([rule])
        # Patch only F3, omit F8 entirely
        patches = _make_patches({
            "R001": {
                "F3": {"value": 0.80, "level": 3, "reasoning": "test"},
            }
        })
        proc = _run_compose_raw(scored, patches)
        assert proc.returncode != 0, "Should fatal when F8 key missing"
        assert "FATAL" in proc.stderr
        assert "F8" in proc.stderr

    def test_partial_patch_f8_only_fatal(self):
        """Patch with F8 but no F3 key → fatal exit."""
        rule = _make_rule("R001")
        scored = _make_scored([rule])
        # Patch only F8, omit F3 entirely
        patches = _make_patches({
            "R001": {
                "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
            }
        })
        proc = _run_compose_raw(scored, patches)
        assert proc.returncode != 0, "Should fatal when F3 key missing"
        assert "FATAL" in proc.stderr
        assert "F3" in proc.stderr

    def test_null_factor_passes_partial_check(self):
        """Null-valued factor {"value": null} is a present key — must NOT fatal.

        This pins the contract Phase 1d depends on: a rule the model couldn't
        score gets {"F3": {"value": null, "level": null, "reasoning": "..."}}
        which is a present key with a null value. The F-16 invariant check
        must pass it through to compose's scoring path.
        """
        rule = _make_rule("R001")
        scored = _make_scored([rule])
        patches = _make_patches({
            "R001": {
                "F3": {"value": None, "level": None, "reasoning": "model_omitted"},
                "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
            }
        })
        # Should succeed — F3 key is present (value is null but key exists)
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert "F3" in r["factors"]
        # Phase 1d: null F3 is excluded from formula, not defaulted to 0.50
        assert r["degraded"] is True
        assert "F3" in r["degraded_factors"]
        assert r["contributions"]["F3"] is None


# ---------------------------------------------------------------------------
# F-13 + F-6: Null factor handling (degraded rules)
# ---------------------------------------------------------------------------

class TestNullFactorHandling:
    """Phase 1d: null factor values are excluded from the formula, not defaulted to 0.50."""

    def test_null_factor_excluded_from_score(self):
        """A rule with null F3 should score differently than one with F3=0.50.

        With F3=0.50: score includes F3 contribution.
        With F3=null: score excludes F3, computed over 6 factors instead of 7.
        The scores must differ — null exclusion is not equivalent to 0.50 substitution.
        """
        rule_with_value = _make_rule("R001")
        scored_with = _make_scored([rule_with_value])
        patches_with = _make_patches({"R001": {
            "F3": {"value": 0.50, "level": 2, "reasoning": "test"},
            "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
        }})
        result_with = _run_compose(scored_with, patches_with)

        rule_with_null = _make_rule("R001")
        scored_null = _make_scored([rule_with_null])
        patches_null = _make_patches({"R001": {
            "F3": {"value": None, "level": None, "reasoning": "model_omitted"},
            "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
        }})
        result_null = _run_compose(scored_null, patches_null)

        score_with = result_with["rules"][0]["score"]
        score_null = result_null["rules"][0]["score"]
        assert score_with != score_null, \
            f"Null exclusion must differ from 0.50 substitution: both={score_with}"

    def test_degraded_flag_set(self):
        """Rule with null factor has degraded=True and degraded_factors list."""
        rule = _make_rule("R001")
        scored = _make_scored([rule])
        patches = _make_patches({"R001": {
            "F3": {"value": None, "level": None, "reasoning": "model_omitted"},
            "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
        }})
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["degraded"] is True
        assert "F3" in r["degraded_factors"]
        # 4 non-null composite factors out of 5 (F8 is parallel, not composite)
        assert r["scored_count"] == 4

    def test_non_degraded_rule(self):
        """Normal rule has degraded=False, empty degraded_factors."""
        rule = _make_rule("R001")
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["degraded"] is False
        assert r["degraded_factors"] == []
        # 5 composite factors (F8 is a parallel signal; F6 is absorbed into F7)
        assert r["scored_count"] == 5

    def test_degraded_skips_dominant_weakness(self):
        """Null F3 should not appear as dominant weakness.

        With F7=0.30 and F3=null, dominant_weakness should be F7 (lowest
        non-null factor), not F3.
        """
        rule = _make_rule("R001", factors={"F7": {"value": 0.30}})
        scored = _make_scored([rule])
        patches = _make_patches({"R001": {
            "F3": {"value": None, "level": None, "reasoning": "model_omitted"},
            "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
        }})
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["dominant_weakness"] != "F3"
        assert r["dominant_weakness"] == "F7"

    def test_null_factor_in_contributions(self):
        """Contribution for a null factor should be None, not 0."""
        rule = _make_rule("R001")
        scored = _make_scored([rule])
        patches = _make_patches({"R001": {
            "F3": {"value": None, "level": None, "reasoning": "model_omitted"},
            "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
        }})
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["contributions"]["F3"] is None
        # F8 is a parallel signal, not in composite contributions
        assert "F8" not in r["contributions"]
        # F8 value is reported separately
        assert r["f8_value"] == 0.65

    def test_degraded_not_in_positive_findings(self):
        """A degraded rule scoring > 0.80 must NOT appear in positive_findings."""
        # All mechanical factors high, so score > 0.80 even without F3
        rule = _make_rule("R001", factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 0.95},
        })
        scored = _make_scored([rule])
        patches = _make_patches({"R001": {
            "F3": {"value": None, "level": None, "reasoning": "model_omitted"},
            "F8": {"value": 0.90, "level": 3, "reasoning": "test"},
        }})
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["score"] > 0.80, f"Setup: need score > 0.80, got {r['score']}"
        assert r["degraded"] is True
        positive_ids = [p.get("file", "") for p in result.get("positive_findings", [])]
        # Degraded rules should be filtered out
        assert len(result.get("positive_findings", [])) == 0

    def test_all_null_edge_case(self):
        """All factors null: score=0.0, no crash, degraded=True."""
        rule = _make_rule("R001", factors={
            "F1": {"value": None}, "F2": {"value": None},
            "F4": {"value": None}, "F7": {"value": None},
        })
        scored = _make_scored([rule])
        patches = _make_patches({"R001": {
            "F3": {"value": None, "level": None, "reasoning": "all null"},
            "F8": {"value": None, "level": None, "reasoning": "all null"},
        }})
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["score"] == 0.0
        assert r["degraded"] is True
        assert r["scored_count"] == 0
        assert len(r["degraded_factors"]) == 5  # 5 composite factors (F8 is a parallel signal)

    def test_mechanical_only_score(self):
        """Rule with null F3/F8 has mechanical_score from F1+F2+F4+F7 only."""
        rule = _make_rule("R001", factors={
            "F1": {"value": 0.85}, "F2": {"value": 0.85},
            "F4": {"value": 0.95}, "F7": {"value": 0.80},
        })
        scored = _make_scored([rule])
        patches = _make_patches({"R001": {
            "F3": {"value": None, "level": None, "reasoning": "model_omitted"},
            "F8": {"value": None, "level": None, "reasoning": "model_omitted"},
        }})
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["mechanical_score"] is not None
        assert r["mechanical_score"] > 0
        # mechanical_score should equal the full score when F3/F8 are null
        # (since those are the only null factors)
        assert abs(r["mechanical_score"] - r["pre_floor_score"]) < 0.01

    def test_value_zero_not_treated_as_null(self):
        """value: 0.0 is a legitimate score, NOT null. Must not be excluded."""
        rule = _make_rule("R001")
        scored = _make_scored([rule])
        patches = _make_patches({"R001": {
            "F3": {"value": 0.0, "level": 0, "reasoning": "no trigger"},
            "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
        }})
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["degraded"] is False
        # 5 composite factors (F8 is a parallel signal)
        assert r["scored_count"] == 5
        assert r["contributions"]["F3"] is not None
        assert r["contributions"]["F3"] == 0.0

    def test_null_f7_skips_soft_floor(self):
        """Null F7 skips the F7 soft floor (assume 1.0, no penalty for unmeasured)."""
        # Normal rule with F7=0.10 gets floor=0.50 from soft_floor(0.10, 0.2)
        rule_low_f7 = _make_rule("R001", factors={"F7": {"value": 0.10}})
        scored_low = _make_scored([rule_low_f7])
        patches_low = _make_patches(_patches_for("R001"))
        result_low = _run_compose(scored_low, patches_low)

        # Rule with F7=null should skip the floor entirely
        rule_null_f7 = _make_rule("R001", factors={"F7": {"value": None}})
        scored_null = _make_scored([rule_null_f7])
        patches_null = _make_patches(_patches_for("R001"))
        result_null = _run_compose(scored_null, patches_null)

        floor_low = result_low["rules"][0]["floor"]
        floor_null = result_null["rules"][0]["floor"]
        assert floor_low == 0.5, f"F7=0.10 should get floor 0.5, got {floor_low}"
        assert floor_null == 1.0, f"F7=null should skip floor (1.0), got {floor_null}"
        assert "F7" in result_null["rules"][0].get("skipped_floors", [])


# ---------------------------------------------------------------------------
# Corpus scoring
# ---------------------------------------------------------------------------

class TestCorpusScoring:
    def test_effective_corpus_quality(self):
        """Effective corpus should aggregate file scores, not rule scores."""
        rules = [_make_rule("R001", line_start=5), _make_rule("R002", line_start=10)]
        sf = [{"path": "CLAUDE.md", "globs": [], "glob_match_count": None,
               "default_category": "mandate", "line_count": 50, "always_loaded": True}]
        scored = _make_scored(rules, sf)
        patches = _make_patches({**_patches_for("R001"), **_patches_for("R002")})
        result = _run_compose(scored, patches)
        assert "effective_corpus_quality" in result
        assert result["effective_corpus_quality"]["score"] > 0

    def test_non_mandate_excluded_from_corpus(self):
        """Override/preference rules excluded from corpus_quality."""
        mandate = _make_rule("R001", category="mandate")
        pref = _make_rule("R002", category="preference")
        scored = _make_scored([mandate, pref])
        patches = _make_patches({**_patches_for("R001"), **_patches_for("R002")})
        result = _run_compose(scored, patches)
        assert result["corpus_quality"]["rule_count"] == 1  # Only mandate
        assert result["guideline_quality"]["rule_count"] == 1


# ---------------------------------------------------------------------------
# Schema output
# ---------------------------------------------------------------------------

class TestSchemaOutput:
    def test_methodology_present(self):
        rule = _make_rule()
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        result = _run_compose(scored, patches)
        assert "methodology" in result
        assert result["methodology"]["weights_version"] == "quality-heuristic-0.1"
        assert result["methodology"]["model_version"] == "test"
        assert result["schema_version"] == "0.1"

    def test_schema_version_mismatch_fatal(self):
        """Wrong schema_version on scored_semi → fatal error."""
        rule = _make_rule()
        scored = _make_scored([rule])
        scored["schema_version"] = "2.0"
        patches = _make_patches(_patches_for("R001"))
        proc = _run_compose_raw(scored, patches)
        assert proc.returncode != 0
        assert "Schema version mismatch" in proc.stderr

    def test_patches_schema_version_mismatch_fatal(self):
        """Wrong schema_version on patches → fatal error."""
        rule = _make_rule()
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001"))
        patches["schema_version"] = "2.0"
        proc = _run_compose_raw(scored, patches)
        assert proc.returncode != 0
        assert "Schema version mismatch" in proc.stderr
        assert "judgment_patches" in proc.stderr


# ---------------------------------------------------------------------------
# F8 is a parallel signal, not a composite contributor
# ---------------------------------------------------------------------------

class TestHookOpportunities:
    def test_composite_score_excludes_f8(self):
        """Per-rule score uses F1/F2/F3/F4/F7 only; F8 does not drag it down."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=0.0))  # F8=0.0
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["score"] >= 0.99  # F8=0.0 does NOT drag composite down

    def test_hook_opportunities_populated_for_low_f8(self):
        """Rules with F8 < threshold appear in audit['hook_opportunities']."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=0.30))
        result = _run_compose(scored, patches)
        assert len(result.get("hook_opportunities", [])) == 1
        assert result["hook_opportunities"][0]["id"] == "R001"
        assert result["rules"][0]["is_hook_candidate"] is True
        assert result["rules"][0]["f8_value"] == 0.30

    def test_hook_opportunities_empty_when_all_high_f8(self):
        """No hook opportunities when all rules score F8 >= threshold."""
        rule = _make_rule(factors={
            "F1": {"value": 0.80}, "F2": {"value": 0.80},
            "F4": {"value": 0.80}, "F7": {"value": 0.80},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=0.80, f8=0.90))
        result = _run_compose(scored, patches)
        assert result.get("hook_opportunities", []) == []
        assert result["rules"][0]["is_hook_candidate"] is False

    def test_dominant_weakness_never_f8(self):
        """Invariant: F8 is parallel, must never appear as dominant_weakness.

        Even when F8 is the lowest-scoring factor for a rule, the dominant_weakness
        field reports the weakest *composite* factor (F1/F2/F3/F4/F7) — F8 is
        excluded from the composite and therefore from the weakness calculation.
        """
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 0.50},  # F7 is the composite weakness
        })
        scored = _make_scored([rule])
        # F8=0.05 is drastically lower than any composite factor, but must not
        # be reported as the dominant weakness.
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=0.05))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        assert r["dominant_weakness"] != "F8", (
            f"F8 appeared as dominant_weakness (got {r['dominant_weakness']}) — "
            "F8 is separated from the composite; it must never be reported "
            "as a dominant weakness."
        )
        assert r["dominant_weakness"] == "F7"  # F7=0.50 is the actual weakest composite factor
        assert r["f8_value"] == 0.05
        assert r["is_hook_candidate"] is True

    def test_suggested_enforcement_routes_commit_to_git_hook(self):
        """Rules mentioning commit/push keywords should suggest a git hook."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        rule["text"] = "Never force-push to the main branch."
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=0.20))
        result = _run_compose(scored, patches)
        assert len(result["hook_opportunities"]) == 1
        assert "Git hook" in result["hook_opportunities"][0]["suggested_enforcement"]

    def test_suggested_enforcement_routes_prettier_to_linter(self):
        """Rules mentioning prettier/lint should suggest a linter/formatter config."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        rule["text"] = "Run prettier on all TypeScript files."
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=0.20))
        result = _run_compose(scored, patches)
        assert "Linter" in result["hook_opportunities"][0]["suggested_enforcement"] or \
               "formatter" in result["hook_opportunities"][0]["suggested_enforcement"]

    def test_suggested_enforcement_routes_edit_to_claude_code_hook(self):
        """Rules about editing/writing src/ files should suggest a Claude Code hook."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        rule["text"] = "When editing files in src/, update the changelog."
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=0.20))
        result = _run_compose(scored, patches)
        assert "Claude Code hook" in result["hook_opportunities"][0]["suggested_enforcement"]

    def test_suggested_enforcement_falls_back_when_no_keyword_matches(self):
        """Rules with no recognizable enforcement-layer keyword fall back to generic."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0}, "F2": {"value": 1.0},
            "F4": {"value": 1.0}, "F7": {"value": 1.0},
        })
        rule["text"] = "Follow the architectural principles."
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=0.20))
        result = _run_compose(scored, patches)
        assert "Mechanical enforcement" in result["hook_opportunities"][0]["suggested_enforcement"]


class TestF4DominantWeaknessUX:
    """F4 regression from Dallas-Digital dogfood: a rule whose F4 evidence is
    `implicit_scope_trust` (0.85 — correctly trusting its paths: frontmatter)
    must not be flagged as `dominant_weakness: F4`. Users followed the resulting
    'Loaded in the wrong context' advice and added redundant trigger prefixes
    that didn't improve the score — because the rule was already structurally
    correct on F4."""

    def test_implicit_scope_trust_is_not_dominant_weakness(self):
        """F4 at 0.85 via implicit_scope_trust cannot dominate other weak factors."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0, "method": "lookup"},
            "F2": {"value": 1.0, "method": "classify"},
            "F4": {"value": 0.85, "method": "keyword_overlap", "loading": "glob-scoped",
                    "trigger_match": "implicit_scope_trust"},
            "F7": {"value": 0.90, "method": "count"},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=0.80))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        # F4 is the structurally lowest factor (0.85 vs F7=0.90 vs all others=1.0),
        # but its implicit_scope_trust evidence means the rule is already well-scoped.
        # Dominant weakness must fall to F7 (next-lowest composite factor), not F4.
        assert r["dominant_weakness"] != "F4", (
            f"F4 with implicit_scope_trust was flagged as dominant weakness "
            f"(got {r['dominant_weakness']}). This regresses the Dallas-Digital "
            "dogfood fix — lean path-scoped rules must not be flagged as misscoped."
        )
        assert r["dominant_weakness"] == "F7"

    def test_explicit_f4_mismatch_still_dominates(self):
        """F4 with trigger_match != implicit_scope_trust remains eligible as dominant."""
        rule = _make_rule(factors={
            "F1": {"value": 1.0, "method": "lookup"},
            "F2": {"value": 1.0, "method": "classify"},
            # F4 0.25 = wrong_scope (explicit trigger mismatches glob)
            "F4": {"value": 0.25, "method": "wrong_scope", "loading": "glob-scoped",
                    "trigger_match": "explicit_mismatch"},
            "F7": {"value": 0.90, "method": "count"},
        })
        scored = _make_scored([rule])
        patches = _make_patches(_patches_for("R001", f3=1.0, f8=0.80))
        result = _run_compose(scored, patches)
        r = result["rules"][0]
        # F4 at 0.25 (wrong_scope) IS a real structural problem and must dominate.
        assert r["dominant_weakness"] == "F4"


class TestMalformedPatchSurvival:
    """Regression from Axo-folio dogfood (2026-04-17): if a malformed F{N}_patch
    reaches compose.py (e.g. from a manually-edited patches file that slipped
    past parse_judgment.py), compose must warn and skip instead of crashing."""

    def test_f7_patch_missing_value_survives(self):
        """F7_patch dict missing the 'value' key → warned and skipped, no crash."""
        rule = _make_rule()
        scored = _make_scored([rule])
        patches = _make_patches({
            "R001": {
                "F3": {"value": 0.80, "level": 3, "reasoning": "test"},
                "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
                "F7_patch": {"reasoning": "forgot value"},  # malformed — no 'value'
            }
        })
        proc = _run_compose_raw(scored, patches)
        assert proc.returncode == 0, f"compose.py crashed on malformed patch: {proc.stderr}"
        assert "malformed" in proc.stderr
        # F7 should retain its original mechanical value, not crash or go None.
        result = json.loads(proc.stdout)
        r = result["rules"][0]
        assert r["factors"]["F7"]["value"] == 0.80  # the _make_rule default

    def test_f7_patch_non_dict_survives(self):
        """F7_patch as a bare number (not a dict) → warned and skipped, no crash."""
        rule = _make_rule()
        scored = _make_scored([rule])
        patches = _make_patches({
            "R001": {
                "F3": {"value": 0.80, "level": 3, "reasoning": "test"},
                "F8": {"value": 0.65, "level": 2, "reasoning": "test"},
                "F7_patch": 0.60,  # malformed — should be a dict
            }
        })
        proc = _run_compose_raw(scored, patches)
        assert proc.returncode == 0, f"compose.py crashed on malformed patch: {proc.stderr}"
        assert "malformed" in proc.stderr
