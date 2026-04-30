# CLAUDE.md Fragment — Iceberg Convention Activation

Copy the block below into the project's `CLAUDE.md` (or append to an existing one). Its purpose is to tell Claude Code, for this specific repo:

1. That the project follows the Iceberg Convention.
2. Where the tip is and where the berg is in this repo's layout.
3. Which enforcers are wired up, *by category and tool*, so Claude doesn't propose redundant ones.
4. Any project-specific exemptions from defaults, with rationale.

The fragment is written language-neutrally. Replace every `{{ placeholder }}` with project-specific values before committing. The structure is stable across languages; only the specific tool names change.

---

## BEGIN FRAGMENT — paste below

```markdown
## Architecture: Iceberg Convention

This repository follows the Iceberg Convention (asymmetric complexity management).
Primary language(s): {{ e.g., TypeScript + Rust }}.
Full rules: [link to the skill's rules.md or to ADR-0001].

### Layer layout

The "tip" is business-logic code that is read and modified frequently. The "berg"
is infrastructure code that is authored by seniors and rarely touched.

**Tip (above the airgap):**
- {{ path }} — e.g., `src/features/**`
- {{ path }} — e.g., `src/app/**`
- {{ path }} — e.g., `src/domain/**` (branded types and pure rules only)

**Berg (below the airgap):**
- {{ path }} — e.g., `src/infra/**`
- {{ path }} — e.g., `src/platform/**`
- {{ path }} — e.g., `src/adapters/**`

When I ask you to change behavior, the change almost always belongs in the tip.
If a task seems to require berg changes, confirm with me before proceeding.

### Active enforcers (by category)

These checks run in CI and block merges. Do not propose adding enforcers that
already exist. Do not silence these checks.

- **Category A — Module boundary:** {{ tool, e.g., dependency-cruiser / ArchUnit / import-linter / cargo-deny }}, config at {{ path }}. Enforces §1.2.
- **Category B — AST-level linter:** {{ tool, e.g., ESLint / detekt / ruff / clippy / Roslyn analyzers }}, with custom rules package at {{ path }}. Enforces §2.3, §3.1, §3.3, §4.1, §4.2, §4.4, §5.4.
- **Category C — Type-level:** {{ language's native mechanism, e.g., TypeScript strict + Brand<K,T> pattern / Kotlin value classes + sealed classes / Rust newtypes + enums / Python NewType + assert_never }}. Enforces §3.1, §3.2, §3.4.
- **Category D — Purity:** {{ mechanism, e.g., pure-pragma lint / crate-boundary / IO monad }}. Enforces §1.3.
- **Category E — Tracing:** {{ tool, e.g., OpenTelemetry {{ language }} SDK with auto-instrumentation for {{ framework }} }}. Enforces §5.1.
- **Category F — PR-level:** {{ CI platform, e.g., GitHub Actions / GitLab CI }}, workflow at {{ path }}. Enforces §5.2 (ADR reference on infra PRs), §2.4 (custom-rules tests run).

### Language-specific gaps and compensations

{{ Identify rules that this language does not enforce as strongly as others.
   For each gap, name the compensation in place. If there are no gaps, say
   "None." explicitly — a silent list signals tacit knowledge.

   Examples:

   - §3.1 (no raw scalars): Python provides only check-time branding via
     NewType; runtime coercion can bypass. Compensation: Pydantic model
     validation at all HTTP/DB boundaries, enforced by Category A import
     restrictions on where raw strings may enter the domain.

   - §3.2 (illegal states unrepresentable): Go has no native sum types.
     Compensation: interface with explicit implementations + exhaustiveness
     linter (exhaustive) + property-based tests for transition correctness.

   - §3.4 (exhaustiveness): Not natively supported in Go without third-party
     linters. Compensation: as above. }}

### Project-specific invariants

{{ Rules that are project-specific, beyond the generic convention.
   Each must name its enforcer. Examples:

   - Every new branded type goes in {{ path }}. Each type has a validation
     constructor in the same file. No other file may construct a branded value
     via direct coercion — enforced by {{ custom-lint-rule-name }}.

   - Every async lifecycle is modeled as a discriminated union FSM. Canonical
     example: {{ path }}. Libraries approved for machines with ≥6 states or
     nested state: {{ list }}.

   - Every cross-boundary call in the berg is wrapped in an OpenTelemetry span
     at adapter construction. Pattern: {{ path }}.

   - Logging: free-form output calls are banned in the tip. Use the structured
     logger from {{ path }}, imported only in the berg. }}

### Exemptions (with rationale)

{{ List any documented deviations. Each must reference an ADR. If there are
   no exemptions, say "None." explicitly.

   Example:
   - §1.1 exemption in framework-provided suspense primitives: {{ framework }}
     returns {{ async-primitive-type }} natively from {{ construct }}; this is
     the framework-provided suspense seam and does not count as a §1.1
     violation. Permitted in {{ paths }}. See ADR-{{ number }}. }}

### Working under the convention

When I ask you to:

- **Write a new feature** — treat it as tip-layer work unless the request
  explicitly involves infrastructure. Start from the branded-types registry
  and the FSM pattern if async.
- **Add a new domain concept** — add the branded type + validation constructor
  to {{ path }} in the same PR. Do not introduce raw primitives for domain
  identifiers.
- **Refactor something "to be simpler"** — simpler means "lower cognitive load
  for a reader who has never seen the code before." Reach for discriminated
  unions, named functions over boolean flags, and early returns. Do not reach
  for clever abstractions that compress lines at the cost of readability.
- **Add infrastructure** — open an ADR alongside the change. Reference the ADR
  number in the PR description; the CI bot checks for this.
- **Write a custom lint rule** — use the project's existing custom-rules
  package at {{ path }}. Every rule needs rationale + fix guidance + ADR link
  (§2.2) and snapshot tests (§2.4).

### Answer in this style

- Cite rule numbers when explaining decisions (e.g., "moved to the berg per §1.2").
- When a proposed change would violate a rule, state the rule and propose the
  compliant alternative. Do not silently re-shape the request.
- When a rule's enforcement mechanism is missing, flag it explicitly in the PR
  description as `ENFORCEMENT GAP: §X.Y — no mechanical enforcer yet, review-only`.
- When the target language has weak support for a rule, name the gap and the
  compensation in place. Do not pretend equivalence with stronger-enforcement
  languages.
```

## END FRAGMENT

## How Claude Code uses this

When Claude Code reads the project's CLAUDE.md, the fragment above:

- Tells it the project is Iceberg-governed without needing the user to mention the convention by name.
- Supplies the path globs, so when Claude writes a file under a tip path, it knows which rules apply.
- Names the active enforcers by category and tool, so Claude doesn't propose installing things that already exist.
- Documents language-specific gaps, so Claude doesn't over-promise enforcement that the language cannot provide.
- Lists exemptions with ADR links, so Claude doesn't flag legitimate framework idioms as violations.

## Checklist before committing

- [ ] Every `{{ placeholder }}` replaced.
- [ ] The "Active enforcers" list reflects reality (run each named tool and confirm it actually executes).
- [ ] The "Language-specific gaps" section says "None." explicitly if there are no gaps, or lists gaps with concrete compensations.
- [ ] The "Project-specific invariants" section lists only things that differ from or extend the generic convention — no restatement of generic rules.
- [ ] The "Exemptions" section explicitly says "None." if empty. Silent empty sections create tacit knowledge.
- [ ] Every exemption references a committed ADR. Exemptions without ADRs are folklore.
