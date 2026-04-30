"""Tests for placement.py — placement-analyzer detectors, compound logic,
and source-file surgery (deletion + atomicity).

Pins the v1 placement-analyzer spec that was folded into scripts/placement.py.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import placement  # noqa: E402
from placement import (  # noqa: E402
    SourceDriftError,
    _collect_judgment_warnings,
    _delete_with_blank_line_cleanup,
    _extract_existing_entry_keys,
    _strip_bullet_marker,
    analyze_corpus,
    assemble_promotions_doc,
    detect_placement,
    plan_deletions,
    write_promotions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rule(rule_id: str, text: str, f8: float | None = None, **extra) -> dict:
    factors = dict(extra.pop("factors", {}))
    if f8 is not None:
        factors["F8"] = {"value": f8, "level": 0}
    return {
        "id": rule_id,
        "text": text,
        "factors": factors,
        "file": extra.pop("file", "CLAUDE.md"),
        "line_start": extra.pop("line_start", 1),
        "line_end": extra.pop("line_end", 1),
        **extra,
    }


# ---------------------------------------------------------------------------
# Hook detector
# ---------------------------------------------------------------------------

class TestHookDetector:
    """Design §3.1 and §10.1 hook cases."""

    def test_git_commit_push_ban_is_hook(self):
        r = _rule("R1", "Never run `git commit` or `git push` for the user.", f8=0.15)
        d = detect_placement(r)
        assert d["best_fit"] == "hook"
        assert any(x["primitive"] == "hook" for x in d["detections"])
        hook = next(x for x in d["detections"] if x["primitive"] == "hook")
        assert hook["confidence"] >= 0.80
        assert "f8-low" in hook["evidence"]
        assert "tool-invocation-match" in hook["evidence"]
        assert "mechanical-verb" in hook["evidence"]

    def test_validate_before_push_is_hook(self):
        r = _rule("R2", "Before pushing, run npm run validate from the repo root.", f8=0.25)
        d = detect_placement(r)
        assert d["best_fit"] == "hook"
        hook = next(x for x in d["detections"] if x["primitive"] == "hook")
        assert "lifecycle-trigger-keyword" in hook["evidence"]

    def test_force_push_ban_is_hook(self):
        r = _rule("R10", "Never force-push to main.", f8=0.18)
        d = detect_placement(r)
        assert d["best_fit"] == "hook"

    def test_functional_components_rule_is_not_hook(self):
        """A rule-shaped directive about React patterns is not a hook candidate."""
        r = _rule("R8", "Use functional components for all new React files.", f8=0.85)
        d = detect_placement(r)
        assert d["best_fit"] is None
        assert d["detections"] == []

    def test_hook_sub_type_deterministic_gate(self):
        r = _rule("R1", "Never run `git commit` or `git push`.", f8=0.15)
        d = detect_placement(r)
        hook = next(x for x in d["detections"] if x["primitive"] == "hook")
        assert hook["sub_type"] == "deterministic-gate"

    def test_hook_sub_type_lifecycle_event(self):
        r = _rule("R2", "Before pushing, run npm run validate.", f8=0.25)
        d = detect_placement(r)
        hook = next(x for x in d["detections"] if x["primitive"] == "hook")
        assert hook["sub_type"] == "lifecycle-event"


# ---------------------------------------------------------------------------
# Skill detector
# ---------------------------------------------------------------------------

class TestSkillDetector:
    """Design §3.2 and §10.1 skill cases."""

    def test_style_guide_reference_is_skill(self):
        r = _rule("R3", "When styling v2 components, follow the style guide at dll-components-v2/docs/dll-styleguide-tokens.md.")
        d = detect_placement(r)
        assert d["best_fit"] == "skill"
        skill = next(x for x in d["detections"] if x["primitive"] == "skill")
        assert "reference-pointer-phrase" in skill["evidence"]
        assert skill["sub_type"] == "reference"

    def test_deploy_workflow_is_action_skill(self):
        r = _rule("R4", "When deploying, first run npm run build, then run npm test, then npm run deploy:prod, then notify slack.")
        d = detect_placement(r)
        assert d["best_fit"] == "skill"
        skill = next(x for x in d["detections"] if x["primitive"] == "skill")
        assert "named-procedure-trigger" in skill["evidence"]
        assert "workflow-step-chain" in skill["evidence"]
        assert skill["sub_type"] == "action"

    def test_real_rule_mentioning_md_stays_non_candidate(self):
        """A directive that mentions CLAUDE.md in its body is still a rule,
        not a skill pointer. Pointer-shape gate prevents the false positive."""
        r = _rule("R12", "When adding a new scoped rule file, update CLAUDE.md to include a pointer to it.", f8=0.85)
        d = detect_placement(r)
        assert d["best_fit"] is None

    def test_two_step_conjunction_not_skill(self):
        """Only two sequenced actions — below the 3-step minimum — must not
        trigger the workflow-step-chain signal."""
        r = _rule("R11", "Use functional components and prefer hooks over class components.", f8=0.80)
        d = detect_placement(r)
        assert d["best_fit"] is None


# ---------------------------------------------------------------------------
# Subagent detector
# ---------------------------------------------------------------------------

class TestSubagentDetector:
    """Design §3.3 and §10.1 subagent cases."""

    def test_read_external_tree_is_subagent(self):
        r = _rule(
            "R5",
            "When investigating code that imports from dll/components, read the source at D:/Projects/Work/DLL/Dallas-Digital before making assumptions.",
        )
        d = detect_placement(r)
        assert d["best_fit"] == "subagent"
        sub = next(x for x in d["detections"] if x["primitive"] == "subagent")
        assert "read-large-tree" in sub["evidence"]

    def test_read_external_tree_windows_backslash_path(self):
        r = _rule(
            "R5b",
            r"When investigating code that imports from dll/components, read the source at D:\Projects\Work\DLL\Dallas-Digital before making assumptions.",
        )
        d = detect_placement(r)
        assert d["best_fit"] == "subagent"

    def test_audit_diff_is_subagent(self):
        r = _rule("R6", "Audit the diff for coverage gaps, return a list of new behaviors not exercised by assertions.")
        d = detect_placement(r)
        assert d["best_fit"] == "subagent"
        sub = next(x for x in d["detections"] if x["primitive"] == "subagent")
        assert "audit-verb" in sub["evidence"]

    def test_naming_rule_is_not_subagent(self):
        r = _rule("R9", "Name boolean variables as questions (isReady, hasAccess, shouldRetry).", f8=0.80)
        d = detect_placement(r)
        assert d["best_fit"] is None


# ---------------------------------------------------------------------------
# Compound detection
# ---------------------------------------------------------------------------

class TestCompoundDetection:
    """Design §3.4."""

    def test_commit_plus_coverage_is_compound_with_glue(self):
        """The canonical compound from the design doc — hook half + subagent half
        joined by 'and make sure' (coordination language triggers glue)."""
        r = _rule(
            "R7",
            "Never commit without running tests, and make sure the test suite covers the change.",
            f8=0.20,
        )
        d = detect_placement(r)
        assert d["compound"] is True
        assert d["best_fit"] == "compound"
        assert d["compound_needs_glue"] is True
        # Both hook and subagent scored above compound_threshold (0.35) even though
        # subagent didn't cross the candidate_threshold (0.60) alone.
        assert d["scores"]["hook"] >= 0.35
        assert d["scores"]["subagent"] >= 0.35

    def test_two_rule_conjunction_without_primitive_split_is_not_compound(self):
        """A rule with two conjoined halves that are both rule-shaped is not compound."""
        r = _rule("R11", "Use functional components and prefer hooks over class components.", f8=0.80)
        d = detect_placement(r)
        assert d["compound"] is False

    def test_compound_without_coordination_does_not_flag_glue(self):
        """A compound where the parts do not need temporal coordination
        (per §12.4) should not flag needs_glue."""
        # Note: crafting a genuine non-coordination compound is hard because
        # most real compounds are implicitly coordinated. This asserts the
        # behavior of the pattern list, which is the contract: only explicit
        # coordination phrases set the glue flag.
        r = _rule(
            "R13",
            "Never run git commit; review the diff for coverage gaps when you are done.",
            f8=0.20,
        )
        d = detect_placement(r)
        # Regardless of whether compound fires, glue should NOT fire because
        # no coordination phrase matches (no 'and make sure', no 'before X and Y').
        if d["compound"]:
            assert d["compound_needs_glue"] is False


# ---------------------------------------------------------------------------
# Corpus analysis
# ---------------------------------------------------------------------------

class TestAnalyzeCorpus:
    def test_empty_corpus(self):
        audit = {"rules": [], "effective_corpus_quality": {"score": 0.5}}
        result = analyze_corpus(audit)
        assert result["candidates"] == []
        assert result["summary"]["total_candidates"] == 0

    def test_mixed_corpus_summary_counts(self):
        audit = {
            "rules": [
                _rule("R1", "Never run git commit or git push.", f8=0.15),
                _rule("R2", "Use functional components.", f8=0.85),
                _rule("R3", "When deploying, first build, then test, then ship, then notify."),
                _rule("R4", "Audit the diff and return a list of gaps."),
            ],
            "effective_corpus_quality": {"score": 0.5},
        }
        result = analyze_corpus(audit)
        assert result["summary"]["hook_candidates"] == 1
        assert result["summary"]["skill_candidates"] == 1
        assert result["summary"]["subagent_candidates"] == 1
        # R2 is not a candidate — total should be 3, not 4.
        assert result["summary"]["total_candidates"] == 3

    def test_audit_grade_formatting(self):
        audit = {"rules": [], "effective_corpus_quality": {"score": 0.593}}
        result = analyze_corpus(audit)
        assert result["audit_grade"] == "C (0.593)"


# ---------------------------------------------------------------------------
# Source-file surgery
# ---------------------------------------------------------------------------

class TestSourceDeletion:
    """Design §6 — atomic source-file surgery."""

    def test_single_bullet_deletion(self, tmp_path):
        src = tmp_path / "CLAUDE.md"
        src.write_text(
            "# Rules\n"
            "\n"
            "- Rule one.\n"
            "- Rule two — this one gets removed.\n"
            "- Rule three.\n",
            encoding="utf-8",
        )
        move = {
            "file": "CLAUDE.md",
            "line_start": 4,
            "line_end": 4,
            "rule_text": "Rule two — this one gets removed.",
        }
        contents = plan_deletions([move], tmp_path)
        new_content = contents[src.resolve()]
        assert "Rule two" not in new_content
        assert "Rule one." in new_content
        assert "Rule three." in new_content

    def test_blank_line_cleanup(self, tmp_path):
        src = tmp_path / "CLAUDE.md"
        src.write_text(
            "- A\n"
            "\n"
            "- B (removed)\n"
            "\n"
            "- C\n",
            encoding="utf-8",
        )
        move = {"file": "CLAUDE.md", "line_start": 3, "line_end": 3, "rule_text": "B (removed)"}
        contents = plan_deletions([move], tmp_path)
        new = contents[src.resolve()]
        # Should not have two consecutive blank lines left.
        assert "\n\n\n" not in new

    def test_source_drift_raises(self, tmp_path):
        """If the file content at line_start..line_end doesn't match rule_text,
        deletion aborts with a clear error."""
        src = tmp_path / "CLAUDE.md"
        src.write_text("- Something completely different.\n", encoding="utf-8")
        move = {
            "file": "CLAUDE.md",
            "line_start": 1,
            "line_end": 1,
            "rule_text": "The rule we think is there.",
        }
        with pytest.raises(SourceDriftError):
            plan_deletions([move], tmp_path)

    def test_multiple_moves_in_same_file_deleted_in_reverse_order(self, tmp_path):
        """Deleting by descending line_start ensures earlier deletions don't
        shift later line numbers."""
        src = tmp_path / "CLAUDE.md"
        src.write_text(
            "- Rule 1\n"
            "- Rule 2\n"
            "- Rule 3\n"
            "- Rule 4\n",
            encoding="utf-8",
        )
        moves = [
            {"file": "CLAUDE.md", "line_start": 1, "line_end": 1, "rule_text": "Rule 1"},
            {"file": "CLAUDE.md", "line_start": 3, "line_end": 3, "rule_text": "Rule 3"},
        ]
        contents = plan_deletions(moves, tmp_path)
        new = contents[src.resolve()]
        assert "Rule 1" not in new
        assert "Rule 3" not in new
        assert "Rule 2" in new
        assert "Rule 4" in new

    def test_blank_line_helper_removes_stacked_blanks(self):
        lines = ["before\n", "\n", "removed\n", "\n", "after\n"]
        result = _delete_with_blank_line_cleanup(lines, 2, 3)
        assert result == ["before\n", "\n", "after\n"]

    def test_blank_line_helper_single_blank_preserved(self):
        lines = ["before\n", "removed\n", "\n", "after\n"]
        result = _delete_with_blank_line_cleanup(lines, 1, 2)
        assert result == ["before\n", "\n", "after\n"]


# ---------------------------------------------------------------------------
# write_promotions (end-to-end atomic write)
# ---------------------------------------------------------------------------

class TestWritePromotions:
    """Design §6.2 — all-or-nothing transactions."""

    def test_creates_promotions_file_and_removes_rule(self, tmp_path):
        src = tmp_path / "CLAUDE.md"
        src.write_text(
            "# Guide\n"
            "\n"
            "- Never run git commit or git push.\n"
            "- Use functional components.\n",
            encoding="utf-8",
        )
        payload = {
            "schema_version": "0.1",
            "project": "test-project",
            "audit_grade": "C (0.500)",
            "generated_at": "2026-04-17T12:00:00Z",
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
                        "why": "Mechanically detectable tool-invocation pattern.",
                        "suggested_shape": "PreToolUse on Bash matching ^git (commit|push)",
                        "next_step": "Add to .claude/settings.json",
                        "tradeoff": None,
                    },
                }
            ],
        }
        result = write_promotions(payload, tmp_path)
        assert result["status"] == "ok"
        assert result["rules_removed"] == 1
        # PROMOTIONS.md exists with our entry
        promo = tmp_path / ".rulesense" / "PROMOTIONS.md"
        assert promo.exists()
        promo_content = promo.read_text(encoding="utf-8")
        assert "Hooks" in promo_content
        assert "Never run git commit" in promo_content
        assert "Mechanically detectable" in promo_content
        # Source file had the rule removed
        src_content = src.read_text(encoding="utf-8")
        assert "Never run git commit" not in src_content
        assert "Use functional components" in src_content

    def test_atomicity_on_drift(self, tmp_path):
        """If any source file drifts, nothing is written — the promotions doc
        is not created and source files are not modified."""
        src = tmp_path / "CLAUDE.md"
        src.write_text("- A different rule than we expected.\n", encoding="utf-8")
        payload = {
            "schema_version": "0.1",
            "project": "test",
            "audit_grade": "C (0.5)",
            "moves": [
                {
                    "rule_id": "R1",
                    "primitive": "hook",
                    "rule_text": "The rule we think is there.",
                    "file": "CLAUDE.md",
                    "line_start": 1,
                    "line_end": 1,
                    "judgment": {"why": "test", "suggested_shape": "", "next_step": ""},
                }
            ],
        }
        result = write_promotions(payload, tmp_path)
        assert result["status"] == "failed"
        assert "drift" in result["reason"]
        # Neither the promotions file nor any source file was modified
        assert not (tmp_path / ".rulesense" / "PROMOTIONS.md").exists()
        assert src.read_text(encoding="utf-8") == "- A different rule than we expected.\n"

    def test_empty_moves_noop(self, tmp_path):
        payload = {"schema_version": "0.1", "moves": []}
        result = write_promotions(payload, tmp_path)
        assert result["status"] == "ok"
        assert result["rules_removed"] == 0
        # No .rulesense/ directory should be created on empty input.
        assert not (tmp_path / ".rulesense").exists()


class TestAssemblePromotionsDoc:
    """The markdown doc structure (design §5)."""

    def test_banner_includes_generation_metadata(self):
        doc = assemble_promotions_doc(
            moves_by_primitive={"hook": [{
                "rule_id": "R1", "rule_text": "Never run git commit.",
                "file": "CLAUDE.md", "line_start": 5,
                "judgment": {"why": "x", "suggested_shape": "y", "next_step": "z", "tradeoff": None},
            }]},
            project="demo",
            audit_grade="C (0.500)",
            generated_at="2026-04-17T12:00:00Z",
        )
        assert "# Rulesense promotion candidates" in doc
        assert "demo" in doc
        assert "C (0.500)" in doc
        assert "2026-04-17T12:00:00Z" in doc

    def test_empty_sections_omitted(self):
        """Sections with no entries should not render."""
        doc = assemble_promotions_doc(
            moves_by_primitive={"hook": [{
                "rule_id": "R1", "rule_text": "t", "file": "f", "line_start": 1,
                "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n", "tradeoff": None},
            }]},
            project="p", audit_grade="C", generated_at="t",
        )
        assert "## Hooks" in doc
        assert "## Skills" not in doc
        assert "## Subagents" not in doc
        assert "## Compound" not in doc

    def test_all_docs_links_present_per_section(self):
        doc = assemble_promotions_doc(
            moves_by_primitive={
                "hook": [{"rule_id": "R1", "rule_text": "t", "file": "f", "line_start": 1,
                          "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n", "tradeoff": None}}],
                "skill": [{"rule_id": "R2", "rule_text": "t", "file": "f", "line_start": 2,
                           "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n", "tradeoff": None}}],
                "subagent": [{"rule_id": "R3", "rule_text": "t", "file": "f", "line_start": 3,
                              "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n", "tradeoff": None}}],
            },
            project="p", audit_grade="C", generated_at="t",
        )
        # Each section has "Learn more" with at least one official-docs link.
        for keyword in ["features-overview#hooks", "features-overview#skills",
                         "features-overview#subagents"]:
            assert keyword in doc, f"Missing docs link containing {keyword}"

    def test_compound_entry_renders_both_parts(self):
        doc = assemble_promotions_doc(
            moves_by_primitive={"compound": [{
                "rule_id": "R7",
                "rule_text": "Never commit without tests, and make sure the suite covers the change.",
                "file": "CLAUDE.md", "line_start": 23,
                "compound": {
                    "split_hint": "the comma before 'and make sure'",
                    "part_a": {
                        "primitive": "hook", "text": "Never commit without tests",
                        "suggested_shape": "PreToolUse on Bash",
                        "next_step": "add to settings.json",
                        "tradeoff": None,
                    },
                    "part_b": {
                        "primitive": "subagent", "text": "make sure the suite covers the change",
                        "suggested_shape": "coverage-auditor subagent",
                        "next_step": "scaffold agent file",
                        "tradeoff": None,
                    },
                    "glue": {
                        "primitive": "skill", "text": "commit-discipline",
                        "suggested_shape": "skill invoked while preparing commit",
                        "next_step": "optional",
                        "tradeoff": None,
                    },
                },
            }]},
            project="p", audit_grade="C", generated_at="t",
        )
        assert "Part A" in doc
        assert "Part B" in doc
        assert "Optional glue" in doc
        assert "PreToolUse on Bash" in doc
        assert "coverage-auditor subagent" in doc

    def test_append_to_existing_doc_preserves_content(self):
        existing = "# Rulesense promotion candidates\n\n> Original content the user may have edited.\n\n## Hooks\n\n### `CLAUDE.md:5` — \"Old entry text\"\n- Why: old\n"
        new_doc = assemble_promotions_doc(
            moves_by_primitive={"hook": [{
                "rule_id": "R2", "rule_text": "New entry text",
                "file": "CLAUDE.md", "line_start": 10,
                "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n", "tradeoff": None},
            }]},
            project="p", audit_grade="C", generated_at="2026-04-17T13:00:00Z",
            existing_content=existing,
        )
        # Existing content preserved verbatim
        assert "Original content the user may have edited." in new_doc
        assert "Old entry text" in new_doc
        # New append block visible
        assert "## Appended 2026-04-17T13:00:00Z" in new_doc
        assert "New entry text" in new_doc

    def test_append_dedupes_by_file_and_text_prefix(self):
        """If the same (file, text) pair is already in the doc, skip on append."""
        existing = '### `CLAUDE.md:5` — "Existing rule text that repeats"\n'
        new_doc = assemble_promotions_doc(
            moves_by_primitive={"hook": [{
                "rule_id": "R99",
                "rule_text": "Existing rule text that repeats",
                "file": "CLAUDE.md", "line_start": 5,
                "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n", "tradeoff": None},
            }]},
            project="p", audit_grade="C", generated_at="t",
            existing_content=existing,
        )
        # The dedupe should drop the re-add; the append section doesn't need a Hooks subsection.
        assert new_doc.count("Existing rule text that repeats") == 1


# ---------------------------------------------------------------------------
# Dallas-Digital dogfood regressions (2026-04-18)
# ---------------------------------------------------------------------------

class TestAgentInvocationSignal:
    """The Dallas dogfood surfaced a clean subagent candidate that scored 0
    on all detectors: 'Run the v2-migration-auditor agent after migrating
    a component.' The new agent-invocation-phrase signal closes the gap."""

    def test_run_named_agent_classifies_as_subagent(self):
        r = _rule("R1", "Run the v2-migration-auditor agent after migrating a component.")
        d = detect_placement(r)
        assert d["best_fit"] == "subagent"
        sub = next(x for x in d["detections"] if x["primitive"] == "subagent")
        assert "agent-invocation-phrase" in sub["evidence"]
        assert sub["sub_type"] == "named-agent"

    def test_delegate_to_named_subagent(self):
        r = _rule("R2", "After implementing the feature, delegate to the coverage-auditor subagent.")
        d = detect_placement(r)
        assert d["best_fit"] == "subagent"

    def test_invoke_release_agent(self):
        r = _rule("R3", "When preparing a release, invoke the release-checker agent before tagging.")
        d = detect_placement(r)
        assert d["best_fit"] == "subagent"

    def test_run_npm_is_not_agent_invocation(self):
        """Negative control: 'run npm test' must not trigger agent-invocation."""
        r = _rule("R4", "Run npm test before pushing.", f8=0.20)
        d = detect_placement(r)
        for det in d["detections"]:
            assert "agent-invocation-phrase" not in det.get("evidence", [])

    def test_call_a_function_is_not_agent_invocation(self):
        """Negative control: 'call the X function' must not trigger."""
        r = _rule("R5", "Call the getUserById function to retrieve the user.")
        d = detect_placement(r)
        assert d["best_fit"] is None

    def test_backticked_agent_name_still_fires(self):
        """Second Dallas dogfood regression: users routinely wrap agent names
        in markdown code spans (backticks). The initial regex required the
        first name character to be a word character, so `v2-migration-auditor`
        (with backticks) didn't fire. The pattern now tolerates optional
        backticks around the name."""
        r = _rule(
            "R51",
            "Run the `v2-migration-auditor` agent after migrating a component.",
        )
        d = detect_placement(r)
        assert d["best_fit"] == "subagent"
        sub = next(x for x in d["detections"] if x["primitive"] == "subagent")
        assert "agent-invocation-phrase" in sub["evidence"]
        assert sub["sub_type"] == "named-agent"

    def test_backticked_subagent_name_fires(self):
        r = _rule("R52", "Delegate to the `coverage-auditor` subagent before commit.")
        d = detect_placement(r)
        assert d["best_fit"] == "subagent"

    def test_backticked_non_agent_token_does_not_fire(self):
        r"""Negative: "Run the `validate` script before pushing" backticks a
        script name, not an agent. Must not trigger agent-invocation —
        'script' isn't in the (agent|subagent) alternation."""
        r = _rule(
            "R53",
            "Run the `validate` script before pushing.",
            f8=0.25,
        )
        d = detect_placement(r)
        for det in d["detections"]:
            assert "agent-invocation-phrase" not in det.get("evidence", [])


class TestEntryRenderingFullRuleText:
    """Dallas dogfood feedback: PROMOTIONS.md entries used to truncate rule
    text at 120 chars with an ellipsis. Because the rule is deleted from
    source on move, the truncation made the doc unusable — the full rule
    only existed in git history. The entry now keeps a compact header
    (file:line) and puts the full rule text in a blockquote below."""

    def test_header_is_compact_file_line_only(self):
        doc = assemble_promotions_doc(
            moves_by_primitive={"hook": [{
                "rule_id": "R1",
                "rule_text": "- When X happens, do Y because Z (rest of a long rule that used to be truncated).",
                "file": "CLAUDE.md", "line_start": 42,
                "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n", "tradeoff": None},
            }]},
            project="p", audit_grade="C (0.5)", generated_at="t",
        )
        # Header is just file:line with no embedded rule text or em-dash.
        assert "### `CLAUDE.md:42`\n" in doc
        assert "### `CLAUDE.md:42` —" not in doc

    def test_full_rule_text_in_blockquote(self):
        long_text = (
            "- Before pushing a branch, run `npm run validate` from the relevant package "
            "directory (`dll-components-v2/` or `dll-components/`), because `validate` runs "
            "the same typecheck -> lint -> test -> build -> size-limit gauntlet the CI "
            "pipeline will, catching failures locally in seconds instead of waiting on CI."
        )
        doc = assemble_promotions_doc(
            moves_by_primitive={"hook": [{
                "rule_id": "R19",
                "rule_text": long_text,
                "file": ".claude/rules/git.md", "line_start": 20,
                "judgment": {
                    "why": "pre-push gate is mechanically checkable",
                    "suggested_shape": "local git pre-push hook",
                    "next_step": "add to .git/hooks/pre-push",
                    "tradeoff": None,
                },
            }]},
            project="p", audit_grade="C (0.5)", generated_at="t",
        )
        # Full rule text lands in a blockquote — no truncation ellipsis.
        assert "…" not in doc  # Unicode ellipsis used by legacy _truncate
        assert "..." not in doc.split("**Why")[0]  # ASCII ellipsis also absent
        # The full-length rule text is present unchanged except for bullet stripping.
        assert "size-limit gauntlet" in doc
        assert "> Before pushing a branch" in doc

    def test_bullet_marker_stripped_from_blockquote(self):
        doc = assemble_promotions_doc(
            moves_by_primitive={"hook": [{
                "rule_id": "R1",
                "rule_text": "- The leading dash-space is a markdown list marker from the source.",
                "file": "CLAUDE.md", "line_start": 1,
                "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n", "tradeoff": None},
            }]},
            project="p", audit_grade="C", generated_at="t",
        )
        # The blockquote line starts with "> " then the directive, NOT "> - ".
        assert "> The leading dash-space" in doc
        assert "> - The leading" not in doc

    def test_numbered_list_marker_also_stripped(self):
        doc = assemble_promotions_doc(
            moves_by_primitive={"hook": [{
                "rule_id": "R1",
                "rule_text": "1. First directive that used a numbered-list marker in source.",
                "file": "CLAUDE.md", "line_start": 1,
                "judgment": {"why": "w", "suggested_shape": "s", "next_step": "n", "tradeoff": None},
            }]},
            project="p", audit_grade="C", generated_at="t",
        )
        assert "> First directive" in doc
        assert "> 1. First" not in doc


class TestStripBulletMarker:
    """Unit tests for the bullet-marker strip helper."""

    def test_strips_dash(self):
        assert _strip_bullet_marker("- rule text") == "rule text"

    def test_strips_asterisk(self):
        assert _strip_bullet_marker("* rule text") == "rule text"

    def test_strips_plus(self):
        assert _strip_bullet_marker("+ rule text") == "rule text"

    def test_strips_numbered(self):
        assert _strip_bullet_marker("1. rule text") == "rule text"
        assert _strip_bullet_marker("42. rule text") == "rule text"

    def test_preserves_text_without_marker(self):
        assert _strip_bullet_marker("rule text") == "rule text"

    def test_strips_leading_whitespace_before_marker(self):
        assert _strip_bullet_marker("  - indented rule") == "indented rule"

    def test_only_strips_first_marker(self):
        assert _strip_bullet_marker("- outer - inner") == "outer - inner"


class TestMissingJudgmentWarnings:
    """Dallas dogfood produced a PROMOTIONS.md with header-only entries
    because the moves payload was missing the `judgment` field. write_promotions
    now warns when required judgment fields are missing."""

    def test_missing_all_judgment_fields_produces_warning(self):
        moves = [{
            "rule_id": "R1",
            "primitive": "hook",
            "rule_text": "Rule text.",
            "file": "CLAUDE.md", "line_start": 1, "line_end": 1,
            # No judgment key at all
        }]
        warnings = _collect_judgment_warnings(moves)
        assert len(warnings) == 1
        assert "R1" in warnings[0]
        assert "why" in warnings[0]
        assert "header-only" in warnings[0]

    def test_partial_judgment_produces_warning_naming_missing_fields(self):
        moves = [{
            "rule_id": "R2",
            "primitive": "hook",
            "rule_text": "Rule text.",
            "file": "CLAUDE.md", "line_start": 1, "line_end": 1,
            "judgment": {"why": "a reason", "suggested_shape": "a shape"},
            # missing: next_step
        }]
        warnings = _collect_judgment_warnings(moves)
        assert len(warnings) == 1
        assert "next_step" in warnings[0]
        assert "why" not in warnings[0]
        assert "suggested_shape" not in warnings[0]

    def test_complete_judgment_produces_no_warning(self):
        moves = [{
            "rule_id": "R3",
            "primitive": "hook",
            "rule_text": "Rule text.",
            "file": "CLAUDE.md", "line_start": 1, "line_end": 1,
            "judgment": {
                "why": "a reason",
                "suggested_shape": "a shape",
                "next_step": "a step",
                "tradeoff": None,
            },
        }]
        assert _collect_judgment_warnings(moves) == []

    def test_compound_move_missing_parts_produces_warning(self):
        moves = [{
            "rule_id": "R4",
            "primitive": "compound",
            "rule_text": "Rule text.",
            "file": "CLAUDE.md", "line_start": 1, "line_end": 1,
            "compound": {"split_hint": "somewhere", "part_a": None, "part_b": None},
        }]
        warnings = _collect_judgment_warnings(moves)
        assert len(warnings) == 1
        assert "compound" in warnings[0]

    def test_write_promotions_surfaces_warnings_in_output_json(self, tmp_path):
        src = tmp_path / "CLAUDE.md"
        src.write_text("- A rule we want to move.\n", encoding="utf-8")
        payload = {
            "schema_version": "0.1",
            "project": "t",
            "audit_grade": "C",
            "moves": [{
                "rule_id": "R1", "primitive": "hook",
                "rule_text": "A rule we want to move.",
                "file": "CLAUDE.md", "line_start": 1, "line_end": 1,
                # No judgment — should warn but not fail
            }],
        }
        result = write_promotions(payload, tmp_path)
        assert result["status"] == "ok"
        assert "warnings" in result
        assert any("R1" in w for w in result["warnings"])


class TestLegacyEntryDedupe:
    """_extract_existing_entry_keys must handle both the current entry shape
    (file:line header + blockquote below) and the legacy shape (file:line
    with text quoted on the same line after an em-dash). Otherwise an audit
    run against a PROMOTIONS.md produced by an earlier version would duplicate
    every entry on re-run."""

    def test_parses_new_format(self):
        content = (
            "### `CLAUDE.md:42`\n"
            "\n"
            "> The new-format rule text lives in a blockquote.\n"
            "\n"
            "- **Why**: something\n"
        )
        keys = _extract_existing_entry_keys(content)
        assert len(keys) == 1
        (file_path, text_prefix), = keys
        assert file_path == "CLAUDE.md"
        assert "new-format rule text" in text_prefix

    def test_parses_legacy_format(self):
        content = (
            '### `.claude/rules/git.md:20` — "- The legacy entry quoted on the same line"\n'
            "- **Why**: something\n"
        )
        keys = _extract_existing_entry_keys(content)
        assert len(keys) == 1
        (file_path, text_prefix), = keys
        assert file_path == ".claude/rules/git.md"
        # Bullet marker stripped during normalization.
        assert text_prefix.startswith("The legacy entry")

    def test_mixed_file_still_dedupes_both(self):
        content = (
            "### `a.md:1`\n\n> new entry\n\n"
            '### `b.md:2` — "- legacy entry"\n'
        )
        keys = _extract_existing_entry_keys(content)
        assert len(keys) == 2
        file_paths = {k[0] for k in keys}
        assert file_paths == {"a.md", "b.md"}


# ---------------------------------------------------------------------------
# CLI entry point smoke test
# ---------------------------------------------------------------------------

class TestCLI:
    def test_prepare_placement_cli(self, tmp_path):
        """Invoke placement.py --prepare-placement via subprocess to ensure the
        CLI wiring works end-to-end."""
        import subprocess
        audit = {
            "project": "p",
            "effective_corpus_quality": {"score": 0.5},
            "rules": [
                _rule("R1", "Never run git commit.", f8=0.15),
                _rule("R2", "Use functional components.", f8=0.85),
            ],
        }
        audit_path = tmp_path / "audit.json"
        audit_path.write_text(json.dumps(audit), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "placement.py"),
             "--prepare-placement", str(audit_path)],
            capture_output=True, text=True, timeout=30, encoding="utf-8",
        )
        assert result.returncode == 0, result.stderr
        out = json.loads(result.stdout)
        assert out["summary"]["hook_candidates"] == 1
        assert out["summary"]["total_candidates"] == 1


# ---------------------------------------------------------------------------
# Phase 3d Step 3 interaction shape (SKILL.md text sanity checks)
# ---------------------------------------------------------------------------

class TestPhase3dInteractionShape:
    """Pin the single-question per-category multiSelect pattern in the audit SKILL.

    Phase 3c Step 4 (formerly Phase 3d Step 3) consolidates per-category
    placement decisions into ONE `AskUserQuestion` call with one option
    per non-empty placement category. The category count never exceeds 4
    (hook / skill / subagent / compound), so every non-empty category
    fits inside `AskUserQuestion`'s 4-option cap without any per-category
    loop. Each option is shaped `"Move all [N] <category> (recommended)"`
    with `multiSelect: true`; an unchecked category leaves those rules
    as-is.

    Earlier shapes — "batches of 3 candidates" and the binary
    Move-all / Keep-all pattern — are both prohibited:
      - "batches of 3" hits the 4-option cap on big categories.
      - The binary per-category pattern produces N sequential questions
        (one per category) instead of one combined decision, which
        dogfood runs found tedious.

    These assertions guard against a regression to either earlier shape.
    """

    SKILL_PATH = (
        Path(__file__).parent.parent / "skills" / "assay" / "SKILL.md"
    )

    @pytest.fixture
    def skill_text(self) -> str:
        return self.SKILL_PATH.read_text(encoding="utf-8")

    def test_old_batching_language_is_gone(self, skill_text):
        """The former 'batches of 3 candidates' instruction must be absent.

        If this assertion fails, someone partially reverted to the
        pre-consolidation 'batches of 3 candidates' approach, which hits
        AskUserQuestion's 4-option cap when a category has more than 3
        candidates.
        """
        assert "batches of 3" not in skill_text, (
            "Phase 3c Step 4 appears to have been reverted to the "
            "pre-consolidation 'batches of 3 candidates' approach, "
            "which hits AskUserQuestion's 4-option cap. Use the single "
            "per-category multiSelect pattern instead."
        )

    def test_per_category_options_are_documented(self, skill_text):
        """All four per-category move options must be present in Phase 3c Step 4."""
        for category in ("hooks", "skills", "subagents", "compound"):
            needle = f"Move all [N] {category}"
            assert needle in skill_text, (
                f"Phase 3c Step 4 is missing the '{needle}' option. "
                "Each non-empty placement category must surface as one "
                "option in the consolidated multiSelect question."
            )

    def test_step4_question_uses_multiselect_true(self, skill_text):
        """The per-category question must specify `multiSelect: true` explicitly.

        Phase 3c has two AskUserQuestion interactions: the Step 3 fix
        menu (multiSelect: true across change classes) and the Step 4
        per-category placement question (multiSelect: true across
        non-empty placement categories). Pinning the literal string
        guards against accidental flips to `false`, which would force
        N sequential questions (one per category).
        """
        assert "header: \"Move which?\"" in skill_text, (
            "Phase 3c Step 4 must include the literal `header: \"Move "
            "which?\"` question shape — the consolidated per-category "
            "AskUserQuestion call."
        )
        # Locate the Step 4 question block and assert multiSelect: true
        # appears within it.
        marker = "header: \"Move which?\""
        idx = skill_text.find(marker)
        window = skill_text[idx : idx + 400]
        assert "multiSelect: true" in window, (
            "Phase 3c Step 4's `Move which?` question must specify "
            "`multiSelect: true`. Using `false` would force one question "
            "per category, which dogfood runs found tedious."
        )

    def test_no_binary_keep_all_pattern(self, skill_text):
        """The earlier binary Move-all / Keep-all pattern must not return.

        That pattern produced one sequential question per non-empty
        category. The current shape is one combined multiSelect; an
        unchecked category in that single question is the equivalent
        of 'keep as rules'.
        """
        assert "Keep all as rules" not in skill_text, (
            "Phase 3c Step 4 contains the deprecated 'Keep all as "
            "rules' option. The current shape uses a single combined "
            "multiSelect — unchecked categories are kept as-is "
            "implicitly."
        )

    @pytest.mark.skip(
        reason="Design-doc drift guard is obsolete: the design/ directory "
        "was removed during the pre-release cleanup pass. The SKILL-side "
        "invariants (binary options, multiSelect: false, preview cap) are "
        "still pinned by the sibling tests in this class."
    )
    def test_design_doc_step3_stays_in_sync(self):
        """Obsolete after design/ directory removal — see skip reason."""
