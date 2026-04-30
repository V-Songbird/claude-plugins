# Iceberg Convention — Normative Rules

This is the single source of truth for the convention's rules. When you cite a rule, use its number (e.g., "violates 3.1"). The five pillars are:

1. The API Airgap — Rules 1.1–1.4
2. Compiler-Driven Mentorship — Rules 2.1–2.4
3. Defensive Type Engineering — Rules 3.1–3.4
4. State-Machine Dictatorships — Rules 4.1–4.4
5. Observability as Documentation — Rules 5.1–5.4

**On examples.** All code snippets in this file are pseudocode written in a typed-language-neutral style. Their purpose is to teach the *shape* of each pattern, not its implementation. Translate to the target language's idiom when generating actual code.

**On enforcement.** Each rule names the *category* of enforcement mechanism required, not a specific tool. See `enforcement-patterns.md` for the six categories and how to find idiomatic tools in any ecosystem.

## Core Axioms

Every rule below derives from these. If a rule seems arbitrary, return to the axiom.

- **A1 — Finite cognitive budget.** Juniors have ~4 active working-memory slots. Each slot consumed by infrastructure is a slot unavailable for business logic.
- **A2 — Tacit knowledge is a bug.** If a rule lives in a senior's head and not in the compiler, it will be violated.
- **A3 — The Curse of Knowledge is neurological, not dispositional.** You cannot reliably predict what a junior will find confusing. Make it explicit.
- **A4 — PRs are the wrong layer for architecture feedback.** If a junior can compile a violation, the senior failed.
- **A5 — Wrong abstraction > duplication.** Above the airgap, duplication is default; abstraction is earned.
- **A6 — Types are the cheapest mentor.** Type inference runs on every keystroke in a modern IDE.
- **A7 — Enforcement is existence.** An unenforced rule is folklore. Delete it or automate it.

---

## Pillar 1 — The API Airgap

**Intent:** a structural boundary between *business logic* (the tip, above water, where juniors live) and *infrastructure complexity* (the berg, below water, where seniors own everything).

### 1.1 The tip is imperative and synchronous-looking

All APIs exposed above the airgap return values, not async primitives. Raw async-returning types (futures, promises, observables, tasks, channels, IO monads) do not appear in the signatures of tip-layer functions.

- **Rationale:** async primitives force the reader to model a scheduler. Intrinsic-load tax per call site.
- **Enforcer category:** AST-level linter that scans return-type annotations in tip-layer files.
- **Escape hatch:** you may expose an async seam if it is wrapped by a framework-provided suspense/effect primitive that removes `await`-style ceremony from the caller. Examples of such primitives (framework-specific, not a commitment to any one): React Server Components returning `Promise<JSX>`, Suspense-boundary hooks, server actions, sagas, structured-concurrency blocks, Elixir `GenServer.call`, `async` return types that are in fact framework-unwrapped by the runtime. The test is: *does the call site contain `await` or equivalent, or does it read as a synchronous function call?*

### 1.2 No infrastructure imports above the waterline

Tip-layer code does not import from: ORMs, HTTP clients, loggers, tracers, cache clients, queue clients, feature-flag SDKs, or any module residing in an infrastructure-layer path (the project's own `infra/`, `adapter/`, `platform/`, `transport/`, `persistence/`, or equivalent).

- **Rationale:** infrastructure imports are the ant trails that drag complexity upward.
- **Enforcer category:** module-boundary enforcer (cross-layer dependency check).

### 1.3 Functional core, imperative shell

Business decisions live in pure functions (the "core"). I/O, mutation, and time live in the shell that wraps them. Juniors extend the core; seniors own the shell.

- **Rationale:** pure functions are trivially testable, composable, and readable. A rule change lives in one deterministic function, not smeared across a controller and three repositories.
- **Enforcer category:** purity enforcer — either a module-boundary check (pure modules have restricted dependencies) or an AST-level check (pure-marked files contain no I/O, time, randomness, or side-effecting imports), or both.
- **Minimum bannable surface in pure modules:** current time, random numbers, filesystem, network, database handles, logger handles, process environment. If the language has language-level effect tracking (e.g., Haskell `IO`, OCaml monad disciplines), use it.

### 1.4 One file should be enough

A typical business-logic change is achievable by reading exactly one file. If the change requires hopping through three abstraction layers, the abstraction is in the wrong place.

- **Rationale:** this is the operational test of whether the airgap is leaking. If changing a validation rule means reading four files, the rule is entangled with persistence.
- **Enforcer category:** design review. No pure-automation enforcer exists; this is judged at review. Partial automation: flag files with high fan-out of local module imports (proxy for abstraction depth).

---

## Pillar 2 — Compiler-Driven Mentorship

**Intent:** shift mentorship from the PR (too late, too human, too expensive) to the IDE (instant, objective, psychologically safe).

### 2.1 No convention survives without an enforcer

If an architectural rule is not enforced by the compiler, a linter, an architecture test, or a pre-commit hook, it does not exist. Delete it from the style guide.

- **Rationale:** unenforced rules train juniors that the document lies, eroding trust in every other rule. They also create selective enforcement, which becomes a political weapon in review.
- **Enforcer category:** PR-level meta-audit (quarterly process check: every rule in the style guide maps to a concrete enforcer, or is deleted).

### 2.2 Lint errors must explain themselves

Every custom lint rule or architecture test includes (a) the rule's rationale in one sentence, (b) the correct pattern, (c) a link to the ADR that justifies it.

- **Rationale:** a red squiggle that says `no-array-reduce` teaches nothing. A red squiggle that says "Reduce forces the reader to simulate accumulator state across iterations. Use a named loop variable or split into map/filter steps. See ADR-0034." teaches the principle.
- **Enforcer category:** meta-lint on the project's custom-rules package — rejects any rule without a populated message, description, and documentation URL.

### 2.3 Ban cognitive hazards at the AST level

Identify the top-5 cognitive hazards in your domain and ban them with AST-level lint rules. Canonical candidates (in any language):

- Accumulator-based reductions where a declarative pipeline works.
- Nested ternaries / conditional expressions beyond one level.
- Boolean flag parameters (`doThing(true)` is always worse than `doThingEagerly()`).
- Implicit timezone, locale, or currency (any date/number formatting call that accepts an unspecified locale/zone/precision parameter).
- Silent catches (catching an exception and not rethrowing, translating, or transitioning an FSM).

- **Rationale:** each forces the reader to hold hidden state. "Don't do this" is a guideline; an IDE squiggle is a rule.
- **Enforcer category:** AST-level linter.

### 2.4 Bespoke rules carry their own tests

Every custom lint or architecture rule ships with at least one passing case and one failing case as a snapshot test.

- **Rationale:** custom rules drift. An un-tested rule is indistinguishable from a broken rule, which is indistinguishable from no rule.
- **Enforcer category:** CI pipeline — the custom-rules package has its own test suite that runs on every commit.

---

## Pillar 3 — Defensive Type Engineering

**Intent:** seniors encode the domain's constraints in the type system. Juniors get IDE autocomplete as their mentor.

### 3.1 No raw scalars in domain signatures

Every identifier, money amount, duration, percentage, email, URL, and enum-like string crossing a domain function boundary is a branded/nominal/opaque type. Raw string, number, boolean are forbidden in domain APIs.

Pseudocode — the pattern:

```
# A branded identifier — structurally a string at runtime,
# distinct from string at type-check time.
type UserId   <: String  brand 'UserId'
type OrderId  <: String  brand 'OrderId'
type Money    record { cents: Int, currency: CurrencyCode }

# Domain function — parameters carry meaning, not just primitive shape.
function transfer(from: AccountId, to: AccountId, amount: Money) -> TransferResult
```

Contrast:

```
# Violates 3.1 — any string×string×number triple compiles.
function transfer(from: String, to: String, amount: Number) -> Result
```

- **Rationale:** the second signature will eventually be called with wrong-order arguments, a `UserId` instead of an `AccountId`, or a cent-value instead of a dollar-value — silently, in production. The first makes these compile errors.
- **Enforcer category:** (a) type-level enforcement via the language's nominal-type mechanism (newtype structs, value classes, opaque aliases, `NewType`, discriminated wrappers), plus (b) an AST-level linter banning raw primitives in domain-file function signatures.
- **Native support varies.** Rust, Kotlin, Scala, F#, Haskell, OCaml, Swift — strong native support. TypeScript — achievable via brand intersection patterns. C# — via record structs with private constructors. Python — `NewType` at check time only, no runtime distinction. Go — `type Foo string` gives nominal typing at the cost of implicit conversions from untyped literals; weakest of the bunch.
- **Escape hatch:** an explicit exemption pragma (e.g., `// @scalar-allowed: <reason>`) in the rare case the domain truly is a raw primitive.

### 3.2 Illegal states must be unrepresentable

Any domain entity whose lifecycle includes mutually exclusive states is modeled as a discriminated union (sum type / tagged union / sealed hierarchy), not a record of optional fields.

Pseudocode — the pattern:

```
# Discriminated union: status is the discriminator; each variant
# carries only the data relevant to that state.
type FetchState<T, E> =
    | { status: 'idle' }
    | { status: 'loading', attempt: Int }
    | { status: 'success', data: T, fetchedAt: Instant }
    | { status: 'failure', error: E, attempts: Int }
```

Contrast:

```
# Violates 3.2 — represents 16 combinations, of which most are impossible.
record FetchState<T> {
    loading?: Boolean
    error?:   Error
    data?:    T
    hasRetried?: Boolean
}
```

- **Rationale:** the second shape permits `{ loading: true, error: err, data: val, hasRetried: true }`. That state cannot happen, yet juniors will write code handling it (and tests for it) forever.
- **Enforcer category:** (a) type-level enforcement — the language's native sum-type mechanism where available (Rust `enum`, Kotlin sealed classes, Scala sealed traits, Swift enums with associated values, TS discriminated unions, Python `Literal`-discriminated dataclasses); (b) an AST-level linter flagging records with ≥2 optional fields in domain files.

### 3.3 Validation boundaries are singular and explicit

Any cast from a raw value into a branded type goes through a single, named constructor function. Direct coercion into a branded type is banned in tip-layer code.

Pseudocode — the pattern:

```
# Lives below the airgap. The ONLY way to produce a UserId.
function createUserId(raw: String) -> Result<UserId, ValidationError>:
    if !matchesPattern(raw, USER_ID_PATTERN):
        return Err(ValidationError.malformed)
    return Ok(UserId.of(raw))
```

- **Rationale:** concentrates validation at the boundary. Inside the tip, the type is a *proof* that validation happened — the junior stops defending against it.
- **Enforcer category:** AST-level linter banning direct type coercion (`as UserId`, `UserId(raw)`, `unsafeCoerce`, or equivalent) to any branded type outside the constructor module. Strength of this rule depends on the language's coercion surface; in languages with unrestricted runtime casting (dynamic languages), this becomes a review-only rule and the residual risk must be covered by property-based validation tests at the boundary.

### 3.4 Exhaustiveness is a compile-time obligation

Every switch/match/when over a domain union includes an exhaustive default branch that fails compilation if a new variant is added upstream. No silent fall-through.

Pseudocode — the pattern:

```
match state:
    Idle         -> renderIdle()
    Loading      -> renderSpinner()
    Success(d)   -> renderResult(d)
    Failure(e)   -> renderError(e)
    # The exhaustiveness check: if a new variant is added to FetchState,
    # this compiles to a type error until the match is updated.
    _ -> assertNever(state)
```

- **Rationale:** when you add a state, every consumer must compile-fail until it handles the new state. This is the mechanism that turns state evolution from a fear into a ritual.
- **Enforcer category:** type-level enforcement — use the language's native exhaustiveness check. Native in Rust, Kotlin (sealed `when`), Scala, F#, Swift, OCaml, Haskell, Python 3.10+ (`match` + `assert_never` from `typing`), TypeScript (`switch-exhaustiveness-check` or `never`-typed sink).

---

## Pillar 4 — State-Machine Dictatorships

**Intent:** eliminate ad-hoc boolean flag tuples that encode illegal states and scatter transitions across the codebase.

### 4.1 No flag tuples

Any feature whose UI or behavior depends on more than one boolean flag derived from the same underlying process is modeled as a state machine. `isLoading + isError + isSuccess + hasRetried` is a state machine that hasn't been admitted.

- **Rationale:** *n* flags = 2ⁿ representable states. Most are impossible; the junior must prove which by reading the code. A state machine enumerates the *k* real states; 2ⁿ − *k* bugs stop being reachable.
- **Enforcer category:** AST-level linter counting boolean state variables per module/component, plus design review.

### 4.2 Transitions are named, centralized, and pure

Transitions are expressed as pure transition functions (`reducer(state, event) -> state`) or declarative machine definitions. Scattered mutations are banned.

Pseudocode — the pattern:

```
function fetchReducer(state: FetchState, event: FetchEvent) -> FetchState:
    match (state, event):
        (Idle,         StartRequested)   -> Loading(attempt = 1)
        (Loading(a),   Succeeded(data))  -> Success(data)
        (Loading(a),   Failed(e)) if a < MAX_ATTEMPTS -> Loading(attempt = a + 1)
        (Loading(_),   Failed(e))        -> Failure(e)
        (_,            Cancelled(reason))-> Cancelled(reason)
        (_,            Reset)            -> Idle
        _                                -> state  # ignore irrelevant events
```

- **Rationale:** a named transition function is a unit of review. A scattered mutation is a git-blame archaeology expedition.
- **Enforcer category:** AST-level linter banning direct state mutation in event-handler or effect files that participate in an FSM; module-boundary check that state-machine files export only reducers/transition functions, not raw setters.

### 4.3 The happy path is a subset, not the default

Every FSM definition enumerates at least: the idle state, every in-flight state, every terminal success state, every recoverable failure state, every terminal failure state. **Cancellation is a state, not an afterthought.**

- **Rationale:** juniors write happy-path tests because happy-path states are the only ones visibly present. If the FSM includes `timeout`, `cancelled`, `partialFailure`, the junior's test file will contain them — the compiler forces it.
- **Enforcer category:** property-based test / review checklist asserting FSM cardinality; partial automation by counting variants in the sum-type definition.

### 4.4 UI renders from the state, not from derived booleans

Components pattern-match on `state.status` (or equivalent discriminator). Local aliases like `let isLoading = state.status == 'loading'` are permitted, but do not cross component boundaries.

- **Rationale:** passing `isLoading` down a tree re-introduces the flag tuple at the consumer. The discriminated union must propagate intact.
- **Enforcer category:** AST-level linter banning boolean component/prop types where the source value is derivable from a discriminated union in the same module.

---

## Pillar 5 — Observability as Documentation

**Intent:** static docs decay; runtime behavior does not. Make the system self-describing.

### 5.1 Every cross-boundary call emits a span

Any function call crossing the airgap (tip → berg, or service → service) is wrapped in a distributed-tracing span with a stable name and an attribute set defined in the platform's tracing spec.

- **Rationale:** turns the runtime into an auto-updating architecture diagram. A junior with a trace ID can answer "what did my code actually do?" without reading the berg.
- **Enforcer category:** tracing instrumentation wrapped *at the adapter*, not at call sites. If juniors have to remember to add spans, they won't.
- **Universal tool:** OpenTelemetry has SDKs for every mainstream language; use the language's auto-instrumentation for the platform's HTTP/DB/queue libraries, then add custom spans at the airgap adapters you author.

### 5.2 The "why" lives in ADRs, not comments

Inline comments explain *why this specific line* (unobvious invariant, bug-ticket reference, known perf trap). Architectural rationale — why this pattern, why this library, why this boundary — lives in a numbered ADR.

- **Rationale:** comments rot with their line; ADRs rot with their decision. The former is invisible to onboarding; the latter is greppable.
- **Enforcer category:** PR-level check — any PR introducing a new module under infrastructure or platform paths must reference an ADR number in its description.

### 5.3 Comment smells are review-blocking

Comments that restate the code (`// increment counter`, `// loop over users`) are removed in review. Comments that explain *why* (`// Stripe returns 402 on insufficient funds, not 4xx-client; see BUG-4412`) are welcome.

- **Rationale:** redundant comments train readers to skip comments, killing the signal of useful ones.
- **Enforcer category:** review heuristic. Partial automation: flag comments whose token overlap with the next code line exceeds a threshold.

### 5.4 Logs are for operators; traces are for readers

A log statement is not a substitute for tracing. A bare `print("entering handler")` is a junior-authored trace span — delete it and instrument properly.

- **Rationale:** logs are linear text; traces are structured graphs. A trace tells you where, when, how long, with what payload, and what called it — a log tells you only that the code ran.
- **Enforcer category:** AST-level linter banning free-form print / console-logger calls in tip-layer files; log levels below `warn` banned outside the berg's structured-logger wrapper.

---

## The Senior's Design-Review Checklist

Before merging any senior-authored change that alters the surface exposed to juniors, answer each question "yes" or rework.

1. Can a junior ship a typical feature using this API by reading exactly one file?
2. Can the junior write a structurally invalid call? (If yes, the type system is insufficient.)
3. Can the junior catch-swallow an error and have it silently pass CI?
4. Can the junior construct a domain value without the validation constructor? (If yes, casts are leaking.)
5. If I add a new state to this flow next quarter, which call sites compile-fail? (If "none" or "I'd have to grep," exhaustiveness is missing.)
6. Is there an ADR for every non-obvious choice?
7. Is every architectural assertion backed by a lint rule, arch test, or type constraint — not a style-guide bullet?
8. If this feature is built 20% wrong by an AI agent, which guardrail catches it?

Question 8 is not optional.
