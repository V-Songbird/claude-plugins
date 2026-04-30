# Mode: Bootstrap

You are setting up the Iceberg Convention's enforcement scaffolding in a fresh project, or retrofitting it into an existing project that has decided to adopt the convention. This file is the procedure.

## Workflow opener — MUST invoke `TodoWrite`

On entering Bootstrap mode, MUST invoke `TodoWrite`:

```
TodoWrite
  todos: [
    { content: "Confirm premise (team, stack, greenfield vs retrofit)", activeForm: "Confirming premise",                 status: "pending" },
    { content: "Plan-gate the bootstrap design",                        activeForm: "Plan-gating the bootstrap design",   status: "pending" },
    { content: "Establish layering (tip/berg)",                         activeForm: "Establishing layering",              status: "pending" },
    { content: "Install Category A — module-boundary enforcer",         activeForm: "Installing module-boundary enforcer", status: "pending" },
    { content: "Install Category B — AST-level linter + custom rules",  activeForm: "Installing AST-level linter",        status: "pending" },
    { content: "Install Category C — type-level scaffolding",           activeForm: "Installing type-level scaffolding",  status: "pending" },
    { content: "Install Category D — purity enforcer",                  activeForm: "Installing purity enforcer",         status: "pending" },
    { content: "Install Category E — tracing instrumentation",          activeForm: "Installing tracing instrumentation", status: "pending" },
    { content: "Install ADR scaffolding + PR template + CLAUDE.md",     activeForm: "Installing ADR + PR + CLAUDE.md",    status: "pending" },
    { content: "Wire CI as blocking checks",                            activeForm: "Wiring CI",                          status: "pending" },
    { content: "Install quarterly-audit reminder",                      activeForm: "Installing quarterly-audit reminder", status: "pending" },
    { content: "Verify the installation (9 deliberate-violation checks)", activeForm: "Verifying the installation",       status: "pending" }
  ]
```

## Step 0 — Confirm the premise

Before installing tooling, MUST invoke `AskUserQuestion`:

```
AskUserQuestion
  questions: [{
    question: "Confirm the bootstrap context before proceeding.",
    header: "Bootstrap",
    multiSelect: true,
    options: [
      { label: "Team aligned",   description: "All seniors have agreed to invest below-waterline effort." },
      { label: "Single language", description: "One primary language; auto-detect from manifests." },
      { label: "Greenfield",     description: "No legacy code to grandfather; strict enforcement from day one." },
      { label: "Retrofit",       description: "Existing codebase; warn → error migration plan required." }
    ]
  }]
```

Rationale each option encodes:

- **Team aligned.** The convention requires seniors to invest effort below the waterline for juniors' benefit above it. Adopting it against a senior's wishes produces un-maintained scaffolding.
- **Single vs multi-language.** Multi-language monorepos need per-language idiomatic tooling but share one ADR directory and PR workflow.
- **Greenfield vs Retrofit.** You cannot apply §3.1 (no raw scalars) to a codebase with 10,000 existing raw-string usages without a migration plan.

If Retrofit is selected, MUST invoke a second `AskUserQuestion`:

```
AskUserQuestion
  questions: [{
    question: "Retrofit migration policy?",
    header: "Retrofit",
    multiSelect: false,
    options: [
      { label: "Warn then escalate", description: "Introduce rules at warn severity; escalate to error after backfill." },
      { label: "Error immediately",  description: "Apply error severity now; accept the backfill debt upfront." },
      { label: "Grandfather all",    description: "Suppress existing violations with `@iceberg-grandfathered` pragma." },
      { label: "Decide per rule",    description: "Claude recommends per-rule severity based on violation density." }
    ]
  }]
```

The `@iceberg-grandfathered: <reason>` pragma itself becomes a todo list — surface the count back to the user after Step 10 verification.

## Plan gate — MUST invoke `EnterPlanMode` before Step 1

After Step 0 premise confirmation completes, MUST invoke `EnterPlanMode` (no params).

Draft the plan with these sections:

- **Stack detected** (from the stack-detection recipe in `convention/SKILL.md`)
- **Layering scheme proposed** (feature-sliced vs hexagonal)
- **Enforcer inventory** — for each Category A–F, the specific tool proposed for this stack, with justification
- **Files to create** (enumerated, with paths)
- **Files to modify**
- **Migration plan** (retrofit only): warn → error escalation timeline
- **Risks and known language gaps** (per the language-native-support matrix)

MUST invoke `ExitPlanMode` presenting that plan for user approval. Do NOT begin Steps 1–10 until the user approves.

For Bash commands the plan pre-authorizes (install commands, CI file edits, `mkdir`, deliberate-violation cleanup), declare them in the project's `settings.json` under `permissions.allow` rather than relying on `ExitPlanMode.allowedPrompts` (not in the canonical tools reference and unreliable). Example entries to propose in the plan: `"Bash(npm i -D *)"`, `"Bash(cargo add --dev *)"`, `"Bash(mkdir -p docs/adr)"`, `"Edit"`, `"Write"`. Deny-wins precedence still applies — check any managed or user-level deny before finalizing.

## Step 1 — Establish the layering

If the repo doesn't have a clear tip/berg separation, that is the first thing to fix. Without it, every other rule is unenforceable.

Propose a layout. The two common templates:

### Feature-sliced

Works well for frontend-heavy codebases, SPAs, and mobile apps.

```
<src root>/
├── features/           # tip: business features
│   └── <feature>/
├── domain/             # tip: shared domain types, pure logic
│   ├── types/          # branded types
│   └── rules/          # pure business rules
├── infra/              # berg: infrastructure adapters
│   ├── persistence/
│   ├── transport/
│   ├── observability/
│   └── flags/
└── platform/           # berg: cross-cutting concerns (auth, telemetry, config)
```

### Hexagonal / DDD-style

Works well for backends, especially JVM, .NET, Python, Go, Elixir.

```
<src root>/
├── application/        # tip: use cases, orchestration
├── domain/             # tip: entities, value objects, pure logic
├── interfaces/         # tip: HTTP handlers, CLI commands, UI
└── infrastructure/     # berg: everything else
```

Create the directory skeleton and a `README.md` per top-level directory explaining what belongs there. Do not skip the READMEs — they are the cheapest form of "layering discoverable from the filesystem."

Adapt the layout to the language's packaging conventions. In Rust, layers usually become crates in a workspace. In Elixir/Erlang, applications. In Python, packages under a project root. In Kotlin/Java, Gradle subprojects. Use whatever the ecosystem considers a first-class module boundary.

## Step 2 — Install the module-boundary enforcer (Category A)

This is the primary enforcer for §1.2 and a key contributor to §1.3.

1. Identify the idiomatic module-boundary tool for the target language. MUST invoke `Read` on `${CLAUDE_SKILL_DIR}/references/enforcement-patterns.md` §A for representatives. If the idiomatic tool for this stack is still unknown, MUST invoke `WebSearch` with `query: "<language> module boundary architecture test idiomatic 2025"`.
2. MUST invoke `Bash` to install — adapt the command to the detected stack:

```
Bash
  command:     "<stack-conditional install command: e.g. `npm i -D dependency-cruiser`, `pip install import-linter`, `cargo add --dev cargo-deny`, `dotnet add package NetArchTest.Rules`, etc.>"
  description: "Installing Category A module-boundary enforcer"
  timeout:     300000
  run_in_background: true
```

For long-running installs, after dispatch MUST invoke `Monitor` with `description: "Monitoring module-boundary-enforcer install"` on the returned task.

3. MUST invoke `Write` (or `Edit` if the config file exists) to configure a single baseline rule: *no imports from berg paths into tip paths*.
4. Wire it into CI as a **blocking** check — MUST invoke `Edit` on `.github/workflows/*.yml` (or the project's CI config) adding the new enforcer to the required checks. Non-blocking means does not exist (§2.1).
5. **Verification test:** MUST invoke `Write` to create a deliberate violation file (e.g., `features/__iceberg-verify.ts` importing from `infra/`). MUST invoke `Bash` with `command: "<local equivalent of the CI check, e.g. npx depcruise --config .dependency-cruiser.js src>"`, `description: "Verifying Category A blocks violations"`, `timeout: 120000`. Confirm non-zero exit. Then MUST invoke `Bash` with `command: "rm features/__iceberg-verify.ts"` (or `del` on Windows) to revert. If you skip this step, the config may be silently passing everything.

## Step 3 — Install the AST-level linter and custom-rules package (Category B)

This is the primary enforcer for §2.3, §3.1, §3.3, §4.1, §4.2, §4.4, §5.4.

1. Identify the project's existing linter via the `Glob` results from Step 0.3. Almost every mainstream ecosystem has one. Use it; do NOT introduce a second linter.
2. MUST invoke `Bash` with `command: "mkdir -p <rules-package-dir>"`, `description: "Scaffolding custom rules package"`. Name it something discoverable: `convention-rules`, `iceberg-rules`, `eslint-plugin-internal`, `detekt-rules-internal`, etc. Adapt the artifact format to the linter's conventions.
3. MUST invoke `Write` to create the package manifest (e.g., `package.json`, `Cargo.toml`, `pyproject.toml`) and the test harness entry point.
4. MUST invoke `Write` three times to author the first three custom rules. Pick the rules with highest leverage for the team's dominant pain points — commonly (a) no raw scalars in domain signatures, (b) no direct coercion into branded types outside the constructor module, (c) no unstructured output calls in tip files. Each rule file MUST include the §2.2-compliant message (rationale + fix + ADR link).
5. MUST invoke `Write` for each rule's passing-case and failing-case test fixtures (§2.4: one passing, one failing per rule).
6. MUST invoke `Edit` on the CI config to register a job that runs the custom-rules package test suite on every PR.

## Step 4 — Install the type-level scaffolding (Category C)

This is the primary enforcer for §3.1, §3.2, §3.4.

1. **Branded types.** MUST invoke `Write` to create the project's initial branded-type registry file (path per language convention: `src/domain/types/brands.ts`, `src/domain/types.rs`, `domain/types.py`, etc.), populating it with 1–2 example types (UserId, OrderId, Money). Use the language's idiomatic nominal-type mechanism — newtype struct (Rust), value class (Kotlin), opaque alias (Scala 3), brand intersection (TypeScript), record struct with private constructor (C#), `NewType` (Python), `type Foo string` (Go; weakest).
2. **Discriminated unions.** Wherever the project has an entity with mutually exclusive states, MUST invoke `Edit` or `Write` to replace optional-field records with the idiomatic sum-type mechanism — native enums with variants (Rust), sealed classes (Kotlin), sealed traits (Scala), discriminated unions (TypeScript), `OneOf`-style library (C#), Pydantic models with `Literal` discriminators (Python), tagged interfaces (Go; weakest).
3. **Exhaustiveness.** MUST invoke `Edit` on the linter config (e.g., `.eslintrc.json`, `detekt.yml`) to enable the language's native exhaustiveness check — TS `@typescript-eslint/switch-exhaustiveness-check` at `error`, Kotlin sealed `when` warnings as errors, Python `mypy --strict` (implies `assert_never`), etc.
4. **Gap reporting.** If the language has weak native support (Go, dynamic languages), MUST invoke `Write` to `docs/adr/<next>-type-gap-compensation.md` documenting the gap, and compensate with heavier Category B rules (added in Step 3) and boundary validation tests.

## Step 5 — Install the purity enforcer (Category D)

This is the primary enforcer for §1.3.

1. Decide the approach: module-boundary (the pure core is a separate module/crate/package with a restricted dependency graph), AST-level pragma (files marked pure cannot call I/O, time, randomness), or language-level effect tracking (Haskell, PureScript).
2. **AST-level approach:** MUST invoke `Write` to author a custom lint rule (in the custom-rules package from Step 3) that reads the pure pragma and bans calls to the language's impurity surface — current time, random generators, filesystem, network, DB, logger, process environment, mutable globals.
3. **Module-boundary approach:** MUST invoke `Edit` on the Category A enforcer's config (from Step 2) to restrict the pure module's dependency graph.
4. Verify: MUST invoke `Write` to insert a `Date.now()` / current-time read in a pure-marked file, then MUST invoke `Bash` with `command: "<project's lint command>"`, `description: "Verifying Category D blocks impurity"`. Expect non-zero exit. MUST revert the violation via `Edit` or `Bash(rm <path>)`.

## Step 6 — Install tracing instrumentation (Category E)

This is the primary enforcer for §5.1.

1. MUST invoke `Bash` with `command: "<stack-conditional SDK install, e.g. `npm i @opentelemetry/api @opentelemetry/sdk-node`, `pip install opentelemetry-api opentelemetry-sdk`, `cargo add opentelemetry tracing tracing-opentelemetry`>"`, `description: "Installing OpenTelemetry SDK"`, `timeout: 300000`.
2. MUST invoke `Edit` on the berg layer's bootstrap entry point to enable auto-instrumentation for the project's HTTP, DB, and queue libraries.
3. MUST invoke `Edit` on each adapter file in the berg layer to wrap construction with a custom span. Naming: `<service>.<operation>.<entity>`. MUST invoke `Write` to `docs/tracing.md` defining the attribute spec.
4. MUST invoke `Write` to add a custom lint rule (in the custom-rules package from Step 3) banning free-form output calls (print, console, etc.) in tip-layer files — structured logging is allowed only in the berg's logger wrapper.

## Step 7 — Install the ADR scaffolding

This is the primary enforcer for §5.2.

1. MUST invoke `Bash` with `command: "mkdir -p docs/adr"`, `description: "Creating ADR directory"`.
2. MUST invoke `Read` on `${CLAUDE_SKILL_DIR}/assets/templates/ADR-0001-adopt-iceberg-convention.md`. Substitute the `{{placeholder}}` values against the detected project context, then MUST invoke `Write` to `docs/adr/0001-adopt-iceberg-convention.md`.
3. MUST invoke `Read` on `${CLAUDE_SKILL_DIR}/assets/templates/adr.md` (ADR skeleton). Using it as a base, MUST invoke `Write` to `docs/adr/0002-layering-scheme.md` documenting the layering scheme chosen in Step 1.
4. Repeat: MUST invoke `Write` to `docs/adr/0003-type-level-mechanisms.md` documenting type-level mechanisms chosen in Step 4, including language gaps and their compensations.
5. Install a PR-level check (Category F): MUST invoke `Write` to `.github/workflows/iceberg-adr-check.yml` (or the equivalent CI path) that blocks PRs touching infrastructure paths without an ADR reference in the PR body.

## Step 8 — Install the design-review checklist and CLAUDE.md

1. MUST invoke `Read` on `${CLAUDE_SKILL_DIR}/assets/templates/PULL_REQUEST_TEMPLATE.md`, then MUST invoke `Write` to the project's conventional location (`.github/PULL_REQUEST_TEMPLATE.md` on GitHub, `.gitlab/merge_request_templates/Default.md` on GitLab). The template contains the 8-question design-review checklist plus mandatory sections for layer affected, rules invoked, and ADR references.
2. MUST invoke `Read` on `${CLAUDE_SKILL_DIR}/assets/templates/CLAUDE.md-fragment.md`. If the project already has `CLAUDE.md`, MUST invoke `Edit` to append the fragment; otherwise MUST invoke `Write` to create `CLAUDE.md`. Replace every `{{ placeholder }}` with project-specific values before committing. **Without this fragment, Claude Code cannot apply the convention correctly to this repository.**
3. Configure CI so that Category A, B, C, D enforcers are all blocking and surfaced behind a single aggregate status check (e.g., `iceberg-check`). MUST invoke `Edit` on the CI workflow file to add the aggregate job. Branch protection requires the aggregate, not the individual checks, so adding new enforcers doesn't require reconfiguring protection.

## Step 9 — Install the quarterly audit

If `gh` CLI is available, MUST invoke `Bash` with `command: "gh issue create --title 'Quarterly Iceberg Convention audit' --body 'Run mode-audit.md against current HEAD; report findings.' --label 'iceberg,recurring'"`, `description: "Creating quarterly-audit GitHub issue"`. Otherwise, this step is manual (calendar reminder or project-management tool) — emit a one-line prose note to the user that no tool call is available and the reminder must be set manually. The audit runs `mode-audit.md` and specifically checks:

- Are all rules in the team's style guide mapped to concrete enforcers? (§2.1 — the meta-rule.)
- Are there custom lint rules that have drifted (no longer match current patterns)?
- Are there ADRs that have been contradicted by later decisions and need deprecation markers?
- Is the custom-rules package test suite still passing?
- For languages with weak native support in any category — has the compensation (heavier review, boundary tests) held up?

## Step 10 — Verify the installation

Do NOT declare bootstrap complete until every check below passes. Each check is a named `Bash` (or `Glob`+`Grep`) invocation, not a prose claim.

**Check 1 — Category A blocks cross-layer imports.** MUST invoke `Write` to create a deliberate violation (tip file importing from berg), then MUST invoke `Bash` with `command: "<the project's category-A command, e.g. npx depcruise src>"`, `description: "Verifying Category A blocks cross-layer import"`, `timeout: 120000`. Expect non-zero exit. MUST revert the file via `Bash(rm <violation-path>)` or `Edit`.

**Check 2 — Categories B+C reject raw primitives in domain signatures.** MUST invoke `Write` to create a domain function with a raw `string` / `number` parameter. MUST invoke `Bash` with the project's lint + typecheck commands (e.g., `npm run lint && npm run typecheck`), `description: "Verifying B+C reject raw primitive"`. Expect non-zero exit. Revert.

**Check 3 — Category D blocks I/O in a pure-marked file.** MUST invoke `Write` to insert a `Date.now()` / `fs.readFile` / equivalent into a file marked pure. MUST invoke `Bash` with the project's lint command, `description: "Verifying D blocks I/O in pure file"`. Expect non-zero exit. Revert.

**Check 4 — Custom-rules package has its own green test suite (§2.4).** MUST invoke `Bash` with `command: "<the custom-rules test command>"`, `description: "Running custom-rules test suite"`, `timeout: 180000`. Expect zero exit.

**Check 5 — ADR-0001 exists and has no unfilled placeholders.** MUST invoke `Read` on `docs/adr/0001-adopt-iceberg-convention.md`, then MUST invoke `Grep` with `pattern: "\\{\\{"`, `path: "docs/adr/0001-adopt-iceberg-convention.md"`, `output_mode: "count"`. Expect count 0.

**Check 6 — CLAUDE.md contains the activation fragment and no unfilled placeholders.** MUST invoke `Read` on `CLAUDE.md`, then MUST invoke `Grep` with `pattern: "Iceberg Convention|tip paths|berg paths"`, `path: "CLAUDE.md"`, `output_mode: "count"`. Expect ≥3. Then MUST invoke `Grep` with `pattern: "\\{\\{"`, `path: "CLAUDE.md"`, `output_mode: "count"`. Expect 0.

**Check 7 — PR template installed with 8-question checklist.** MUST invoke `Grep` with `pattern: "^\\s*- \\[ \\]"`, `path: "<PR template path>"`, `output_mode: "count"`. Expect ≥8.

**Check 8 — CI runs all enforcers as blocking.** MUST invoke `Grep` with `pattern: "iceberg-check|depcruise|eslint|typecheck|architecture-test"`, `glob: ".github/workflows/**"` (or equivalent CI glob), `output_mode: "content"`. Manually verify each appears in a `required` / `always` / blocking context.

**Check 9 — At least one tip and one berg example exist.** MUST invoke `Glob` with `pattern: "{features,domain,app}/**/*.<primary-ext>"` (tip) and with `pattern: "{infra,adapters,platform}/**/*.<primary-ext>"` (berg). Expect ≥1 match each.

Any FAIL blocks bootstrap completion. Address, then re-run the failing check.

## Output structure

Return to the user:

1. **Summary** — what was installed, what's blocking in CI, what's advisory.
2. **Files created** — full list with paths.
3. **Files modified** — existing files that now reference the new scaffolding.
4. **Enforcer inventory** — for each of Categories A–F, which tool was installed and what it covers. If a category is gapped (no idiomatic tool for this language), say so.
5. **Migration plan** (retrofit only) — rules at "warn" vs "error", timeline, estimated backfill effort.
6. **First three ADRs to write** — prompts, not full content.
7. **Known gaps** — rules the language/stack cannot automatically enforce and must stay at review-level, with the compensations in place.

## Common bootstrap pitfalls

- **Shipping enforcement at "warn" forever.** The plan must include escalation to "error." Warnings that never escalate are folklore with extra steps.
- **Creating the custom-rules package empty and never adding to it.** The first three rules should be installed during bootstrap, not deferred.
- **Forgetting the PR template.** Without the design-review checklist at the author's fingertips, the convention never reaches the human judgment step.
- **Over-installing.** Don't add every possible lint rule on day 1. Pick the three that give most leverage for the team's dominant bug patterns.
- **Under-documenting.** If the ADRs don't explain *why*, the next team will rip the scaffolding out. §5.2 is not optional even during bootstrap.
- **Treating a prototype as an Iceberg candidate.** The convention has overhead. Three-file scripts and internal tooling probably do not need it. Be honest about fit.
- **Copy-pasting tooling choices across languages.** The tool that satisfies Category A for TypeScript (dependency-cruiser) is wrong for Rust (crate boundaries + cargo-deny). Detect the language, then pick the idiomatic tool per category.
- **Pretending a language-level gap doesn't exist.** If the target is Go or Python, say so. Compensate honestly. Do not ship scaffolding that claims equivalence with Rust or Kotlin.
