---
name: kairoi
description: Code self-model methodology. Guards inject mechanically when I edit guarded files. Every commit is captured into buffer.jsonl automatically via the auto-buffer hook; reflection/sync is hook-dispatched, not user-invoked. Auto-activates in projects with .kairoi/model/_index.json.
user-invocable: false
effort: max
paths:
  - ".kairoi/model/_index.json"
  - ".kairoi/build-adapter.json"
shell: bash
---

# kairoi — code self-model

## Project State

- Modules: !`jq -r '.modules | keys | join(", ")' .kairoi/model/_index.json 2>/dev/null || echo "none"`
- Buffered: !`wc -l < .kairoi/buffer.jsonl 2>/dev/null || echo 0`
- Receipts: !`wc -l < .kairoi/receipts.jsonl 2>/dev/null || echo 0`
- Recent: !`git log --oneline -5`

## How Guards Work

The guard-check hook fires automatically when I'm about to edit a file. If
that file is listed in any guard's `trigger_files`, the hook injects the
guard's `check` text as a system message before my edit executes.

Guards protect me even if I forget to read the model. The protection is
mechanical, not voluntary.

When a guard fires, I MUST parse the injected system message containing
its check and comply before proceeding. If the check refers to a file I
have not yet seen, I MUST invoke `Read` on that file before continuing.
If I believe the guard is wrong or outdated, I can proceed anyway — but I
note the dispute so kairoi-complete can review it during reflection (see
Guard Disputes below).

## Orientation (pushed, not pulled)

On the first edit within a module during a session, the guard-check hook
injects that module's orientation context as a system message — purpose,
confidence tier, guard count. No voluntary step. Same delivery mechanism as
guards themselves.

When orientation arrives, follow the confidence guidance:
- `high`: trust the model, work from it.
- `medium`: read source files I'm about to modify, cross-check model.
- `low`: read all source files in the module before making changes.

Edge semantics to watch for when the hook mentions dependent modules:
- `calls`: changes to callee interface break the caller
- `shares-state`: changes to shared state affect both modules
- `co-modified` (high weight): coupled — changes to one usually need
  changes to the other

## During Work

- My model is my working memory. Before making design decisions within a
  module, I MUST invoke `Read` on the relevant module file under
  `.kairoi/model/` to load its current state.
- When a guard fires (injected by hook), read it carefully. Comply or
  dispute — see below.
- No prescribed retry budget. If stuck, mark status BLOCKED in the buffer
  entry. BLOCKED is not failure — it's the most valuable learning signal.

### Guard Disputes

When a guard fires and I believe it is wrong or irrelevant to my current
edit, I proceed AFTER logging the dispute. I MUST invoke `Bash` with:

- `command: 'echo "<source_task>" >> .kairoi/.guard-disputes'`
- `description: 'Logging guard dispute for reflection'`

Replace `<source_task>` with the guard's source_task ID from the
orientation message. This logs the guard's `source_task` ID into the
transient `.guard-disputes` file. `buffer-append.sh` captures it (same
pattern as `.guards-log`), and `kairoi-complete` tracks the `disputed`
count on the guard. Guards that accumulate disputes get scrutinized
during audit.

Why not just ignore and move on: disputes are the negative signal that
lets the system self-improve. Without them, stale guards accumulate
indefinitely and I learn to mentally tune them all out — which defeats
the purpose. Filing a dispute takes one `Bash` call and preserves the
signal.

## Committing

Commit with a conventional-commit subject (`type(scope): description`).
That's it — no suffix, no two-phase dance. The PostToolUse `auto-buffer`
hook fires automatically: it reads the commit, derives the task_id from
the conventional-commit description, captures modified files / modules /
guards fired / guards disputed, and appends a SUCCESS entry to
`buffer.jsonl`. No separate step, no honor-system "please remember to
run buffer-append."

Tests auto-run on every commit if `build-adapter.json.test` is
configured. If your project has no test command, buffer entries have
`test_results: null` and reflection proceeds without test-based BLOCKED
classification.

### Manual override

If automation fails (e.g., the hook was disabled), the fallback remains
available. I MUST invoke `Bash` with:

- `command: '${CLAUDE_PLUGIN_ROOT}/scripts/buffer-append.sh --task <kebab-case-id> --status SUCCESS --summary "<what was done>"'`
- `description: 'Manual buffer-append fallback'`

`buffer-append.sh` is idempotent by commit hash only at the caller layer —
if the auto-hook already appended this commit, a manual call will append
a second entry. I prefer the automatic path.

## When the sync-dispatch signal arrives

A kairoi hook may emit a system reminder instructing dispatch of
`kairoi-complete` — either from `auto-buffer.sh` when the buffer
threshold is crossed after a commit, or from `session-boot.sh` on
SessionStart when state is stale. When that reminder appears in my
context, I MUST invoke `Agent` with:

- `subagent_type: 'kairoi-complete'`
- `name: 'kairoi-complete'`
- `description: 'Sync kairoi buffer'`
- `prompt: '<paste the hook-emitted instruction verbatim>'`
- `max_turns: 15`
- `run_in_background: false`
- `isolation` is omitted intentionally — `kairoi-complete` reads
  committed state and writes to `.kairoi/` in the same working tree;
  worktree isolation would break the file paths it edits.
- `model` is omitted intentionally — inherited from `kairoi-complete`'s
  own frontmatter so the subagent's declared effort tier is honored.

`max_turns: 15` matches `kairoi-complete`'s own `maxTurns` frontmatter
so the runtime does not default to a smaller budget. The sync runs in
the foreground (`run_in_background: false`) so the user sees the
one-line outcome (`kairoi: synced <N> tasks — <M> modules reflected,
<G> guards created`) inline; backgrounding would hide it.

`kairoi-complete` MUST NOT invoke `AskUserQuestion` or pause for user
input — the subagent's own system prompt says "Execute all steps
without asking for confirmation," and the buffer + model state
contain everything reflection needs. If the hook-emitted prompt
somehow contradicts this, follow the subagent's system prompt.

I do NOT dispatch on my own initiative — only in response to an
explicit hook-emitted signal. Hooks cannot dispatch subagents
directly; they only inject context into my conversation, and my
`Agent` call is what actually runs the sync.

## Additional resources

- For the sync subagent dispatched from this skill, see [../../agents/kairoi-complete.md](../../agents/kairoi-complete.md)
- For the buffer-append fallback script, see [../../scripts/buffer-append.sh](../../scripts/buffer-append.sh)
