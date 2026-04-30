# State File Schemas

Authoritative reference for all `.kairoi/` files.

## build-adapter.json

```json
{
  "kairoi_version": "1.0.0-alpha",
  "stack": "node-vitest",
  "test": "pnpm test",
  "source_dirs": ["src/"],
  "test_dirs": ["tests/", "__tests__/"],
  "exclude_dirs": ["src/generated/"],
  "edge_prune_min_weight": 2,
  "edge_prune_max_age_days": 30
}
```

## model/_index.json

```json
{
  "source_dirs": ["src/"],
  "modules": {
    "auth": { "source_paths": ["src/auth/"] },
    "api": { "source_paths": ["src/api/"] }
  },
  "edges": [
    {
      "from": "api",
      "to": "auth",
      "type": "calls",
      "weight": 1,
      "label": "api calls auth.validateToken() on every request",
      "last_seen": "2026-04-01"
    }
  ]
}
```

### Edge types

| Type | Meaning | Risk direction |
|------|---------|----------------|
| calls | A invokes B's exports | Changes to B's interface break A |
| shares-state | Both read/write shared state | Bidirectional |
| co-configured | Wired together in config/DI/routing | Bidirectional |
| co-modified | Change together statistically (from receipts) | Weakest signal |

Semantic edges (calls, shares-state, co-configured) require a `label` and
are only removed by kairoi-audit. Co-modified edges are auto-managed by
kairoi-complete and pruned when weight < `edge_prune_min_weight` AND older
than `edge_prune_max_age_days`.

## model/<module>.json

```json
{
  "purpose": "Handles OAuth2 PKCE token lifecycle — issuance, refresh, revocation",
  "entry_points": ["src/auth/index.ts", "src/auth/token.ts"],
  "guards": [
    {
      "trigger_files": ["src/auth/token.ts"],
      "check": "Verify mutex lock in refreshToken() is preserved — concurrent calls corrupt session state",
      "rationale": "Removed in fix-api-cleanup, caused race condition. Re-added in fix-token-race. The lock looks unnecessary but prevents concurrent refresh calls from overwriting each other's tokens.",
      "source_task": "fix-token-race",
      "created": "2026-03-15",
      "confirmed": 3,
      "disputed": 0
    }
  ],
  "known_patterns": [
    "All API calls route through httpClient wrapper — never use fetch directly",
    "Error types extend BaseAppError — catch blocks depend on instanceof chain"
  ],
  "negative_invariants": [
    "NOT exhaustive: all consumers use filtered checks, none enumerate all cases",
    "No callers outside this module — interface changes are PSI-shape-safe"
  ],
  "dependencies": ["config", "http-client"],
  "_meta": {
    "last_validated": "2026-03-28",
    "tasks_since_validation": 3,
    "churn_since_validation": 7
  }
}
```

### Field semantics

**purpose** — One sentence. What this module does. For orientation only.

**entry_points** — Files I should start reading from, ordered by importance.
Can include function-level specificity: `"src/auth/token.ts:refreshToken"`.

**guards** — Pattern-action tripwires with file-path triggers. The most
critical field. When I'm about to edit a file listed in any guard's
`trigger_files`, the guard-check hook injects the guard's `check` text
as a system message. I don't need to remember to consult them — they're
pushed to me mechanically.

Guard fields:
| Field | Description |
|-------|-------------|
| trigger_files | File paths or directory prefixes (ending in `/`) that activate this guard |
| check | What I must verify before proceeding. Prescriptive, not descriptive. |
| rationale | WHY this constraint exists. The intent chain — what was tried, what failed, what the current code does and why. Replaces source annotations. |
| source_task | Task ID that created this guard (provenance) |
| created | ISO date |
| confirmed | Times this guard has been verified as relevant during reflection. 0 = never verified. |
| disputed | Times this guard fired but I judged it irrelevant and proceeded anyway (task succeeded). High disputed relative to confirmed signals the guard may be stale or poorly scoped. Reviewed during audit. |

Guard trigger matching:
- Path ends with `/` → directory prefix match (any file under that directory)
- Otherwise → exact file path match
- A guard fires if the file being edited matches ANY of its trigger_files

**known_patterns** — Structural invariants I must maintain. Not style
preferences. Things that break if violated.

**negative_invariants** — Absence claims that grant permission to skip
audit work. The inverse of `known_patterns`: instead of "this breaks if
violated," these say "this is NOT the case, so you can skip the audit."
Examples: "NOT exhaustive — no consumer enumerates all cases", "No
callers outside this module", "Private rule — stub bump not required."
High-leverage: one negative invariant can eliminate hours of manual audit.

**change_patterns** — Recurring change archetypes for this module, injected
during orientation. Each entry: `{ archetype: "short label", check: "what to verify" }`.
Populated when reflection recognizes that a task fits a pattern seen before
(e.g., every "BNF alternation widening" in the grammar module requires the
same downstream audit + stub bump decision). Surfaced before the first edit
of a session so the agent recognizes its task type and applies the right
checklist without having to re-derive it.

**dependencies** — Module IDs this module depends on.

### _meta

| Field | Description |
|-------|-------------|
| last_validated | ISO date of last kairoi-audit or initial population. |
| tasks_since_validation | Task count since last audit/population. Informational only. |
| churn_since_validation | Sum of modified_files.length across tasks since last audit. Primary confidence signal. |

**Confidence is derived at read time, never stored.**

```
if purpose is null → "low"
elif churn_since_validation <= 10 → "high"
elif churn_since_validation <= 25 → "medium"
else → "low"
```

`churn_since_validation` weights staleness by the scope of changes: a
1-file doc fix contributes 1 unit; a 10-file structural refactor contributes
10. Four trivial touches and four structural refactors both increment
`tasks_since_validation` by 4, but have churn of 4 and ~40 respectively.
The churn-based formula decays trust proportionally to structural scope.

No self-assessment. No prediction tracking. Every reader computes
confidence the same way from `churn_since_validation`. Storing the derived
value invites drift between writers, so nothing persists it.

Why staleness over self-assessment: I cannot reliably judge whether my own
model misled me. A model that says "this module uses pattern X" shapes how
I work — if X is wrong, I may never notice because I operated within the
wrong frame. Staleness admits what I actually know: the model MIGHT have
drifted, and the only way to be sure is to re-read source.

## buffer.jsonl

Lightweight task log for batched reflection. One JSON object per line.
Appended after each git commit by `buffer-append.sh` (invoked via the
auto-buffer PostToolUse hook — every commit is captured
unconditionally). Consumed and cleared by kairoi-complete.

```json
{
  "task_id": "fix-date-parsing",
  "timestamp": "2026-04-01T14:30:00Z",
  "status": "SUCCESS",
  "summary": "Fixed timezone handling in date parser to use UTC normalization",
  "modules_affected": ["parser"],
  "modified_files": ["src/parser/dates.ts", "tests/parser/dates.test.ts"],
  "test_results": { "total": 12, "passed": 12, "failed": 0, "skipped": 0 },
  "commit_hash": "abc1234",
  "guards_fired": ["fix-tz-silent-fail"],
  "guards_disputed": [],
  "blocked_diagnostics": null
}
```

`modules_affected` and `modified_files` are derived automatically by
`buffer-append.sh` from the HEAD commit and `_index.json` module mappings.

`test_results` are auto-captured by `buffer-append.sh`: it reads the test
command from `build-adapter.json` and runs it, parsing output from common
frameworks (vitest, jest, pytest). If `--tests` is provided explicitly, it
overrides auto-run. If `--skip-tests` is passed, test_results is null. The
auto-run may include a `raw_exit` field (exit code) and `parse_note` if
output format wasn't recognized.

`guards_fired` is captured automatically from `.guards-log` (see below).

`guards_disputed` is captured automatically from `.guard-disputes` (see
below).

### .guards-log (temp file)

The guard-check hook appends fired guard `source_task` IDs to
`.kairoi/.guards-log` each time a guard matches. `buffer-append.sh`
reads this file, deduplicates, includes the IDs in the buffer entry's
`guards_fired` field, and clears the file. This makes guard tracking
fully mechanical — no honor-system fields.

### .guard-disputes (temp file)

When I decide a fired guard is irrelevant to my current edit and proceed
anyway, I append the guard's `source_task` ID to `.kairoi/.guard-disputes`.
`buffer-append.sh` reads this file, deduplicates, includes the IDs in
the buffer entry's `guards_disputed` field, and clears the file.

During reflection, `kairoi-complete` increments `disputed` on each
disputed guard. During audit, guards with `disputed >= 3` AND
`disputed >= confirmed` are flagged for review — either the guard needs
rewriting, removal, or I was wrong to dispute it.

## overrides.json

Human corrections. Never auto-modified except consuming `corrections`.

```json
{
  "modules": {
    "auth": {
      "pinned": { "purpose": "OAuth2 PKCE — NOT client credentials" },
      "corrections": ["The retry logic in token refresh is intentional"],
      "protected_guards": ["setup-oauth-flow"]
    }
  }
}
```

- `pinned`: override model fields at read time. Persistent.
- `corrections`: consumed during next reflection, then removed.
- `protected_guards`: source_task IDs whose guards must never be removed.

## receipts.jsonl

Append-only. One JSON object per line. Emitted by kairoi-complete after
processing buffered tasks.

```json
{
  "task_id": "fix-date-parsing",
  "timestamp": "2026-04-01T14:30:00Z",
  "status": "SUCCESS",
  "modules_affected": ["parser"],
  "modified_files": ["src/parser/dates.ts"],
  "test_results": { "total": 12, "passed": 12, "failed": 0, "skipped": 0 },
  "commit_hash": "abc1234",
  "guards_fired": ["fix-tz-silent-fail"],
  "guards_disputed": [],
  "guards_created": ["fix-date-parsing"],
  "model_updated": ["parser"],
  "edges_updated": [],
  "blocked_diagnostics": null
}
```

Rotation: >200 lines → keep last 100.
