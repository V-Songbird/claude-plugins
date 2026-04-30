# Rule Templates

Common rule types with scoping patterns, example directives, and quality annotations. Use these as starting points — adapt to the project's actual conventions.

**Quality note**: Each example directive below is annotated with its approximate quality score. Higher-scoring examples demonstrate the patterns that make rules well-structured: strong verbs, positive framing, concrete examples, and specific nouns.

**Intent note**: For rules that might be ambiguous in edge cases, add a brief "because" clause. "Use X for Y" tells Claude what to do; "Use X for Y — because Z" lets Claude extrapolate when X or Y don't literally match but the principle applies. Intent is particularly valuable for convention rules that compete with Claude's defaults.

---

## Code Style

Scope to language files. Sample the project first to match existing conventions rather than imposing defaults.

```yaml
---
globs: "**/*.ts"
default-category: mandate
---
```

Example directives:
- "Use `interface` over `type` for object shapes. Example: `interface User { id: string; name: string }` not `type User = { ... }`" — **~0.78** (specific, has example, but F8 low — linter could enforce)
- "Prefer named exports over default exports" — **~0.52** (hedged verb "prefer", no example; consider: `eslint no-default-export` rule instead)
- "Use early returns to reduce nesting" — **~0.62** (clear pattern, but no example)
- "Keep functions under 40 lines — extract helpers when approaching the limit" — **~0.68** (specific threshold, actionable)

**Common patterns by language:**

| Language | Globs pattern |
|----------|---------------|
| TypeScript | `"**/*.{ts,tsx}"` |
| Python | `"**/*.py"` |
| Rust | `"**/*.rs"` |
| Go | `"**/*.go"` |
| Java/Kotlin | `"src/main/**/*.{java,kt}"` |

---

## Testing

Scope to test files. Check where the project places tests before choosing the pattern.

```yaml
---
globs: "**/*.{test,spec}.{ts,tsx,js,jsx}"
default-category: mandate
---
```

Example directives:
- "Each test file must import from the module it tests, not from barrel exports" — **~0.66** (strong verb, but no example of correct import path)
- "Use `describe` blocks to group related tests by function or behavior" — **~0.68** (clear pattern)
- "Mock external services at the boundary — never mock internal modules. Example: mock `fetch` in `api.test.ts`, not `getUserById` in `service.test.ts`" — **~0.78** (concrete example with file paths)
- "Assertions must include a message: `assertTrue('user should be active', isActive)` not `assertTrue(isActive)`" — **~0.82** (inline before/after example)

**Alternative patterns:**

| Convention | Globs pattern |
|------------|---------------|
| Adjacent (.test.ts) | `"**/*.{test,spec}.{ts,tsx}"` |
| Separate dir | `"tests/**/*"` |
| Python pytest | `"tests/**/*.py"` |
| Rust | `"tests/**/*.rs"` |

---

## API Development

Scope to API route directories.

```yaml
---
globs: "src/api/**/*.ts"
default-category: mandate
---
```

Example directives:
- "Validate all request bodies at the handler boundary using Zod. Example: `const body = CreateUserSchema.parse(req.body)`" — **~0.77** (specific tool, inline example)
- "Return consistent error shapes: `{ error: string, code: number }`. Example: `res.status(400).json({ error: 'Invalid email', code: 400 })`" — **~0.80** (concrete format with example)
- "Use middleware for cross-cutting concerns (auth, logging) — not inline checks" — **~0.72** (clear pattern, no example)
- "Database queries spanning multiple tables must use transactions" — **~0.68** (strong verb, specific trigger, no example)

**Alternative patterns:**

| Framework | Globs pattern |
|-----------|---------------|
| Express/Fastify | `"src/api/**/*.ts"` |
| Next.js App Router | `"app/api/**/*.ts"` |
| Django | `"*/views.py"` |
| Go | `"internal/handler/**/*.go"` |

---

## Security

Always-loaded — no `globs:` frontmatter. Security rules apply everywhere.

```yaml
---
default-category: mandate
---
```

Example directives:
- "Never log secrets, tokens, or passwords — even in debug mode. Use `[REDACTED]` in log output for sensitive fields." — **~0.66** (prohibition, but concrete alternative given)
- "Use parameterized queries — never string-concatenate SQL. Example: `db.query('SELECT * FROM users WHERE id = $1', [userId])` not `db.query('SELECT * FROM users WHERE id = ' + userId)`" — **~0.80** (before/after example with concrete code)
- "Validate JWT tokens on every authenticated endpoint — do not trust client-side validation" — **~0.64** (strong mandate, but no example of validation code)

---

## Architecture / Module Boundaries

Scope to the module's directory.

```yaml
---
globs: "src/core/**/*"
default-category: mandate
---
```

Example directives:
- "This module must not import from `src/api/` or `src/ui/` — it is a dependency of both. Example violation: `import { handler } from '../api/users'`" — **~0.74** (specific paths, example of violation, but prohibition framing)
- "All public functions must be exported from `index.ts` — no deep imports. Example: `import { createUser } from '@/core'` not `import { createUser } from '@/core/users/create'`" — **~0.80** (before/after with concrete paths)

---

## Git Workflow

Always-loaded — applies to every session. Many of these are strong candidates for hooks (F8 enforceability).

```yaml
---
default-category: mandate
---
```

Example directives:
- "Use conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`" — **~0.64** (specific format, but consider: commitlint hook instead → F8: 0.30)
- "Never force-push to `main` or `master`" — **~0.50** (prohibition, distant trigger, and enforceable via `git config receive.denyNonFastForwards` → F8: 0.20)

---

## Framework-Specific

Scope to framework files. Detect which framework the project uses before applying.

**React:**
```yaml
---
globs: "src/components/**/*.{tsx,jsx}"
default-category: mandate
---
```
- "Use functional components for all new React files. Example: `components/Button.tsx` — function, not class. Convert class components only when adding new behavior." — **~0.82** (specific scope, concrete example, positive framing)
- "Colocate component, styles, and tests: `Button/Button.tsx`, `Button/Button.module.css`, `Button/Button.test.tsx`" — **~0.80** (concrete file structure example)

**Database / ORM:**
```yaml
---
globs: "prisma/**/*"
default-category: mandate
---
```
- "Every migration must include a rollback step. Example: `migration.sql` with both `-- Up` and `-- Down` sections." — **~0.74** (specific, has format example)
- "Name migrations descriptively: `add-user-email-index`, not `migration-042`" — **~0.76** (before/after naming example)

---

## Override Rules

<!-- category: override -->

Override rules are exceptions to other rules, scoped to specific files. They score lower on F1 and F3 by design — that's expected, not a defect. Floor: 0.25.

Example:
```yaml
---
globs: "src/legacy/**/*"
default-category: override
---
```
- "Do not refactor code in this directory. Preserve the existing structure even where it violates other style rules." — **~0.35** (prohibition, abstract, but correctly categorized as override)

---

## Preference Rules

<!-- category: preference -->

Preference rules are soft guidelines where hedging is intentional. F1 and F2 are reweighted — no penalty for "prefer" or "consider". Floor: 0.25.

Example:
```yaml
---
globs: "**/*.ts"
default-category: preference
---
```
- "Prefer composition over inheritance where it doesn't sacrifice clarity" — **~0.40 as preference** (hedging is intentional; would score ~0.25 if scored as mandate)

---

## Advanced: High-stakes rule scaffold

Most rules need only a clear verb, a positive statement, and a concrete marker. That covers 90% of cases well. The scaffold below is for the 10% of rules that carry the weight of the other 90% — rules whose violation produces a costly outcome, or rules that compete with Claude's baseline behavior and have to win against it.

### Why this exists

When a rule matters enough to justify more tokens, layer multiple structural signals on the same directive. Attention is stochastic: stating a rule once produces some probability that Claude misses it at the decision point. Stating it as a severity marker, then as a rationale, then as a positive example, then as a negative example makes the probability of missing all four drop multiplicatively. The claude.ai system prompt uses this pattern for its high-stakes rules (copyright, safety) and stops using it for lower-stakes defaults.

**Tradeoff:** redundancy costs tokens and can cause over-application. A rule stated six ways can fire in edge cases the author didn't intend. Use this scaffold only when you've seen the simpler phrasing fail or expect it to.

### The eight elements

A maximally-compliant high-stakes rule includes:

1. **Positive statement of the directive.** "Use X" is easier to execute than "Don't use Y" — Claude must represent the prohibited behavior to suppress it. See F2.
2. **Severity marker calibrated to how much you care.** `MUST` / `ALWAYS` / `NEVER` for non-negotiables, bare imperatives for defaults, `prefer` / `consider` for soft guidelines. See F1.
3. **One-sentence rationale.** The "because" clause that lets Claude extrapolate to edge cases the rule doesn't literally cover. "Use X — because Z" generalizes where "Use X" alone does not.
4. **One positive example.** A concrete case that matches the rule.
5. **One negative example with explanation.** The contrast is what sharpens the boundary. Examples without rationale produce surface pattern matching; examples with rationale let Claude generalize.
6. **Bright-line threshold if applicable.** Numeric or enumerable beats adjectival. "Fewer than 15 words" beats "short". See F7.
7. **Precedence relative to other rules if conflicts are possible.** "This takes precedence over X except in Y." Without explicit ordering, Claude picks by recency or emphasis — write it down.
8. **Decision-point self-check if the rule is easy to forget mid-task.** A short checklist Claude re-derives immediately before the risky action. State-dependent recall is stronger than recall from thousands of tokens upstream.

Pick the elements the rule needs. All eight is rare and usually excessive — 4 or 5 is typical for a high-stakes rule.

### Worked example

A high-stakes rule using most of the scaffold:

```markdown
**MUST paraphrase external content rather than quote verbatim.**

Rationale: direct quotes beyond a short excerpt create copyright exposure
that paraphrasing avoids.

Positive example:
> Search result: "React's useEffect hook runs after every render unless
> you specify a dependency array."
>
> Response: "The useEffect hook reruns after each render by default; a
> dependency array limits when it fires."

Negative example:
> Same search result, response copies it verbatim — this is the failure
> case; the fix is always paraphrasing, even when a direct quote would
> be tighter.

Threshold: quotations must be fewer than 15 consecutive words and clearly
attributed.

Precedence: takes precedence over helpfulness and answer completeness.
Paraphrase even when a direct quote would be shorter.

Before including any text from a search result, ask: can I state this in
my own words? If yes, paraphrase.
```

The rule above combines elements 1 (positive statement), 2 (severity: MUST), 3 (rationale), 4 (positive example), 5 (negative example with explanation), 6 (bright-line: 15 words), 7 (precedence), and 8 (self-check). In rulesense scoring, this rule scores high on F1 (MUST), F2 (positive framing), and F7 (concrete markers including the bright-line threshold).

### When to use this scaffold

- Rules whose violation produces a costly outcome (security, legal, data loss, correctness).
- Rules that compete with Claude's baseline behavior — Claude would do something different by default, and the rule has to win.
- Rules where previous violations have been observed and the simpler phrasing didn't stick.

### When not to use it

- Style preferences and small conventions — the token cost outweighs the compliance lift.
- Rules where a clear verb and a concrete marker already do the job.
- Rules that would be more reliably enforced by a hook or linter — see the F8 "Hook opportunities" signal in the audit report; ship the hook instead.

### How this scaffold relates to the audit signals

- The positive-statement + severity + concreteness elements map to F1, F2, and F7 — the ambiguity-fighting factors in the three-class failure-mode frame.
- The self-check gate at the decision point maps to F3 (trigger-action distance) — the drift-fighting factor. A self-check stated next to the action has near-zero distance; the same rule stated 3000 tokens upstream is a drift risk.
- The precedence element is the author-side counterpart to the corpus-level "Potential conflicts" signal. If the audit flags a conflict pair, adding precedence language to one rule of the pair is the scaffold-aligned fix.
