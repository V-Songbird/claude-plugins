---
name: critic-review
description: Dispatches the `adversarial-critic` subagent (Opus, read-only) against the master plan currently in conversation context. The critic ground-truths the plan against the actual codebase, surfaces blocking issues / high-priority gaps / open questions, and returns a structured critique. Use as Step 5 of the forge workflow, immediately after `/forge:master-plan` produces the plan. The critique drives `/forge:plan-revise` in the next step.
user-invocable: false
allowed-tools: Read Grep Glob Task
color: red
---

# Critic Review Dispatch

Thin dispatcher that hands the master plan to the `adversarial-critic` subagent for ground-truth review against the codebase. The subagent is fixed-role (Opus, read-only, bounded `maxTurns`) and returns a structured critique the orchestrator consumes in `/plan-revise`.

## Required Inputs

- The master plan in conversation context (produced by `/forge:master-plan`).
- The original feature requirements as the user expressed them.
- Optional: any expert reports the plan was synthesized from (paste paths or references; the critic will load what it needs).

## Dispatch Template

MUST invoke `Agent` exactly once. Single dispatch — the critic must hold the entire plan to spot cross-cutting issues; parallel slicing breaks coherence.

```
Agent(
  description: "Adversarial critique of master plan against codebase",
  name: "adversarial critic",
  subagent_type: "adversarial-critic",
  run_in_background: false,
  prompt: """
## Master plan to critique
<full master plan, verbatim from conversation>

## Original feature requirements
<feature requirements as the user expressed them>

## Expert reports the plan was synthesized from
<inline paste OR reference to where in the conversation the reports live; if paths exist, list them>

## What you return
A single structured critique per the format defined in your system prompt (Blocking / High-priority / Open questions / What the plan got right / **Findings I couldn't ground in code** / Verdict rationale). Cite `file:line` on every issue. The "Findings I couldn't ground in code" section is mandatory: it lists hunches you formed but could not verify against actual files within the budget, so `/plan-revise` knows where to look first.
"""
)
```

The subagent's role, tool set, and `maxTurns` are encoded in `../../agents/adversarial-critic.md`; do not duplicate them in the prompt above.

## Critical Constraints

- **Single dispatch.** Splitting the critique across parallel critics produces siloed reports that miss cross-section issues. The critic needs the whole plan in one context.
- **Foreground only.** NEVER set `run_in_background: true`. The next step (`/forge:plan-revise`) consumes the critique immediately; backgrounding adds latency without benefit.
- **Pass the plan verbatim.** The critic reads the plan and the codebase. Paraphrasing the plan loses citations; loses citations loses critic effectiveness.
- **Do not pre-filter the plan.** Even if you suspect a section is fine, send it. The critic's value is independent verification — not confirming your suspicions.
- **Subagent prompts cannot use `AskUserQuestion`.** The critic's system prompt already instructs it to file ambiguities as open questions. Do not add an "ask the user if unsure" instruction to the dispatch prompt.

## Next Step

After the critic returns, invoke `/forge:plan-revise` to verify each critique and fold the verified ones back into the plan.
