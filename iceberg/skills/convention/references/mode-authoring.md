# Mode: Authoring

You are writing new code, modifying existing code, or implementing a feature in a codebase that follows (or should follow) the Iceberg Convention. This file is the procedure.

## Workflow opener — MUST invoke `TodoWrite`

On entering Authoring mode, MUST invoke `TodoWrite`:

```
TodoWrite
  todos: [
    { content: "Detect language and stack",              activeForm: "Detecting language and stack",              status: "pending" },
    { content: "Establish tip/berg layer context",       activeForm: "Establishing tip/berg layer context",       status: "pending" },
    { content: "Classify the change",                    activeForm: "Classifying the change",                    status: "pending" },
    { content: "Apply the rules while generating",       activeForm: "Applying the rules while generating",       status: "pending" },
    { content: "Run the 8-question design-review self-check", activeForm: "Running design-review self-check",     status: "pending" },
    { content: "Generate enforcement for new invariants", activeForm: "Generating enforcement for new invariants", status: "pending" },
    { content: "Produce the structured output",          activeForm: "Producing the structured output",           status: "pending" }
  ]
```

MUST invoke `TodoWrite` to update the list: mark the current item `in_progress` at step entry and `completed` at step exit — NEVER batch status updates.

**Foreground-only gate:** this procedure invokes `AskUserQuestion` in Steps 1 and (potentially) 4. The consuming session MUST be running in foreground — NEVER enter Authoring mode from an `Agent` dispatch set with `run_in_background: true`. If an upstream session needs to delegate code generation, it MUST resolve layer and scope ambiguity in its OWN session first, then pass the resolved context in the subagent prompt.

## Step 0 — Detect the language and stack

Before anything else, identify the target language from the repo. Read whichever manifest files exist:

- `package.json` → JavaScript/TypeScript
- `pom.xml`, `build.gradle`, `build.gradle.kts` → JVM (Java/Kotlin/Scala)
- `*.csproj`, `*.fsproj` → .NET
- `Cargo.toml` → Rust
- `pyproject.toml`, `requirements.txt`, `setup.py` → Python
- `go.mod` → Go
- `Gemfile` → Ruby
- `mix.exs` → Elixir
- `composer.json` → PHP
- `Package.swift` → Swift

In multi-language monorepos, the language of the file you are about to write or modify is what matters — not the repo's dominant language.

Once identified, you will translate each convention rule into that language's native idiom. The rules describe patterns; the syntax and tooling are language-specific. See `enforcement-patterns.md` for the six categories of enforcer and how to find the idiomatic one in the target ecosystem.

## Step 1 — Establish layer context

Determine whether the work lives in the **tip** (above the airgap) or the **berg** (below the airgap).

- **Tip:** business logic, domain rules, UI, feature handlers. Frequent changes, junior-owned. Typical paths: `features/`, `domain/`, `app/`, `application/`, `interfaces/`, `routes/`, `pages/`, view models, controllers.
- **Berg:** infrastructure, persistence, transport, caching, observability, third-party SDK wrappers. Rare changes, senior-owned. Typical paths: `infra/`, `infrastructure/`, `adapters/`, `platform/`, `transport/`, `persistence/`.

If the repo has no tip/berg separation, this is a precondition violation. MUST invoke `AskUserQuestion`:

```
AskUserQuestion
  questions: [{
    question: "No tip/berg layer separation was found. How should I proceed?",
    header: "No Layers",
    multiSelect: false,
    options: [
      { label: "Add labels now", description: "Introduce the layer labeling scheme inline as part of this change." },
      { label: "Bootstrap mode", description: "Switch to Bootstrap mode to establish the convention first." },
      { label: "Abort",          description: "Stop; I will set up layering manually before re-invoking." }
    ]
  }]
```

If you cannot determine the layer from the path alone, MUST invoke `Read` with `file_path` set to the absolute path of the project's `CLAUDE.md` (resolve from the current working directory) to look for the convention's activation fragment — it lists the tip and berg paths explicitly. If that's not present either, MUST invoke `AskUserQuestion`:

```
AskUserQuestion
  questions: [{
    question: "Which layer does this code belong to?",
    header: "Layer",
    multiSelect: false,
    options: [
      { label: "Tip",       description: "Business logic surface (features, domain, UI, handlers)." },
      { label: "Berg",      description: "Infrastructure (persistence, transport, caching, observability)." },
      { label: "Unclear",   description: "No layering exists yet — switch to Bootstrap mode first." }
    ]
  }]
```

Do NOT guess.

## Step 2 — Classify the change

Match your change to one of these classes. Each has a different set of rules to apply.

| Change class | Primary rules | Key references |
|---|---|---|
| New tip-layer feature or endpoint | 1.1, 1.2, 1.4, 3.1, 3.4, 4.1, 4.4 | `rules.md` §Pillar 1, §Pillar 3, §Pillar 4 |
| New berg-layer module (adapter, repository, client) | 1.3, 2.1, 3.1, 5.1 | `rules.md` §Pillar 1, §Pillar 5 |
| Async/lifecycle state (loading, retrying, polling, optimistic) | 4.1, 4.2, 4.3, 4.4, 3.4 | `rules.md` §Pillar 4 (FSM pseudocode pattern) |
| New domain identifier, money type, or scalar-like primitive | 3.1, 3.3 | `rules.md` §Pillar 3 (branded-type pseudocode pattern) |
| New enum-like status or lifecycle | 3.2, 3.4 | `rules.md` §Pillar 3 |
| Architectural seam / layer boundary | 1.2, 2.1, 2.4, 5.2 | `rules.md` §Pillar 2, `enforcement-patterns.md` §A |
| Custom lint rule or arch test | 2.1, 2.2, 2.4 | `rules.md` §Pillar 2, `enforcement-patterns.md` §B |
| Refactor of existing code "to be more junior-friendly" | all | `anti-patterns.md` first |

## Step 3 — Apply the rules as you write

For each rule triggered by the change class, apply it during generation. The rules are in `rules.md`; here is how each translates into the target language.

### Tip-layer work

- **Signatures (§1.1):** no raw async types in return positions (no Promise, Observable, Task, Future, IO-monad, channel, whatever the language calls it). If async is needed, wrap it in the language's framework-provided suspense/effect primitive so the call site reads synchronously.
- **Imports (§1.2):** no infrastructure modules. If the feature needs one, call a berg-layer facade. Use the module-boundary enforcer (Category A) to catch violations at build time.
- **Parameters and return types (§3.1):** no raw scalars for domain concepts. Use the language's branded/nominal type mechanism (newtype struct, value class, opaque alias, `NewType`, record with private constructor, etc.). Construct only via the validation constructor (§3.3).
- **State (§4.1, §3.2):** if the feature has async lifecycle (loading, retrying, polling, success, failure, cancellation), use a discriminated union / sum type / sealed hierarchy, not boolean flags. See pseudocode pattern in `rules.md` §4.2.
- **Exhaustiveness (§3.4):** every switch/match/when over a union ends with an exhaustive default that fails compilation on a new variant. Use the language's native mechanism (Rust `_` with compile-error expansion, Kotlin sealed `when`, TS `never`-typed sink, Python `assert_never`, etc.).
- **Comments (§5.2, §5.3):** explain *why* only. No narrator comments. For architectural rationale, open an ADR stub.

### Berg-layer work

- **Purity marker (§1.3):** if you are extending the functional core (pure logic), mark the module as pure using whatever mechanism the project uses (a pragma comment like `@pure`, a language-level effect annotation, or module-boundary placement). Ensure nothing in the file reads time, generates randomness, or imports side-effecting modules.
- **Imperative shell (§5.1):** wrap every cross-boundary call in a tracing span using OpenTelemetry (or the platform's equivalent). Instrument at adapter construction, not at call sites.
- **Public surface:** expose synchronous-looking (or framework-wrapped) functions to the tip. Hide retries, cancellation tokens, transaction handles, connection pools.
- **Types (§3.1):** even berg-internal types should use branded identifiers when they cross the airgap.

### FSM work

When writing a state machine, enumerate at minimum: `idle`, every in-flight state, every terminal success state, every recoverable failure, every terminal failure, and **cancellation**. Cancellation is a state, not an afterthought (§4.3).

Transitions go in a pure reducer function or a declarative machine definition. Do not scatter setters across event handlers (§4.2). Use the language's idiomatic pattern — reducer + events in TS/JS, sealed events + `when` in Kotlin, `enum` + match in Rust, `match` + dataclasses in Python, etc.

Consumers render/dispatch from the state discriminator, not from derived booleans (§4.4).

### New branded types

Follow the pseudocode pattern in `rules.md` §3.1. Concretely, for each new branded type:

1. If the project's brand primitive (the mechanism for creating new nominal types from a base type) does not yet exist, create it once in a berg-layer file. Use the language's idiomatic approach — newtype struct, value class, brand intersection, `NewType`, private-constructor record.
2. Export the branded type.
3. Export a validation constructor in the same file. The constructor either returns a result/option type or raises a typed error — never silently coerces.
4. Tip code imports the type and the constructor. Tip code never constructs branded values via direct coercion.
5. Wire an AST-level linter (Category B) banning direct coercion to any branded type outside the constructor module.

### Custom linter/arch-test authoring

When you author a custom rule for the project's linter or architecture-test framework, it must include (§2.2):

1. A one-sentence description surfaced in the IDE.
2. An error message that explains *why* the rule exists and *what pattern to use instead*. No bare "don't do this."
3. A link to the justifying ADR.
4. At least one passing test and one failing test (§2.4).

The idiomatic authoring mechanism varies by linter — ESLint rule modules, detekt rule classes, ruff rules in Rust, Roslyn analyzers, custom clippy lints via `dylint`, etc. Use whatever the project's linter uses.

## Step 4 — Design-review self-check

Before returning the code to the user, walk through the 8-question checklist in `rules.md` § Senior's Design-Review Checklist. For anything that fails, either fix it or emit a summary of the failing check with the proposed fix inline in your response text (no tool call required — this is part of the Step 6 Output, Section 5 "Design-review answers").

**Answer all 8 questions inline in your response** when the change is non-trivial (new feature, new module, new architectural seam). For small changes (bug fix, typo, single-function modification), skip the checklist but still apply the rules.

## Step 5 — Generate enforcement for new invariants

If your change introduces a new invariant that the convention does not already enforce, you must either:

- Add a lint rule, arch test, or type constraint that will fail the build on violation; **or**
- Document the invariant in an ADR with an explicit `Status: No automated enforcer (manual review required)` note, so it is visible and will be revisited at the next quarterly audit.

Never introduce an un-enforced invariant silently. That creates folklore, which the convention exists to destroy.

When you add enforcement, identify the category from `enforcement-patterns.md` and pick the idiomatic tool for the target language. Do not introduce a new tool if the project's existing tooling covers the category.

## Step 6 — Output

Structure your response as:

1. **Summary** — what you did, in 2–3 sentences.
2. **Code** — the files, clearly labeled by layer (tip/berg). Language: whatever the project uses.
3. **New enforcement** (if any) — the lint rule / arch test / type constraint added, with its rationale and the category it belongs to. Name the specific tool used.
4. **ADR stub** (if needed) — title, context, decision, consequences. Can be minimal; the user will flesh it out.
5. **Design-review answers** (if non-trivial change) — the 8 questions with yes/no + one-line reasoning each.
6. **Rules applied** — a bulleted list like `- §3.1: OrderId is now a newtype struct with createOrderId constructor` so the user can verify.
7. **Enforcement gaps** (if any) — rules that would apply to this change but cannot be enforced in the target language, with a note on the residual risk.

Do not pad the response.

## Common authoring pitfalls

- **Writing tip code that imports from an adapter file.** The compiler won't flinch but you just punched a hole in the airgap. Re-layer before submitting.
- **Using an unchecked coercion to satisfy a branded type.** This defeats §3.3 entirely. Route through the validation constructor or fail loudly.
- **Adding a boolean flag "just this once" to a component that already has a discriminated union.** §4.4 exists because this escalates. Extend the union with a new variant instead.
- **Writing "defensive" null-checks in tip code.** If you feel the need, the type system upstream is insufficient. Fix upstream (§3.2).
- **Generating a helper with a boolean parameter.** Call-site readability dies (`doThing(true, false, true)`). Split into two named functions.
- **Silent catch-and-log.** Every catch must rethrow, translate to a domain error, or transition an FSM. Logging is not handling.
- **Auto-generating an API client and dumping it into the tip.** Generated infrastructure lives in the berg. Wrap it in a domain-facing adapter.
- **Using a TS-flavored pattern verbatim in a non-TS language.** MUST translate the pattern to the target language's idiomatic construct; do NOT ship pseudocode verbatim. A Rust newtype is not the same thing as a TS brand intersection; use the language's native mechanism.
