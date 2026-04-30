---
name: convention
description: Apply the Iceberg Convention — an asymmetric complexity management framework in which senior-authored code absorbs system complexity below an architectural airgap, exposing a frictionless, hard-to-misuse surface above it for juniors and AI agents. This is a language- and framework-agnostic convention; Claude applies the rules as patterns and picks the idiomatic enforcement mechanism for whatever ecosystem the target code lives in. Use this skill whenever writing, reviewing, or auditing code in a codebase that follows the Iceberg Convention (or should); when setting up a new project's architectural guardrails; when authoring module-boundary rules, AST-level linters, branded/nominal type scaffolding, finite state machines for async workflows, or Architectural Decision Records; when making design-review decisions about API boundaries, state management, type systems, purity, or how to make code hard to misuse. Trigger whenever the user mentions 'iceberg convention,' 'airgap,' 'asymmetric complexity,' 'junior-friendly architecture,' 'compiler-driven mentorship,' 'defensive type engineering,' 'state-machine dictatorship,' 'observability as documentation,' or the five pillars. Also trigger — even without those phrases — when the user asks to reduce cognitive load for less-experienced teammates, make an API hard to misuse, replace ad-hoc boolean flags with a state machine, brand scalar primitives to prevent ID mix-ups, enforce a layered architecture at compile time, build guardrails for AI coding agents, or audit an existing codebase for maintainability and mentorship-quality issues. Do not skip this skill just because the user didn't use the exact name — if the task is about making senior-authored code safe for juniors or AI agents to consume, this skill applies.
---

# Iceberg Convention

## What this skill does

The Iceberg Convention is a coding convention *for senior and staff engineers* whose goal is to make the code juniors (and AI agents) actually touch maximally frictionless. It does this by quarantining complexity behind an **architectural airgap**: seniors absorb the sophistication (types, state machines, custom linters, architecture tests, observability) below the waterline, and the surface above it reads as linear, synchronous-looking, imperative business logic.

This skill helps you **apply the convention while writing or reviewing code**. It is organized around three modes:

- **Authoring** — you are about to write or modify code. Apply the rules during generation.
- **Audit** — you are reviewing an existing codebase against the convention. Produce a structured report.
- **Bootstrap** — you are setting up the convention's enforcement scaffolding in a fresh project.

## This is a language-agnostic convention

The rules describe **patterns** (airgap separation, branded types, discriminated unions, exhaustive matching, pure cores, runtime tracing, written rationale). The patterns have implementations in every mainstream typed language; their syntax differs and their *native* support varies, but the intent is invariant.

When applying the convention:

1. **Detect the target language** from the repo — `package.json`, `pom.xml`, `Cargo.toml`, `pyproject.toml`, `*.csproj`, `go.mod`, `mix.exs`, `Gemfile`, `composer.json`, etc. If multi-language monorepo, identify the language of the file you're about to write or review.
2. **Translate each rule's pattern into the language's native idiom.** The enforcer category (below) tells you *what kind of tool*; the idiomatic-tool lookup is governed by the `WebSearch` / `WebFetch` directive in the paragraph immediately below the numbered list.
3. **Be honest when a language's native support is weak.** Some rules enforce more strictly in Rust or Kotlin than in Python or Go. Flag the gap explicitly; do not pretend a `type UserID string` in Go is as safe as a Rust newtype struct.

Do not hard-code tool names into your output. The rule is "branded types with a validation constructor"; the enforcer is "whatever this language calls an AST-level linter, plus whatever this language calls nominal typing."

When the idiomatic enforcer for a (language, Category A–F) pair is unknown:

- If `WebSearch` is available: MUST invoke `WebSearch` with `query: "<language> <category-name> linter OR architecture test idiomatic 2025"` to verify the tool is currently maintained.
- Else if `WebFetch` is available: MUST invoke `WebFetch` on the ecosystem's curated tool-list page (e.g., `https://awesome-rust.com`, `https://github.com/ziadoz/awesome-php`, `https://github.com/vinta/awesome-python`).
- If neither is available: MUST state in the response that the enforcer recommendation cannot be verified, and flag it as `Unverified — review before installing`.

Do NOT recommend a tool you have not verified is currently maintained.

The convention's **Axiom of Enforcement** governs everything: *if a rule is not enforced by the compiler, a linter, an architecture test, or a build gate, it does not exist.* Your output is weighted toward **generating enforcement** (configuration, custom rules, type scaffolding, ADRs), not prose advice.

## Stack detection recipe (shared by all modes)

Before applying any rule, MUST detect the target language(s). Invoke `Glob` in a single parallel batch with patterns:

- `**/package.json` · `**/pom.xml` · `**/build.gradle` · `**/build.gradle.kts`
- `**/Cargo.toml` · `**/pyproject.toml` · `**/requirements.txt` · `**/setup.py`
- `**/*.csproj` · `**/*.fsproj` · `**/go.mod` · `**/Gemfile`
- `**/mix.exs` · `**/composer.json` · `**/Package.swift`

For every hit, MUST invoke `Read` with `limit: 80`. Record detected languages + manifest paths in one line before proceeding.

If no manifest matches, MUST invoke `AskUserQuestion`:

```
AskUserQuestion
  questions: [{
    question: "No recognized manifest found. Which language family is this code?",
    header: "Language",
    multiSelect: false,
    options: [
      { label: "TS/JS/Python", description: "TypeScript, JavaScript (Node/Deno/Bun/browser), or any Python ecosystem." },
      { label: "JVM / .NET",   description: "Java, Kotlin, Scala, Clojure; or C#, F#, VB.NET." },
      { label: "Rust / Go",    description: "Cargo-based or embedded Rust; or standard Go toolchain." },
      { label: "Other",        description: "Ruby, Swift, Elixir, PHP, etc. — describe in chat; convention may have reduced enforcement." }
    ]
  }]
```

## Step 1 — Select the mode

Skip `AskUserQuestion` ONLY if the user's request contains one of the keyword sets below:

- **Authoring:** "implement", "write", "add", "refactor", "fix", "build [feature]"
- **Audit:** "audit", "review the codebase", "check the codebase", "how well does this follow"
- **Bootstrap:** "bootstrap", "set up", "scaffold", "configure conventions", "new project"
- **Education:** "what would the convention say", "explain the convention", "how does the convention handle"

If the request matches keywords from ≥2 rows, OR matches no row cleanly, MUST invoke `AskUserQuestion`:

```
AskUserQuestion
  questions: [{
    question: "Which Iceberg Convention mode applies to this task?",
    header: "Mode",
    multiSelect: false,
    options: [
      { label: "Authoring", description: "Writing or modifying code under the convention." },
      { label: "Audit",     description: "Reviewing an existing codebase; produces a findings report." },
      { label: "Bootstrap", description: "Setting up enforcement scaffolding (greenfield or retrofit)." },
      { label: "Education", description: "Read-only — explain what the convention would say about a design." }
    ]
  }]
```

After mode is determined, MUST invoke `Read` on the mode file:

| Mode | File to `Read` |
|---|---|
| Authoring | `references/mode-authoring.md` |
| Audit | `references/mode-audit.md` |
| Bootstrap | `references/mode-bootstrap.md` |
| Education | `references/rules.md` (read-only; do not load mode files) |

The design-review-only sub-branch ("is this design compliant?") falls under Authoring — `references/mode-authoring.md` § Design Review.

## Rule index (the 20 normative rules)

Cite rules by number. The full rationale and escape hatches for each rule live in `references/rules.md` — load it only when you need rationale (e.g. responding to user pushback), an escape hatch, or the language-native-support matrix for a specific rule.

**Pillar 1 — API Airgap** (structural boundary between business logic and infrastructure):
- **§1.1** — tip is imperative and synchronous-looking (no raw futures/promises/observables/channels in tip-layer signatures) — enforcer **B**
- **§1.2** — no infrastructure imports (ORMs, HTTP clients, loggers, tracers, cache, queues, feature flags) above the waterline — enforcer **A**
- **§1.3** — functional core, imperative shell (business decisions are pure; I/O/time/randomness/mutation live in the shell) — enforcer **D** (primary), **A** (secondary)
- **§1.4** — one file is enough for a typical change (if a change requires hopping 3+ abstraction layers, the abstraction is misplaced) — enforcer **Design Review**

**Pillar 2 — Compiler-Driven Mentorship** (mentorship belongs in the IDE, not the PR):
- **§2.1** — no convention survives without an enforcer (unenforced rules train juniors to distrust the guide) — enforcer **F** (meta-audit)
- **§2.2** — lint errors explain themselves (rationale + correct pattern + ADR link in every custom-rule message) — enforcer **B** (meta-lint on the custom-rules package)
- **§2.3** — ban cognitive hazards at the AST level: accumulator reductions, nested ternaries, boolean flag params (`doThing(true)`), implicit timezone/locale/currency, silent catches — enforcer **B**
- **§2.4** — every custom lint or arch rule ships with passing + failing snapshot tests — enforcer **F** (CI)

**Pillar 3 — Defensive Type Engineering** (encode domain constraints in types; IDE autocomplete mentors the junior):
- **§3.1** — no raw scalars in domain signatures (every ID, money, duration, percentage, email, URL, enum-like string is a branded/nominal/opaque type) — enforcer **C** (primary), **B** (secondary)
- **§3.2** — illegal states unrepresentable (discriminated unions / sum types / sealed hierarchies, not records of optional fields) — enforcer **C** (primary), **B** (secondary)
- **§3.3** — validation boundaries are singular and explicit (one named constructor per branded type; direct coercion banned in tip) — enforcer **B** (primary), **C** (secondary)
- **§3.4** — exhaustiveness is a compile-time obligation (every match over a domain union has a compile-fail sink for unhandled variants) — enforcer **C**

**Pillar 4 — State-Machine Dictatorships** (no ad-hoc boolean tuples encoding async lifecycles):
- **§4.1** — no flag tuples (2+ booleans derived from the same underlying process = unadmitted FSM) — enforcer **B** (primary), **Design Review** (secondary)
- **§4.2** — transitions are named, centralized, pure (reducer `(state, event) → state` or declarative machine; scattered mutations banned) — enforcer **B** (primary), **A** (secondary)
- **§4.3** — happy path is a subset: FSMs enumerate idle + in-flight + success + recoverable-failure + terminal-failure; **cancellation is a state, not an afterthought** — enforcer **Design Review** (partial automation via variant count)
- **§4.4** — UI renders from state (discriminator match), not from derived booleans passed across component boundaries — enforcer **B**

**Pillar 5 — Observability as Documentation** (runtime behavior doesn't decay; static docs do):
- **§5.1** — every cross-boundary call (tip → berg, or service → service) emits a span, wrapped **at the adapter** not at call sites — enforcer **E**
- **§5.2** — the "why" lives in ADRs, not comments (comments rot with their line; ADRs rot with their decision) — enforcer **F** (PR references ADR number)
- **§5.3** — comment smells (restating code) are review-blocking; "why" comments (bug references, unobvious invariants, perf traps) are welcome — enforcer **Design Review**, **B** partial
- **§5.4** — logs are for operators; traces are for readers. `print("entering handler")` is a junior-authored trace — delete it, instrument properly — enforcer **B**

## Enforcer categories (A–F)

Every rule above maps to one or more of these. When proposing enforcement, identify the category, then pick the idiomatic tool in the target stack. **Per-language canonical tool lists and the full tool-selection discipline live in [references/enforcement-patterns.md](references/enforcement-patterns.md) — MUST invoke `Read` on it before proposing a tool you haven't used before in that ecosystem, or when authoring a project-specific custom rule (§2.2 discipline).** The A–F definitions below are the routing surface; the catalogs are in the reference.

- **A — Module-boundary enforcer.** Fails the build when code in one layer imports from another it shouldn't. Enforces §1.2, §1.3 (via dep graph restriction), §4.2.
- **B — AST-level linter.** Fails on syntactic patterns. Enforces §1.1, §2.3, §3.1 (paired with C), §3.3, §4.1, §4.2, §4.4, §5.4.
- **C — Type-level enforcement.** Makes invalid states, values, or missing cases unrepresentable. Enforces §3.1, §3.2, §3.4. **Native strength varies wildly** — strong in Rust/Kotlin/Scala/Swift/F#/OCaml/Haskell/Elm; library-enabled in TS/C#/Java17+; check-time only in Python; weak in Go and JS-without-TS. Consult `references/enforcement-patterns.md` § Category C for the per-language matrix before committing.
- **D — Purity enforcer.** Pure modules have no I/O, time, random, network, DB, logger, env, or mutable global in their surface. Enforces §1.3. Three implementation approaches: (1) module-boundary restriction via Category A tools; (2) AST linter over `@pure`-tagged files via Category B; (3) language-level effect tracking (Haskell `IO`, PureScript `Effect`).
- **E — Tracing instrumentation.** Wraps every cross-airgap call in a distributed-tracing span with stable naming and required attributes. Enforces §5.1. **Universal tool: OpenTelemetry**, with language-specific SDKs and auto-instrumentation for common HTTP/DB/queue libraries. **Wrap at the adapter**, never at call sites — if juniors have to remember to add spans, they won't.
- **F — PR-level check.** Runs on every PR, gates merge on repo-level invariants. Enforces §2.1 (meta-audit), §2.4, §5.2. Always use the project's existing CI platform — installing a new one for this alone is a cognitive-load violation.

**Honest gaps to remember:** Go has no sum types (§3.2 becomes interface + known impls + review; weaker). Python has no runtime brands (§3.1 is check-time only; compensate with boundary validation via Pydantic/attrs + property tests). Dynamic languages (no static types) cannot enforce §3.1/§3.2 at the type level at all — lean on B + D. When you hit a gap, name (a) the rule, (b) the language limitation, (c) the closest available enforcer, (d) the residual risk review must cover.

## When to load each reference

| Reference | MUST invoke `Read` when | Do NOT load when |
|---|---|---|
| `references/mode-authoring.md` | Authoring mode selected. | Any other mode. |
| `references/mode-audit.md` | Audit mode selected. | Any other mode. |
| `references/mode-bootstrap.md` | Bootstrap mode selected. | Any other mode. |
| `references/rules.md` | User challenges a rule; an escape hatch applies; language-native-support matrix needed; Education mode. | Rule number/title alone suffices — that's already in §"Rule index" above. |
| `references/enforcement-patterns.md` | Proposing a tool you haven't used before in the target ecosystem; authoring a project-specific custom rule (§2.2 discipline). | Enforcer category is obvious from the rule index. |
| `references/anti-patterns.md` | Audit mode; any refactor task in Authoring mode. | Greenfield feature authoring with no legacy shape to recognize. |

For `assets/templates/` files (ADR skeleton, ADR-0001 example, CLAUDE.md fragment, PR template): MUST invoke `Read` on `${CLAUDE_SKILL_DIR}/assets/templates/<file>.md` only in Bootstrap mode (or when explicitly adapting a template into a repo). Apply placeholder substitutions, then MUST invoke `Write` to the project's conventional destination path.

## Hard invariants for every mode

Regardless of mode, these apply to anything you produce:

1. **Never weaken a rule to fit existing code.** If the current code violates the convention, say so. Do not pretend it complies.
2. **Every rule you invoke cites its number.** "This violates §3.1 (no raw scalars in domain signatures)" beats "this should be branded."
3. **Every prescription names its enforcer category.** If you say "use branded IDs," name which A–F category enforces it. If a specific tool is idiomatic for the target language, name it. If you cannot name an enforcer category, the prescription is folklore — rewrite it.
4. **Distinguish berg from tip in every artifact.** When you write code, mark it with the project's layering convention (path placement or a layer pragma). Enforcement rules cannot target what isn't labeled.
5. **Treat AI agents as a first-class consumer of the surface.** If you are writing a new API or enforcer, ask: does an autonomous agent producing code against this surface have the same or better guardrails as a human junior? If not, strengthen.
6. **Never produce a visual diagram, chart, or widget for this task.** This skill's deliverables are code, configuration, and structured text. Diagrams would be cognitive-load injection, which is what the convention is designed to prevent.
7. **Pseudocode teaches the pattern; committed language implements it.** The pseudocode in `rules.md` teaches the *shape*; when you generate actual code, use the target language's idioms — do not copy pseudocode verbatim.
8. **Tool-invocation enforcement for user-visible actions.** Every *user-visible action* step in this skill's mode files (ask-user, scan-repo, install-tool, write-file, run-build, gate-plan, and — only where governed — dispatch-subagent) MUST fire as a named tool invocation with full UX-critical parameters. This top-level index file itself dispatches no subagents; concrete `Agent` / `EnterPlanMode` / `Bash` invocations live in the mode files, governed by this invariant. Pure reasoning steps (classify-change, interpret-findings) are exempt. Prose-only action steps are folklore — the same failure mode §2.1 warns against, applied to this skill itself.

## Default output expectations

- **Authoring deliverables:** the requested code in the target language, in the correct layer (tip vs. berg), plus the enforcement additions (custom lint rule, module-boundary config, ADR stub) the change necessitates — in whatever tool the target ecosystem uses.
- **Audit deliverables:** a Markdown report structured as in `references/mode-audit.md`, grouping findings by pillar, each finding citing its rule number, severity, concrete remediation, and the enforcer category (plus a specific tool recommendation if one is idiomatic for the target language).
- **Bootstrap deliverables:** configuration files appropriate to the stack, an ADR directory with ADR-0001 explaining adoption, a filled CLAUDE.md fragment, and a PR template.

## When the user pushes back

The convention is demanding. Users may argue that a specific rule is overkill for their context. Respond as follows:

- If their argument is cognitive-load-based ("this makes the code harder to read for *everyone*"), take it seriously — the convention exists to reduce cognitive load; a rule that increases it in a specific case may deserve exemption. Document the exemption as an ADR.
- If their argument is effort-based ("setting up branded types is too much work"), the rule stands. The convention's entire premise is that seniors trade effort-below-the-waterline for frictionlessness-above. Name the tradeoff explicitly.
- If their argument is "we don't have juniors," redirect to the AI-agent rationale. Autonomous agents are the new juniors and their error modes are worse.
- If their argument is "this language doesn't really support that pattern," **it is probably true and probably matters**. Check the language-native-support matrix in `references/rules.md` for that specific rule. Acknowledge the gap, propose the closest available enforcer, note the residual risk that must be covered by review.
- If they insist on violating a rule, produce the code they asked for but include a clearly-marked comment (in the language's comment syntax) indicating `CONVENTION: violates §X.Y — see ADR-NNNN` and open an ADR stub documenting the exemption.

## Additional resources

- For the 20 normative rules with full rationale, escape hatches, and the language-native-support matrix, see [references/rules.md](references/rules.md)
- For per-language tool catalogs (A–F), tool-selection discipline, and the full rule→enforcer-category mapping, see [references/enforcement-patterns.md](references/enforcement-patterns.md)
- For anti-pattern recognition — load in Audit mode and in any refactor task — see [references/anti-patterns.md](references/anti-patterns.md)
- For Authoring-mode step sequence and the Design Review sub-branch, see [references/mode-authoring.md](references/mode-authoring.md)
- For Audit-mode step sequence and findings-report structure, see [references/mode-audit.md](references/mode-audit.md)
- For Bootstrap-mode step sequence and scaffold-generation flow, see [references/mode-bootstrap.md](references/mode-bootstrap.md)
- For the Bootstrap-mode ADR skeleton template, see [assets/templates/adr.md](assets/templates/adr.md)
- For the Bootstrap-mode ADR-0001 adoption example, see [assets/templates/ADR-0001-adopt-iceberg-convention.md](assets/templates/ADR-0001-adopt-iceberg-convention.md)
- For the Bootstrap-mode project CLAUDE.md fragment, see [assets/templates/CLAUDE.md-fragment.md](assets/templates/CLAUDE.md-fragment.md)
- For the Bootstrap-mode pull-request template, see [assets/templates/PULL_REQUEST_TEMPLATE.md](assets/templates/PULL_REQUEST_TEMPLATE.md)

Now, per the §"When to load each reference" table above, MUST invoke `Read` on the mode file matching the selected mode, and proceed.
