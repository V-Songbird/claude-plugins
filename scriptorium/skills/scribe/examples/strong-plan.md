# Example: a strong plan file

The hypothetical: a backend team wants to migrate the authentication
layer from long-lived session cookies to short-lived JWTs behind a
feature flag, with both schemes running in parallel during rollout.
The plan below is what a Claude Code session produces during plan
mode and presents via `ExitPlanMode`. It is strong because every
section is scoped, every file path is explicit, every risk has a
paired mitigation, and the post-approval execution phase is
pre-authorized through `permissions.allow` rules in
`.claude/settings.json` — chosen for per-invocation scope over
`ExitPlanMode.allowedPrompts`, whose pre-approvals persist
session-wide.

## The strong example

```markdown
# Plan: JWT auth migration behind feature flag

## Problem
Session cookies are stored server-side in Redis and require a round
trip on every authenticated request. That round trip has become the
dominant tail-latency contributor on the `/api/v2/*` surface, and the
ops team has flagged Redis CPU as the next scaling bottleneck. We need
to migrate to short-lived JWTs (15-minute access, 7-day refresh)
without breaking existing sessions, and we need a feature flag so we
can roll back instantly if the new flow misbehaves in production.

## Approach
Introduce a `JWT_AUTH` feature flag (boolean, defaulting to `false`)
read from `process.env` at startup. When the flag is on, the auth
middleware mints and validates JWTs; when off, it falls back to the
existing session-cookie path. Both code paths share a single `User`
lookup so downstream handlers see the same shape regardless of
mechanism. Rollout is dark-launch first (flag off in prod, on in
staging), then a 10 percent canary, then full enable. Rollback is a
single env-var flip — no data migration is involved.

Key steps:

- Add `JWT_AUTH` flag plumbing and a typed config accessor.
- Implement JWT mint/verify behind a thin adapter so the existing
  cookie path is untouched.
- Branch the auth middleware on the flag; preserve the `req.user`
  contract so downstream handlers do not change.
- Add contract tests that run the same suite against both code paths.
- Document the rollback procedure in the runbook and link it from the
  on-call wiki.

## Files touched
- `src/config/feature-flags.ts` — add `JWT_AUTH` flag and typed accessor.
- `src/auth/jwt.ts` — new; mint/verify helpers wrapping `jose`.
- `src/auth/session.ts` — unchanged logic; refactored for shared `User` shape.
- `src/auth/middleware.ts` — branch on `JWT_AUTH`; preserve `req.user`.
- `src/auth/index.ts` — re-export the unified entry.
- `src/routes/login.ts` — issue JWT or session based on flag.
- `src/routes/logout.ts` — revoke the active mechanism.
- `src/routes/refresh.ts` — new; refresh-token endpoint, JWT path only.
- `test/auth/jwt.test.ts` — new; unit tests for mint/verify.
- `test/auth/middleware.contract.test.ts` — new; runs against both paths.
- `test/routes/login.test.ts` — extend to cover both flag states.
- `docs/runbooks/auth-rollback.md` — new; one-page rollback steps.
- `.env.example` — document `JWT_AUTH` and `JWT_SIGNING_KEY`.

## Risks
- **Token signing key leaks via logs.** Mitigation: add a redactor
  entry for `JWT_SIGNING_KEY` in the existing log scrubber, plus a
  unit test that asserts the key never appears in serialized error
  payloads.
- **Clock skew between issuer and verifier rejects valid tokens.**
  Mitigation: configure a 30-second `clockTolerance` in
  `jose.jwtVerify` and add a test that injects a skewed clock.
- **Refresh-token replay after logout.** Mitigation: persist a
  per-user `tokenVersion` integer; bump on logout; verify on refresh.
  Covered by a new contract test that issues, logs out, then attempts
  to refresh.
- **Flag flip mid-request orphans an in-flight session.** Mitigation:
  read the flag once per request at middleware entry; document the
  race in the runbook; add an integration test that flips the flag
  between two requests.
- **Downstream services assume the cookie still exists.** Mitigation:
  grep for `req.cookies.session` across the monorepo; the flag-on
  path keeps setting the cookie for one release as a compatibility
  shim, removed in the follow-up plan tracked separately.

## Test strategy
Run the full Jest suite after each phase. Success means: all existing
tests pass, the new `test/auth/**` suites pass under both
`JWT_AUTH=false` and `JWT_AUTH=true`, lint is clean, and
`tsc --noEmit` reports zero errors. Measure tail latency in staging
via the existing `p99_auth_ms` Grafana panel; expect a >40 percent
drop with the flag on. Revert by setting `JWT_AUTH=false` and
redeploying — no schema change is involved, so rollback is one env
flip and takes effect on the next deploy.

## Pre-approval: Bash commands required
- `npm test` — full suite, run after every phase.
- `npm run lint` — ESLint over `src/**` and `test/**`.
- `npm run typecheck` — `tsc --noEmit`.
- `git status` — verify clean tree before committing each phase.

These commands are declared in `.claude/settings.json` under `permissions.allow` so the post-approval execution phase does not stall on per-call prompts.
```

## Exiting plan mode

Invoke `ExitPlanMode` with the above plan content. For the listed Bash commands, ensure they are covered by a `permissions.allow` rule in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm test)",
      "Bash(npm run lint)",
      "Bash(npm run typecheck)",
      "Bash(git status)"
    ]
  }
}
```

`ExitPlanMode` also accepts
`allowedPrompts: [{ tool: "Bash", prompt: "npm test" }, ...]` as a
pre-authorization shortcut. It's a real parameter, but pre-approvals
persist session-wide rather than per-plan
([anthropics/claude-code#27160](https://github.com/anthropics/claude-code/issues/27160);
see `references/plans.md`). For this plan the `permissions.allow`
route was picked deliberately — per-invocation exact-match specifiers
keep the grant narrow. If an artifact does use `allowedPrompts`,
surface the session-wide scope caveat alongside it.

## What to notice

1. **Problem is one paragraph and names a measurable symptom** (tail
   latency on `/api/v2/*`, Redis CPU as the next bottleneck). It does
   not narrate the system or recap the codebase — the reader already
   has that context.
2. **Approach states the chosen direction first**, then a short
   bullet list of the load-bearing steps. Discarded alternatives are
   omitted because none were close calls; if there had been a real
   fork (e.g. opaque tokens via Redis vs. signed JWTs), it would
   belong here with the rationale for the pick.
3. **Files touched is an explicit bullet list** (13 files, under the
   15-file ceiling), each with a one-line per-file intent. New files
   are flagged with "new"; touched files state what changes. Paths
   are concrete enough that a reviewer can spot omissions like a
   missing test file.
4. **Each risk is paired with a specific mitigation**, not a generic
   "we will be careful." Mitigations name the file, test, or config
   that enacts them — e.g. "add a redactor entry for
   `JWT_SIGNING_KEY`" rather than "scrub logs." The mitigation is
   verifiable, which means a reviewer can check it landed.
5. **Test strategy specifies what to run, what passing looks like,
   and how to revert.** The revert path is one sentence because the
   plan was designed to make rollback cheap (env flip, no schema
   change). If rollback required a migration reversal, it would
   warrant its own subsection.
6. **Bash pre-approval lives in `.claude/settings.json` rather than
   `ExitPlanMode.allowedPrompts`** because `allowedPrompts`
   pre-approvals persist session-wide, while `permissions.allow` rules
   apply per-invocation. The `permissions.allow` rules use exact-match
   Bash specifiers (`Bash(npm test)`, not `Bash(npm *)`) so the grant
   stays narrow — broad patterns like `Bash(npm *)` would also authorize
   `npm publish`, which the plan never asks for.
7. **The plan stays under ~120 lines** because every section is
   scoped to what the executing session needs to act, not what a
   human reviewer would want for a design doc. Long discursive
   context belongs in a separate design note that the plan can link
   to.
8. **Section headings match the recommended defaults** in
   `references/plans.md` (Problem / Approach / Files touched / Risks
   / Test strategy) so the executing session can locate any section
   by header without re-reading the plan top to bottom.
9. **The "Pre-approval: Bash commands required" section names every
   command the post-plan execution phase will issue.** Commands
   omitted here will stall on a permission prompt during execution,
   defeating the point of the pre-approval. Keep the list short and
   exact so the corresponding `permissions.allow` entries stay
   narrow.
