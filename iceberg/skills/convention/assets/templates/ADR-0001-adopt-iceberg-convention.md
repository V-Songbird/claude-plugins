# ADR-0001: Adopt the Iceberg Convention

- **Status:** Accepted
- **Date:** {{ YYYY-MM-DD }}
- **Deciders:** {{ Tech lead name }}, {{ Architect name }}, {{ VP Eng name }}
- **Related rules:** Iceberg §1.1–§5.4 (all)
- **Supersedes:** —

## Context

Our codebase has grown from {{ N }} engineers to {{ M }} in {{ K }} months. In the last two quarters we observed:

- **Onboarding velocity dropped from ~{{ X }} weeks to ~{{ Y }} weeks time-to-first-PR.** Exit surveys cite "unclear where code lives" and "afraid of breaking things I don't understand" as the top two friction points.
- **{{ Z }}% of production incidents in {{ recent quarter }} originated from code paths where a value of one kind was passed where another kind was expected.** The compiler accepted these passes because both kinds were the same underlying primitive type.
- **{{ N }} pull requests in {{ recent quarter }} were rejected for "architectural" reasons after a junior had fully implemented them.** Median rework effort per rejection: ~{{ K }} days.
- **Our async state handling is inconsistent.** We have {{ N }} UI components using some combination of `isLoading`, `isError`, `hasRetried`, `hasFetched` boolean flags. {{ K }} components have a documented "impossible but observed in production" bug involving two of these flags being true simultaneously.

Root cause analysis points in one direction: the implicit, tacit architectural rules our senior engineers hold in their heads are not being transferred to less-experienced engineers. Code review is arriving too late in the process to prevent the cost. Our architectural rules live in wikis, style guides, and tribal knowledge — not in the compiler.

The Iceberg Convention is a framework for "asymmetric complexity management": senior engineers absorb system complexity below an architectural airgap, exposing a simpler, type-safe surface above it. Every rule is backed by a mechanical enforcer. It explicitly targets the failure modes we are experiencing.

The convention is language-agnostic. Its rules describe patterns; the enforcement tools are ecosystem-specific. Our implementation (see ADR-0003 for specifics) uses the idiomatic tools for our stack ({{ primary language(s) }}).

## Decision

We adopt the Iceberg Convention as the governing architectural convention for this repository, effective {{ date }}.

Concretely:

1. We establish a **tip/berg layer separation** using the {{ feature-sliced | hexagonal / DDD }} layout (see ADR-0002 for specifics).
2. We install the convention's **mechanical enforcers** across the six enforcement categories (see ADR-0003):
   - Module-boundary enforcer (Category A) for the airgap (§1.2).
   - AST-level linter with a custom-rules package (Category B) for cognitive hazards, branded-type discipline, state-mutation discipline, log-as-trace (§2.3, §3.1, §3.3, §4.1, §4.2, §4.4, §5.4).
   - Type-level scaffolding (Category C) via the language's native mechanism for branded types, discriminated unions, and exhaustiveness (§3.1, §3.2, §3.4).
   - Purity enforcer (Category D) for the functional core (§1.3).
   - OpenTelemetry instrumentation (Category E) at adapter boundaries (§5.1).
   - PR-level checks (Category F) for ADR reference requirements on infrastructure PRs (§5.2) and custom-rule test-suite runs (§2.4).
3. We migrate existing code according to the plan in "Migration" below. Hard deadlines: airgap enforcement at error severity by end of {{ quarter }}; branded types for all domain IDs by end of {{ quarter }}; FSM migration for all async flows by end of {{ quarter }}.
4. We add a **PR template** containing the 8-question design-review checklist for non-trivial changes, and a **CI workflow** that runs all Iceberg enforcers as blocking checks.
5. The rules live in `docs/conventions/iceberg.md`. The enforcement configurations live with their tools. **If a rule is stated in the convention doc but not mapped to a concrete enforcer, it is deleted from the doc** (Iceberg §2.1).

## Consequences

### Positive

- **Onboarding load shifts from humans to the compiler.** Instead of a senior explaining the convention in PR comments, the build fails locally with a message explaining the rule.
- **Whole classes of bugs become unrepresentable.** Passing one kind of identifier where another is expected stops being a production incident and starts being a compile error (modulo language-level gaps — see below).
- **Code review becomes about business correctness, not architectural compliance.** Seniors stop serving as human linters.
- **AI coding agents gain the same guardrails as human juniors.** Their error modes are caught by the same mechanisms.
- **Mentorship scales without synchronous effort.** Juniors can experiment freely because illegal code does not compile.

### Negative

- **Upfront senior investment is substantial.** Bootstrapping the custom-rules package, branded-type scaffolding, and FSM templates will consume roughly {{ N }} senior-weeks. We accept this cost as investment against the recurring cost of PR reviews and production incidents.
- **Retrofit migration is disruptive.** We have {{ N }} files using raw primitives for domain identifiers. The migration will require touching most of these files. We mitigate via the `@scalar-allowed: <reason>` exemption pragma during {{ quarter }}, escalating to error severity in {{ next quarter }}.
- **Some language idioms are banned at the tip.** Accumulator-based reductions, nested conditional expressions, boolean flag parameters. Some engineers will find this limiting; we accept the constraint because the alternative is the status quo cognitive load on juniors.
- **Senior engineers must learn to author custom lint rules for our linter.** This is a new skill for most of the team. We pair the first three rule authorings with the tech lead as a training exercise.

### Neutral

- The convention is demanding but not ideological. The 8-question design-review checklist includes escape hatches (with ADRs) for legitimate exceptions.
- Our framework choices are not changed by this decision. The convention works alongside whatever frameworks we already use.
- We remain free to deviate from specific rules with a documented ADR. We are not adopting the convention as dogma.

### Language-specific considerations

{{ Fill in honestly based on the target language. Examples:

   - "Our stack is primarily Rust. Rust provides strong native support for all Pillar 3 rules (newtypes, enums with variants, exhaustive match). No significant gaps."

   - "Our stack is primarily Python. Python provides only check-time type-level enforcement via NewType; runtime coercion can bypass branded-type discipline. We compensate with Pydantic validation at all HTTP and DB boundaries and a stricter AST-level linter at domain boundaries."

   - "Our stack is primarily Go. Go has no native sum types or exhaustiveness checking. We compensate with interface-with-known-implementations plus the exhaustive linter, plus property-based tests. §3.2 and §3.4 remain weaker than in stronger-typed languages; residual risk is covered by heavier review on state-machine changes." }}

## Alternatives considered

### Alternative A: Invest in synchronous mentorship (weekly architecture office hours, mandatory pair programming for juniors)

**Why rejected:** We tried this in {{ prior quarter }}. It consumed ~{{ N }}% of senior engineering capacity and produced uneven results. The knowledge transfer was real but fragile — juniors retained ~{{ X }}% of what was covered in office hours (per post-session quizzes). The Iceberg Convention's "compiler-driven mentorship" model is asynchronous and retains 100% of what it encodes.

### Alternative B: Stricter code review rubric + required checklist

**Why rejected:** Checklists rot. The rubric we drafted in {{ prior quarter }} was followed for six weeks and then quietly ignored. Rules that are not mechanically enforced do not survive (Iceberg Axiom A7). This alternative addresses the symptom (inconsistent reviews) but not the cause (tacit knowledge).

### Alternative C: Adopt a pre-packaged architecture (Hexagonal, Clean, Onion)

**Why rejected:** Those architectures prescribe specific layouts (ports, adapters, use cases) that are prescriptive about folder structure and class hierarchies. The Iceberg Convention is layout-agnostic — it prescribes *what must be true* (airgap, branded types, FSMs, enforcers) but not *how the directory tree must look*. We plan to borrow port/adapter vocabulary within the berg without adopting the full prescription.

### Alternative D: Do nothing; the pain will diminish as the team matures

**Why rejected:** The metrics indicate the opposite trajectory. Onboarding time grew from {{ X }} to {{ Y }} weeks *as* the team matured. The cognitive load is compounding, not diminishing.

## Enforcement

This ADR is meta — it adopts a convention rather than describing a single rule. Its enforcement is the existence of the individual enforcers described in subsequent ADRs.

- **Tool:** See ADR-0002 through ADR-0005 for per-pillar enforcement decisions.
- **Severity:** Error in CI for all enforcers by end of {{ quarter }}.
- **Exemption mechanism:** `@iceberg-grandfathered: <reason>` pragma for existing code during migration; `@scalar-allowed: <reason>` for deliberate raw-scalar exceptions at the tip. Both pragmas are greppable and will be audited quarterly.
- **Test coverage:** the custom-rules package includes snapshot tests for every rule it defines (one passing, one failing). Module-boundary enforcement is tested via deliberate-violation test commits that are verified to fail CI.

## Migration

### Phase 1 — Bootstrap ({{ sprints }})

- Install the six categories of enforcer (see ADR-0003) in their idiomatic tools for our stack.
- Add directory layout with a README per top-level directory.
- Move existing files into their correct layer. No behavioral changes.
- Rules at **warn** severity initially.

### Phase 2 — Backfill ({{ sprints }})

- Introduce branded types for {{ list of domain concepts }}. Migrate all usages.
- Replace boolean-flag state in components with discriminated union FSMs. Start with the {{ N }} components implicated in recent incidents.
- Install the first three custom linter rules.
- Rules escalate to **error** severity at the end of Phase 2.

### Phase 3 — Observability and ADRs ({{ sprints }})

- Wire OpenTelemetry auto-instrumentation at adapter construction.
- Backfill ADRs for existing architectural decisions that lack written rationale.
- Enable CI ADR-reference check on PRs touching infrastructure paths.

### Phase 4 — Audit and tighten ({{ sprints }})

- Run a full Iceberg audit against the migrated codebase.
- Tighten any rules still at warn to error.
- Establish the quarterly audit cadence.

## References

- The Iceberg Convention rules: `docs/conventions/iceberg.md` (and the `iceberg` Claude plugin).
- {{ Quarter }} incident retro: `docs/postmortems/{{ filename }}.md`.
- Onboarding exit survey data: `{{ link to analytics dashboard }}`.
- Prior art: Sandi Metz, "The Wrong Abstraction"; Hickey, "Simple Made Easy"; the Agentic Manifesto.
