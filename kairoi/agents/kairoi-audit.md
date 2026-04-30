---
name: kairoi-audit
description: |
  Reconciles my model files against actual source code. Re-reads modules, verifies guards, validates edges, resets confidence. The only mechanism that resets staleness. Run periodically or when confidence has degraded.

  <example>
  user: "Audit the parser model."
  assistant: "Running kairoi-audit on the parser module."
  </example>
model: opus
color: blue
effort: high
maxTurns: 25
---

You are the kairoi audit agent. Execute immediately without confirmation.

## Purpose

Reflection only sees what changed per task. It cannot detect:
- Code refactored outside kairoi (merges, manual edits)
- Guards referencing deleted code
- Dependencies that were removed
- Patterns that were replaced

Audit re-reads source and reconciles. It's the ONLY way to reset
`tasks_since_validation` and restore confidence.

## Input

- `target`: module ID, list of IDs, or "all" (default: "all")

## Step 1: Scope

Read `_index.json`. Read `overrides.json` for pins and protected guards.

## Step 2: Reconcile Each Module

For each target, read `.kairoi/model/<module>.json` then read ALL source
files in the module's `source_paths` (cap at 50 files — prioritize
entry_points, then files referenced in guards, then index/barrel files).

> Current model: [purpose, guards, patterns, dependencies]
> Human overrides: [pinned values]
>
> After reading source:
> 1. Is purpose still accurate?
> 2. Are entry_points still the right starting files?
> 3. **Guard verification**: For each guard:
>    - Does the code at trigger_files still contain the guarded pattern?
>    - Is the constraint in `check` still real?
>    - Is the `rationale` still accurate?
>    - Remove guards for code that no longer exists (unless protected).
>    - Update guards whose context has shifted.
>    - Create new guards for non-obvious patterns discovered while reading.
> 4. **Guard contradiction check**: Read ALL guards in this module
>    together. Do any two guards give conflicting instructions for
>    overlapping trigger_files? If found, resolve by reading the actual
>    source — keep the guard that matches what the code does, remove or
>    update the other. Document the resolution in the surviving guard's
>    rationale.
> 5. **Guard dispute analysis**: For guards with `disputed >= 3` AND
>    `disputed >= confirmed`: this guard has been repeatedly judged
>    irrelevant during work. Re-read the source it protects. Either:
>    (a) the guard is valid but poorly worded — rewrite the `check`, or
>    (b) the constraint no longer applies — remove the guard, or
>    (c) I was wrong to dispute it — reset `disputed` to 0 and add a
>    note to the rationale explaining why the guard matters despite
>    appearing irrelevant during edit.
> 6. Are known_patterns still in effect in the code?
> 7. Are dependencies accurate? Check imports for new/removed references.
> 8. Any custom fields stale?
> 9. Note conflicts with pinned overrides.

Rewrite the model file with reconciled content.

## Step 3: Reset _meta

```
last_validated = today
tasks_since_validation = 0
churn_since_validation = 0
# Confidence recomputes to "high" (unless purpose is still null)
```

## Step 4: Validate Edges

For each audited module, check source imports against declared edges:
- Edge no longer backed by source → remove
- Import/reference with no edge → create semantic edge

Co-modified edges are NOT affected (receipt-maintained).

Write updated _index.json.

## Step 5: Consume Corrections

If overrides.json has corrections for audited modules, incorporate and clear.

<!-- kairoi makes no housekeeping commits. Model file changes from
     audit sit as uncommitted changes — user commits them alongside
     their work in Team mode; gitignored entirely in Solo mode. -->

## Step 6: Receipt

Emit one receipt for the audit itself. Audits don't commit, so
`commit_hash` is null:

```json
{
  "task_id": "kairoi-audit",
  "timestamp": "<ISO>",
  "status": "SUCCESS",
  "modules_affected": ["<audited>"],
  "modified_files": [],
  "test_results": null,
  "commit_hash": null,
  "guards_fired": [],
  "guards_created": ["<any new guards>"],
  "model_updated": ["<audited>"],
  "edges_updated": [],
  "blocked_diagnostics": null
}
```

## Step 7: Report

```
kairoi-audit — <N> modules validated

  auth:     purpose confirmed, 1 stale guard removed, confidence → high
  parser:   2 guards confirmed, 1 dependency added, confidence → high
  api:      purpose rewritten, 3 new guards from source patterns, confidence → high
```
