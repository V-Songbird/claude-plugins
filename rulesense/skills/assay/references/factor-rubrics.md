# Factor Scoring Rubrics

Measurement procedures for the 6 factors in the rule-quality model — F1, F2, F3, F4, F7 contribute to the comprehension composite; F8 is reported as a parallel signal. Each section is self-contained.

> **Drift guard — F3 and F8 level boundaries are summarized inline in `skills/assay/SKILL.md` Phase 2 and `skills/forge/SKILL.md` Phase 3 Step 2 as quick-reference rows.** When changing level numbers, boundaries, or short descriptors for F3 or F8 in this file, also update those two SKILL.md quick-reference rows in the same commit.

**Epistemic anchor**: F1 and F2 are mechanically scored (deterministic lookup tables and regex, no LLM judgment) to provide an introspection-independent foundation for the comprehension composite. F4 and F7 are semi-mechanical — F4 uses bag-of-words keyword overlap (testable but not strictly deterministic), F7 uses deterministic counting (concrete vs abstract markers, code references, examples) with LLM fallback. F3 and F8 require constrained LLM judgment against explicit rubrics.

---

## F1: Verb Strength (Mechanical)

**What it measures**: The modal commitment level of the rule's primary imperative verb. Stronger modal verbs communicate higher binding to Claude — less room for the model to parse the rule as optional. Whether Claude actually complies depends on baseline behavior beyond rule text (see `quality-model.md` §6); F1 measures the commitment signal encoded in the verb, not compliance probability.

**Procedure**: Extract the primary imperative verb phrase from the rule. Match against the lookup table below. If a rule contains multiple imperative verbs, score the *strongest* one (the rule's commitment signal to Claude is gated by its most binding verb).

### Lookup Table

| Score | Verb Pattern | Examples |
|-------|-------------|----------|
| 1.00 | `MUST`, `ALWAYS` + imperative, `REQUIRED` | "Every commit MUST end with [State: SYNCED]" |
| 0.95 | `NEVER`, `DO NOT`, `FORBIDDEN`, `CANNOT` | "NEVER edit files in src/main/gen/ directly" |
| 0.85 | Bare imperative: `Use`, `Run`, `Ensure`, `Place`, `Return`, `Validate` | "Use CachedValuesManager for expensive computations" |
| 0.70 | `Should`, `Always` (as adverb, not paired with MUST) | "Always validate parsed output shape" |
| 0.50 | `Prefer`, `Default to`, `Favor` | "Prefer named exports over default exports" |
| 0.30 | `Consider`, `Aim to`, `Where practical` | "Consider using batch operations where practical" |
| 0.20 | `Try to`, `Try to prefer`, `Where possible`, `When you can` | "Try to prefer functional components when possible" |
| 0.10 | `You might want to`, `It's worth`, `Keep in mind` | "Keep in mind that error handling is important" |

**Compound hedging**: When a verb phrase contains multiple hedges, score the lowest applicable pattern. "Try to prefer X where possible" matches 0.20 (`Try to`), not 0.50 (`Prefer`).

**Implicit verbs**: Sentences structured as statements rather than imperatives ("Test files mirror source paths") receive 0.70 — they read as expectations but lack explicit commitment.

### Worked Examples

| Rule | Verb Phrase | Score | Reasoning |
|------|------------|-------|-----------|
| "ALWAYS use project-aware methods for command database access" | ALWAYS + use | 1.00 | Unconditional mandate |
| "NEVER edit files in src/main/gen/ directly" | NEVER + edit | 0.95 | Strong prohibition |
| "Use functional components for all new React files" | Use | 0.85 | Bare imperative |
| "Each test file must import from the module it tests" | must + import | 1.00 | Must = unconditional |
| "Prefer named exports over default exports" | Prefer | 0.50 | Non-binding preference |
| "Use good judgment about error handling" | Use | 0.85 | Note: verb is strong but object is vacuous — F7 (specificity) catches that |
| "Try to prefer functional components when possible" | Try to prefer | 0.20 | Doubly hedged |

---

## F2: Framing Polarity (Mechanical)

**What it measures**: Whether the rule tells the model what TO DO (positive imperative), what NOT to do (prohibition), or merely expresses a preference. Positive imperatives bind trigger and action at the same parsing step — Claude reads "when X, do Y" as a single directive. Prohibitions require Claude to recognize an action it's about to take and interrupt — a multi-step parse that gives Claude more interpretation surface.

**Procedure**: Classify the rule's framing into one of 5 categories. If a rule contains both positive and negative framing (e.g., "Use X, never Y"), score the dominant framing — whichever occupies more of the rule's semantic weight.

### Classification Table

| Score | Category | Pattern | Example |
|-------|----------|---------|---------|
| 0.95 | Positive imperative with concrete alternative | "Use X instead of Y", "X not Y" | "Use `getProjectCommands(project)` not `.database.commands`" |
| 0.85 | Positive imperative | "Use X", "Always do X", "Ensure X" | "Use functional components for all new React files" |
| 0.70 | Positive with negative clarification | "Do X. Do not do Y." (two sentences) | "Edit the .bnf source and regenerate. Never edit gen/ directly." |
| 0.50 | Prohibition | "Never X", "Do not X", "Avoid X" | "NEVER edit files in src/main/gen/ directly" |
| 0.35 | Hedged preference | "Prefer X", "Default to X", "When possible, X" | "Prefer named exports over default exports" |

**Prohibition + positive follow-up**: If a prohibition is immediately followed by the positive alternative ("Never use git commit directly — use commit-validator"), score 0.70 (positive with negative clarification), not 0.50 (prohibition).

### Worked Examples

| Rule | Category | Score |
|------|----------|-------|
| "ALWAYS use project-aware methods: `.getProjectCommands(project)` not `.database.commands`" | Positive with concrete alternative | 0.95 |
| "Use CachedValuesManager for expensive computations" | Positive imperative | 0.85 |
| "NEVER edit files in src/main/gen/ directly. Edit the .bnf/.flex source and regenerate." | Positive with negative clarification | 0.70 |
| "NEVER edit files in src/main/gen/ directly." (without follow-up) | Prohibition | 0.50 |
| "Prefer named exports over default exports" | Hedged preference | 0.35 |
| "Try to prefer functional components when possible" | Hedged preference | 0.35 |

---

## F3: Trigger-Action Distance (Judgment)

**What it measures**: How far in the future the rule's required action occurs from the moment the rule is read. Rules whose trigger and action are bound to the same moment (e.g., "when writing an import, import from the module directly") have near-zero trigger-action distance and maximum Claude-parsing reliability. Rules whose action must happen at a future moment the model has to independently recognize (e.g., "before committing, run prettier") are harder to parse as a forward directive because Claude's attention is elsewhere when the trigger fires.

**Procedure**: Read the rule. Identify the trigger (when does this rule apply?) and the action (what does the model do?). Classify into one of 5 levels below. Apply the rubric level whose description best matches the rule's trigger-action relationship.

### Rubric Levels

**Level 4 — Immediate (0.90–1.00)**: The action is part of the same operation as the trigger. There is no gap between recognizing the trigger and executing the action.

> "Use `getProjectCommands(project)` not `.database.commands`"
> Trigger: writing code that accesses command database. Action: use the project-aware method.
> The trigger and action are the same keystroke — you're choosing which API to call *as you write*.

> "Each test file must import from the module it tests, not from barrel exports"
> Trigger: writing a test import. Action: import from the module directly.
> Same moment — the import statement is being written.

**Level 3 — Soon (0.65–0.85)**: The action happens during the same task but at a slightly later step. The trigger is recognizable and proximate.

> "When adding new grammar rules, add corresponding PSI visitor methods and test coverage."
> Trigger: adding grammar rules. Action: add visitor methods + tests.
> Same task, but the action is a follow-up step the model must remember after the grammar edit.

> "Use functional components for all new React files."
> Trigger: creating a new React file. Action: use a functional component.
> The trigger and action overlap — creating the file IS writing the component — but "new" requires recognizing the file doesn't exist yet.

**Level 2 — Distant (0.40–0.60)**: The action must happen at a future moment the model has to independently recognize, separated from the current task focus by multiple intermediate steps.

> "Every commit modifying src/ MUST end with [State: SYNCED]"
> Trigger: committing code. Action: add the suffix.
> The model encounters this rule at session start, processes it, then 40+ turns later must recall it at commit time.

> "Run prettier on modified files before committing"
> Trigger: about to commit. Action: run prettier first.
> Same distance — the trigger is a future event the model must interrupt itself to recognize.

**Level 1 — Abstract (0.15–0.35)**: The rule expresses a principle or disposition rather than a concrete trigger-action pair. There is no specific moment it fires.

> "Use good judgment about error handling."
> No trigger. No specific action. This is a disposition, not an instruction.

> "Be thoughtful about naming."
> Same — no recognizable moment where "be thoughtful" activates.

> "Try to prefer functional components when possible"
> "When possible" is an abstract trigger — there's no specific moment the model should recognize as the firing condition.

**Level 0 — No trigger (0.00–0.10)**: The rule has no identifiable trigger or action. It's a statement, not an instruction.

> "All files, conventions, naming, and state schemas are optimized for agent consumption."
> This is a description of the system, not a directive. Score 0.00.

### Scoring Within Levels

Within each level, score higher when:
- The trigger is more concrete ("when creating `.tsx` files" > "when working with React")
- The action is more specific ("add PSI visitor methods" > "add test coverage")
- The trigger is a recognized programming event (file creation, import writing) rather than a subjective judgment ("when something is expensive")

---

## F4: Load-Trigger Alignment (Semi-mechanical)

**What it measures**: Whether the rule's file-level loading scope (determined by `globs:` frontmatter or always-loaded status) matches the conditions under which the rule actually applies. A rule that says "When editing API files, validate with Zod" but loads on every session (no globs) pays full attention cost but only fires some of the time.

**Measurement class**: Semi-mechanical. The procedure below extracts the rule's trigger text with regex, but the comparison to the loading scope uses bag-of-words keyword overlap between glob path components and rule text — not exact glob matching. The procedure is testable and reproducible, but the semantic-similarity step places F4 closer to F7 (concreteness) than to the strictly deterministic F1/F2. See `quality-model.md` § "Epistemic anchor" for the full discussion.

**Procedure**:

1. **Extract the rule's loading scope**:
   - If the file has `globs:` frontmatter → the loading scope is the glob pattern
   - If the file has no `globs:` frontmatter → always-loaded (scope = all files)

2. **Extract the rule's internal trigger scope**: look for trigger language in the rule text:
   - "When editing X files..." → trigger scope = X files
   - "For Python files..." → trigger scope = Python files
   - "In the API directory..." → trigger scope = API directory
   - No explicit trigger language → check if the rule's content domain semantically matches the file's glob pattern (e.g., an "API validation" rule in a file scoped to `src/api/**`). If yes, treat as implicitly matched — the glob IS the trigger.
   - No trigger language and no semantic match to globs → trigger scope = universal (applies to all work)

3. **Compare and score**:

| Loading Scope | Trigger Scope | Alignment | Score |
|---------------|--------------|-----------|-------|
| Glob matches trigger | Any | **Matched** | 0.90–1.00 |
| Always-loaded | Universal | **Matched** | 0.90–1.00 |
| **Glob-scoped, no explicit trigger, no keyword overlap** | **Trusts the scope** | **Implicit scope trust** | **0.80–0.90** |
| Always-loaded | Specific subsystem | **Misaligned** | 0.30–0.50 |
| Glob exists but doesn't match trigger | Specific subsystem | **Wrong scope** | 0.15–0.30 |
| Any | Stale reference (entity doesn't exist) | **Stale** | 0.05 |

**Implicit scope trust**: a rule inside a `paths:`-scoped file that does NOT repeat the scope in its text (e.g., "When writing TypeScript in packages/ui, ...") scores high because the `paths:` frontmatter IS the alignment mechanism. Re-stating the scope inside the rule text is redundant padding — the lens rewards concise rules that trust the frontmatter.

4. **Verify glob validity**: For rules with `globs:` frontmatter, run `Glob` against the pattern. If zero matches → score 0.05 (dead glob, functionally stale).

### Worked Examples

| Rule | Loading | Trigger Language | Score | Reasoning |
|------|---------|-----------------|-------|-----------|
| "Use Zod for API validation" in `api-rules.md` with `globs: "src/api/**/*.ts"` | Scoped to API | "API validation" | 0.95 | Glob matches trigger perfectly |
| "Validate request bodies with Zod" in the same file (no in-text trigger) | Scoped to API | None (trusts the scope) | 0.85 | Implicit scope trust — the rule correctly doesn't re-state the scope |
| "Use Zod for API validation" in root `CLAUDE.md` (no globs) | Always-loaded | "API validation" | 0.40 | Paying attention cost every session for a rule that only fires in API work |
| "Use TypeScript strict mode" in root `CLAUDE.md` (no globs) | Always-loaded | Universal (applies always) | 0.95 | Always-loaded rule with no specific trigger is correctly scoped |
| "Run tests for `src/legacy/auth.js`" but `src/legacy/` is deleted | Any | Stale reference | 0.05 | Referenced entity doesn't exist |

---

## F7: Concreteness (Semi-mechanical, formerly Specificity)

**What it measures**: How concrete and constraining the rule's nouns and objects are. A rule with specific file paths, API names, pattern names, and concrete triggers constrains behavior to a narrow set of actions. A rule with abstract nouns ("good judgment", "appropriate error handling") constrains nothing because any behavior is consistent with it.

**Concreteness and examples**: F7 serves two roles. A rule with rich examples scores high on F7 because the example backticks and file paths register as concrete markers. A rule that names specific APIs without examples also scores high on F7. Both patterns indicate the same underlying property — the presence of concrete code markers that constrain interpretation.

**Procedure**:

1. **Count concrete markers** in the rule text:
   - Named APIs, functions, classes, methods (e.g., `CachedValuesManager`, `getProjectCommands`)
   - File paths or glob patterns (e.g., `src/main/gen/`, `components/Button.tsx`)
   - Named patterns or frameworks (e.g., "JUnit 3", "functional components", "Zod")
   - Specific values or formats (e.g., `[State: SYNCED]`, `{ error: string, code: number }`)
   - Named file types or extensions (e.g., `.tsx`, `.bnf`)
   - **Bright-line numeric thresholds** — comparators + numbers, numbers with units, or ranges (e.g., "fewer than 15 words", "under 100ms", "at least 80%", "between 1 and 10"). These convert an adjectival standard ("short", "soon", "a lot") into something Claude can mechanically check; they count as concrete markers.

2. **Count abstract markers** in the rule text:
   - "good", "appropriate", "reasonable", "clean", "thoughtful"
   - "when possible", "where practical", "as needed"
   - "properly", "correctly", "carefully"
   - Unbounded nouns: "error handling", "naming", "code quality", "best practices"

3. **Score**:

| Concrete:Abstract Ratio | Score | Label |
|-------------------------|-------|-------|
| All concrete, no abstract | 0.90–1.00 | Fully specific |
| Mostly concrete, minor abstract qualifiers | 0.70–0.85 | Specific with hedges |
| Mixed — some concrete nouns, some abstract | 0.45–0.65 | Partially specific |
| Mostly abstract with one concrete noun | 0.25–0.40 | Weak specificity |
| All abstract, no concrete markers | 0.05–0.20 | Non-specific |

4. **Counterexample test (LLM fallback)**: For borderline cases, apply the counterexample test from the design: "Can you construct a specific action that would violate this rule?" If no concrete violation is imaginable, the rule is non-specific regardless of marker count. Score <= 0.20.

### Worked Examples

| Rule | Concrete Markers | Abstract Markers | Score |
|------|-----------------|-----------------|-------|
| "ALWAYS use `getProjectCommands(project)` not `.database.commands`" | 4 (two API methods, parameter, class) | 0 | 0.95 |
| "Use functional components for all new React files" | 2 (functional components, React files) | 0 | 0.85 |
| "NEVER edit files in src/main/gen/ directly" | 2 (directory path, file type) | 0 | 0.85 |
| "Use CachedValuesManager for expensive computations over PSI trees" | 2 (CachedValuesManager, PSI trees) | 1 (expensive) | 0.70 |
| "Always validate parsed output shape" | 1 (parsed output shape) | 1 (validate — what method?) | 0.40 |
| "Prefer named exports over default exports" | 2 (named exports, default exports) | 0 | 0.70 |
| "Try to prefer functional components when possible" | 1 (functional components) | 2 (try to, when possible) | 0.35 |
| "Keep PR titles under 70 characters" | 1 ("under 70 characters") | 0 | 0.80 |
| "Keep PR titles short" | 0 | 0 (no markers at all — "short" is adjectival but not in the abstract-markers list) | 0.05 |
| "Use good judgment about error handling" | 0 | 3 (good, judgment, error handling) | 0.05 |

---

## F8: Enforceability Ceiling (Judgment — Parallel Signal)

**Role**: F8 is scored and reported but is **NOT part of the composite comprehension score**. It measures tool-selection optimality (can a hook do this more reliably?), not Claude comprehension (does Claude understand the rule?). Rules with F8 < 0.40 are listed in the audit report as "Hook opportunities" — a parallel suggestion that does not affect the letter grade. See `quality-model.md` §4.

**What it measures**: Whether a hook, linter, test, or other mechanical enforcement tool could do this rule's job strictly better than a context-injected instruction. If yes, the rule's appropriate enforcement layer is not the instruction layer — the text rule is a stopgap until the mechanical enforcement is configured.

This factor does NOT penalize rules that happen to be enforceable — it identifies rules whose *appropriate enforcement layer* is not the instruction layer. The score represents the gap between "how well-structured this rule is as an instruction" and "how well it would work as a hook."

**Procedure**: Read the rule. Ask: "Can this rule's compliance be verified by a deterministic tool (shell command, linter rule, AST check, test, file watcher) without requiring LLM judgment?" Classify into one of 4 levels.

### Rubric Levels

**Level 3 — Not mechanically enforceable (0.85–1.00)**: The rule requires judgment, context, or understanding that no deterministic tool can provide. The instruction layer is the *correct* enforcement mechanism.

> "Use CachedValuesManager for expensive computations over PSI trees."
> "Expensive" is subjective — no linter can determine which computations are expensive. Only an LLM can apply this judgment. Score: 0.90.

> "When adding new grammar rules, add corresponding PSI visitor methods and test coverage."
> The correspondence between grammar rules and visitor methods requires domain understanding. Score: 0.90.

> "Use good judgment about error handling."
> This is ironic — the rule itself is unenforceable because it's non-specific, but it's also not mechanically enforceable because "good judgment" is inherently a judgment call. Score: 1.00 on F8, but it will score near 0 on F7 (specificity), which correctly kills the comprehension composite.

**Level 2 — Partially enforceable (0.55–0.80)**: A linter or tool could catch some violations but not all. The rule has a component that requires judgment and a component that's deterministic.

> "Use functional components for all new React files."
> eslint-plugin-react's `prefer-stateless-function` can flag class components, but it can't distinguish "new" from "existing" files, and edge cases (HOCs, error boundaries) require judgment. Score: 0.70.

> "Each test file must import from the module it tests, not from barrel exports."
> An ESLint rule could flag barrel imports in test files, but determining "the module it tests" requires understanding the test's intent. Score: 0.65.

**Level 1 — Mostly enforceable (0.30–0.50)**: A hook or linter could enforce the rule's core requirement. The instruction exists as a stopgap until the mechanical enforcement is configured.

> "NEVER edit files in src/main/gen/ directly."
> A PreToolUse hook on Edit/Write matching `src/main/gen/**` could block this entirely. The instruction is a weak substitute for the hook. Score: 0.35.

> "Every commit modifying src/ MUST end with [State: SYNCED]"
> A pre-commit hook could grep the commit message for the required suffix. Score: 0.35.

> "Prefer named exports over default exports"
> eslint `no-default-export` rule does exactly this. Score: 0.30.

**Level 0 — Fully enforceable (0.10–0.25)**: A shell command, linter, or hook can fully verify compliance. The rule has no component that requires judgment. Its presence as an instruction is a quality deficit — it should be mechanical enforcement.

> "Run prettier on modified files before committing"
> A pre-commit hook running `prettier --check` does this with exit-code enforcement. Score: 0.15.

> "Ensure no TypeScript errors exist before pushing"
> A pre-push hook running `tsc --noEmit` does this. Score: 0.15.

### Scoring Within Levels

Within each level, score higher when:
- The mechanical tool doesn't exist or isn't configured for this project (the instruction is doing real work, even if it shouldn't need to)
- The rule has nuances that the mechanical tool can't capture (e.g., "for all new files" — the "new" qualifier)

Score lower when:
- The mechanical tool exists and is commonly available
- The rule's phrasing maps 1:1 to a tool's capability

---

## Reproducibility Check

After drafting these rubrics, verify reproducibility by scoring 5 rules not used during this document's development. Apply each factor independently. The "second auditor" can be yourself in two passes separated by enough time or other work to break the recency effect.

**Pass criterion**: scores agree within +/- 1 level (for judgment factors) or +/- 0.15 (for mechanical factors) on at least 4 of 5 rules. If not, revise the rubric for the factor(s) that diverged.
