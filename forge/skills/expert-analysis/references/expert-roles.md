# Expert role catalog

The `/expert-analysis` skill dispatches one `forge-expert` subagent per chosen domain (Sonnet, read-only, bounded `maxTurns`). This file is the orchestrator's selection catalog: which domains apply to which features, and the stack-specific addendum to pass when the orchestrator knows the consuming project's stack.

The role archetype itself ("you are a senior X engineer who finds the integration points first…"), the citation discipline, the return-format template, and the read-only constraints all live in `forge/agents/forge-expert.md`. The orchestrator only passes the **domain key** (e.g. `performance`) and an optional **stack-experience addendum** in the dispatch prompt — see the `/expert-analysis` Dispatch Template. The role lines below are kept as orchestrator-facing reference for what each expert covers; they are NOT spliced into the dispatch prompt anymore.

## How to pick which experts to dispatch

For any feature, ask three questions:

1. **What's the architectural shape?** Cross-cutting (touches many layers) → architecture is mandatory. Localized → architecture optional.
2. **What's the primary risk axis?** UI responsiveness / large data → performance. Auth / data exposure / external input → security. Persistence / migration → data/state. Visual or interaction-heavy → UI/UX.
3. **What's the validation surface?** Behavior-changing → testing expert is worthwhile. Pure refactor → skip testing expert.

**Pick as many experts as the Step-2 search genuinely surfaced, capped at 5.** Every distinct architectural concern from the search becomes one expert dispatch. There is no hard floor — a focused single-expert dispatch is occasionally the right call.

**Merge near-duplicates:** if two domains' analyses would overlap by > 50% (e.g. data-lifecycle and UI/UX both reasoning about the same dialog state machine), dispatch one combined expert with both lenses in the role line, not two separate experts.

If the user explicitly names domains ("get a security review and a performance review"), honor that list and skip the picking heuristic.

## Domain catalog

Each entry lists the role name and when to dispatch it. The role archetype text below is orchestrator-facing reference for what each expert covers — it is NOT spliced into the dispatch prompt. The archetype itself lives in `forge/agents/forge-expert.md`; the orchestrator passes only the **domain key** (e.g. `performance`) and the optional **stack-experience addendum** in the dispatch prompt — see the `/expert-analysis` Dispatch Template.

### Architecture (almost always)

When to pick: any feature that adds new modules, integrations, or cross-cutting concerns. Skip only for trivial localized changes (single-method bug fix).

Role line:
> **You are a senior software architect** with deep experience integrating new features into mature codebases. You don't accept "we'll figure it out" — you find the precise integration points first. You map the change against the codebase's existing layering, dependency direction, and ownership boundaries before recommending where new code lives.

### Performance

When to pick: feature touches a hot path (UI render loop, request handler, batch processor, large-dataset operation), introduces background work, or changes data volumes.

Role line:
> **You are a senior performance engineer** with experience in UI responsiveness, batch processing, and memory profiling. You don't accept "this should be fast enough" — you identify the specific allocation, lock, I/O, or layout invalidation that will degrade under realistic load, with `file:line` evidence.

### Data / State

When to pick: feature changes persistence shape, introduces migrations, alters state machines, or affects shared mutable state.

Role line:
> **You are a senior data / state engineer** with experience in schema evolution, state-machine design, and concurrency. You don't accept "we'll add a column" — you map the migration path, the rollback path, and every place the existing shape is read or written before approving the change.

### UI / UX

When to pick: feature is visible to end-users — new dialog, new control, new gesture, new keyboard binding, layout change, accessibility-relevant change.

Role line:
> **You are a senior UI / UX engineer** with experience in interaction design, accessibility, and platform conventions. You don't accept "we'll iterate on the design later" — you flag the keyboard-trap, the screen-reader gap, the convention break, and the discoverability problem before code is written.

### Security

When to pick: feature crosses a trust boundary (user input → execution, external network → parser, untrusted file → memory), handles credentials / tokens / PII, or changes permission checks.

Role line:
> **You are a senior security engineer** with experience in threat modeling, input validation, and secret handling. You don't accept "the input comes from our own UI" — you find every untrusted source, every authority check, and every place trust is assumed without verification.

### Testing

When to pick: feature is behavior-changing AND the area has existing tests (so a testing expert can recommend additions). Skip when adding tests is part of a separate step or the area is untested by design.

Role line:
> **You are a senior test engineer** with experience in unit, integration, and end-to-end test design. You don't accept "we'll add tests after" — you identify the specific behaviors that need fixtures, the seams that make the new code testable, and the regression points existing tests already cover.

### Build / Tooling

When to pick: feature changes the build pipeline, packaging, dependencies, or CI/CD. Rare; usually only for plumbing-level changes.

Role line:
> **You are a senior build / tooling engineer** with experience in package management, build pipelines, and release engineering. You don't accept "it builds on my machine" — you trace the dependency graph, the artifact path, and the version-bump implications before approving.

## Stack-specific role tuning

The role lines above are stack-agnostic. When the orchestrator knows the stack, sharpen the role line:

| Stack | Architecture line addendum |
|---|---|
| .NET / WPF | "with deep experience integrating new tools into mature WPF applications" |
| JetBrains plugin | "with deep experience extending IntelliJ Platform plugins" |
| React / TypeScript | "with deep experience evolving large React codebases" |
| Node.js backend | "with deep experience operating large Node.js services" |
| Python / FastAPI | "with deep experience scaling Python service codebases" |

The orchestrator splices the addendum into the `<STACK / DOMAIN-SPECIFIC EXPERIENCE>` slot in `/expert-analysis`'s template. If the stack is unknown, leave the slot empty rather than guessing.
