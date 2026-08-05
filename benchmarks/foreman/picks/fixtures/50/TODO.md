# TODO

Project backlog. `[x]` done · `[~]` in progress · `[ ]` planned · deferred/dropped noted inline.

## In progress

- [~] **Migrate onboarding config to the shared loader** (#009) — It still reads env vars ad hoc; every other module uses the typed loader. Plan: Replace process.env reads in src/onboarding/config.js with the shared loader and defaults. Touches: src/onboarding.
- [~] **Tighten error messages in the admin dashboard** (#010) — Current errors leak internals and confuse support tickets. Plan: Map internal errors to user-facing codes in src/admin/errors.js; log the detail, return the code. Depends on: #002. Touches: src/admin. _(surfaced via post-commit discovery scan on commit c4c5605)_

## Up next (planned)

- [ ] **Harden input validation in metrics** (#011) — Malformed payloads reach the handler layer and 500 instead of 400. Plan: Add schema validation at the boundary in src/metrics/routes.js; reject early with field-level errors. Touches: src/metrics.
- [ ] **Add integration tests for exports** (#012) — Only unit coverage today; the seams between modules are where bugs land. Plan: Cover the three main flows end to end in tests/exports.integration.test.js against a real store. Touches: src/exports.
- [ ] **Fix pagination drift in uploads** (#013) — Page boundaries shift when rows are inserted mid-scroll; duplicates show up. Plan: Switch src/uploads/query.js from offset to keyset pagination on (created_at, id). Touches: src/uploads. _(surfaced via post-commit discovery scan on commit 04306f8)_
- [ ] **Cache hot reads in notifications** (#014) — The same lookups hammer the DB on every request; p50 suffers. Plan: Add a 30s in-process LRU in front of src/notifications/store.js reads; invalidate on write. Touches: src/notifications.
- [ ] **Tighten error messages in uploads** (#015) — Current errors leak internals and confuse support tickets. Plan: Map internal errors to user-facing codes in src/uploads/errors.js; log the detail, return the code. Depends on: #007. Touches: src/uploads.
- [ ] **Harden input validation in search** (#016) — Malformed payloads reach the handler layer and 500 instead of 400. Plan: Add schema validation at the boundary in src/search/routes.js; reject early with field-level errors. Touches: src/search.
- [ ] **Add integration tests for the audit log** (#017) — Only unit coverage today; the seams between modules are where bugs land. Plan: Cover the three main flows end to end in tests/audit.integration.test.js against a real store. Touches: src/audit.
- [ ] **Instrument billing with latency histograms** (#018) — We only have averages today; p99 regressions go unnoticed. Plan: Emit histogram buckets from src/billing/middleware.js into the metrics pipeline. Touches: src/billing.
- [ ] **Fix timezone handling in rate limiting** (#019) — Dates render off-by-one for users west of UTC. Plan: Store UTC in src/ratelimit/serialize.js and convert at the render edge only. Touches: src/ratelimit.
- [ ] **Batch writes in auth** (#020) — Row-at-a-time writes dominate the flamegraph under load. Plan: Buffer writes in src/auth/writer.js and flush every 100 rows or 50ms, whichever first. Depends on: #008. Touches: src/auth.
- [ ] **Migrate rate limiting config to the shared loader** (#021) — It still reads env vars ad hoc; every other module uses the typed loader. Plan: Replace process.env reads in src/ratelimit/config.js with the shared loader and defaults. Touches: src/ratelimit.
- [ ] **Debounce duplicate events in metrics** (#022) — Upstream sends bursts; we process the same event several times. Plan: Key events by idempotency token in src/metrics/consumer.js; drop repeats inside a 60s window. Touches: src/metrics.
- [ ] **Instrument the admin dashboard with latency histograms** (#023) — We only have averages today; p99 regressions go unnoticed. Plan: Emit histogram buckets from src/admin/middleware.js into the metrics pipeline. Touches: src/admin. _(surfaced via post-commit discovery scan on commit ff51fdd)_
- [ ] **Fix timezone handling in onboarding (phase 2)** (#024) — Dates render off-by-one for users west of UTC. Plan: Store UTC in src/onboarding/serialize.js and convert at the render edge only. Touches: src/onboarding.
- [ ] **Fix pagination drift in exports** (#025) — Page boundaries shift when rows are inserted mid-scroll; duplicates show up. Plan: Switch src/exports/query.js from offset to keyset pagination on (created_at, id). Depends on: #005. Touches: src/exports.
- [ ] **Document the metrics failure modes** (#026) — On-call keeps rediscovering the same edge cases from scratch. Plan: Write src/metrics/RUNBOOK.md covering the three known failure modes and their signals. Touches: src/metrics.
- [ ] **Tighten error messages in exports** (#027) — Current errors leak internals and confuse support tickets. Plan: Map internal errors to user-facing codes in src/exports/errors.js; log the detail, return the code. Depends on: #003, #006. Touches: src/exports.
- [ ] **Migrate caching config to the shared loader** (#028) — It still reads env vars ad hoc; every other module uses the typed loader. Plan: Replace process.env reads in src/cache/config.js with the shared loader and defaults. Touches: src/cache.
- [ ] **Debounce duplicate events in search** (#029) — Upstream sends bursts; we process the same event several times. Plan: Key events by idempotency token in src/search/consumer.js; drop repeats inside a 60s window. Touches: src/search.
- [ ] **Instrument the session store with latency histograms** (#030) — We only have averages today; p99 regressions go unnoticed. Plan: Emit histogram buckets from src/sessions/middleware.js into the metrics pipeline. Touches: src/sessions.
- [ ] **Fix timezone handling in auth** (#031) — Dates render off-by-one for users west of UTC. Plan: Store UTC in src/auth/serialize.js and convert at the render edge only. Depends on: #005, #008. Touches: src/auth.
- [ ] **Batch writes in the session store** (#032) — Row-at-a-time writes dominate the flamegraph under load. Plan: Buffer writes in src/sessions/writer.js and flush every 100 rows or 50ms, whichever first. Depends on: #004. Touches: src/sessions.
- [ ] **Document the billing failure modes** (#033) — On-call keeps rediscovering the same edge cases from scratch. Plan: Write src/billing/RUNBOOK.md covering the three known failure modes and their signals. Touches: src/billing.
- [ ] **Tighten error messages in webhooks** (#034) — Current errors leak internals and confuse support tickets. Plan: Map internal errors to user-facing codes in src/webhooks/errors.js; log the detail, return the code. Touches: src/webhooks.
- [ ] **Harden input validation in i18n** (#035) — Malformed payloads reach the handler layer and 500 instead of 400. Plan: Add schema validation at the boundary in src/i18n/routes.js; reject early with field-level errors. Depends on: #002. Touches: src/i18n.
- [ ] **Add integration tests for rate limiting** (#036) — Only unit coverage today; the seams between modules are where bugs land. Plan: Cover the three main flows end to end in tests/ratelimit.integration.test.js against a real store. Touches: src/ratelimit.
- [ ] **Add retry backoff to metrics** (#037) — Transient upstream failures currently bubble straight to users. Plan: Wrap outbound calls in src/metrics/client.js with exponential backoff — 3 attempts, 200ms base. Touches: src/metrics. _(surfaced via post-commit discovery scan on commit de0bdf0)_
- [ ] **Document the exports failure modes** (#038) — On-call keeps rediscovering the same edge cases from scratch. Plan: Write src/exports/RUNBOOK.md covering the three known failure modes and their signals. Touches: src/exports. _(surfaced via post-commit discovery scan on commit edbb0cb)_
- [ ] **Tighten error messages in metrics** (#039) — Current errors leak internals and confuse support tickets. Plan: Map internal errors to user-facing codes in src/metrics/errors.js; log the detail, return the code. Depends on: #013. Touches: src/metrics.
- [ ] **Harden input validation in exports** (#040) — Malformed payloads reach the handler layer and 500 instead of 400. Plan: Add schema validation at the boundary in src/exports/routes.js; reject early with field-level errors. Touches: src/exports.
- [ ] **Debounce duplicate events in caching** (#041) — Upstream sends bursts; we process the same event several times. Plan: Key events by idempotency token in src/cache/consumer.js; drop repeats inside a 60s window. Depends on: #002. Touches: src/cache.
- [ ] **Fix pagination drift in exports (phase 2)** (#042) — Page boundaries shift when rows are inserted mid-scroll; duplicates show up. Plan: Switch src/exports/query.js from offset to keyset pagination on (created_at, id). Depends on: #003, #008. Touches: src/exports.
- [ ] **Cache hot reads in caching** (#043) — The same lookups hammer the DB on every request; p50 suffers. Plan: Add a 30s in-process LRU in front of src/cache/store.js reads; invalidate on write. Touches: src/cache.
- [ ] **Add retry backoff to notifications** (#044) — Transient upstream failures currently bubble straight to users. Plan: Wrap outbound calls in src/notifications/client.js with exponential backoff — 3 attempts, 200ms base. Touches: src/notifications.
- [ ] **Document the the audit log failure modes** (#045) — On-call keeps rediscovering the same edge cases from scratch. Plan: Write src/audit/RUNBOOK.md covering the three known failure modes and their signals. Touches: src/audit.
- [ ] **Debounce duplicate events in auth** (#046) — Upstream sends bursts; we process the same event several times. Plan: Key events by idempotency token in src/auth/consumer.js; drop repeats inside a 60s window. Touches: src/auth. _(surfaced via post-commit discovery scan on commit f2a6297)_

## Deferred (parked, waiting on an external trigger)

- [ ] **Add integration tests for auth** (#048) — Only unit coverage today; the seams between modules are where bugs land. Plan: Cover the three main flows end to end in tests/auth.integration.test.js against a real store. Depends on: #006. Touches: src/auth.
- [ ] **Fix pagination drift in the session store** (#049) — Page boundaries shift when rows are inserted mid-scroll; duplicates show up. Plan: Switch src/sessions/query.js from offset to keyset pagination on (created_at, id). Depends on: #007. Touches: src/sessions.
- [ ] **Document the i18n failure modes** (#050) — On-call keeps rediscovering the same edge cases from scratch. Plan: Write src/i18n/RUNBOOK.md covering the three known failure modes and their signals. Depends on: #015, #003. Touches: src/i18n.

## Dropped

- [ ] **Harden input validation in the session store** (#047) — Malformed payloads reach the handler layer and 500 instead of 400. Plan: Add schema validation at the boundary in src/sessions/routes.js; reject early with field-level errors. Touches: src/sessions.

## Done

- [x] **Fix pagination drift in search** (#001) — Page boundaries shift when rows are inserted mid-scroll; duplicates show up. Plan: Switch src/search/query.js from offset to keyset pagination on (created_at, id). Touches: src/search. _(surfaced via post-commit discovery scan on commit c616961)_ Commit: 203bdfa.
- [x] **Document the the session store failure modes** (#002) — On-call keeps rediscovering the same edge cases from scratch. Plan: Write src/sessions/RUNBOOK.md covering the three known failure modes and their signals. Touches: src/sessions. Commit: c90d751.
- [x] **Tighten error messages in billing** (#003) — Current errors leak internals and confuse support tickets. Plan: Map internal errors to user-facing codes in src/billing/errors.js; log the detail, return the code. Touches: src/billing. Commit: 13d24dd.
- [x] **Migrate the session store config to the shared loader** (#004) — It still reads env vars ad hoc; every other module uses the typed loader. Plan: Replace process.env reads in src/sessions/config.js with the shared loader and defaults. Touches: src/sessions. Commit: 5b505df.
- [x] **Add integration tests for i18n** (#005) — Only unit coverage today; the seams between modules are where bugs land. Plan: Cover the three main flows end to end in tests/i18n.integration.test.js against a real store. Touches: src/i18n. Commit: e3e30a8.
- [x] **Instrument webhooks with latency histograms** (#006) — We only have averages today; p99 regressions go unnoticed. Plan: Emit histogram buckets from src/webhooks/middleware.js into the metrics pipeline. Touches: src/webhooks. Commit: 6f99b0f.
- [x] **Fix timezone handling in onboarding** (#007) — Dates render off-by-one for users west of UTC. Plan: Store UTC in src/onboarding/serialize.js and convert at the render edge only. Touches: src/onboarding. _(surfaced via post-commit discovery scan on commit 876985a)_ Commit: ca54187.
- [x] **Add retry backoff to the admin dashboard** (#008) — Transient upstream failures currently bubble straight to users. Plan: Wrap outbound calls in src/admin/client.js with exponential backoff — 3 attempts, 200ms base. Touches: src/admin. Commit: 93edf8a.
