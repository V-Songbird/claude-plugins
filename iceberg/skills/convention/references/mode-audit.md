# Mode: Audit

You are reviewing an existing codebase against the Iceberg Convention. Your deliverable is a structured findings report. This file is the procedure.

## Workflow opener — MUST invoke `TodoWrite`

On entering Audit mode, MUST invoke `TodoWrite`:

```
TodoWrite
  todos: [
    { content: "Resolve scope and detect stack",       activeForm: "Resolving scope and detecting stack",   status: "pending" },
    { content: "Run mechanical scans by pillar",       activeForm: "Running mechanical scans by pillar",    status: "pending" },
    { content: "Interpret findings and assign severity", activeForm: "Interpreting findings and assigning severity", status: "pending" },
    { content: "Produce the structured report",        activeForm: "Producing the structured report",       status: "pending" }
  ]
```

## Scale gate — decide main-session vs subagent

MUST invoke `Glob` with `pattern: "**/*.{ts,tsx,js,py,go,rs,kt,java,cs,rb,ex}"` (narrow to the primary detected language). Count the returned paths.

If count > 200, MUST invoke `Agent` — do NOT inline scans:

```
Agent
  subagent_type: "Explore"
  description:   "Iceberg audit scan for pillar <N>"
  prompt:        "<self-contained prompt: tip/berg paths, detected language, full list of Grep patterns below for the targeted pillar, expected output format as a findings table>"
  max_turns:     10
```

The `prompt` passed to `Agent` MUST be self-contained. Resolve scope, tip/berg paths, language, and scan patterns in THIS session via `AskUserQuestion` BEFORE the dispatch. The subagent MUST NOT be instructed to invoke `AskUserQuestion` — foreground subagents may be backgrounded (Ctrl+B), after which `AskUserQuestion` fails silently.

## Step 0 — Scope and stack detection

Before scanning, establish:

1. **Language(s).** Apply the stack-detection recipe from `convention/SKILL.md` (parallel `Glob` + `Read limit: 80` on manifests).
2. **Layering convention.** MUST invoke `Glob` with `pattern: "{features,domain,infra,adapters,platform,application,infrastructure,interfaces}/**"` to detect tip/berg separation. If no layering exists, **that is the top finding** and most other rules cannot be audited rigorously until layering is introduced.
3. **Existing enforcement.** MUST invoke `Glob` for the following to inventory Categories A–F coverage: `**/.dependency-cruiser.*`, `**/import-linter.cfg`, `**/archunit*`, `**/.eslintrc*`, `**/detekt.yml`, `**/ruff.toml`, `**/clippy.toml`, `**/depguard.yml`, `**/adr/**`, `**/docs/adr/**`. Do NOT flag what's already caught.
4. **Scope boundaries.** If the user did not specify scope, MUST invoke `AskUserQuestion`:

```
AskUserQuestion
  questions: [{
    question: "What scope should the audit cover?",
    header: "Scope",
    multiSelect: false,
    options: [
      { label: "Whole repo", description: "Every source file under the repo root." },
      { label: "Subpath",    description: "A named directory (e.g., features/) — specify in chat." },
      { label: "Current PR", description: "Only files changed on the current branch." },
      { label: "You decide", description: "Let Claude pick scope by repo size and request shape." }
    ]
  }]
```

## Step 1 — Mechanical scan by pillar

For each scan below, MUST invoke `Grep` with the named parameters. Adapt `pattern` to the detected language(s) — the convention governs every mainstream typed language. Skip to Step 2 interpretation only if a scan returns zero hits.

All `Grep` calls use `output_mode: "content"`, `-n: true`. Scope with `glob:` to tip or berg paths based on Step 0.2.

### 1.1 Airgap leakage (Pillar 1)

**Infrastructure imports in tip files (§1.2)** — MUST invoke `Grep`:

```
Grep
  pattern: "(from|import).*(infra|adapters|platform|infrastructure)"
  glob:    "{features,domain,app,application,interfaces,routes,pages}/**/*.{ts,tsx,js,py,go,rs,kt,java,cs,rb,ex}"
  output_mode: "content"
  -n:      true
```

**Async primitives in tip signatures (§1.1)** — MUST invoke `Grep`:

```
Grep
  pattern: "\\b(Promise|Observable|Task|Future|CompletableFuture|Mono|Flux|Coroutine|IO)<"
  glob:    "{features,domain,app,application,interfaces,routes,pages}/**/*.{ts,tsx,java,kt,scala,rs,cs}"
  output_mode: "content"
  -n:      true
```

**Direct I/O in tip files** — MUST invoke `Grep` with a pattern scoped to the detected HTTP/DB/logger clients (e.g., `axios|fetch|prisma|sequelize|logger\\.`). Use `glob:` to restrict to tip paths.

**God files (§1.4 proxy)** — resolve `<tip-roots>` from the layering paths detected in Step 0.2 (e.g., `features domain app`) and `<primary-ext>` from the primary language detected in Step 0.1 (e.g., `ts` for TypeScript). Then MUST invoke `Bash`:

```
Bash
  command:     "find <resolved-tip-roots> -name '*.<resolved-ext>' | xargs wc -l | sort -rn | head -20"
  description: "Listing largest tip-layer files"
  timeout:     30000
```

Substitute real values before firing — NEVER pass literal angle brackets. Example resolved command: `find features domain app -name '*.ts' | xargs wc -l | sort -rn | head -20`.

On Windows or when `find`/`wc` are unavailable, fall back to `Glob` on `{<tip-roots>}/**/*.<ext>`, then for the first 20 results MUST invoke `Read` with `file_path` set to each path and `limit: 1` (header sampling only — we just want the byte count, not content). Threshold: ~300 LOC in low-ceremony languages, ~800 in Java/C#.

### 1.2 Compiler-driven mentorship (Pillar 2)

**Enforcer inventory vs stated conventions** — reuse the `Glob` results from Step 0.3. If the repo has a style guide (`CONTRIBUTING.md`, `docs/conventions.md`, `docs/STYLE.md`), MUST invoke `Read` with `file_path` set to the path returned by `Glob` and `limit: 200`, then cross-check that every stated rule maps to an enforcer file detected in Step 0.3. If the ratio is bad, this is the headline finding.

**Custom-rule messages without rationale (§2.2)** — MUST invoke `Grep`:

```
Grep
  pattern: "message:|messages:"
  glob:    "**/{eslint,detekt,rules}*/**/*.{js,ts,kt,py,rs}"
  output_mode: "content"
  -C:      3
```

Review output for messages containing only prohibitions without a why + fix + ADR link.

**Custom-rules package test suite (§2.4)** — MUST invoke `Glob` with `pattern: "**/{eslint,detekt,rules}*/**/{test,tests,__tests__,spec}/**"`. Absence is a finding.

### 1.3 Type defensiveness (Pillar 3)

**Raw scalars in domain signatures (§3.1)** — MUST invoke `Grep`:

```
Grep
  pattern: "function \\w+\\([a-zA-Z_]\\w*: (string|number|int|long|float|boolean)\\b"
  glob:    "{domain,features}/**/*.{ts,tsx,py,kt,scala,java,cs,rs}"
  output_mode: "content"
  -n:      true
```

**Optional-field state bags (§3.2)** — MUST invoke `Grep`:

```
Grep
  pattern: "^\\s*\\w+\\??: .+\\?.*\\n\\s*\\w+\\??:"
  glob:    "{domain,features}/**/*.{ts,tsx}"
  output_mode: "content"
  multiline: true
```

Adapt to Python (`Optional[...]`), Kotlin (`?`), etc.

**Unchecked coercions into branded types (§3.3)** — MUST invoke `Grep`:

```
Grep
  pattern: "\\bas (UserId|OrderId|\\w+Id|Money|Email|Url)\\b|unsafeCoerce|@unchecked"
  glob:    "{features,domain,app,application,interfaces}/**/*.{ts,tsx,scala}"
  output_mode: "content"
  -n:      true
```

**Non-exhaustive matching (§3.4)** — MUST invoke `Grep`:

```
Grep
  pattern: "switch\\s*\\(.+\\)\\s*\\{[^}]*\\}"
  glob:    "{features,domain}/**/*.{ts,tsx}"
  output_mode: "content"
  multiline: true
```

Flag any match lacking a `default:` that calls `assertNever` (or language equivalent).

### 1.4 State management (Pillar 4)

**Boolean state tuples (§4.1)** — MUST invoke `Grep`:

```
Grep
  pattern: "(isLoading|isPending|isFetching|isError|isSuccess|hasRetried)"
  glob:    "{features,app,pages,components}/**/*.{ts,tsx,jsx}"
  output_mode: "count"
```

Files with ≥2 matches are candidate §4.1 violations.

**Render-time triple-boolean pattern (§4.4)** — MUST invoke `Grep`:

```
Grep
  pattern: "isLoading\\s*&&.*isError|!isError\\s*&&\\s*data"
  glob:    "{features,app,pages,components}/**/*.{ts,tsx,jsx,vue,svelte}"
  output_mode: "content"
  -n:      true
```

**Scattered setters in FSM files (§4.2)** — MUST invoke `Grep` twice, then cross-reference the two file lists:

```
Grep
  pattern: "setState\\(|dispatch\\(\\{"
  glob:    "{features,app,domain}/**/*.{ts,tsx,js}"
  output_mode: "files_with_matches"
```

```
Grep
  pattern: "createMachine\\(|useReducer\\("
  glob:    "{features,app,domain}/**/*.{ts,tsx,js}"
  output_mode: "files_with_matches"
```

Files appearing in BOTH result sets are §4.2 candidates (the file exports an FSM but also mutates state ad-hoc outside the reducer).

**FSMs missing cancellation (§4.3)** — MUST invoke `Grep`:

```
Grep
  pattern: "createMachine\\(|useReducer\\("
  glob:    "**/*.{ts,tsx,js}"
  output_mode: "files_with_matches"
```

For each hit file path, MUST invoke `Read` with `file_path` set to the path returned by `Grep` and `limit: 150` (FSM declarations are typically in the first 150 lines). Confirm presence of `cancelled|aborted|timeout` state names.

### 1.5 Observability and rationale (Pillar 5)

**ADR directory (§5.2)** — MUST invoke `Glob` with `pattern: "{adr,docs/adr,doc/adr,architecture/adr}/**/*.md"`. Count; 0–2 in a non-trivial repo is a §5.2 violation signal.

**Print-as-log (§5.4)** — MUST invoke `Grep`:

```
Grep
  pattern: "\\b(console\\.log|print|println|fmt\\.Print)"
  glob:    "{features,domain,app,application,interfaces}/**/*.{ts,tsx,js,py,go,rs,java,kt}"
  output_mode: "content"
  -n:      true
```

Every instance is a §5.4 finding.

**Missing span instrumentation at adapter boundaries (§5.1)** — MUST invoke `Grep` for the detected tracing SDK import (e.g., `@opentelemetry/api`, `opentelemetry.trace`) inside `{infra,adapters,platform,infrastructure}/**`. Absence at adapter construction is §5.1 inverted.

**Comment smell (§5.3)** — this check is fuzzy; skip mechanical scan. Surface during the interpret-findings pass by sampling 20 recent diffs.

## Step 2 — Interpret findings

Mechanical hits are candidates, not findings. For each candidate, judge:

- **Is it a genuine violation?** Some async-returning functions at the tip are unavoidable (framework-provided suspense primitives). Apply the escape-hatch test in the rule.
- **Is it already enforced by existing tooling and merely slipped through?** That is a finding about the enforcer, not the code.
- **What's the blast radius?** One violation in a prototype route is trivial; the same violation in the authentication flow is severe.

Use this severity scale:

- **Critical** — permits silently corrupt state, security/auth holes, or makes a whole module unsafe to modify. Example: branded `UserId` is routinely bypassed with unchecked coercion; persistence layer leaks into UI throughout the app.
- **Major** — significantly increases cognitive load or will cause bugs under reasonable conditions. Example: `isLoading + isError + data` pattern across 30+ components; no ADRs for a 2-year-old codebase.
- **Minor** — localized, low impact, low-effort to fix. Example: one comment that restates code; one component with two booleans that could be a union.
- **Hygiene** — not wrong per se, but a rule is present without an enforcer and will rot. Example: convention document says "prefer discriminated unions" but no enforcer enforces it.

## Step 3 — Produce the report

Output a Markdown report with this structure:

```markdown
# Iceberg Convention Audit — [repo name]

**Scope:** [what was audited]
**Languages:** [detected]
**Existing enforcement:** [brief summary across the six categories: A (module boundary), B (AST lint), C (type-level), D (purity), E (tracing), F (PR-level)]
**Overall posture:** [one paragraph]

## Headline findings

[1–3 bullets. The findings that, if fixed, would move the needle most.]

## Findings by pillar

### Pillar 1 — The API Airgap
| ID | Severity | Rule | Location | Issue | Remediation | Enforcer category + tool |
|---|---|---|---|---|---|---|
| P1-01 | Critical | 1.2 | [path:line] | [description] | [fix] | [category + idiomatic tool for the target language] |

### Pillar 2 — Compiler-Driven Mentorship
[...]

### Pillar 3 — Defensive Type Engineering
[...]

### Pillar 4 — State-Machine Dictatorships
[...]

### Pillar 5 — Observability as Documentation
[...]

## Recommended remediation order

1. [Highest leverage — unblocks other fixes]
2. [Next]
3. [...]

## Suggested ADRs to write

- ADR-NNN: [topic] — context: [one line]
- [...]

## Enforcement gaps

[Rules that would apply in this language but lack an idiomatic automated enforcer. For each: which rule, which language limitation, closest available compensation, residual risk.]

## Follow-up audits

[What you couldn't check and why.]
```

## Step 4 — Output rules

- **Cite rules by number, not by name.** "Violates §3.1" is unambiguous; "violates the no-raw-scalars thing" is not.
- **Every finding names its enforcer category.** From `enforcement-patterns.md` §A–§F. If a specific tool is idiomatic for the target language, name that tool. If no mechanical enforcer exists for the target language (legitimate gap), note: *Enforcer: none available in [language] — review-only; see Enforcement gaps section*.
- **Every critical or major finding has a file:line pointer.** Not "throughout the codebase." If it's pervasive, include 2–3 representative pointers and say so.
- **Do not recommend a tool without justification.** "Use dependency-cruiser" is bad advice. "Install a module-boundary enforcer (Category A); dependency-cruiser is idiomatic for this TypeScript project — configure it with a forbidden-dependency rule from `features/` to `infra/`" is good.
- **Do not pad.** A 20-finding report is fine. A 20-finding report where 15 are style nits is noise. Merge, downgrade, or drop.

## Common audit pitfalls

- **Mistaking framework idioms for convention violations.** A React Server Component returning `Promise<JSX>` is not a §1.1 violation — it is the framework-provided suspense seam. Similar exemptions exist in every ecosystem; know the framework before flagging.
- **Grepping for symptoms without checking causes.** If every domain function takes raw strings, the issue isn't 20 functions — it is that no branded-type scaffolding exists. One headline finding, not 20 identical ones.
- **Ignoring what the team already does well.** A report that is 100% negative is unreviewable. Include a short "Strengths" note if warranted.
- **Flagging hygiene findings at critical severity.** A missing ADR is not the same as silently-allowed state corruption. Calibrate.
- **Treating the convention as dogma.** Some codebases legitimately do not need the full stack (a 3-file script, a prototype, an internal tool with 2 users). Note when the convention may be over-engineered for the context and recommend a subset.
- **Applying stronger-language expectations to weaker-enforcement languages.** If the target is Go or Python, §3.1 cannot be enforced as strictly as in Rust or Kotlin. Flag the gap; do not manufacture findings that assume language-level support that doesn't exist.
