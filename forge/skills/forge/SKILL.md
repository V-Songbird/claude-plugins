---
name: forge
description: Reference for the forge robust-development workflow. Loads when the user requests a non-trivial feature — particularly when they say "use forge", "review this design before I build it", or describe a change that crosses architectural boundaries. The 10-step pipeline is parallel domain experts → master plan → adversarial critic → user approval → parallel implementation → build + report. Heavy-by-design; the parallel agents are also a token-cost lever (the dispatching session never reads the full expert / implementer transcripts). Loads alongside the action skills it references — the action skills do the dispatch, this reference tells Claude when and in what order to invoke them.
model: opus
effort: high
color: green
---

# Forge: robust-development workflow

Forge is a 10-step pipeline that produces robust, code-grounded feature implementations. The value comes from the gates: parallel domain experts surface cross-domain conflicts; the adversarial critic ground-truths the plan against the actual code; the user-approval step gives the human the chance to redirect before any edit happens; parallel implementers in isolated worktrees finish the work without stepping on each other.

The workflow is heavy by design. Dispatching parallel agents (instead of doing all the analysis in the main session) is also the token-cost lever — the main session never reads the full expert or implementer transcripts, only their structured reports.

## When to enter the workflow

Enter forge when ANY hold:

- The feature crosses ≥ 2 architectural areas (UI + persistence; service + worker; etc.).
- The feature touches a hot path or trust boundary (UI render loop, request handler, auth, parser).
- The user says "review this design", "use forge for this", or similar.

For trivial localized changes (typo, single-method bug fix, copy edit), do NOT use forge — direct edit is appropriate.

## The 10 steps

| #  | Action                                                                       | Model                | Skill                       |
|----|------------------------------------------------------------------------------|----------------------|-----------------------------|
| 1  | Understand and identify the feature requirements and intention               | inherit              | —                           |
| 2  | Quick search for essential structural codebase knowledge                     | inherit              | —                           |
| 2.5| Reality-check spike against the riskiest assumption (≤ 30 lines)             | inherit              | —                           |
| 3  | Dispatch domain experts in parallel                                          | sonnet               | `/forge:expert-analysis`    |
| 4  | Consolidate expert reports into a master implementation plan                 | opus (effort high)   | `/forge:master-plan`        |
| 5  | Dispatch the adversarial critic against the master plan                      | opus                 | `/forge:critic-review`      |
| 6  | Verify each critique; fold verified findings back into the plan              | opus (effort high)   | `/forge:plan-revise`        |
| 7  | Present the revised plan to the user; wait for approval                      | inherit              | —                           |
| 8  | Implement the plan (parallel-first when ≥ 2 disjoint steps; in-session else) | sonnet (per worker)  | `/forge:dispatch-implementation` |
| 9  | Bump version (per consuming project's convention) and run the project build  | sonnet               | `/forge:build-and-report`   |
| 10 | Deliver the final implementation report                                      | sonnet               | `/forge:build-and-report`   |

Steps 1, 2, 2.5, 7 run in the main session with no skill — they are orchestrator actions. Steps 9 and 10 are produced by a single skill (`/forge:build-and-report`) in one pass. Step 8 runs `/forge:dispatch-implementation` when the plan has ≥ 2 disjoint steps; otherwise the orchestrator implements directly in-session.

## Step 2.5 — Reality-check spike

Before dispatching experts, run a ≤ 30-line spike against the single riskiest assumption — whichever claim, if false, would invalidate the whole design. Examples: "does this metric actually separate the cases in real data?", "does this API return the shape we assumed?", "does the existing parser already emit the event we want to subscribe to?".

If the spike refutes the assumption, STOP — surface the refutation to the user with `file:line` evidence and ask for a corrected scope before continuing. Do NOT silently re-scope.

Skip Step 2.5 only when the feature has no risky assumption (pure refactor, well-trodden CRUD, well-covered by existing patterns).

## Step 7 — Approval gate

Once the plan is revised, MUST invoke `AskUserQuestion`:

```
AskUserQuestion(questions: [{
  question: "The revised plan is ready. Do you approve implementation?",
  header: "Approval",
  multiSelect: false,
  options: [
    { label: "Approve",   description: "Proceed to implementation. Parallel implementers if the plan has ≥ 2 disjoint steps; in-session otherwise." },
    { label: "Revise",    description: "Tell me what to change; I'll update the plan before implementing." },
    { label: "Cancel",    description: "Abort the forge run at this point." }
  ]
}])
```

No risk tiers. No diff preview. The user reads the plan above the prompt and either approves, asks for a revision, or cancels.

## After approval (Step 8)

Default mode is **parallel-first**: invoke `/forge:dispatch-implementation` whenever the plan has ≥ 2 steps marked `Parallel-friendly: yes` (the annotation guarantees disjoint Files-touched sets and no ordering dependency). One `forge-implementer` subagent per qualifying step, each in `isolation: "worktree"`, all dispatched in a single tool-use block.

Fall back to in-session implementation when the plan has < 2 disjoint parallel-friendly steps. In that case the orchestrator writes the code directly; the coordination overhead of parallel dispatch does not pay for itself on a single coherent edit.

## Build and report (Steps 9 and 10)

After implementation lands, invoke `/forge:build-and-report`. The skill bumps the version per the consuming project's convention (read from the project's CLAUDE.md), runs the project's build / verification commands, and emits the final report with the two mandatory sections "How to test this feature" and "How is this feature useful?".

The forge plugin is stack-agnostic; the actual version-bump file (`plugin.xml`, `package.json`, `Cargo.toml`, `pyproject.toml`, etc.) and build command (`./gradlew buildPlugin`, `npm run build`, `cargo build`, `pytest`) are the consuming project's responsibility to declare in its own CLAUDE.md.

## Workflow principles

- **Citations required.** Experts, critic, plan — every claim cites `file:line`. Summaries without citations break verification chains.
- **Single canonical plan in conversation.** `/forge:plan-revise` rewrites in place; the conversation never holds v1 + v2 + v3 simultaneously.
- **Foreground subagents.** Every `Agent` dispatch in this workflow is `run_in_background: false`. The next step needs the prior step's output.
- **No persistent state files.** The plan, critique, and expert reports live in conversation context. The workflow does not write `.claude/plans/*.md` or similar.
- **User approval is non-negotiable.** Step 7 is the gate. The orchestrator never silently proceeds to writing code.
- **`TaskCreate` per work unit before dispatch.** When `/forge:dispatch-implementation` runs, MUST invoke `TaskCreate` for each work unit (paired `content` + `activeForm`) before the parallel `Agent` calls — the dispatch skill's body specifies the exact wording.

## Re-running a single phase

The action skills are independently invocable for re-runs:

- Bad expert coverage → re-run `/forge:expert-analysis` with a different role list.
- Plan needs revision after the user pushed back → re-run `/forge:plan-revise`. Re-dispatch the critic only if the change is structural.
- One dispatched implementer blocked → re-run `/forge:dispatch-implementation 2` (just unit W2) after revising the plan.
- Build broke after a tangential change → re-run `/forge:build-and-report`.

Each action skill is `user-invocable: false` — only the orchestrator (Claude) invokes them, at the right step in the pipeline. They are deliberately hidden from the slash-command menu so the workflow runs as a single coherent pipeline driven by this reference. Do not auto-fire skills out of sequence: the workflow's value comes from the gates between steps, and skipping ahead defeats them.
