# Gap-fill flow (invoked from Phase 3c Step 7)

Fires when the user picks `"Fix coverage gaps"` at Phase 3c Step 7. Load on-demand when that branch fires.

## Per-gap multiSelect

Invoke `AskUserQuestion` exactly once, `multiSelect: true`, one option per gap identified in Phase 3a's read-only summary (plus a skip option when useful):

```
questions: [{
  question: "I found gaps in [gap areas]. Which would you like me to draft rules for?",
  header: "Cover gaps",
  multiSelect: true,
  options: [
    { label: "[Gap 1 name]", description: "Draft rules for this area" },
    { label: "[Gap 2 name]", description: "Draft rules for this area" },
    { label: "[Gap 3 name]", description: "Draft rules for this area" },
    { label: "Skip",         description: "Return to the post-apply question without drafting" }
  ]
}]
```

Cap at 4 options (harness auto-injects an "Other" escape if needed). If more than 3 gaps exist, pick the 3 most relevant to the detected stack and drop the rest.

Handle selections:
- **One or more gaps picked, no Skip** — proceed to "Gap umbrella" below.
- **"Skip" picked alone, or Skip + any gaps** — return to Phase 3c Step 7 without invoking build.

## Gap umbrella task — single task, inserted before "Clean up temp files"

Append exactly ONE umbrella task via `TaskUpdate`, regardless of how many gaps the user picked. **Position matters**: the umbrella MUST be inserted immediately before the `"Clean up temp files"` task so cleanup stays the last entry in the list. A bare append places the umbrella at the tail, after cleanup, which visually breaks the list (users reported this).

Shape by pick count (`N`):

- **`N == 1`** (single gap picked):
  ```
  { content: "Draft rules for gap — [gap name]",
    activeForm: "Drafting rules for gap — [gap name]" }
  ```
  Substitute `[gap name]` with the literal gap label (e.g. `"TypeScript strictness"`).

- **`N >= 2`** (multiple gaps picked):
  ```
  { content: "Draft rules for [N] coverage gaps",
    activeForm: "Drafting rules for gap 1 of [N] — [first gap name]" }
  ```
  Substitute `[N]` with the pick count and `[first gap name]` with the first gap in pick order.

The em-dash separator is intentional; it prevents the gap name being read as a modifier of the preceding word. NEVER use parentheticals like `"(optional)"` in the label.

## Sequential build invocation (strict order, pick order)

Process picked gaps sequentially — NEVER in parallel. The single umbrella stays `in_progress` across all gaps. Mark it `in_progress` immediately before invoking build for the first gap.

Between gaps (when `N >= 2`), `TaskUpdate` mutates ONLY the umbrella's `activeForm`:

1. `"Drafting rules for gap 1 of [N] — [gap 1 name]"` (before first build)
2. `"Drafting rules for gap 2 of [N] — [gap 2 name]"` (between first and second)
3. … and so on

The umbrella's `content` stays constant (`"Draft rules for [N] coverage gaps"`).

### Between-gap state rules

- Do NOT run `--cleanup` or remove `.rulesense-tmp/audit.json` — the bridge marker MUST survive every gap's build flow so each invocation takes Context B. Build's Phase 4 only removes `draft_*` files, so audit state survives automatically.
- Do NOT re-run `--prepare` or re-score between gaps — `audit.json` is still the source of truth; new rule files the builds produce don't affect previously computed analysis.
- **If build aborts for a gap** (user picks `"Start over"` repeatedly at build's draft-review, or exits without writing): emit a one-line note (`"No rules written for [gap name] — user aborted the draft. Continuing with next gap."`) and advance `activeForm`. The umbrella stays `in_progress`.
- **If the user asks mid-flight to stop remaining gaps**: emit `"Skipping remaining [K] gaps at user request."`, mark the umbrella `completed`, and return to Phase 3c Step 7.

## Forge skill context

Forge detects `.rulesense-tmp/audit.json` and takes its Context B path (suppresses `TaskCreate`; no internal tasks appended to the audit list). See `skills/forge/SKILL.md` "Context B — Audit-bridge invocation".

## Completion

After the final gap's build returns (or the user stopped early), mark the umbrella `completed` via `TaskUpdate` and re-fire Phase 3c Step 7 so the user can then pick `"Run audit again"` or `"Finish"`. If every gap was aborted or the user stopped before any build wrote rules, the umbrella still marks `completed` — the task represents the attempt, not the outcome count.
