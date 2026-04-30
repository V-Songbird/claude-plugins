# Phase 3 Step 2 — Scoring mechanics

Full script invocations, JSON shapes, and the rubric quick-reference for mechanical + judgment scoring of draft rules. Load when executing Phase 3 Step 2.

The control-flow outline lives in `SKILL.md`. This file carries the templates and command payloads.

## Variable setup

Set these at the top of the scoring step if not already set:

```bash
SCRIPTS="${CLAUDE_PLUGIN_ROOT}/scripts"
PYTHON_CMD="python3"  # or "python"
export PYTHONIOENCODING=utf-8
```

## Draft rules payload

Write the draft rules to `.rulesense-tmp/draft_rules.json` via the `Write` tool:

```json
{
  "rules": [
    {"id": "XX01", "text": "Rule text here"},
    {"id": "XX02", "text": "Another rule text"}
  ],
  "file": ".claude/rules/<target-filename>.md",
  "category": "mandate"
}
```

## Mechanical scoring

Invoke `Bash` with `description: "Score draft rules mechanically"`:

```bash
$PYTHON_CMD "$SCRIPTS/run_audit.py" --score-draft .rulesense-tmp/draft_rules.json
```

The output JSON now carries a `status` field. Branch on it:

**`status: "ok"`** — the mechanical scores are present:

```json
{
  "status": "ok",
  "rules": [ {"id": "T01", "text": "...", "factors": { "F1": {...}, ... }, "needs_judgment": true}, ... ],
  "judgment_prompt": ".rulesense-tmp/draft_prompt.md"
}
```

Proceed to the judgment scoring section below.

**`status: "needs_revision"`** — one or more drafts would fragment under `extract.py` when written to markdown and re-audited. The shape is:

```json
{
  "status": "needs_revision",
  "fragmenting_rules": [
    {"id": "T03", "text": "...", "fragment_count": 2,
     "fragments_preview": ["first clause...", "second clause..."],
     "reason": "Rule contains a splitter pattern..."}
  ]
}
```

Do NOT surface this to the user as a scoring failure — this is an internal guardrail, not a quality judgment. Revise each flagged rule per the "Extractor self-check" section in [`writing-principles.md`](writing-principles.md) (swap `, and` for `or`, drop `;`, collapse to one directive), overwrite `.rulesense-tmp/draft_rules.json` with the revised texts, and re-invoke `--score-draft`. Repeat until `status == "ok"`. Cap the revision loop at 3 passes; if a rule still fragments after 3 passes, collapse it to its single most important directive before re-scoring.

## Judgment scoring (F3 and F8)

Read the judgment prompt, then score F3 and F8 for each rule. The canonical rubrics live in [`../../assay/references/factor-rubrics.md`](../../assay/references/factor-rubrics.md) — read those for the full level criteria and worked examples when a rule is ambiguous.

Quick reference — canonical rubric level boundaries:

- **F3 (trigger specificity)**: Level 4 (0.90–1.00) Immediate · Level 3 (0.65–0.85) Soon · Level 2 (0.40–0.60) Distant · Level 1 (0.15–0.35) Abstract · Level 0 (0.00–0.10) No trigger
- **F8 (enforceability ceiling)**: Level 3 (0.85–1.00) Not enforceable · Level 2 (0.55–0.80) Partially · Level 1 (0.30–0.50) Mostly · Level 0 (0.10–0.25) Fully enforceable

## Write judgments

Write to `.rulesense-tmp/draft_judgments.json` via a temp Python script. The `draft_` prefix prevents collision with the audit pipeline's `all_judgments.json` when this skill is invoked via the audit's gap bridge:

```python
# .rulesense-tmp/_draft_judgments.py
import json
judgments = [
    {"id": "XX01", "F3": {"value": 0.85, "level": 4, "reasoning": "..."}, "F8": {"value": 0.90, "level": 3, "reasoning": "..."}},
    {"id": "XX02", "F3": {"value": 0.70, "level": 3, "reasoning": "..."}, "F8": {"value": 0.80, "level": 2, "reasoning": "..."}}
]
with open(".rulesense-tmp/draft_judgments.json", "w", encoding="utf-8") as f:
    json.dump(judgments, f, indent=2, ensure_ascii=False)
```

Invoke `Bash` with `description: "Write draft judgments; remove temp script"`:

```bash
$PYTHON_CMD .rulesense-tmp/_draft_judgments.py && rm -f .rulesense-tmp/_draft_judgments.py
```

## Finalize

Invoke `Bash` with `description: "Finalize draft scoring"`:

```bash
$PYTHON_CMD "$SCRIPTS/run_audit.py" --finalize-draft
```

## Present results to the user

Use the friendly format below — no factor codes shown to the user. Check-marks for rules that pass the quality floor, warning signs for rules that need work. Show friendly problem descriptions and suggested fixes inline.

```
## Scoring Results

1. ✓ "When adding a new API endpoint..." — Grade: A
   Strong action verb, concrete examples, well-scoped.

2. ⚠ "Use meaningful test names..." — Grade: C
   Too vague — add an example of a good vs bad test name.

3. ✓ "Integration tests call real handlers..." — Grade: A
   Specific, concrete, not automatable — text rule is the right format.
```
