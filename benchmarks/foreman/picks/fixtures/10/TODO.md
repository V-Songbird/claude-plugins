# TODO

Project backlog. `[x]` done · `[~]` in progress · `[ ]` planned · deferred/dropped noted inline.

## In progress

- [~] **Tighten error messages in billing** (#003) — Current errors leak internals and confuse support tickets. Plan: Map internal errors to user-facing codes in src/billing/errors.js; log the detail, return the code. Touches: src/billing.

## Up next (planned)

- [ ] **Migrate the session store config to the shared loader** (#004) — It still reads env vars ad hoc; every other module uses the typed loader. Plan: Replace process.env reads in src/sessions/config.js with the shared loader and defaults. Touches: src/sessions.
- [ ] **Add integration tests for auth** (#005) — Only unit coverage today; the seams between modules are where bugs land. Plan: Cover the three main flows end to end in tests/auth.integration.test.js against a real store. Depends on: #002. Touches: src/auth.
- [ ] **Instrument rate limiting with latency histograms** (#006) — We only have averages today; p99 regressions go unnoticed. Plan: Emit histogram buckets from src/ratelimit/middleware.js into the metrics pipeline. Touches: src/ratelimit. _(surfaced via post-commit discovery scan on commit dc884b4)_
- [ ] **Fix timezone handling in i18n** (#007) — Dates render off-by-one for users west of UTC. Plan: Store UTC in src/i18n/serialize.js and convert at the render edge only. Depends on: #002. Touches: src/i18n. _(surfaced via post-commit discovery scan on commit cbf7776)_
- [ ] **Add retry backoff to exports** (#008) — Transient upstream failures currently bubble straight to users. Plan: Wrap outbound calls in src/exports/client.js with exponential backoff — 3 attempts, 200ms base. Touches: src/exports. _(surfaced via post-commit discovery scan on commit bde4018)_
- [ ] **Document the onboarding failure modes** (#009) — On-call keeps rediscovering the same edge cases from scratch. Plan: Write src/onboarding/RUNBOOK.md covering the three known failure modes and their signals. Depends on: #004, #001. Touches: src/onboarding.

## Deferred (parked, waiting on an external trigger)

- [ ] **Debounce duplicate events in notifications** (#010) — Upstream sends bursts; we process the same event several times. Plan: Key events by idempotency token in src/notifications/consumer.js; drop repeats inside a 60s window. Touches: src/notifications.

## Done

- [x] **Fix pagination drift in billing** (#001) — Page boundaries shift when rows are inserted mid-scroll; duplicates show up. Plan: Switch src/billing/query.js from offset to keyset pagination on (created_at, id). Touches: src/billing. Commit: 351f896.
- [x] **Document the the session store failure modes** (#002) — On-call keeps rediscovering the same edge cases from scratch. Plan: Write src/sessions/RUNBOOK.md covering the three known failure modes and their signals. Touches: src/sessions. Commit: d353248.
