# kairoi Recovery Guide

Scenario-driven troubleshooting. If kairoi produces surprising
behavior or you need to undo something, start here.

The two first-line tools:

- `/kairoi:doctor` — structural health report. Run this first if
  anything feels off; it will often tell you the problem before you
  need to dig.
- `KAIROI_DEBUG=1` — set in your environment to surface normally-
  suppressed script errors to stderr. Useful when hooks seem not to
  be firing or when state files appear stale.

---

## 1. A reflection produced something wrong

**Symptoms:** After a sync, a module's `purpose` got less specific,
a wrong guard appeared, a known pattern was deleted, or a model
claim contradicts what's actually in the source.

**Cause:** The reflection subagent made a mistake while processing
the buffer.

**Recovery:**

1. Read the latest receipt to understand what the sync did:
   ```bash
   tail -1 .kairoi/receipts.jsonl | jq .
   ```
   This shows `task_id`, `modules_affected`, `guards_created`,
   `model_updated`, and `edges_updated` for the most recent sync.

2. If you're in Team mode and the model change was committed,
   inspect the commit and revert if needed:
   ```bash
   git log --oneline -- .kairoi/model/
   git show <hash> -- .kairoi/
   git revert <hash>  # if the whole reflection is wrong
   ```
   In Solo mode, `.kairoi/` isn't committed, so just edit
   `.kairoi/model/<module>.json` back to a sane state.

3. Add a persistent correction so the next sync doesn't redo it:
   ```json
   { "modules": { "<module>": { "pinned": { "purpose": "exact value here" } } } }
   ```
   `pinned` is enforced mechanically during sync — reflection cannot
   overwrite it.

4. If the issue is a one-shot hint ("on next sync, please notice X"):
   ```json
   { "modules": { "<module>": { "corrections": ["purpose should be X, not Y"] } } }
   ```
   Corrections are consumed on the next reflection.

5. Run `/kairoi:audit <module>` to re-read source and reset
   staleness. Audit is the only path besides init that resets the
   confidence counter.

---

## 2. A guard fired and it's wrong

**Symptoms:** A guard's `check` fires during an edit but the
constraint is stale, too broad, or mismatched with the current code.

**Cause:** Code the guard protected was refactored; the guard didn't
get updated.

**Recovery:**

- **During work** — record the dispute and keep going:
  ```bash
  echo "<source_task>" >> .kairoi/.guard-disputes
  ```
  The next buffer-append captures the dispute. Guards with high
  `disputed` relative to `confirmed` get flagged during audit.

- **Persistent fix** — edit the model directly:
  Open `.kairoi/model/<module>.json`, find the guard by its
  `source_task`, and either update its `check` / `rationale` or
  remove it entirely.

- **Protect a guard that reflection keeps removing:**
  ```json
  { "modules": { "<module>": { "protected_guards": ["<source_task>"] } } }
  ```

- **Full reconciliation:** `/kairoi:audit <module>` re-reads all
  source and verifies every guard.

---

## 3. The buffer got corrupted

**Symptoms:** `/kairoi:doctor` flags `buffer.jsonl` as invalid,
scripts error during sync, or the session-boot banner shows
implausible buffer content.

**Cause:** Interrupted write, merge conflict, or a hand-edit.

**Recovery:**

1. Enable debug output:
   ```bash
   export KAIROI_DEBUG=1
   ```
   Re-run whatever triggered the issue; normally-suppressed errors
   will appear on stderr.

2. Validate the buffer line by line:
   ```bash
   while IFS= read -r line; do
     echo "$line" | jq . > /dev/null 2>&1 || echo "BAD LINE: $line"
   done < .kairoi/buffer.jsonl
   ```

3. Remove the bad lines (they're lost; sync won't reflect on them,
   but new commits will buffer cleanly):
   ```bash
   jq -c 'select(. != null)' .kairoi/buffer.jsonl > .kairoi/buffer.tmp \
     && mv .kairoi/buffer.tmp .kairoi/buffer.jsonl
   ```

4. If nothing in the buffer is worth recovering (e.g., it's a local
   Solo-mode buffer you're happy to drop), truncate it:
   ```bash
   : > .kairoi/buffer.jsonl
   ```
   `receipts.jsonl` and `overrides.json` are preserved — you only
   lose the unreflected portion.

5. As a nuclear option: re-run `/kairoi:init`. It re-bootstraps
   models from source. Receipts and overrides survive.

---

## 4. A model file got hand-edited by mistake

**Symptoms:** `/kairoi:doctor` flags schema drift, or `tasks_since_validation`
numbers don't increment the way they should.

**Cause:** Someone (you, a teammate, a merge conflict resolver) edited
`.kairoi/model/<module>.json` directly. The agent-written fields
(`tasks_since_validation`, guard `confirmed`/`disputed` counts,
`_meta`) drift easily when touched by hand.

**Recovery:**

1. In Team mode, restore the file from git:
   ```bash
   git checkout -- .kairoi/model/<module>.json
   ```

2. If the edit captured a correction you wanted to keep, move it to
   `overrides.json` instead — that's the correct correction surface
   and the only one the agent respects mechanically. See scenario 1
   for the pinned / corrections / protected_guards pattern.

3. Run `/kairoi:audit <module>` to rebuild the model against source
   and reset staleness.

4. If the drift is widespread across multiple files, `/kairoi:doctor`
   will enumerate what it sees; work through the list module by
   module.

---

## 5. Sync dispatched but Claude didn't reflect

**Symptoms:** `auto-buffer` logged a dispatch of `kairoi-complete`
(buffer-full or stale session-start), but the buffer is still full a
while later and no receipts appeared.

**Cause:** Hook-dispatched agent signals are best-effort. If the
current Claude session is mid-task, didn't pick up the signal, or
the dispatch happened in a context where the agent couldn't run,
the sync didn't execute.

**Recovery:**

- **Preferred:** start a fresh Claude Code session in the project.
  `session-boot.sh` re-checks the buffer; if it's still non-empty and
  the newest receipt is older than 7 days, it re-dispatches
  `kairoi-complete` and the new session picks it up cleanly.

- **On-demand alternative:** run `/kairoi:audit <module>` on any
  modules you've edited recently. Audit does a full source-vs-model
  reconciliation — not the same as sync (no buffer processing, no
  new receipts) but it'll catch anything reflection would have
  caught that matters for trust.

- This is a known limitation of the hook-dispatch model. Explicit
  user-invoked sync is intentionally gone; the fresh-session
  workaround is the escape hatch when dispatch misses.

---

## 6. `/kairoi:doctor` flags something you don't understand

**Symptoms:** Doctor reports a schema issue, a missing file, an
index/model mismatch, or an orphaned transient marker.

**What it's telling you:**

- **Index / model mismatch:** every key in `.kairoi/model/_index.json`
  `.modules` should have a matching `.kairoi/model/<key>.json` file,
  and vice versa. Doctor surfaces orphans in either direction.
  Recovery: delete the orphan, or run `/kairoi:init` to re-scan
  source (safe — init preserves `receipts.jsonl` and `overrides.json`).

- **Schema issue in a state file:** doctor runs `validate-schema.sh`
  against each state file. A failure points at a specific field and
  the expected type. Hand-edit the field if obvious; otherwise
  `/kairoi:audit <module>` for the model, or truncate the buffer
  (scenario 3) if it's `buffer.jsonl`.

- **Orphaned transient marker:** `.kairoi/.seen-<module>`,
  `.kairoi/.reflect-result-*.json`, or similar from an interrupted
  sync. Safe to delete; they're scratch space and get re-created
  on demand.

---

## 7. `.gitignore` got misconfigured (mode detection is off)

**Symptoms:** `/kairoi:init` re-prompts for Team/Solo when you've
already chosen, or committed state files leak into diffs in ways
that don't match your chosen mode.

**Cause:** Mode is inferred from `.gitignore` entries on every read
(not from a separate `mode.json` file). If those entries get edited,
removed, or clobbered by a merge, detection breaks.

**Recovery:**

- **Team mode** expects `.gitignore` to contain:
  ```
  .kairoi/buffer.jsonl
  .kairoi/receipts.jsonl
  .kairoi/session.log
  .kairoi/.*
  ```

- **Solo mode** expects `.gitignore` to contain:
  ```
  .kairoi/
  ```

  (the entire directory).

Restore the appropriate block. If you've lost track of what mode
you were in, re-run `/kairoi:init` — it detects existing state and
re-prompts when the gitignore entries are absent.

---

## Debug mode reference

```bash
export KAIROI_DEBUG=1
```

All normally-suppressed error output from kairoi scripts surfaces on
stderr. Each script also emits a `kairoi-debug: <script-name> starting`
banner, making hook execution order visible during a session.

Useful for diagnosing any of the scenarios above, and for confirming
whether a particular hook fired at all when behavior is surprising.
