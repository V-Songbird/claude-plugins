---
name: patterns
description: When writing, modifying, or refactoring code in any language for any task, apply senior-authored patterns that reduce cognitive load for junior readers and AI agents — branded/nominal types for domain identifiers, discriminated unions over optional-field records, finite state machines over boolean tuples, pure functions for business logic separated from I/O, explicit validation boundaries, exhaustive matching over domain unions, sync-looking APIs over exposed async primitives, named call sites over boolean parameters, no silent catches, no raw console logs in business-logic code. Trigger on any code-writing, code-modifying, or feature-implementation task — no project setup, bootstrap, or convention infrastructure required. Adapt to the surrounding codebase's conventions first, then lean toward these patterns within the scope of the current change. Do not trigger when the user asks to audit a codebase, set up enforcement infrastructure (custom linters, architecture tests, build gates), bootstrap a project's conventions, or explicitly invokes the full Iceberg Convention framework — those tasks belong to the companion convention skill. This skill produces inline code that adapts to surroundings; it does not produce ADRs, PR templates, lint configs, or audit reports.
---

# Iceberg Patterns

## What this does

Bias toward senior-authored code patterns on any code-writing task so the output is easier for junior readers and AI agents to maintain. Produce inline code that leans these patterns; do not propose enforcement infrastructure, ADRs, or audit reports. For that, the companion `convention` skill runs in Audit/Bootstrap/Authoring modes.

## Step 0 — Detect surrounding conventions (MUST run before generating code)

Before applying any pattern below, MUST detect the surrounding conventions:

1. MUST invoke `Glob` with `pattern` resolved from the target file's parent directory and primary extension. Derive `<target-file-parent>` from the path of the file the user asked to write/modify; derive `<ext>` from the detected language. Example: target `src/features/auth/login.ts` in a TypeScript project → `pattern: "src/features/auth/**/*.{ts,tsx}"`. Python target → `pattern: "<parent>/**/*.py"`. Emit the resolved pattern in the tool call — NEVER pass literal angle brackets.
2. MUST invoke `Grep` in parallel for each detection probe — every call uses `output_mode: "count"`:

| Signal | `pattern` | Typical `glob` |
|---|---|---|
| Branded type (TS) | `__brand:` | `**/*.{ts,tsx}` |
| Sealed/union (Kotlin/Scala) | `sealed (class\|interface\|trait)` | `**/*.{kt,scala}` |
| Discriminated union (TS) | `\| \{ status:` | `**/*.{ts,tsx}` |
| FSM | `createMachine\|useReducer\|typestate` | (language-appropriate) |
| Raw-scalar domain signature | `function \w+\([a-z]\w*: string\b` | `**/*.{ts,tsx,js}` |

Every `Grep` call above MUST also pass `path` scoped to the target file's parent directory (or the nearest source root when writing a new file at the tree root). Omitting `path` causes an unscoped global search that silently inflates counts in large monorepos and breaks the density signal.

3. Emit a one-line density summary in your response text before writing code: *"Branded: N, Unions: M, FSMs: K, Raw-scalars: L."* False positives are acceptable — counts are density signals, not boolean decisions.

### Bias rule

- High density on senior-authored patterns → follow suit; these patterns are load-bearing.
- High density on raw-scalar / ad-hoc-state → match the surrounding idiom *within the scope of the current change*. Introducing one isolated branded type in a sea of raw strings creates inconsistency, not improvement. Return one prose line in your response text (no tool call required) naming the pattern opportunity and its scope; do NOT refactor uninvited.
- Mixed or low density → lean toward the patterns below.

The patterns are defaults, not mandates. They apply when the surrounding code doesn't contradict them.

### Scale escape

For a parent directory with > 2,000 source files of the target language, MUST invoke `Agent`:

```
Agent
  subagent_type:     "Explore"
  name:              "surroundings-scan"
  description:       "Iceberg surroundings density scan"
  prompt:            "<self-contained: file glob, language, every Grep pattern from the table above, return as a count summary line>"
  max_turns:         6
  run_in_background: false
  isolation:         "none"
```

`run_in_background: false` is load-bearing: the density-scan result gates subsequent code generation, and foreground subagents can be backgrounded mid-run (Ctrl+B). Explicitly setting `false` prevents the session from proceeding without the scan. `name` surfaces the scan in the user's agent panel with a readable label rather than an opaque id. `isolation: "none"` is correct because the scan is read-only — worktree isolation would waste disk and add latency with no benefit.

The prompt MUST be self-contained. Do NOT instruct the subagent to invoke `AskUserQuestion`.

## Handoff — when to yield to the `convention` skill

If the request shifts toward enforcement, audit, or bootstrap, STOP writing code. Tell the user: *"This is a `convention` skill task — I am invoking it now."* Then MUST invoke the `Skill` tool with `skill: "iceberg:convention"`. Do NOT attempt a slash-command route — the harness routes via the `Skill` tool.

## The patterns

### Types over raw scalars
Domain identifiers (`UserId`, `OrderId`, SKU, etc.), money amounts, durations, percentages, email/URL — use the language's nominal-type mechanism when available.

- **TS**: branded intersection types (`type UserId = string & { __brand: 'UserId' }`)
- **Rust**, **Kotlin**, **Scala**, **Swift**, **F#**: newtype structs / value classes
- **Python**: `typing.NewType` (check-time only via `mypy --strict` — runtime is indistinguishable; note the gap if it matters)
- **Go**: `type UserId string` (weaker — implicit convertible from untyped literals; flag it)
- **Untyped JS/Ruby/Python-without-mypy**: skip this pattern; use the next ones

**Why**: a junior reads `transfer(from: UserId, to: AccountId, amount: Money)` and the signature teaches the domain. `transfer(from: string, to: string, amount: number)` teaches nothing and will eventually be called with swapped arguments.

### Discriminated unions over optional-field records
For values whose shape is mutually exclusive across states (API fetch, form submit, auth, payment, any lifecycle):

Good:
```
type FetchState<T, E> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success', data: T }
  | { status: 'failure', error: E }
```

Bad:
```
{ loading?: bool, error?: Error, data?: T, hasRetried?: bool }
```

**Why**: the record represents 16 combinations; most are impossible, and a junior will write code defending against them forever.

### Finite state machines over boolean tuples
When two or more booleans derive from the same underlying process (`isLoading + isPending + isSuccess + isCancelled`), that's an unadmitted FSM. Prefer a single `status` discriminator with a pure reducer `(state, event) -> state`, or the idiomatic FSM library for the target ecosystem (XState for TS/React, typestate pattern for Rust, `transitions` for Python, Redux/Zustand with a status field, etc.).

Enumerate all states up front: `idle`, `in_flight`, `success`, `recoverable_failure`, `terminal_failure`, `cancelled`. **Cancellation is a state, not an afterthought.** If you skip it, a junior's test won't cover it.

### Pure functions for business logic
Keep decisions (pricing, validation, formatting, routing, business rules) in pure functions; wrap them in a thin shell that handles I/O, time, randomness, and logging. If the user asks for a small feature, put the business decision in a pure function even when the surrounding shell is messy.

**Why**: pure functions are trivially testable and readable. A junior can read one function and understand the rule. An imperative controller scattered across I/O calls hides the rule.

### Single validation boundary for branded types
Any cast from a raw primitive into a branded/nominal type goes through a single named constructor (`createUserId(raw): UserId | ValidationError`). Direct coercion (`raw as UserId`, `UserId(raw)`, `unsafeCoerce`) in business-logic code is a smell — the junior sees the cast and wonders whether validation happened.

### Exhaustive matching over domain unions
When matching on a discriminated union / sum type, include a compile-fail sink for unhandled variants.

- **TS**: `default: return assertNever(state)` with `function assertNever(x: never): never { throw new Error(...) }`
- **Rust**, **Kotlin sealed `when`**, **Scala**, **Swift**, **OCaml**, **Haskell**, **F#**: native exhaustiveness — the compiler errors on missing arms
- **Python 3.11+**: `case _: typing.assert_never(state)` in a `match`

**Why**: adding a new variant upstream should break every consumer loudly. A silent `default` clause is a state-handling bug waiting to happen.

### Named call sites over boolean parameters
`doThingEagerly()` / `doThingLazily()` beat `doThing(true)` / `doThing(false)`. A bare boolean at a call site is a puzzle the junior has to resolve by reading the function signature. Split into two functions, use an enum, or accept a string literal union.

### Silent catches are forbidden
`catch (e) { }` and `catch (e) { log(e) }` without rethrowing, translating to a domain error, or transitioning a state machine are silent failure modes. Juniors read the call site and assume nothing can fail. Either:
- Rethrow (after logging)
- Translate to a typed domain error (`throw new PaymentFailedError({ cause: e })`)
- Transition an FSM state (`dispatch({ type: 'failed', error: e })`)

### Sync-looking APIs when the framework permits
Don't expose raw async primitives (futures, promises, observables, tasks, channels) in the signatures of business-logic functions unless the call site can't avoid it. Wrap them in framework-provided primitives that hide the `await` ceremony — React Server Components returning `Promise<JSX>`, server actions, Suspense-boundary hooks, structured concurrency blocks, `GenServer.call`, etc. Frameworks that have no such primitive (raw tokio in Rust, raw goroutines in Go) are exceptions — be honest.

### No raw console/print in business-logic code
`console.log`, `println!`, `print()` in tip-layer code is junior-authored tracing. Use the project's structured logger or omit the log. For debugging sessions, `console.log` is fine; for code that ships, it's not.

### Observability wrapped at the adapter
If you're writing an HTTP client, DB client, cache client, or queue publisher, wrap tracing/logging at the adapter construction (e.g., a decorator, middleware, or `tracing::instrument` attribute), not at call sites. Juniors get observability for free without having to remember to add it.

## What this skill does NOT do

- Does not generate ADRs, CLAUDE.md fragments, PR templates, or architecture documents.
- Does not propose enforcement tooling (custom linters, arch tests, cargo-deny rules, architectural CI gates). That's the `convention` skill.
- Does not audit an existing codebase for violations of these patterns. That's also the `convention` skill (Audit mode).
- Does not override the user's explicit choice. If the user says "just use a boolean, don't overengineer it," respect that.
- Does not introduce these patterns against the grain of the surrounding code. If the repo's idiom is different, match the idiom and mention the opportunity once.

## When to defer to `convention` instead

Defer when the user's task is about the *framework*, not the code:

- "Audit / review / check this codebase for architectural issues" → convention Audit
- "Set up / bootstrap / configure conventions or CI gates" → convention Bootstrap
- User explicitly names the convention, airgap, five pillars, Axiom of Enforcement, or Compiler-Driven Mentorship → convention
- User asks for enforcement tooling (custom lint rule, arch test, type scaffolding) rather than a feature → convention Authoring

In those cases, do NOT engage — MUST invoke the `Skill` tool with `skill: "iceberg:convention"` and let that skill run.

## Scope reminder

Your output on an `patterns` task is **code that fits where the user asked for it**. A table component stays a table component. A util function stays a util function. The patterns above bias the internal structure of what you write; they do not grow the scope into an architectural document.

## Additional resources

- For the companion skill that handles audit, bootstrap, and authoring modes, invoke `Skill` with `skill: "iceberg:convention"` — cross-skill dispatch only; no reference file in this skill.
