# Fix-menu umbrella task — shape and progression

Called from Phase 3c Step 3 (append) and Step 5 (progression). Load on-demand when Step 3 appends the umbrella.

## Why a single umbrella

Users reported that spawning one sibling task per checked fix-menu option — even in one batch at the decision point — reads as "tasks multiplying" and produces a chaotic list (3 new entries appearing after a single Submit click). One umbrella with a mutating `activeForm` communicates the same information without growing the list.

This matches the single-task discipline used for the gap handoff in Phase 3a.

## Shape at append time (Phase 3c Step 3)

Let `N` = count of checked fix-menu options. The per-category follow-up in Step 4 is a sub-step of the Promote path, NOT a separate fix, so it does NOT count toward `N`.

### `N == 1` — name the umbrella after the single checked option

| Option | `content` | `activeForm` |
|---|---|---|
| Promote only | `"Promote [P] placement candidates into PROMOTIONS.md"` | `"Promoting placement candidates into PROMOTIONS.md"` |
| Rewrite only | `"Rewrite [R] weak rules"` | `"Rewriting weak rules"` |
| Reorganize only | `"Reorganize [O] rules into scoped files"` | `"Reorganizing rules into scoped files"` |

### `N >= 2` — umbrella form

```
{ content: "Apply [N] fix-menu changes",
  activeForm: "Applying fix 1 of [N] — <first sub-step's progressive form>" }
```

`<first sub-step's progressive form>` is the first sub-step in the fixed execution order `promote → rewrite → reorganize`, restricted to the checked options. Example: user checked Rewrite + Reorganize → first sub-step is `"rewriting weak rules"`.

### Substitutions

`[P]` placement-candidate count · `[R]` weak-rule count · `[O]` organization-move count · `[N]` checked-option count.

## Progression across sub-steps (Step 5, only when `N >= 2`)

As Step 5 advances from one sub-step to the next, invoke `TaskUpdate` to mutate ONLY the umbrella's `activeForm` — NEVER append a new task, NEVER close-and-reopen the umbrella.

Example transitions when all three options are checked (`N == 3`):

1. `"Applying fix 1 of 3 — promoting placement candidates"` (before Step 5a runs)
2. `"Applying fix 2 of 3 — rewriting weak rules"` (between Step 5a completion and Step 5b start)
3. `"Applying fix 3 of 3 — reorganizing rules into scoped files"` (between Step 5b completion and Step 5c start)

The umbrella's `content` (`"Apply 3 fix-menu changes"`) stays constant; only the `activeForm` mutates.

## Completion

Mark the umbrella `completed` via `TaskUpdate` ONLY after the final selected sub-step finishes, OR after Step 5a aborts the batch due to a `--write-promotions` failure (rewrite + reorganize are then skipped, umbrella closes with an explanatory chat note).

Produces a steady single-spinner UX instead of 2–3 sibling spinners ticking on and off.

## Step 4 "no categories checked" re-shape

If Step 3's Promote option was checked but Step 4 returned zero category boxes, flip `selected_changes.promote` back to `false` and re-shape the umbrella:

- If the umbrella was the Promote-only form (`N == 1`), remove it via `TaskUpdate` — it never starts.
- If the umbrella was the multi-change form (`N >= 2`), re-compute `N` (now one less) and use `TaskUpdate` to either:
  - Replace with the option-specific form when new `N == 1`, OR
  - Rewrite `content` to `"Apply [new N] fix-menu changes"` and `activeForm` to the new first sub-step's progressive form when new `N >= 2`.
