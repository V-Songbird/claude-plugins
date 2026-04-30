#!/usr/bin/env bash
# Flow 1: guard-check writes fired source_task IDs to .guards-log; buffer-append
# reads/clears the log into the buffer entry's guards_fired field.
#
# This is the load-bearing mechanical contract that makes guards honor-free.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
GUARD_CHECK="$PLUGIN/scripts/guard-check.sh"
BUFFER_APPEND="$PLUGIN/scripts/buffer-append.sh"

init_git_repo
setup_kairoi_state "auth" "Auth module" 0
add_guard "auth" "fix-token-race" "Verify mutex lock in refreshToken" "src/auth/token.ts"

CWD="$(pwd)"

# --- Stage 1: guard-check fires on Write to a trigger file ---
# tool_name must be supplied: guard-check classifies the call as write-class
# vs read-class to decide whether to run guard scanning (Phase 2). Read/Grep
# only get orientation (Phase 1).
INPUT="$(jq -n --arg cwd "$CWD" '{
  cwd: $cwd,
  tool_name: "Write",
  tool_input: { file_path: "src/auth/token.ts" }
}')"

OUTPUT="$(echo "$INPUT" | bash "$GUARD_CHECK")"

# Hook must emit hookSpecificOutput.additionalContext containing the guard
# check text. PreToolUse stdout MUST use the
# `{hookSpecificOutput: {hookEventName, additionalContext}}` envelope —
# bare `{systemMessage}` is silently dropped from PreToolUse delivery.
if ! echo "$OUTPUT" | jq -e '.hookSpecificOutput.additionalContext' >/dev/null 2>&1; then
  echo "guard-check produced no hookSpecificOutput.additionalContext"
  echo "raw output: $OUTPUT"
  exit 1
fi

MSG="$(echo "$OUTPUT" | jq -r '.hookSpecificOutput.additionalContext')"
if ! echo "$MSG" | grep -qF "Verify mutex lock"; then
  echo "additionalContext missing guard check text"
  echo "got: $MSG"
  exit 1
fi

# .guards-log must now contain the source_task
assert_contains ".kairoi/.guards-log" "fix-token-race" || exit 1

# --- Stage 2: buffer-append reads and clears the log ---
commit_file "src/auth/token.ts" "// token" "fix(auth): token race [State: BUFFERED]"

bash "$BUFFER_APPEND" \
  --task "fix-token-race" \
  --status "SUCCESS" \
  --summary "improved token handling" \
  --skip-tests >/dev/null

assert_line_count ".kairoi/buffer.jsonl" 1 || exit 1
assert_jq ".kairoi/buffer.jsonl" '.guards_fired[0]' "fix-token-race" || exit 1
assert_empty_or_missing ".kairoi/.guards-log" || exit 1

# --- Stage 3: edit to a non-trigger file produces no guard text ---
INPUT2="$(jq -n --arg cwd "$CWD" '{
  cwd: $cwd,
  tool_name: "Write",
  tool_input: { file_path: "src/auth/unrelated.ts" }
}')"

OUTPUT2="$(echo "$INPUT2" | bash "$GUARD_CHECK")"

# Should be empty or have no additionalContext mentioning this guard
# (scope/edge hints allowed, but no guard content). Assertion: output must
# not contain the guard's check text.
if echo "$OUTPUT2" | grep -qF "Verify mutex lock"; then
  echo "guard-check fired on non-trigger file"
  echo "output: $OUTPUT2"
  exit 1
fi

exit 0
