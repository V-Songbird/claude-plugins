---
name: expert-analysis
description: Dispatches `forge-expert` subagents in parallel — one per chosen domain — to produce focused analyses of a feature against the codebase before a plan is drafted. Each expert covers one domain (architecture, performance, data/state, UI/UX, security, testing, build/tooling — pick from the role catalog) and returns a structured report citing `file:line` evidence. Use as Step 3 of the forge workflow, after the user has stated the feature and the orchestrator has gathered baseline codebase context. Do NOT auto-fire; always orchestrator-triggered to keep the workflow sequence intact.
user-invocable: false
color: yellow
---

# Expert Analysis Dispatch

Dispatch N domain experts in parallel via the `forge-expert` subagent. The agent's system prompt owns the role archetype, citation discipline, return format, and read-only constraints — this skill provides the per-dispatch parameters and orchestrates the parallel call.

## Required Inputs

- The feature requirements as the user expressed them (verbatim, not paraphrased).
- A short orchestrator summary of the codebase area the feature touches (≤ 10 bullet points or file paths).
- 3–5 anchor files (`path` or `path:line`) the experts should start from. Experts walk the code themselves; the anchor list seeds, it does not bound.
- The list of domains to cover, picked from `references/expert-roles.md`.

## Picking experts

Use as many experts as the feature genuinely needs, capped at **5**. The selection is driven by the Step-2 search — every distinct architectural concern surfaced by the search becomes one expert dispatch.

- **Cap: 5 experts.** Past 5, reports start to repeat each other and `/forge:master-plan` spends its budget reconciling overlap.
- **Merge near-duplicates.** If two domains' analyses would overlap by > 50% (e.g. both reasoning about the same dialog state machine), dispatch one combined expert with both lenses in the role line, not two separate experts.
- **Honor explicit user picks.** If the user names domains ("get a security review and a performance review"), dispatch exactly that list and skip the heuristic.

There is no hard floor and no narrow-feature gate. A focused single-expert dispatch is occasionally the right call (e.g. a pure performance question). The cap is the only structural constraint.

## Dispatch Template

MUST invoke `Agent` once per chosen domain, all calls in a single tool-use block so they run in parallel. For each dispatch:

```
Agent(
  description: "<Domain>: analyze <feature> against codebase",
  name: "<Domain> expert",
  subagent_type: "forge-expert",
  run_in_background: false,
  prompt: """
## Domain
<one of: architecture, performance, data-state, ui-ux, security, testing, build-tooling>

## Stack experience
<one-line addendum from references/expert-roles.md "Stack-specific role tuning" — leave empty if stack unknown>

## Feature
<verbatim feature requirements from user>

## Anchor files
- `path/to/anchor1.ext` — <one phrase: why this anchor>
- `path/to/anchor2.ext:42` — <…>
- ...
"""
)
```

The `forge-expert` agent's system prompt (in `forge/agents/forge-expert.md`) carries the role archetype, return format, citation discipline, and read-only constraints. The dispatch prompt only inlines the four sections above.

For the role catalog (which domains apply to which features, stack-specific tuning), see [references/expert-roles.md](references/expert-roles.md).

## Critical Constraints

- **Parallel, not sequential.** All `Agent` calls go in a single tool-use block. Sequential dispatch wastes wall-time and breaks the workflow timing assumptions of `/forge:master-plan`.
- **`subagent_type: "forge-expert"` on every dispatch.** The agent definition handles model, `maxTurns`, tools, and the canonical role / return-format / constraints.
- **Cap at 5.** This is the only quantity gate. No floor, no narrow-feature gate; let the Step-2 search drive the count.
- **Anchor, don't dump.** Inline 3–5 anchor files with one-phrase reasons, not a long context summary. The `file:line` citation discipline is what produces grounded output; prefatory context dumps just inflate the prompt.
- **Keep prompts self-contained.** The expert receives only what's in the `prompt` field; it cannot see the orchestrator's prior conversation. Inline the feature text and the anchor list verbatim.

## Next Step

After all experts return, invoke `/forge:master-plan` to synthesize their reports into a single implementation plan.

## Additional resources

- For the catalog of expert domains, role-pick guidance, and stack-specific role addenda, see [references/expert-roles.md](references/expert-roles.md)
