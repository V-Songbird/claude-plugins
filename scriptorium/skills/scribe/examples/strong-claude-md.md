# Example: a strong CLAUDE.md

A CLAUDE.md for a TypeScript monorepo (`orderly`: Fastify API + Next.js web + shared Zod schemas) that correctly instructs Claude Code to invoke its interactive tools at the right moments. Notice: facts only in the body (no procedures — those go in skills), every long-running command names `Bash` with `description`, every anticipated decision names `AskUserQuestion` with full shape, any multi-step instruction names `TodoWrite` with paired `content` / `activeForm`, and the hook reference cites a verified event (`SessionStart`) with an explicit fallback.

## The strong example

````markdown
# orderly

Monorepo with three packages managed via pnpm workspaces:

- `packages/api` — Fastify 5.x, Node 20, Zod for request/response validation
- `packages/web` — Next.js 15 (App Router), React 19, Tailwind v4
- `packages/shared` — Zod schemas and TypeScript types consumed by both

## Conventions

- All exported functions are named; no anonymous default exports.
- Zod schemas live only in `packages/shared`; API and web import from there. Never re-declare.
- Route handlers in `packages/api/src/routes/*.ts` export a `register(fastify)` function. Handlers `MUST` call `reply.type("application/json")` before returning.
- React components are function declarations (not arrows) and live under `packages/web/src/components/<domain>/`.

@docs/contributing.md

## Verification commands

Before returning any change, invoke `Bash` three times in sequence:

- `{ command: "pnpm lint", description: "Linting the monorepo", timeout: 90000 }`
- `{ command: "pnpm typecheck", description: "Running TypeScript strict typecheck", timeout: 120000 }`
- `{ command: "pnpm test", description: "Running the Vitest suites", timeout: 180000 }`

If any fails, fix the issue and re-run — do NOT commit on failing checks.

## Decision points

### New route placement

When adding a new HTTP route, invoke `AskUserQuestion` before editing:

- `question: "Where should the new route live?"`
- `header: "Route"`
- `multiSelect: false`
- `options:`
  - `{ label: "Existing module", description: "Add to a route file that already covers this domain" }`
  - `{ label: "New module", description: "Create a new route file under packages/api/src/routes/<domain>/" }`
  - `{ label: "Shared utility", description: "Not a route — belongs in packages/shared" }`

### Schema migration

When a Zod schema change would break `packages/web` consumers, invoke `AskUserQuestion`:

- `question: "How should the breaking schema change land?"`
- `header: "Migration"`
- `multiSelect: false`
- `options:`
  - `{ label: "In-place", description: "Update schema + all consumers in one commit" }`
  - `{ label: "Versioned", description: "Introduce a v2 schema alongside v1; migrate consumers incrementally" }`
  - `{ label: "Feature-flagged", description: "Gate the new schema behind a runtime flag until consumers migrate" }`

## Multi-step workflows

When asked to add a new feature touching ≥2 packages, invoke `TodoWrite` with:

- `{ content: "Explore affected packages", activeForm: "Exploring affected packages", status: "pending" }`
- `{ content: "Update shared schemas", activeForm: "Updating shared schemas", status: "pending" }`
- `{ content: "Wire API route", activeForm: "Wiring API route", status: "pending" }`
- `{ content: "Update web consumer", activeForm: "Updating web consumer", status: "pending" }`
- `{ content: "Run lint / typecheck / tests", activeForm: "Running lint typecheck tests", status: "pending" }`

Mark each `in_progress` before starting and `completed` immediately on finish — never batch completions.

## Hooks

This project uses a `SessionStart` hook at `.claude/hooks/session_start.sh` (matcher: `startup`) that loads environment variables from `.env.local` into the Claude Code session. If the hook is missing or `.env.local` is absent, invoke `Bash` with `{ command: "pnpm --version && node --version", description: "Verifying tool versions", timeout: 10000 }` as a sanity check before any build command.

Hook configuration lives in `.claude/settings.json`. Do NOT invent or reference hook events beyond what is documented — see the project's hook script for the canonical behavior.

## Path-specific rules

Migration-related guidance lives in `.claude/rules/migrations.md` with `paths: ["packages/api/migrations/**"]` frontmatter so it loads automatically only when editing migration files.
````

## What to notice

1. **Facts, not procedures.** The body lists conventions and commands; it does not describe the Claude Code workflow itself. Procedures that span a workflow (exploration → plan → implement → verify) belong in a skill, not in CLAUDE.md.
2. **`Bash` with `description` + `timeout`** for all three verification commands — scribe checklist item 3.
3. **`AskUserQuestion` with full shape** at both decision points — `question`, `header` (≤12 chars), `multiSelect`, `options` with paired `label` + `description`. Scribe checklist item 1.
4. **`TodoWrite` with paired `content` / `activeForm`** on every todo, status transitions explicit — scribe checklist item 2.
5. **Hook reference cites a verified event** (`SessionStart` with matcher `startup`) and supplies an observable fallback — no fabricated events, no invented behavior. Aligns with `references/hooks.md`.
6. **No `AskUserQuestion` from subagents.** Both decision points fire in the main session; there's no delegation pattern that would run them from a subagent (scribe checklist item 6).
7. **`@docs/contributing.md` import** illustrates the import syntax (max 5 hops per `references/claude-md.md`) without embedding the full contributing content inline — keeps CLAUDE.md under the ~200-line guidance.
8. **Path-specific rules via `.claude/rules/migrations.md`** rather than inlining migration guidance — matches the recommended pattern.
9. **Literal tool names with directive verbs** throughout — `invoke Bash`, `invoke AskUserQuestion`, `invoke TodoWrite`, `do NOT commit`, `do NOT invent`. No weasel verbs.
