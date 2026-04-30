---
name: dispatch-implementation
description: Step 8 of the forge workflow when the approved plan has ≥ 2 steps marked `Parallel-friendly: yes`. Dispatches one `forge-implementer` subagent per such step, each in an isolated git worktree, so they can write code in parallel without stepping on each other. Each implementer receives only its assigned step (the "work unit") + the integration contract; the implementer constraints are baked into the `forge-implementer` agent's system prompt. MUST invoke `TaskCreate` for each work unit (paired `content` + `activeForm`) before the parallel `Agent` calls. Returns a per-unit completion report; the orchestrator aggregates and hands off to `/forge:build-and-report`. For plans with fewer than 2 disjoint steps, the orchestrator implements directly in the main session — coordination overhead beats wall-time savings.
user-invocable: false
argument-hint: [step W-ID number, or "all" — default "all"]
model: sonnet
effort: medium
color: green
---

# Dispatch Implementation

Step 8 helper for plans with ≥ 2 steps marked `Parallel-friendly: yes`. Dispatches one `forge-implementer` subagent per qualifying step, each in `isolation: "worktree"`. Once a step is assigned to a parallel implementer, this skill (and the `forge-implementer` subagent) refers to it as the implementer's "work unit". Worktree isolation is the safety net: implementers cannot see or stomp on each other's edits, the orchestrator gets per-unit branches/diffs, and the user's main worktree stays clean until merge.

If the plan has fewer than 2 parallel-friendly steps, do NOT use this skill. Implement in the main session — the parallelism does not pay for itself once you account for orchestrator-side dispatch + merge overhead. The forge skill's "After approval" section spells out the routing.

## Required Inputs

- The approved revised master plan in conversation context (from `/forge:plan-revise`, with user approval at Step 7).
- The list of `Parallel-friendly: yes` steps from the plan. If invoked with `all` (default), dispatch every qualifying step in parallel; if invoked with a specific W-ID (e.g. `2` for W2), dispatch only that one (used for re-runs of a failed step).

## Pre-dispatch — TaskCreate per work unit

Before the parallel `Agent` calls, MUST invoke `TaskCreate` once per work unit being dispatched. Pair `content` + `activeForm` per the workflow standard:

```
TaskCreate(
  content: "Implement step W<N>: <step title>",
  activeForm: "Implementing step W<N>: <step title>"
)
```

The task list is what the user reads while the parallel implementers run. One row per work unit, in W-ID order.

After all `TaskCreate` calls land, mark every work-unit task `in_progress` via `TaskUpdate` in a single tool-use block, then fire all `Agent` calls in the next single tool-use block. Do NOT interleave per-unit `TaskUpdate` calls with `Agent` calls — every task must be `in_progress` before any implementer dispatches.

## Dispatch Template

For each qualifying step being dispatched, MUST invoke `Agent` in a single tool-use block (parallel execution):

```
Agent(
  description: "Implement step W<N>: <step title>",
  name: "Implementer W<N>",
  subagent_type: "forge-implementer",
  model: "sonnet",         # mirrors forge-implementer.md frontmatter; explicit so the dispatch is self-documenting
  max_turns: 30,           # mirrors forge-implementer.md maxTurns; explicit so the dispatch is self-documenting
  run_in_background: false,
  isolation: "worktree",
  prompt: """
## Your work unit (plan step W<N>)
<full step block from the plan: title, files touched, description (with inline contract-clause references like "fulfills C1, C3"), done-when criterion, Parallel-friendly: yes annotation>

## Integration contract (your unit fulfills only the clauses cited in your description, but you MUST not violate other clauses)
<full integration contract appendix from the plan — appears only when ≥ 2 disjoint steps exist, which is the precondition for this skill running>
"""
)
```

The `forge-implementer` agent's system prompt (in `forge/agents/forge-implementer.md`) carries the full constraints — files-touched discipline, contract honoring, citation discipline, blocker escalation, single-commit rule, return format. The dispatch prompt only inlines the per-step content.

## Critical Constraints

- **`isolation: "worktree"` on every dispatch.** Without it, parallel implementers race on the same files. The worktree gives each its own filesystem view + branch.
- **`subagent_type: "forge-implementer"` on every dispatch.**
- **All dispatches in one tool-use block.** Sequential dispatch defeats the parallelism the worktree isolation enables.
- **`TaskCreate` before `Agent`.** The user reads the task list while implementers run; one row per work unit.
- **NEVER instruct implementers to call `AskUserQuestion`.** Subagents cannot reliably use it (background mode fails silently). Implementers escalate blockers in their report; the orchestrator handles user interaction.
- **NEVER tell implementers to merge their worktrees.** The orchestrator merges after aggregation, in `/forge:build-and-report`.

## Handling implementer reports

When implementers return:

- **Hard blockers (non-empty Blockers section)** — STOP. The orchestrator decides between revise-plan-and-redispatch, reassign-unit, or accept-with-evidence. Do not proceed to merge with an unresolved hard blocker. MUST invoke `TaskUpdate` to keep the task `in_progress` (with an updated `activeForm` describing the blocker) until the user decides.
- **Done-when criterion: no / partial-because** — same treatment as a hard blocker.
- **All units returned clean** — MUST invoke `TaskUpdate` to mark each work-unit task `completed`. Then proceed to `/forge:build-and-report`.

## Next Step

After all implementers return clean, invoke `/forge:build-and-report` to merge worktrees, run the project's build, and emit the final report.
