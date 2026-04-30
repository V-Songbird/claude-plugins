# Enforcement Patterns

This file teaches Claude how to satisfy the Iceberg Convention's **Axiom of Enforcement** (A7: *an unenforced rule is folklore*) in any language or ecosystem. It names the six categories of enforcement the convention requires, explains what each one does, gives you the questions to ask when looking for the idiomatic tool, and lists common representatives so you recognize one when you see it.

**Core principle.** Do not commit to specific tools before detecting the target stack. When a rule needs enforcement, identify the *category*, then search for the idiomatic tool in the target ecosystem. `tool_search` and `web_search` are your friends here.

## The six categories

### Category A — Module-boundary enforcer

**What it does.** Fails the build when code in one module/package/layer imports from another module/package/layer it should not depend on. This is the mechanism that enforces the API Airgap.

**Rules it enforces.** §1.2 (no infra imports above the waterline), §1.3 (pure core modules have no side-effecting dependencies), parts of §2.1 and §5.4.

**Canonical representatives** (not exhaustive — confirm the right choice for the target repo via search):

- JavaScript/TypeScript: `dependency-cruiser`, `ts-arch`, `eslint-plugin-boundaries`.
- JVM (Java, Kotlin, Scala): `ArchUnit`, Gradle/Maven module dependency constraints.
- Python: `import-linter`, `deptry`.
- Rust: crate boundaries with `cargo-deny`, `pub(crate)` / `pub(super)` visibility discipline.
- .NET: `NetArchTest`, `ArchUnitNET`.
- Go: `depguard` (via `golangci-lint`), internal package convention.
- Elixir/Erlang: `mix xref`, Boundary library.

**How to pick the right one.** Search the project's existing tooling first. If nothing is installed, search `<language> module boundary enforcement` or `<language> architecture test`. Pick the tool with active maintenance, a simple configuration surface (ideally declarative, not imperative), and explicit failure messages.

**Minimum viable configuration.** Define the layer map (what counts as tip, what counts as berg), then a single rule: *no inbound dependencies from berg-path files into tip-path files*. Everything else follows.

### Category B — AST-level linter

**What it does.** Fails on specific syntactic patterns by inspecting the parsed abstract syntax tree. This is the mechanism for catching cognitive hazards at the source-character level.

**Rules it enforces.** §1.1 (async primitives in tip signatures), §2.3 (cognitive hazards: reduce, nested ternaries, boolean flag params, implicit locale, silent catches), §3.1 (raw scalars in domain signatures), §3.3 (casts into branded types outside constructors), §4.1 (flag tuples), §4.2 (scattered mutations in FSM files), §4.4 (booleans from unions), §5.4 (print-as-log).

**Canonical representatives:**

- JavaScript/TypeScript: `ESLint` with custom rules plus `typescript-eslint`, `eslint-plugin-unicorn`.
- Kotlin: `detekt` with custom rule sets.
- Java: `checkstyle`, `PMD`, Error Prone, `ArchUnit` for bytecode-level checks that overlap with AST.
- Python: `ruff` with custom rules (preferred for speed), `flake8` with plugins, `pylint`.
- Rust: `clippy` with custom lints via `dylint`.
- .NET: Roslyn analyzers.
- Go: custom analyzers under `go/analysis`, runnable via `golangci-lint`.
- Swift: `SwiftLint` with custom rules.
- Ruby: `RuboCop` with custom cops.
- Elixir: `Credo` with custom checks.

**How to pick the right one.** Almost always: use whatever linter the project already has, and extend it with custom rules. Installing a second linter in an ecosystem that already has one is a cognitive-load violation in itself.

**Custom-rule authoring discipline** (§2.2, §2.4): every custom rule must have (a) a one-sentence description surfaced in the IDE, (b) an error message that explains why the pattern is banned and what to do instead, (c) a link to the justifying ADR, (d) at least one passing and one failing snapshot test.

### Category C — Type-level enforcement

**What it does.** Uses the language's type system to make certain values, states, or transitions unrepresentable. The strongest form of enforcement — the code cannot even be written, not just cannot pass lint.

**Rules it enforces.** §3.1 (branded/nominal types), §3.2 (discriminated unions / sum types), §3.4 (exhaustiveness), parts of §4.1 and §4.4.

**Native support varies widely by language:**

- **Strong native support:** Rust (enums + newtype structs + match), Kotlin (sealed classes + value classes + sealed `when`), Scala (sealed traits + opaque types + match), Swift (enums with associated values + exhaustive switch), F#, OCaml, Haskell, Elm.
- **Library-enabled:** TypeScript (brand intersection types + discriminated unions + `switch-exhaustiveness-check`), C# (record structs + OneOf library or manual sum-type pattern), Java (sealed classes from 17+, records, Optional discipline).
- **Check-time only:** Python (`typing.NewType` + `typing.Literal` + `match` + `assert_never`, enforced by `mypy --strict` or `pyright`; no runtime distinction).
- **Weak:** Go (`type Foo string` allows implicit conversions from untyped literals; no sum types; exhaustiveness via third-party linters only). JavaScript without TypeScript (no static types at all).

**How to pick the right mechanism.** Use the language's native construct first. If the language lacks one, use the idiomatic library (e.g., TypeScript's `Brand<K, T>` pattern, C#'s OneOf). If the language has no good option (Go sum types, Python runtime branding), **say so explicitly** and compensate with heavier Category B (AST-level) and Category D (purity/validation) rules.

**Do not invent type-level patterns the language does not support.** A Go `type UserID string` is nominal typing; it is not as strong as a Rust newtype. Document this in the ADR. Do not pretend the enforcement strength is equivalent across languages.

### Category D — Purity enforcer

**What it does.** Fails the build when code marked as pure (the functional core) calls I/O, reads time, generates randomness, or imports side-effecting modules.

**Rules it enforces.** §1.3 (functional core purity). Overlaps with Category A and Category B but has its own identity because the concern — "this specific file or module must be deterministic" — is distinct.

**Implementation approaches:**

1. **Module-boundary approach.** Place the core in its own module/crate/package and restrict its dependency graph to exclude everything side-effecting. Works well in Rust (crate boundary), Scala (module), Go (package). Enforced by Category A tools.
2. **AST-level approach.** Mark pure files with a pragma (e.g., `@pure` comment at the top) and run a custom linter over them that bans calls to the language's impurity surface (current time, randomness, I/O syscalls, network, DB, logger). Works well in TypeScript, Python, Ruby, Kotlin. Enforced by Category B tools.
3. **Language-level approach.** If the language tracks effects in the type system (Haskell `IO`, PureScript `Effect`), let the compiler do it.

**The minimum bannable surface in any language:** reads of current time, random-number generators, filesystem, network, database handles, logger handles, process environment variables, mutable global state.

### Category E — Tracing instrumentation

**What it does.** Wraps every cross-boundary call in a distributed-tracing span with a stable name and attribute set. Turns the runtime into an auto-updating architecture diagram.

**Rules it enforces.** §5.1 (every cross-boundary call emits a span), partly §5.4 (logs are for operators; traces are for readers).

**Universal tool:** OpenTelemetry. It has SDKs for every mainstream language plus auto-instrumentation agents for common HTTP, DB, and queue libraries. Use it.

**How to wire it:**

1. Install the OpenTelemetry SDK for the target language.
2. Enable auto-instrumentation for the project's HTTP client, web server, database driver, and queue client.
3. At the airgap boundary (the adapter layer), wrap every public method of each adapter in a custom span. **Do this at adapter construction, not at call sites** — if juniors have to remember to add spans at call sites, they won't.
4. Define a tracing spec (a short document): naming conventions for spans (`service.operation.entity`), required attributes (`user.id`, `tenant.id`), forbidden attributes (PII, secrets).

**For the berg only.** Tracing belongs below the airgap. The tip calls a facade; the facade emits a span; the tip remains synchronous-looking and trace-free.

### Category F — PR-level check

**What it does.** Runs on every pull request / merge request and gates the merge on repository-level invariants that are not per-file linting (e.g., "this PR must reference an ADR," "this PR must update the CHANGELOG," "the CLAUDE.md fragment still has no unreplaced placeholders").

**Rules it enforces.** §5.2 (ADRs for rationale), §2.1 (meta-audit that every style-guide rule has an enforcer; periodic rather than per-PR, but lives in the same infrastructure).

**Canonical representatives:**

- GitHub: GitHub Actions workflow, merge queue rules.
- GitLab: GitLab CI pipeline.
- Bitbucket: Bitbucket Pipelines.
- Self-hosted: Jenkins, Drone, Woodpecker, Concourse.

**How to pick the right one.** Always use the project's existing CI platform. Install a new one only if the project genuinely has none.

**Minimum viable checks:**

1. All Category A, B, C, D enforcers run as blocking.
2. PRs touching infrastructure paths must reference an ADR number in the description.
3. Branch protection requires an aggregate status check (one name that covers all Iceberg checks), so adding new enforcers does not require reconfiguring protection rules.

## Mapping rules to categories

Use this table to look up which category (or categories) a rule needs. Multiple categories per rule is normal and expected.

| Rule | Primary | Secondary |
|---|---|---|
| 1.1 Sync-looking tip | B | — |
| 1.2 No infra imports above waterline | A | — |
| 1.3 Functional core purity | D | A |
| 1.4 One file should be enough | Design review | — |
| 2.1 All rules automated | F (meta-audit) | — |
| 2.2 Lint errors explain themselves | B (meta-lint) | — |
| 2.3 Cognitive hazards banned | B | — |
| 2.4 Bespoke rules have tests | F (CI) | — |
| 3.1 No raw scalars in domain | C | B |
| 3.2 Illegal states unrepresentable | C | B |
| 3.3 Single validation boundary | B | C |
| 3.4 Exhaustiveness | C | — |
| 4.1 No flag tuples | B | Design review |
| 4.2 Centralized pure transitions | B | A |
| 4.3 Full FSM enumeration | Design review | — |
| 4.4 UI renders from state | B | — |
| 5.1 Spans at boundaries | E | — |
| 5.2 ADRs for rationale | F | — |
| 5.3 Comment smells | Design review | B (partial) |
| 5.4 Logs for operators | B | — |

**When a rule's primary category is Design review**, it means no automated enforcer exists that is both reliable and low-false-positive. Do not pretend otherwise; flag these rules explicitly in the ADR and include them on the quarterly-audit checklist.

## How to propose enforcement for a new rule

When you introduce a project-specific rule (or adapt a generic rule to a project), follow this procedure:

1. **Identify the category.** Which of A–F does this rule belong to? If "none of the above," the rule is probably a value judgment rather than a mechanical invariant — reconsider whether it should be a rule at all.
2. **Detect the target stack.** Read `package.json`, `pom.xml`, `Cargo.toml`, etc. Identify the idiomatic tool in that category for that stack.
3. **Check if the tool is already installed.** If yes, extend its configuration. If no, evaluate whether installing a new tool is justified (usually: if the ecosystem's established linter doesn't cover the category, yes; if it does, extend the existing one).
4. **Write the rule.** Include message text, rationale, fix suggestion, and a link to the ADR (§2.2).
5. **Write the test.** At least one passing case, one failing case (§2.4).
6. **Wire it into CI.** Blocking, not advisory (§2.1).
7. **Document the ADR.** Context, decision, consequences, enforcement details (§5.2).

**If steps 2–3 reveal that no idiomatic tool exists**, the rule becomes review-only — flag it as `ENFORCEMENT GAP` in the ADR and include it on the quarterly audit list. Do not pretend coverage exists when it does not.

## Honest gaps and how to talk about them

Some rules cannot be enforced fully in some languages. Examples you will encounter:

- **Go has no sum types.** §3.2 becomes interface-with-known-implementations + convention + review. Weaker than a Rust enum; be honest.
- **Python has no runtime branded types.** §3.1 is check-time only; runtime coercion can bypass it. Compensate with boundary validation (Pydantic, attrs) and explicit tests.
- **Dynamic languages (Python, Ruby, JavaScript-without-TS) cannot enforce §3.1 or §3.2 at the type level at all.** Lean heavily on Category B (AST linting at domain boundaries) and Category D (purity enforcement for the core).
- **Exhaustiveness checking** (§3.4) is native in Rust, Kotlin sealed `when`, Scala, Swift, Haskell, F#, OCaml; requires tooling in TypeScript, Python (3.10+), C#; requires third-party linters in Go.

When you flag a gap, name (a) the rule, (b) the language limitation, (c) the closest available enforcer, (d) the residual risk review must cover. Do not present weaker-enforcement languages as equivalent to stronger-enforcement ones.
