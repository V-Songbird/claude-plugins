---
name: assay
description: >-
  Invoke this skill (or /rulesense:assay) any time a user wants feedback on rule
  files they already have. This covers CLAUDE.md and .claude/rules/ — grading,
  scoring, auditing, reviewing, or critiquing the structural clarity of existing
  instructions. Trigger broadly: if someone asks "are my rules any good",
  "look at my rules", "check my CLAUDE.md", "grade my instruction files",
  "which rules are weak/vague/passive/garbage", "triage this inherited rule
  set", or "which rules should be hooks instead" — this is the skill. Also
  trigger when someone references /rulesense:assay with any flags (--json, --fix,
  --verbose). The core signal is: the user has existing Claude Code rules and
  wants an opinion on their quality. This skill reads and evaluates — it never
  creates new rules (that's forge), never reviews code or PRs, and
  ignores non-Claude-Code config like eslint or prettier.
user-invocable: true
version: 1.0.0-alpha
---

# Rules Assay — Quality Scoring

Score the project's Claude Code instruction files for structural clarity — how clearly Claude can parse and apply each rule.
**Language:** Scoring is English-only. Non-English rules will receive inaccurate scores.
If arguments are provided, treat them as flags: $ARGUMENTS
Supported flags: `--fix` (suggest + apply rewrites), `--verbose` (detailed factor breakdown), `--json` (machine-readable)

**Architecture**: Four factors (F1, F2, F4, F7) are scored by deterministic Python scripts. Score two judgment factors (F3, F8) plus edge-case patches. The `run_audit.py` orchestrator handles all pipeline mechanics — the only bash interactions are calling its modes and writing judgment data files.

## User interaction discipline — read before any phase

Every point in this skill where the user is asked to pick between options, approve an action, or confirm next steps **must** use the `AskUserQuestion` tool. Never ask a decision question as free-form text in chat — users may not notice the question, and there is no way for the harness to chain into the next step without the structured selection.

Rules:
1. **If you are asking the user to choose between options, use `AskUserQuestion`.** Plain-text questions like "Want me to do X, or Y?" break the UX.
2. **If the choices are not mutually exclusive** (e.g. multiple coverage gaps, multiple files to split), set `multiSelect: true` on that question.
3. **If you finish a step and have a new finding to offer**, treat that as a new decision point and use `AskUserQuestion` again — not prose.
4. **If a re-audit or second-pass cycle runs**, every checkpoint fires again. Phase 3c's fix menu, the Step 4 per-category follow-up (when Promote is checked), and the Step 7 post-apply follow-up (including its `"Fix coverage gaps"` branch when gaps remain) all re-invoke `AskUserQuestion` on each pass through the flow; NEVER silently skip them on subsequent runs.
5. **Only fall back to plain text** when presenting read-only information (the report, the teaching summary, the diff summary). Decisions always go through `AskUserQuestion`.

### `AskUserQuestion` shape constraints — apply to every invocation below

- `header` MUST be ≤12 characters (tool-enforced; longer values truncate silently).
- `options` MUST contain 2–4 entries. The harness auto-injects an "Other" escape when needed — do NOT add a 5th option manually.
- Every option MUST have `label` and `description`. Omitting `description` produces bare buttons with no guidance.
- `multiSelect: true` ONLY when selections are logically independent (e.g. multiple coverage gaps). Default to `false`.
- Bash Python commands in this skill use `$PYTHON_CMD` (set during pre-flight). Every `Bash` invocation MUST include a short `description` (5–10 words) naming its purpose.

## Task tracking — create the list before pre-flight

Before running the pre-flight check, create a task list via `TaskCreate` (fall back to `TodoWrite` in non-interactive / SDK sessions). The pipeline spans many phases and users need visible progress.

Every task MUST carry paired `content` (imperative) and `activeForm` (progressive) fields. `content` renders when the task is `pending` or `completed`; `activeForm` renders while `in_progress`. They are NOT interchangeable.

Initial tasks (create all of these up front, with both forms):

1. `{ content: "Run pre-flight Python check", activeForm: "Running pre-flight Python check" }`
2. `{ content: "Find rules and compute baseline scores", activeForm: "Finding rules and computing baseline scores" }` — Phase 1
3. `{ content: "Score rule clarity and enforceability", activeForm: "Scoring rule clarity and enforceability" }` — Phase 2
4. `{ content: "Present the audit report", activeForm: "Presenting the audit report" }` — Phase 3
5. `{ content: "Analyze rule file organization", activeForm: "Analyzing rule file organization" }` — Phase 3b
6. `{ content: "Detect placement candidates", activeForm: "Detecting placement candidates" }` — Phase 3c Step 1
7. `{ content: "Offer the fix menu", activeForm: "Offering the fix menu" }` — Phase 3c Step 3
8. `{ content: "Summarize what the rules cover", activeForm: "Summarizing what the rules cover" }` — Phase 3c Step 6.5 (renders intention map + coverage gaps right before the Step 7 decision)
9. `{ content: "Clean up temp files", activeForm: "Cleaning up temp files" }` — Phase 4 (ALWAYS the last entry in the list; conditional tasks MUST be inserted before this one, NEVER after)

Append conditional tasks via `TaskUpdate` ONLY when their gate fires. **Position rule**: every conditional task MUST be inserted immediately before the `"Clean up temp files"` task so cleanup stays the last entry in the list. A bare append at the tail places the task AFTER cleanup and visually breaks the list (users reported this). When calling `TaskUpdate`, pass the full list with the new task at position `len(list) - 1` (or, equivalently, insert before the entry whose `content == "Clean up temp files"`).

Conditional tasks and their gates:

- **Fix-menu umbrella** — gate: Phase 3c Step 3 returns ≥1 checked option OR `--fix` was passed. Exactly ONE task regardless of how many options checked. Shape + progression rules: `references/umbrella-task.md`.
- **Gap umbrella** — gate: Phase 3c Step 7 returns `"Fix coverage gaps"`. Exactly ONE task regardless of how many gaps the user picks. Shape + progression rules: `references/gap-fill.md`.
- **Re-run assay** — `{ content: "Re-run the assay", activeForm: "Re-running the assay" }` when Phase 3c Step 7 follow-up is `"Run assay again"`.

Single-spinner discipline: mark each task `in_progress` immediately before starting, `completed` immediately on finishing; mutate the umbrella's `activeForm` between sub-steps rather than opening new tasks. NEVER leave two tasks `in_progress` simultaneously. NEVER batch completions.

## Pre-flight

Invoke `Bash` with `description: "Verify Python 3.10+ is available"`:

```bash
python3 -c "import sys; assert sys.version_info >= (3,10), f'Requires Python 3.10+. Found: {sys.version}'" 2>&1 || python -c "import sys; assert sys.version_info >= (3,10), f'Requires Python 3.10+. Found: {sys.version}'" 2>&1
```

If this fails, tell the user: "rulesense requires Python 3.10+. Install Python to continue." and stop.

Determine which Python command succeeded (`python3` or `python`). Record it as the literal token `PYTHON_CMD` (either `python3` or `python`) and use that token in every subsequent `Bash` block in this skill. Shell state does NOT persist across `Bash` tool calls in Claude Code — the variable is a *template placeholder* you substitute into each command string, not an exported shell variable. Do not inline "python" or "python3" anywhere else — the token is the single source of truth and keeps every downstream call consistent.

## Phase 1 — Run the Pipeline

Invoke `Bash` with `description: "Run deterministic audit pipeline"`:

```bash
SCRIPTS="${CLAUDE_PLUGIN_ROOT}/scripts"
$PYTHON_CMD "$SCRIPTS/run_audit.py" --prepare --project-root "$(pwd)"
```

This runs the full deterministic pipeline (discover → extract → score → build prompts) and outputs JSON:

```json
{
  "rule_count": 34,
  "batch_mode": true,
  "batch_count": 3,
  "prompt_files": [".rulesense-tmp/batches/prompt_001.md", "..."],
  "single_prompt": null,
  "manifest": ".rulesense-tmp/batches/batch_manifest.json"
}
```

When `batch_mode` is false, `single_prompt` has the path and `prompt_files` is empty. If the command fails, report the error to the user and stop.

## Phase 2 — Score F3 and F8

Read each prompt file from Phase 1 output (`single_prompt` or each file in `prompt_files`). Score every rule on two judgment factors using the rubrics in `references/factor-rubrics.md` (canonical — full level criteria and worked examples live there).

**Calibration discipline (multi-batch corpora).** When `batch_mode: true` and `batch_count > 1`, score ALL batches in a single continuous turn. Do NOT interleave unrelated tool calls or dispatch subagents between batches — rubric anchoring (what "Level 2 distant" vs "Level 3 soon" feels like) degrades when the rubric text drops out of attention, and independent subagents each reload the rubric fresh and drift. Before writing `.rulesense-tmp/all_judgments.json`, spot-check cross-batch consistency: pick two rules with similar trigger-action distance from different batches; if you assigned meaningfully different F3 or F8 values, revise until the scores reflect the same scale across the whole corpus.

Quick reference (summary of the canonical rubric level boundaries — read `references/factor-rubrics.md` for the full criteria when a rule is ambiguous):

- **F3 (trigger-action distance)**: Level 4 (0.90–1.00) Immediate · Level 3 (0.65–0.85) Soon · Level 2 (0.40–0.60) Distant · Level 1 (0.15–0.35) Abstract · Level 0 (0.00–0.10) No trigger
- **F8 (enforceability ceiling)**: Level 3 (0.85–1.00) Not enforceable · Level 2 (0.55–0.80) Partially · Level 1 (0.30–0.50) Mostly · Level 0 (0.10–0.25) Fully enforceable

For flagged rules (noted in the prompt), also provide the requested F7 patch with reasoning.

### Writing judgments

Read `references/judgment-shapes.md` for the batched schema, the unscorable-rule null convention, and the strict F-patch shape (including shapes the pipeline silently drops). Write `.rulesense-tmp/all_judgments.json` via a temp Python script following that reference, then invoke `Bash` with `description: "Write judgments JSON; remove temp script"`:

```bash
$PYTHON_CMD .rulesense-tmp/_judgment_all.py && rm -f .rulesense-tmp/_judgment_all.py
```

Include every rule ID. Emit `F{N}_patch` ONLY for rules flagged `needs_judgment: true` in the prompt.

## Phase 3 — Present Results

Invoke `Bash` with `description: "Finalize audit and render report"`:

```bash
$PYTHON_CMD "$SCRIPTS/run_audit.py" --finalize
```

Pass `--verbose` or `--json` if the user requested those flags. Read the output and present it.

After the pipeline report, get structured analysis data. Invoke `Bash` with `description: "Build structured analysis for report sections"`:

```bash
$PYTHON_CMD "$SCRIPTS/run_audit.py" --build-analysis
```

Read the output JSON. It contains grade distribution, file metrics,
organization data, best/worst rules, and a compact rules list for
theme classification — all with standard A/B/C/D/F grades. Use this
data for the sections below. Do NOT construct ad-hoc Python scripts
to read audit.json.

### Phase 3a — (moved)

The intention map + coverage gaps block that used to live here now renders at **Phase 3c Step 6.5** (immediately before the Step 7 post-apply question), so the user sees the gap list fresh when deciding whether to fill them. Skip straight to Phase 3b.

### Phase 3b — Organization Analysis

Analyze whether rules follow Claude Code's recommended organization. Read `references/organization-guide.md` for detailed guidance on file naming, `paths:` frontmatter, and methodology.

Core principle: CLAUDE.md is for instructions every session needs. `.claude/rules/` files with `paths:` frontmatter only load when Claude works on matching files, saving context.

Present which rules stay in CLAUDE.md vs move to scoped files, with specific file names and line-count impact. If CLAUDE.md is already well-organized, say so briefly and skip.

## Phase 3c — Fix menu (combined decision)

Phase 3c consolidates every class of change rulesense can apply — placement promotions, text rewrites, file reorganization — into a single decision point so the user sees the full picture before committing to anything. Placement detection runs FIRST inside this phase (rather than in a later phase) because a rule promoted to a hook or subagent no longer needs its text rewritten, and running rewrites on a rule that will be removed is wasted budget.

**Ordering guarantee.** When multiple classes are selected, Phase 3c Step 5 executes them in the fixed order `promote → rewrite → reorganize`. This is not user-configurable: promotion removes rules from the tree first so rewrite never processes a rule about to disappear; rewrite matches by exact `original_text` so earlier line shifts do not break it; reorganize moves remaining rules by content so it operates on the post-rewrite text.

### Step 1 — Detect placement candidates

Mark the `"Detect placement candidates"` task `in_progress` via `TaskUpdate`. Invoke `Bash` with `description: "Detect placement-opportunity candidates"`:

```bash
$PYTHON_CMD "$SCRIPTS/run_audit.py" --prepare-placement
```

Emits JSON with this shape:

```json
{
  "candidates": [
    {"rule_id": "R42", "rule_text": "...", "file": "CLAUDE.md", "line_start": 42, "line_end": 42,
     "detections": [{"primitive": "hook", "confidence": 0.85, "evidence": [...], "sub_type": "deterministic-gate"}],
     "scores": {"hook": 0.85, "skill": 0.1, "subagent": 0.2},
     "compound": false, "compound_needs_glue": false, "best_fit": "hook"}
  ],
  "summary": {"total_candidates": N, "hook_candidates": n1, "skill_candidates": n2, "subagent_candidates": n3, "compound_candidates": n4}
}
```

Retain the full output in context — Step 2 uses it to render category previews and Step 5a consumes it when writing promotions.

Load `references/promotion-guide.md` only when Step 5a actually runs (on-demand reference); Step 2 needs only the candidate summary to render its preview.

Mark the `"Detect placement candidates"` task `completed` via `TaskUpdate` before continuing.

### Step 2 — Compose the menu summary (read-only)

Read `references/fix-menu-preamble.md` and render its output template, substituting the actual counts and Phase 3b targets. First-person voice; matches Step 3's question. OMIT any block whose class has no applicable content. The locked header wording in that reference MUST be used verbatim — NEVER the bare `Hook candidates (N)` / `Subagent candidates (N)` form. Do NOT ask the user anything during Step 2; the decision point is Step 3.

### Step 3 — Combined multiSelect question (the fix menu)

Mark the `"Offer the fix menu"` task `in_progress` via `TaskUpdate`.

Build the `options` array by including one entry per applicable class of change. OMIT an option whose class has nothing to apply:

- Include `"Promote …"` ONLY if at least one placement category is non-empty (`summary.total_candidates > 0`).
- Include `"Rewrite …"` ONLY if at least one mandate rule scored below 0.50.
- Include `"Reorganize …"` ONLY if Phase 3b recommended reorganization.

**If the `options` array would be empty after this filtering**, skip Phase 3c entirely (no fix menu to offer). Mark the `"Offer the fix menu"` task `completed` with an explanatory note and proceed to Phase 4.

**If `--fix` was passed in `$ARGUMENTS`**, skip this question and pre-select `rewrite = true` plus `reorganize = true` if Phase 3b recommended reorganization. `promote` stays `false` under `--fix` because promotion writes to `.rulesense/PROMOTIONS.md` and modifies `.claude/settings.json` semantics — those deserve explicit consent. Mark the `"Offer the fix menu"` task `completed` and jump to Step 4.

Otherwise, invoke `AskUserQuestion` exactly once:

```
questions: [{
  question: "Which of these changes should I apply? Check any combination — unchecked items are left as-is.",
  header: "Fix menu",
  multiSelect: true,
  options: [
    { label: "Promote [P] placement candidates (recommended)",
      description: "Move rules to .rulesense/PROMOTIONS.md and remove them from source files; I will ask which categories next" },   // ONLY if placement candidates exist
    { label: "Rewrite [R] weak rules (recommended)",
      description: "Draft and score rewrites for the [R] mandate rules below 0.50; apply the ones that pass safety gates" },         // ONLY if any mandate rules below 0.50
    { label: "Reorganize [O] rules (recommended)",
      description: "Move [O] rules from CLAUDE.md into scoped .claude/rules/*.md files — scoped files only load when Claude works on matching files, keeping always-loaded context lean" }   // ONLY if Phase 3b recommended reorganization
  ]
}]
```

Substitute `[P]` with the placement-candidate count, `[R]` with the weak-rule count, and `[O]` with the organization-move count (the exact number of rules Phase 3b flagged to move into scoped files). Every emitted option is labelled `(recommended)` — rulesense only surfaces an option when there is real evidence the change is worth applying.

Record the returned selection as `selected_changes = { promote: bool, rewrite: bool, reorganize: bool }`. If no options are checked, mark the `"Offer the fix menu"` task `completed` and proceed to Phase 4 — the user declined every change.

If at least one option is checked, mark the `"Offer the fix menu"` task `completed` via `TaskUpdate`, then append exactly ONE umbrella task per `references/umbrella-task.md` (shape depends on the checked-option count). NEVER append one task per checked option. Do NOT mark the umbrella `in_progress` yet — Step 4 (Promote's per-category follow-up) runs first if applicable; Step 5 flips it to `in_progress` before the first sub-step.

### Step 4 — Per-category placement follow-up (only if Promote was checked)

Fires if and only if `selected_changes.promote == true`. Otherwise skip straight to Step 5.

Invoke `AskUserQuestion` with `multiSelect: true` and one option per non-empty placement category. Category count never exceeds 4 (hook / skill / subagent / compound), so every non-empty category fits inside the 4-option cap without any per-category loop:

```
questions: [{
  question: "Which placement categories should move to .rulesense/PROMOTIONS.md? Leave a category unchecked to keep those rules as-is.",
  header: "Move which?",
  multiSelect: true,
  options: [
    { label: "Move all [N] hooks (recommended)",      description: "Move all [N] hook rules to .rulesense/PROMOTIONS.md and remove them from the source files" },      // ONLY if hook category non-empty
    { label: "Move all [N] skills (recommended)",     description: "Move all [N] skill rules to .rulesense/PROMOTIONS.md and remove them from the source files" },     // ONLY if skill category non-empty
    { label: "Move all [N] subagents (recommended)",  description: "Move all [N] subagent rules to .rulesense/PROMOTIONS.md and remove them from the source files" },  // ONLY if subagent category non-empty
    { label: "Move all [N] compound (recommended)",   description: "Move all [N] compound rules to .rulesense/PROMOTIONS.md (each splits across two primitives with an optional glue skill)" }  // ONLY if compound category non-empty
  ]
}]
```

Substitute `[N]` with the per-category count in each included option.

Handle the returned selections:
- **A category checked** — record every candidate in that category as selected.
- **A category unchecked** — record zero moves for that category; those rules remain as-is and will re-flag on the next audit.
- **No categories checked** — flip `selected_changes.promote` back to `false` and re-shape the umbrella per the "Step 4 re-shape" section in `references/umbrella-task.md`. Proceed to Step 5.

Do NOT fall back to a per-category loop or plain-text "which ones do you want to move?". One `AskUserQuestion` call, one pass, every category decision captured.

### Step 5 — Execute selected changes in fixed order

Run ONLY the sub-steps whose flag is `true` in `selected_changes`, in the order `5a → 5b → 5c`. Exactly ONE umbrella task (appended in Step 3) represents the entire batch; do NOT close and re-open it between sub-steps. Instead, `TaskUpdate` the umbrella's `activeForm` at each sub-step transition (only when `N >= 2`) so the user sees steady progress on a single spinner. Mark the umbrella `in_progress` in Step 5a (or in Step 5b / 5c if Step 5a doesn't fire) and mark it `completed` only after the final selected sub-step finishes. NEVER run two sub-steps concurrently.

#### Step 5a — Promote (if `selected_changes.promote == true`)

**Umbrella.** If the umbrella is still `pending`, mark it `in_progress`. Per `references/umbrella-task.md`: set `activeForm` to `"Applying fix 1 of [N] — promoting placement candidates"` when `N >= 2`; leave Step 3's Promote-only `activeForm` unchanged when `N == 1`.

Read `references/promotion-guide.md` for per-primitive judgment-string templates and `references/promotions-payload.md` for the full `_write_promotions.py` template, the judgment-field contract, and post-write warning handling. Both are on-demand references — load them now that Step 5a is firing.

Compose one move entry per selected candidate following the contract in `references/promotions-payload.md`. Invoke `Write` to produce `.rulesense-tmp/_write_promotions.py` from the template in that reference, substituting real values for every `<...>` placeholder.

Then invoke `Bash` twice in sequence, each with its own `description`:

- `{ command: "$PYTHON_CMD .rulesense-tmp/_write_promotions.py && rm -f .rulesense-tmp/_write_promotions.py", description: "Write promotions payload; remove temp script" }`
- `{ command: "$PYTHON_CMD \"$SCRIPTS/run_audit.py\" --write-promotions --project-root \"$(pwd)\" < .rulesense-tmp/promotions_input.json", description: "Atomically write PROMOTIONS.md and prune source files" }`

**Check the output JSON for `warnings`.** If any move was missing judgment fields, `--write-promotions` emits a warnings array plus stderr messages identifying the rule IDs. Regenerate the payload with complete judgment strings and re-run before presenting results — the user should NEVER see a header-only entry in `.rulesense/PROMOTIONS.md`.

The script is atomic: either `.rulesense/PROMOTIONS.md` is written AND all moved rules are removed from their source files, or nothing changes. On hard failure (source-file drift, write error), the JSON output has `status: "failed"` with a `reason` field.

**On `status: "ok"`**, render the result:

```
Moved [N] rules to `.rulesense/PROMOTIONS.md`.

Files modified:
- [file1] ([k] rules removed)
- [file2] ([j] rules removed)
...

Review with `git diff` before committing. The PROMOTIONS doc has official-docs
links per primitive to help you promote these items when you're ready.
```

If this was the final selected sub-step (no rewrite and no reorganize queued after it), mark the umbrella task `completed` via `TaskUpdate` and continue to Step 6. Otherwise continue to Step 5b (if `selected_changes.rewrite`) or Step 5c (if only `selected_changes.reorganize`) — the umbrella stays `in_progress` and its `activeForm` will be mutated at the start of the next sub-step.

**On `status: "failed"`**, report the failure reason to the user, abort the remaining Step 5 sub-steps (do NOT run rewrite or reorganize — a failed atomic write signals source-file drift that invalidates downstream operations), `TaskUpdate` the umbrella task to `completed` with an explanatory note in chat ("Promotion write failed; rewrites and reorganize skipped."), and jump to Phase 4 so cleanup still runs.

#### Step 5b — Rewrite (if `selected_changes.rewrite == true`)

**Umbrella.** If Step 5a did NOT fire, mark the umbrella `in_progress`. Per `references/umbrella-task.md`: set `activeForm` to `"Applying fix [k] of [N] — rewriting weak rules"` (`[k]` = 1-based index within selected sub-steps) when `N >= 2`; leave Step 3's Rewrite-only `activeForm` unchanged when `N == 1`.

Run the rewrite pipeline from `references/rewrite-pipeline.md` (Steps A–D: `--prepare-fix` → generate + extractor self-check → `--score-rewrites` → `--finalize-fix`). Return here for the apply step below.

**Text-based apply (survives promotion-induced line shifts).** After `--finalize-fix` completes and its report is presented, for each rewrite that passed safety gates:

1. `Read` the source file at `rewrite.file`.
2. Locate the exact `rewrite.original_text` in the file by content match — do NOT rely on `rewrite.line_start`, which may be stale if Step 5a ran first and shifted lines.
3. Replace with `rewrite.suggested_rewrite` using the `Edit` tool.
4. Report each change: `file:line` with a before/after summary.

If any source file no longer contains `rewrite.original_text` (e.g., the rule was promoted in Step 5a and removed from source), skip that rewrite and log a one-line note — it is not an error, just a sign that promotion handled that rule already.

If this was the final selected sub-step (no reorganize queued after it), mark the umbrella task `completed` via `TaskUpdate` and continue to Step 6. Otherwise continue to Step 5c — the umbrella stays `in_progress` and its `activeForm` will be mutated at the start of Step 5c.

#### Step 5c — Reorganize (if `selected_changes.reorganize == true`)

**Umbrella.** If neither 5a nor 5b fired, mark the umbrella `in_progress`. Per `references/umbrella-task.md`: set `activeForm` to `"Applying fix [k] of [N] — reorganizing rules into scoped files"` when `N >= 2`; leave Step 3's Reorganize-only `activeForm` unchanged when `N == 1`.

Read `references/organization-guide.md` now for the per-file methodology, then:

1. Create the scoped `.claude/rules/*.md` files Phase 3b identified, each with the correct `paths:` frontmatter.
2. Move the identified rules into those files by exact text (NOT line number — rewrites in Step 5b may have changed line offsets).
3. Remove the moved rules from their original location (typically `CLAUDE.md`).
4. Invoke `Glob` to verify each new `paths:` pattern matches at least one file in the tree; if a pattern matches zero files, revise it or drop that file.

Mark the fix-menu umbrella task `completed` via `TaskUpdate`. Step 5c is always the final sub-step when it runs (by the fixed promote → rewrite → reorganize ordering), so closing the umbrella here is unconditional.

### Step 6 — Teaching summary (only if any change was applied)

If every `selected_changes.*` flag was false OR every sub-step was aborted due to Step 5a failure, skip Step 6 entirely.

Otherwise Read `references/teaching-patterns.md` and produce the teaching summary per the rendering rules in that reference — pattern table, grouping, 4–6-line sections per non-empty pattern, prioritization for the two structural patterns when they fired, and a separate note for any rewrites that stayed below the quality floor.

### Step 6.5 — Render intention map + coverage gaps (immediately before Step 7)

Mark the `"Summarize what the rules cover"` task `in_progress` via `TaskUpdate`. Build the intention map in three passes:

1. **Theme assignment** — for each rule in `rules_for_intention_map` (from the `--build-analysis` output consumed at the start of Phase 3), assign a theme that describes what the rule is trying to make Claude do. Use project-appropriate labels (e.g. "Code style", "Architecture", "Testing", "Workflow", "Documentation", "Git discipline"). Each rule belongs to exactly one theme — pick the dominant intention.
2. **Aggregate** rules by theme into `{theme → [rule_ids]}`; drop themes with zero rules.
3. **Render** the output template (keep total output to 10–15 lines):

```
## What the rules cover

The [N] rules break down into these intentions:

- **[Theme]** ([count] rules) — [one-line description]
- ...

**Coverage gaps:** [2–3 areas relevant to the detected tech stack]
```

Frame gaps as suggestions ("consider adding"), not requirements. This block is read-only context for the Step 7 question immediately below — users need the gap list fresh when deciding whether to fill gaps.

Mark the `"Summarize what the rules cover"` task `completed` via `TaskUpdate` before continuing to Step 7.

### Step 7 — Post-apply follow-up

Invoke `AskUserQuestion`. Include `"Fix coverage gaps"` as an option ONLY when Step 6.5 identified at least one gap:

```
questions: [{
  question: "I've applied the changes. Run git diff to review. What next?",
  header: "Next step",
  multiSelect: false,
  options: [
    { label: "Fix coverage gaps (recommended)", description: "Draft rules for one or more of the gaps listed above; I'll ask which gaps next" },   // ONLY if Step 6.5 listed any gaps
    { label: "Run assay again",   description: "Re-run the assay from scratch on the updated files to measure improvement and catch anything new" },
    { label: "Finish",            description: "Clean up temp files and end this session" }
  ]
}]
```

If the user picks `"Fix coverage gaps"`, Read `references/gap-fill.md` and execute the gap-fill flow per that reference (per-gap multiSelect → gap umbrella inserted **before** `"Clean up temp files"` → sequential build invocation → close umbrella). After the flow returns, **re-fire Step 7** so the user can then pick `"Run audit again"` or `"Finish"`. Include `"Fix coverage gaps"` in the re-fired Step 7 only if unfilled gaps remain from the Step 6.5 list.

If the user picks `"Run assay again"`, append `{ content: "Re-run the assay", activeForm: "Re-running the assay" }` via `TaskUpdate` inserted **before** `"Clean up temp files"`, mark it `in_progress`, and re-invoke the full audit flow from Phase 1. Every checkpoint (Phase 3c fix menu, Phase 3c Step 4 per-category follow-up, Phase 3c Step 7 post-apply follow-up) MUST fire again on the re-audit — do NOT shortcut them with prose. If the re-audit surfaces a *new* category of problem that none of the standard checkpoints cover (e.g. "I notice I introduced orphan fragments during the first rewrite pass"), raise it as a fresh `AskUserQuestion` with the full shape — 2–3 options each with `label` and `description` — NEVER as a free-text question.

If the user picks `"Finish"`, proceed to Phase 4.

## Phase 3.5 — Rewrite pipeline mechanics

Phase 3.5 is the set of pipeline mechanics called from Phase 3c Step 5b when `selected_changes.rewrite == true`. The full detail (Steps A–D: `--prepare-fix`, generate + extractor self-check, `--score-rewrites`, `--finalize-fix`) lives in `references/rewrite-pipeline.md`. Read it when Step 5b fires. The text-based apply step stays in Phase 3c Step 5b so it honours the fixed `promote → rewrite → reorganize` execution order.

## Additional resources

Read on demand, not upfront. The workflow steps above are self-contained; these references add depth for specific phases.

- For the rule extraction algorithm and debugging `--prepare` output, see [references/instruction-parser.md](references/instruction-parser.md) (Phase 1).
- For the formal scoring contract — per-rule formula, factor weights, floors, staleness gate — see [references/quality-model.md](references/quality-model.md) (Phase 2).
- For F3 and F8 rubric level boundaries and worked examples, see [references/factor-rubrics.md](references/factor-rubrics.md) (Phase 2).
- For the batched judgment schema, unscorable-rule null convention, and F-patch shape, see [references/judgment-shapes.md](references/judgment-shapes.md) (Phase 2).
- For rewrite pattern taxonomy and extractor compatibility, see [references/rewrite-guide.md](references/rewrite-guide.md) (Phase 3c Step 5b).
- For the full Steps A–D rewrite mechanics (`--prepare-fix` through `--finalize-fix`), see [references/rewrite-pipeline.md](references/rewrite-pipeline.md) (Phase 3c Step 5b).
- For organization analysis methodology and file naming, see [references/organization-guide.md](references/organization-guide.md) (Phase 3b analyzing; Phase 3c Step 5c applying).
- For per-primitive judgment-string templates, see [references/promotion-guide.md](references/promotion-guide.md) (Phase 3c Step 5a).
- For the `_write_promotions.py` template, field contract, and post-write warning handling, see [references/promotions-payload.md](references/promotions-payload.md) (Phase 3c Step 5a).
- For the fix-menu read-only snapshot template and locked header wording, see [references/fix-menu-preamble.md](references/fix-menu-preamble.md) (Phase 3c Step 2).
- For fix-menu umbrella shape, progression, and Step 4 re-shape, see [references/umbrella-task.md](references/umbrella-task.md) (Phase 3c Steps 3 / 4 / 5).
- For gap-fill per-gap multiSelect and gap umbrella mechanics, see [references/gap-fill.md](references/gap-fill.md) (Phase 3c Step 7 `"Fix coverage gaps"` branch).
- For teaching summary pattern table and rendering rules, see [references/teaching-patterns.md](references/teaching-patterns.md) (Phase 3c Step 6).
- For the fallback manual pipeline when `run_audit.py` fails, see [references/manual-pipeline.md](references/manual-pipeline.md).
- For markdown and JSON report output schemas, see [references/report-schema.md](references/report-schema.md) (Phase 3).

## Phase 4 — Cleanup

Invoke `Bash` with `description: "Remove audit pipeline temp files"`:

```bash
$PYTHON_CMD "$SCRIPTS/run_audit.py" --cleanup
```

Runs after all reporting and optional fix/apply steps complete or are declined.
