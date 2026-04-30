#!/usr/bin/env bash
# kairoi PostToolUse hook: after ANY git commit succeeds, automatically
# append a buffer entry for it. Every commit is buffered unconditionally;
# reflection (dispatched separately on auto-sync triggers) classifies tasks
# as SUCCESS or BLOCKED from test results and other signals.
#
# Flow:
#   1. Fires PostToolUse on Bash(git commit *).
#   2. Exits silently if not in a kairoi-tracked project.
#   3. If the commit's hash already appears in buffer.jsonl, skip (dedup).
#   4. Reads FULL commit message (%B, not %s) — subject for task_id,
#      body available to reflection for text-heuristic BLOCKED detection.
#   5. Derives task_id from the conventional-commit subject's description.
#   6. Invokes buffer-append.sh; buffer-append auto-runs the configured
#      test command from `build-adapter.json.test` if set, else leaves
#      `test_results` null.

set -euo pipefail

command -v jq &>/dev/null || exit 0

_DEVNULL="/dev/null"
if [ "${KAIROI_DEBUG:-}" = "1" ]; then
  _DEVNULL="/dev/stderr"
  echo "kairoi-debug: auto-buffer starting" >&2
fi

INPUT="$(cat)"
CWD="$(echo "$INPUT" | jq -r '.cwd // empty')"
[ -n "$CWD" ] || exit 0
STATE_DIR="$CWD/.kairoi"
[ -f "$STATE_DIR/model/_index.json" ] || exit 0

# Script-side gate: only proceed for `git commit` invocations. The hook
# matcher in hooks.json is `Bash` (the only documented matcher granularity);
# a per-command predicate must be enforced here, otherwise this script runs
# after every Bash tool call and HEAD-buffers spuriously on commands like
# `ls`, `pytest`, etc. (Dedup catches re-buffers on the second hit, but
# only after a wasted run.)
TOOL_CMD="$(echo "$INPUT" | jq -r '.tool_input.command // empty')"
case "$TOOL_CMD" in
  *"git commit"*|*"git "*"commit"*) ;;
  *) exit 0 ;;
esac

# Resolve plugin root even when CLAUDE_PLUGIN_ROOT is unset (e.g., manual test).
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
BUFFER_APPEND="$PLUGIN_ROOT/scripts/buffer-append.sh"
[ -x "$BUFFER_APPEND" ] || [ -f "$BUFFER_APPEND" ] || exit 0

# HEAD: full message (%B), subject (first line), hash. Reading the full
# message lets reflection scan body text for the BLOCKED keyword heuristic.
FULL_MSG="$(cd "$CWD" && git log -1 --pretty=%B 2>"$_DEVNULL" || true)"
HASH="$(cd "$CWD" && git rev-parse HEAD 2>"$_DEVNULL" || true)"
[ -n "$FULL_MSG" ] && [ -n "$HASH" ] || exit 0

SUBJECT="$(echo "$FULL_MSG" | head -1)"

# Dedup: if this commit is already in the buffer, do nothing (agent already
# called buffer-append manually, or this hook fired twice).
if [ -f "$STATE_DIR/buffer.jsonl" ] && grep -qF "\"$HASH\"" "$STATE_DIR/buffer.jsonl" 2>"$_DEVNULL"; then
  exit 0
fi

# Derive task_id from the subject: strip `type(scope):` prefix, then
# kebab-case what remains. Fall back to hash-prefix if the description
# ends up empty.
RAW_DESC="$(echo "$SUBJECT" \
  | sed -E 's/^[a-zA-Z]+(\([^)]*\))?:\s*//')"

TASK_ID="$(echo "$RAW_DESC" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g' \
  | sed -E 's/^-+|-+$//g' \
  | cut -c1-60)"

[ -n "$TASK_ID" ] || TASK_ID="buffered-$(echo "$HASH" | cut -c1-7)"

SUMMARY="${RAW_DESC:-auto-buffered commit $HASH}"

# STATUS is always SUCCESS at buffer time. BLOCKED classification moves to
# reflection — driven by test-result failures or text-heuristic scan of
# commit messages.
STATUS="SUCCESS"

ARGS=(--task "$TASK_ID" --status "$STATUS" --summary "$SUMMARY")

# Run from the project cwd so buffer-append's relative .kairoi/ lookups resolve.
( cd "$CWD" && bash "$BUFFER_APPEND" "${ARGS[@]}" ) >"$_DEVNULL" 2>&1 || {
  echo "kairoi: auto-buffer failed for $HASH — run buffer-append manually" >&2
}

# Mechanical signals to surface back into Claude's context. Two triggers
# share a single hookSpecificOutput envelope (PostToolUse only delivers one
# JSON object; emitting two would invalidate the JSON and silently drop
# both):
#
#   A) Test/build failure on the just-buffered entry. buffer-append already
#      auto-promoted STATUS to BLOCKED and filled blocked_diagnostics from
#      the test output — but its stdout is /dev/null'd above, so Claude
#      never saw the failure. We re-read the just-written entry to surface
#      the failure as a system-reminder.
#
#   B) Buffer-threshold reached. Same dispatch signal as before — telling
#      Claude to invoke the kairoi-complete agent for batch reflection.
#
# Hooks can't dispatch subagents directly; they can only inject context.
# PostToolUse MUST emit JSON with hookSpecificOutput containing BOTH
# hookEventName and additionalContext fields for the message to reach the
# model. Raw stdout from PostToolUse is dropped.
BUFFER_FILE="$STATE_DIR/buffer.jsonl"
COMBINED_MSG=""

if [ -f "$BUFFER_FILE" ]; then
  # Signal A: did this commit's entry get promoted to BLOCKED?
  LAST_ENTRY="$(tail -1 "$BUFFER_FILE" 2>"$_DEVNULL" | tr -d '\r' || true)"
  if [ -n "$LAST_ENTRY" ]; then
    LAST_HASH="$(echo "$LAST_ENTRY" | jq -r '.commit_hash // empty' 2>"$_DEVNULL" || true)"
    if [ "$LAST_HASH" = "$HASH" ]; then
      LAST_STATUS="$(echo "$LAST_ENTRY" | jq -r '.status // "SUCCESS"' 2>"$_DEVNULL" || echo SUCCESS)"
      if [ "$LAST_STATUS" = "BLOCKED" ]; then
        LAST_DIAG="$(echo "$LAST_ENTRY" | jq -r '.blocked_diagnostics // ""' 2>"$_DEVNULL" || echo "")"
        COMBINED_MSG="kairoi: ⚠ commit ${HASH:0:7} was buffered as BLOCKED."
        if [ -n "$LAST_DIAG" ] && [ "$LAST_DIAG" != "null" ]; then
          COMBINED_MSG="$COMBINED_MSG Diagnostic: $LAST_DIAG."
        fi
        COMBINED_MSG="$COMBINED_MSG This is a mechanical kairoi signal from buffer-append's auto-promotion (test failures, test-disablement in the diff, or a revert commit). Address the underlying failure before continuing — don't move on to a new task while this one is broken, and don't paper over by disabling more tests."
      fi
    fi
  fi

  # Signal B: buffer-threshold reached → dispatch kairoi-complete.
  BUFFER_COUNT="$(wc -l < "$BUFFER_FILE" 2>/dev/null | tr -d ' ')"
  THRESHOLD="$(jq -r '.auto_sync_buffer_threshold // 10' "$STATE_DIR/build-adapter.json" 2>/dev/null || echo 10)"
  [ "$THRESHOLD" = "null" ] && THRESHOLD=10
  if [ "$BUFFER_COUNT" -ge "$THRESHOLD" ]; then
    THRESHOLD_MSG="kairoi: buffer holds $BUFFER_COUNT unreflected task(s), threshold $THRESHOLD reached. Dispatch the kairoi-complete agent now via the Agent tool to batch-reflect and sync. This is an automated signal from the hook — follow it via the Agent tool without asking the user for confirmation."
    if [ -n "$COMBINED_MSG" ]; then
      COMBINED_MSG="$COMBINED_MSG"$'\n\n'"$THRESHOLD_MSG"
    else
      COMBINED_MSG="$THRESHOLD_MSG"
    fi
  fi

  if [ -n "$COMBINED_MSG" ]; then
    jq -n --arg msg "$COMBINED_MSG" \
      '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
  fi
fi

exit 0
