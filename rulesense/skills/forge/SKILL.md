---
name: forge
description: >-
  Invoke this skill (or /rulesense:forge) when a user wants to create new Claude
  Code rules or add conventions to their project. This covers creating
  .claude/rules/ files, drafting rule sets for specific topics, and scaffolding
  rules from project patterns. Trigger broadly: if someone asks "I need rules
  for testing", "make Claude always do X", "create a rule that enforces Y",
  "scaffold rules for this project", "add conventions for my API layer", "help
  me write better rules", or "I want Claude to follow these patterns" — this
  is the skill. Also trigger when the user picks a coverage gap identified by
  the assay skill and wants to fill it with new rules. The core signal is: the
  user wants NEW rules written, not existing rules reviewed. This skill creates
  and writes .claude/rules/ files — it never audits or scores existing rules
  (that's the assay skill), never modifies CLAUDE.md directly, and never writes
  code or tests.
user-invocable: true
version: 1.0.0-alpha
---

# Rules Builder — Quality-Scored Rule Creation

Create `.claude/rules/` files that are specific, scoped, and quality-scored.
**Language:** Rule drafting and scoring is English-only.

If arguments are provided, treat them as the rule topic: $ARGUMENTS

## `AskUserQuestion` shape constraints — apply to every invocation in this skill

Every decision point in this skill that presents a fixed, option-shaped answer space MUST use `AskUserQuestion` — plain-text questions like "Want me to do X, or Y?" break the button-driven flow and users may not notice them.

- Every invocation MUST pass the canonical top-level shape `{ questions: [{ question, header, multiSelect, options }] }`. The `questions: [...]` array wrapper is required — flat-form inputs without it are rejected by the tool schema. Each field list below describes the contents of the single entry inside that array.
- `header` MUST be ≤12 characters (tool-enforced; longer values truncate silently).
- `options` MUST contain 2–4 entries. The harness auto-injects an "Other" escape when needed — do NOT add a 5th option manually.
- Every option MUST have `label` and `description`. Omitting `description` produces bare buttons with no guidance.
- `multiSelect: true` ONLY when selections are logically independent (e.g. multiple test scopes). Default to `false`.
- Open-ended prompts with no enumerable answer space (like Phase 1 Step 2's opening question, or "Which directories are the focus?") stay as plain prose — see per-phase notes below.
- Every `Bash` invocation MUST include a short `description` field (5–10 words) naming its purpose.

## Task tracking — branch on invocation context

Build runs in one of two contexts, and each uses a different task-tracking strategy. Before doing anything else, check whether `.rulesense-tmp/audit.json` exists in the project root — that is the assay→forge bridge marker (same check as Phase 1 Step 1 below; doing it here lets the task-list decision precede the first user-visible tool call).

### Context A — Standalone invocation (no bridge marker)

The user invoked `/rulesense:forge` directly. Build owns the task list for this session. Create it via `TaskCreate` (fall back to `TodoWrite` in non-interactive / SDK sessions). Every task MUST carry paired `content` (imperative) and `activeForm` (progressive) fields — `content` renders when `pending` or `completed`, `activeForm` renders while `in_progress`, and they are NOT interchangeable.

Initial tasks (create all of these up front, with both forms):

1. `{ content: "Detect audit→build bridge marker", activeForm: "Detecting audit→build bridge marker" }` — Phase 1 Step 1
2. `{ content: "Capture the user's intent", activeForm: "Capturing the user's intent" }` — Phase 1 Steps 2–3
3. `{ content: "Analyze the project", activeForm: "Analyzing the project" }` — Phase 2
4. `{ content: "Scope the rules via questionnaire", activeForm: "Scoping the rules" }` — Phase 2b
5. `{ content: "Draft the rule set", activeForm: "Drafting the rule set" }` — Phase 3 Step 1
6. `{ content: "Score the draft rules", activeForm: "Scoring the draft rules" }` — Phase 3 Step 2
7. `{ content: "Write the rule files", activeForm: "Writing the rule files" }` — Phase 4
8. `{ content: "Clean up temp files", activeForm: "Cleaning up temp files" }` — Phase 4 final step

Mark each task `in_progress` via `TaskUpdate` immediately before starting it and `completed` immediately upon finishing. Do not batch completions — update the list as each step resolves.

### Context B — Audit-bridge invocation (bridge marker present)

The assay skill delegated here from its Phase 3c Step 7 `"Fix coverage gaps"` branch. The assay skill already appended a single gap-umbrella task (inserted before `"Clean up temp files"` — see `../assay/references/gap-fill.md`) and marked it `in_progress` before invoking forge. **Forge MUST NOT call `TaskCreate` or `TodoWrite` in this context** — appending the eight Phase-1-to-4 tasks would pollute the assay list with duplicated names (e.g. two "Clean up temp files" entries, one from assay's Phase 4 and one from forge's Phase 4) and produce the "chaotic list" users have reported.

Instead, in Context B:

- Skip the initial `TaskCreate` / `TodoWrite` call entirely.
- Communicate build's per-phase progress to the user through streamed prose — the phase headers ("Picking up from the assay — I'll draft rules for this gap.", "Analyzing the project…", "Drafting the rule set…", "Scoring the drafts…", "Writing to dll-components-v2/.claude/rules/<topic>.md…") already render as visible event markers in the Claude Code UI.
- Skip Phase 1 Steps 2–3 and Phase 2b's questionnaire as described in the phase text below — the assay skill already collected those inputs.
- When forge finishes (after Phase 4 cleanup of `draft_*` temp files), return control to the assay skill without touching its task list. The assay skill mutates the umbrella's `activeForm` between gaps and marks it `completed` after the final gap per [`../assay/references/gap-fill.md`](../assay/references/gap-fill.md).

## Phase 1 — Understand What the User Wants

### Step 1 — Detect audit-bridge context

First, check whether `.rulesense-tmp/audit.json` exists in the project root.

- **If the file exists**: the user came from the assay skill's Phase 3c Step 7 `"Fix coverage gaps"` branch. The topic and project context are already available. Skip Phase 1 Steps 2-3 and go directly to Phase 2 with the gap topic as the scoping input. Say: "I'll draft rules for [gap topic] based on your project. Let me ask a couple of questions to get the scope right."
- **If the file does not exist**: the user invoked build directly. Continue with Step 2.

### Step 2 — Ask the opening question

Ask one question as plain prose (this is the one intentional exception to the `AskUserQuestion` discipline — the answer space is open-ended and free-text is required):

"What do you want me to do (or stop doing) in this project?"

Expect anything from a specific request ("always use Vitest for tests") to a vague wish ("help me write better TypeScript"). Both are valid starting points. Every subsequent clarification MUST use `AskUserQuestion` per the shape constraints at the top of this file.

**If the request is vague**, narrow scope by invoking `AskUserQuestion` (do NOT ask in prose — the option set is fixed and mutually exclusive):

- **question**: `"Which area do you care about most?"`
- **header**: `"Rule area"`
- **multiSelect**: `false`
- **options** (exactly 4 — the AskUserQuestion harness adds an "Other" escape automatically for free-text answers):
  - `{ label: "Testing", description: "Test placement, coverage expectations, mocking discipline" }`
  - `{ label: "Code style", description: "Naming, imports, file organization, formatting" }`
  - `{ label: "Architecture", description: "Layer boundaries, module isolation, API contracts" }`
  - `{ label: "Workflow / process", description: "Git discipline, PR conventions, commit hygiene" }`

If the user picks "Other" and supplies free text, treat that text as the topic and proceed.

### Step 3 — Infer these from the user's words, do not ask about them

- **Category** — infer from verbs: "always", "must", "never" → mandate; "prefer", "try to" → preference; "except when", "override" → override. Default to mandate when unclear.
- **Scope** — determine during Phase 2 from the project's directory structure. Rules that apply to specific directories use `paths:` frontmatter; rules that apply everywhere do not.
- **Scale** — infer from the breadth of the request: "Add a rule about X" → single rule. "I want testing discipline" → convention set. "Set up rules for this project" → project scaffold.

## Phase 2 — Analyze Project

Before writing anything, understand what exists:

1. **Scan existing instructions** — read all `.claude/rules/*.md` and `CLAUDE.md`. Count current rules.

2. **Detect tech stack** — check for marker files (package.json, Cargo.toml, pyproject.toml, go.mod, etc.).

3. **Sample conventions** — read 3-5 representative source files. Look for naming patterns, import style, test placement. Rules should codify what the project already does.

4. **Check for linters/formatters** — read .eslintrc*, .prettierrc*, biome.json, etc. If a linter already handles it, tell the user instead of creating a rule.

5. **Map directory structure** — identify directories and their purposes. Verify candidate glob patterns match actual files using Glob.

**Heavy-context escape**: if the project has more than ~200 source files in the relevant subsystem, or the subsystem is unfamiliar territory (e.g. you've never touched the framework before), do NOT read samples in main context. Dispatch `Agent` with the full parameter shape:

- **subagent_type**: `"Explore"`
- **description**: one-line summary (e.g. `"Sample testing conventions in src/api"`)
- **prompt**: focused instruction asking the subagent to return ONLY a summary of naming patterns, import style, test placement, and 2–3 representative file paths — NOT raw file contents
- **max_turns**: set high enough that the subagent returns a complete summary in one turn (typically 4–8 depending on subsystem size; do not over-prescribe)
- **run_in_background**: `false` (you need the summary before drafting)
- Do NOT set `model` — inherit from the parent session

Use the returned summary to inform Phase 3 drafting. Do not re-load the raw files into main context.

See `references/rule-templates.md` for common rule types and scoping patterns.

## Phase 2b — Scope the Rules (Questionnaire)

After analyzing the project, narrow scope with **at most 3 questions**, tailored to the topic. Every question whose answer space is a fixed enumerable set MUST be asked via `AskUserQuestion` — do NOT ask these in prose. Only genuinely open-ended questions ("Is there a style guide or reference project I should match?", "Which directories are the focus?") may stay as plain text.

**Pattern — adapt to the topic, don't use the option labels verbatim. Substitute concrete labels drawn from the project analysis in Phase 2 (real directories, real frameworks).**

For the per-topic `AskUserQuestion` option sets (testing / code style / architecture), see [`references/questionnaire-patterns.md`](references/questionnaire-patterns.md).

**Rules for the questionnaire:**
- Maximum 3 questions total per session — more is interrogation.
- Questions must be plain language. No factor codes, no "frontmatter", no "mandate vs override."
- The 4-option cap on `AskUserQuestion` is binding. If a category has more than 4 candidates, pick the 4 most-likely-from-Phase-2 and rely on the harness's auto-injected "Other" escape for the rest.
- If the user gave a detailed initial request, skip the questionnaire entirely — they've already scoped it.
- The user's answers determine: which rules to draft, how strict they are, and which directories they apply to.

## Phase 3 — Design a Rule Set

Based on the user's request, project analysis, and questionnaire answers, design a **coherent set** of rules covering the topic from multiple angles.

### Step 1 — Draft the full set

Generate 3-8 rules that together cover the topic. Organize them into logical groups:

```
Based on the project analysis, here are [N] rules for [topic]:

**[Group 1 name]:**
1. "[Rule text]"
2. "[Rule text]"

**[Group 2 name]:**
3. "[Rule text]"
4. "[Rule text]"

**[Group 3 name]:**
5. "[Rule text]"

These would go in .claude/rules/[filename].md
[scoped to [pattern] if applicable].

Want me to adjust any of these, or should I score them?
```

Before presenting, apply the rule-writing checklist and full-set drafting guidance from [`references/writing-principles.md`](references/writing-principles.md): each rule must have a concrete trigger (WHEN), explicit action (WHAT), brief intent clause (WHY), exactly one interpretation, and self-contained ambiguity resolution; the set must cover different angles, mix structural / quality / process rules, draw concrete examples from the real project, and surface hook / linter alternatives when enforcement belongs there.

### Step 1 checkpoint — Review the draft set

After presenting the proposed rules, invoke `AskUserQuestion` with:

- **question**: `"Here are [N] rules for [topic]. What would you like to do?"` (substitute count and topic)
- **header**: `"Draft review"`
- **multiSelect**: `false`
- **options**:
  - `{ label: "Score them", description: "Check each rule for quality and flag any that need work" }`
  - `{ label: "Adjust", description: "Pick which rules to modify, add, or remove" }`
  - `{ label: "Start over", description: "Discard and return to the scope questionnaire" }`

If "Adjust", iterate until the user picks "Score them". Each re-present is a new decision point — fire `AskUserQuestion` again, not prose.

### Step 2 — Score the draft rules

Execute the scoring pipeline in this order:

1. Set up variables (`SCRIPTS`, `PYTHON_CMD`, `PYTHONIOENCODING`).
2. Write `.rulesense-tmp/draft_rules.json` via the `Write` tool.
3. Invoke `Bash` with `description: "Score draft rules mechanically"` to run `--score-draft`.
4. **Fragmentation pre-flight check** — if the `--score-draft` output JSON has `status: "needs_revision"`, the script detected rules that would fragment when written to markdown and re-extracted on the next audit. Do NOT present the fragmentation warnings to the user as scoring failures — they are a silent guardrail, not a quality judgment. Silently revise the flagged rules per [`references/writing-principles.md`](references/writing-principles.md) (the "Extractor self-check" section), overwrite `.rulesense-tmp/draft_rules.json` with the revised text, and re-run `--score-draft`. Repeat until `status == "ok"` (cap at 3 revision passes; if a rule still fragments after 3 passes, collapse it to its single most important directive). Only when the status is `ok` does the judgment phase begin.
5. Read the judgment prompt, score F3 and F8 per rule against the canonical rubrics at [`../assay/references/factor-rubrics.md`](../assay/references/factor-rubrics.md).
6. Write `.rulesense-tmp/draft_judgments.json` via a temp Python script (the `draft_` prefix prevents collision with the audit pipeline's `all_judgments.json` on the gap bridge).
7. Invoke `Bash` with `description: "Finalize draft scoring"` to run `--finalize-draft`.
8. Present the scored rules to the user with check-marks (pass) or warning signs (needs work), plus friendly problem descriptions and suggested fixes.

For the full command-line payloads, JSON/Python templates, rubric level boundaries, and the scoring-results presentation format, see [`references/scoring-mechanics.md`](references/scoring-mechanics.md).

### Step 3 checkpoint — Review scores

After presenting scoring results, invoke `AskUserQuestion`. The shape depends on whether any rules fell below the quality floor — pick ONE of the two branches below:

**Branch A — all rules passed:**

- **question**: `"All [N] rules passed. What next?"` (substitute the count)
- **header**: `"After score"`
- **multiSelect**: `false`
- **options**:
  - `{ label: "Write them", description: "Write the rule file(s) into .claude/rules/" }`
  - `{ label: "Adjust rules", description: "Edit the draft set, then re-score" }`
  - `{ label: "Skip scoring", description: "Write the rules as-is without further scoring" }`

**Branch B — some rules scored below the quality floor:**

- **question**: `"[N] drafts passed, [M] drafts need work. What next?"` (substitute both counts; the word "drafts" disambiguates this from the assay skill's Phase 3c question about pre-existing rules)
- **header**: `"After score"`
- **multiSelect**: `false`
- **options**:
  - `{ label: "Improve [M] drafts", description: "Suggest stronger rewrites for the [M] weak drafts, re-score, show before/after" }` (substitute [M])
  - `{ label: "Write them", description: "Write all drafts as-is; I'll flag which ones are weak" }`
  - `{ label: "Adjust drafts", description: "Edit the draft set, then re-score" }`
  - `{ label: "Skip scoring", description: "Write as-is without further scoring" }`

## Additional resources

Read on demand, not upfront. The workflow steps above are self-contained; these references add depth for specific phases.

- For common rule types, scoping patterns, and quality-annotated examples (Phase 2), see [`references/rule-templates.md`](references/rule-templates.md). The same file's "Advanced: High-stakes rule scaffold" section lists the 8 structural elements (severity marker, rationale, ±examples, bright-line threshold, precedence, self-check) for rules important enough to justify more tokens.
- For per-topic questionnaire option sets — testing, code style, architecture (Phase 2b), see [`references/questionnaire-patterns.md`](references/questionnaire-patterns.md).
- For rule-writing principles and `paths:` scoping guidance (Phase 3 Step 1), see [`references/writing-principles.md`](references/writing-principles.md).
- For scoring pipeline commands, JSON/Python templates, rubric level boundaries, and the scoring-results presentation format (Phase 3 Step 2), see [`references/scoring-mechanics.md`](references/scoring-mechanics.md).
- For the validation checklist, category floors, and structural checks for scored rules (Phase 3 Step 2), see [`references/quality-gates.md`](references/quality-gates.md).

## Phase 4 — Finalize and Write

After all rules pass the quality floor (or are accepted by the user):

1. **Determine file organization:**
   - If all rules share one scope -> one `.claude/rules/<topic>.md` file
   - If rules have different scopes -> multiple files, each with appropriate `paths:` frontmatter
   - If adding to an existing `.claude/rules/` file -> append to that file instead of creating a new one

2. **Write the files** using the Write tool. Each file gets:
   - YAML frontmatter with `paths:` (if scoped) and `default-category:` (if not mandate)
   - One rule per bullet (`- Rule text here`)
   - No factor codes, no scores — just clean rule text

3. **Report what was created:**

```
## Created

.claude/rules/<topic>.md — [N] rules, scoped to [pattern]
  Mean quality: A (0.84)
  All rules meet the quality bar

The project now has [N] total rules across [M] files.
```

### Phase 4 checkpoint — After writing

After writing the file(s), invoke `AskUserQuestion` with:

- **question**: `"Created [file] with [N] rules. What next?"` (substitute filename and count)
- **header**: `"Next step"`
- **multiSelect**: `false`
- **options**:
  - `{ label: "Run assay", description: "Run /rulesense:assay to see how new rules fit with existing ones" }`
  - `{ label: "More rules", description: "Start a new build session for another topic" }`
  - `{ label: "Done", description: "Finish and clean up" }`

4. **Clean up:**

Check whether `.rulesense-tmp/audit.json` exists (the audit-bridge marker from Phase 1 Step 1).

- **If `.rulesense-tmp/audit.json` exists** — build was invoked via the audit gap-bridge. Remove only draft-specific files; audit pipeline state (`scored_semi.json`, `all_judgments.json`, `audit.json`) must survive for the remaining audit phases. Invoke `Bash` with `description: "Remove draft-specific temp files"`:
  ```bash
  rm -f .rulesense-tmp/draft_*.json .rulesense-tmp/draft_*.md .rulesense-tmp/_draft_*.json .rulesense-tmp/draft_rules.json
  ```
- **If `.rulesense-tmp/audit.json` does not exist** — build was invoked standalone. Invoke `Bash` with `description: "Remove entire temp directory"`:
  ```bash
  rm -rf .rulesense-tmp
  ```
