# Example: a strong SKILL.md

The hypothetical below is `pr-review-runner` — a skill that drives a structured PR review pass against the current branch. It is non-trivial enough to exercise every UX-shaping tool in scribe's checklist: it asks the user to scope the review (`AskUserQuestion`), tracks a multi-step pipeline (`TodoWrite`), runs lint/test commands (`Bash` with descriptions), dispatches a subagent to enumerate touched files (`Agent`), and gates the synthesized findings through plan mode (`EnterPlanMode` / `ExitPlanMode`). Notice how every tool name appears literally adjacent to its trigger, every schema is filled in, and the prose uses directive verbs (`MUST invoke`, `ALWAYS mark`, `NEVER batch`).

## The strong example

````markdown
---
name: pr-review-runner
description: Use when the user asks for a PR review, code review, branch review, or pre-merge sweep against the current branch. Drives a fixed pipeline — scope confirmation, file enumeration, parallel reading, lint/typecheck/test verification, and a gated findings report — so the reviewer never skips steps and every clarification, progress update, shell call, and subagent dispatch fires through the correct tool with full UX-shaping parameters.
allowed-tools: Read Grep Glob Edit Bash(git *) Bash(npm run lint) Bash(npm run typecheck) Bash(npm test) TodoWrite AskUserQuestion Agent EnterPlanMode ExitPlanMode
---

# PR Review Runner

## When this skill applies

- The user asks for "a PR review", "code review", "review the branch", or "pre-merge check"
- A pull request URL or branch name appears in the prompt with intent to assess
- The current git branch has uncommitted or unmerged changes the user wants critiqued

## When this skill does not apply

- The user asks for help authoring code (use the implementation skill)
- The user asks for a security audit specifically (use `security-review`)
- The branch has zero diff against `main` — return early with a note instead of running the pipeline

## Workflow

### Step 1 — Build the pipeline

ALWAYS invoke `TodoWrite` first with these six todos in order:

```
Invoke TodoWrite with:
  todos: [
    { content: "Confirm review scope with user",          activeForm: "Confirming review scope with user",          status: "pending" },
    { content: "Enumerate changed files via subagent",    activeForm: "Enumerating changed files via subagent",     status: "pending" },
    { content: "Read each changed file and note issues",  activeForm: "Reading changed files and noting issues",    status: "pending" },
    { content: "Run lint, typecheck, and tests",          activeForm: "Running lint, typecheck, and tests",         status: "pending" },
    { content: "Draft and gate findings via plan mode",   activeForm: "Drafting and gating findings via plan mode", status: "pending" },
    { content: "Deliver findings to user",                activeForm: "Delivering findings to user",                status: "pending" }
  ]
```

NEVER skip the `activeForm` field. NEVER batch status updates — mark each todo `in_progress` immediately before starting it and `completed` immediately on finish via a follow-up `TodoWrite` call.

### Step 2 — Confirm scope

Mark the first todo `in_progress` via `TodoWrite`. Then MUST invoke `AskUserQuestion` exactly once:

```
Invoke AskUserQuestion with:
  questions: [{
    question: "What depth of review should I run on this branch?",
    header: "Depth",
    multiSelect: false,
    options: [
      { label: "Smoke",       description: "Lint + types + obvious bugs only; ~2 min." },
      { label: "Standard",    description: "Smoke plus design, naming, test coverage; ~10 min." },
      { label: "Deep",        description: "Standard plus architecture, perf, edge cases; ~30 min." },
      { label: "You decide",  description: "Pick based on diff size and risk." }
    ]
  }]
```

Mark the todo `completed` via `TodoWrite`.

### Step 3 — Enumerate changed files via subagent

Mark the second todo `in_progress` via `TodoWrite`. The diff may touch many files; enumerating them inline bloats main context. MUST dispatch `Agent`:

```
Invoke Agent with:
  subagent_type: "general-purpose"
  description: "Enumerating changed files for PR review"
  name: "pr-file-scout"
  prompt: "Run `git diff --name-status main...HEAD`. For each path, return one line: '<status> <path> — <≤15-word role summary>'. Group by top-level directory. Do NOT read file contents; names and roles only."
  model: "sonnet"
  max_turns: 4
  run_in_background: false
```

Background subagents fail silently on `AskUserQuestion`; foreground subagents pass it through but can be backgrounded mid-run (Ctrl+B) and then start failing silently too. So the depth choice from Step 2 MUST already be resolved before this dispatch — never rely on clarification from inside the subagent. Mark the todo `completed` on return.

### Step 4 — Read changed files

Mark the third todo `in_progress` via `TodoWrite`. For each path returned by the subagent, invoke `Read` with the absolute path. For files over 1,000 lines, instruct `Read` with `offset` and `limit` covering only diff hunks (derive hunk ranges from `git diff --unified=0`). Note issues in working memory, grouped by file.

Mark the todo `completed` via `TodoWrite`.

### Step 5 — Run verification commands

Mark the fourth todo `in_progress` via `TodoWrite`. MUST invoke `Bash` three times in sequence:

```
Invoke Bash with: { command: "npm run lint",      description: "Linting the changed code",     timeout: 90000 }
Invoke Bash with: { command: "npm run typecheck", description: "Type-checking the project",    timeout: 120000 }
Invoke Bash with: { command: "npm test",          description: "Running the Jest test suite",  timeout: 300000 }
```

Capture failures verbatim. Do NOT abort on the first failure — record all three results so the findings cover the full picture.

Mark the todo `completed` via `TodoWrite`.

### Step 6 — Draft and gate findings

Mark the fifth todo `in_progress` via `TodoWrite`. MUST invoke `EnterPlanMode` with `{}`. Inside plan mode, draft the findings report with these sections in order: Summary · Blocking Issues · Recommended Changes · Questions for Author · Verification Results.

Then MUST invoke `ExitPlanMode`. Do NOT supply `allowedPrompts` here — by this stage all required `Bash` commands have already run; pre-authorizing more would only enable post-approval execution that this skill does not perform.

Mark the todo `completed` via `TodoWrite` once the user approves the plan.

### Step 7 — Deliver

Mark the sixth todo `in_progress` via `TodoWrite`. Render the approved findings as a single message addressed to the user. Mark the todo `completed`.

## Pre-completion check

Before returning control to the user, verify:

1. All six todos are `completed` via the most recent `TodoWrite` snapshot.
2. The `AskUserQuestion` from Step 2 fired exactly once and the chosen depth is reflected in the report's depth band.
3. All three `Bash` verification commands ran and their results appear in the Verification Results section, including failures.
4. The findings report passed through `EnterPlanMode` / `ExitPlanMode` and the user approved.
5. No subagent attempted `AskUserQuestion` — every clarification went through the main session before dispatch.

## Scope reminder

This skill drives the review pipeline only — it never modifies code, never pushes branches, and never opens or closes the PR.
````

## What to notice

1. **AskUserQuestion shape (checklist item 1).** Step 2 names `AskUserQuestion` literally with `question`, `header: "Depth"` (≤12 chars), `multiSelect: false`, and four `options`, each with `label` + `description`. The terminal `You decide` option is included — a scribe convention for multi-choice prompts.
2. **TodoWrite pairing (checklist item 2).** Step 1 lists every todo with both `content` (imperative) and `activeForm` (progressive); the surrounding prose explicitly forbids batching status updates and requires `in_progress`/`completed` transitions via follow-up `TodoWrite` calls.
3. **Bash with description (checklist item 3).** Step 5 invokes `Bash` three times, each with `command`, `description`, and `timeout`. No bare `Bash` calls anywhere.
4. **Agent parameters (checklist item 4).** Step 3 names `Agent` with `subagent_type`, `description`, `name` (user-facing scout label), `prompt`, `model: "sonnet"`, `max_turns: 4`, and `run_in_background: false`. The prose calls out the subagent's `AskUserQuestion` limitation.
5. **Plan-mode gates (checklist item 5).** Step 6 uses both `EnterPlanMode` (with `{}` since it takes no parameters) and `ExitPlanMode`, with an explicit justification for omitting `allowedPrompts`.
6. **Subagent ambiguity resolution (checklist item 6).** Scope confirmation in Step 2 happens before the `Agent` dispatch in Step 3, and Step 3 states the constraint inline so a future maintainer cannot accidentally reorder.
7. **Literal tool names with directive verbs (checklist item 7).** Every tool name appears literally next to its trigger — `MUST invoke AskUserQuestion`, `ALWAYS invoke TodoWrite`, `MUST dispatch Agent`, `MUST invoke Bash`, `MUST invoke EnterPlanMode`. No weasel verbs (`should consider`, `may want to`) anywhere in the example.
