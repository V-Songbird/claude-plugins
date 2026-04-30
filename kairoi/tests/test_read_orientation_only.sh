#!/usr/bin/env bash
# Read-class tools (Read/Grep/Glob and the WebStorm read-equivalents) must
# trigger Phase 1 (first-touch module orientation) but NOT Phase 2 (file-level
# guard scanning) or Phase 3 (dependent-edge warnings). This is what closes
# the gap reported by the user: an agent that goes "straight to source via
# Read/Grep" was bypassing kairoi entirely; it now gets the model context
# pushed on first read, while guard-scan stays out of the way of pure reads.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
GUARD_CHECK="$PLUGIN/scripts/guard-check.sh"

init_git_repo
setup_kairoi_state "auth" "OAuth2 PKCE token lifecycle" 0
add_guard "auth" "fix-token-race" "Verify mutex lock in refreshToken" "src/auth/token.ts"

CWD="$(pwd)"

# --- Read tool: orientation fires, guard scan does NOT ---
INPUT_READ="$(jq -n --arg cwd "$CWD" '{
  cwd: $cwd,
  tool_name: "Read",
  tool_input: { file_path: "src/auth/token.ts" }
}')"

OUT_READ="$(echo "$INPUT_READ" | bash "$GUARD_CHECK")"
MSG_READ="$(echo "$OUT_READ" | jq -r '.hookSpecificOutput.additionalContext // empty')"

if ! echo "$MSG_READ" | grep -qF "OAuth2 PKCE"; then
  echo "Read tool did NOT receive Phase 1 orientation"
  echo "got: $MSG_READ"
  exit 1
fi

if echo "$MSG_READ" | grep -qF "Verify mutex lock"; then
  echo "Read tool erroneously received Phase 2 guard scan output"
  echo "got: $MSG_READ"
  exit 1
fi

# .guards-log must NOT have been written — it's the load-bearing record
# for guards-fired tracking on edits, and reads should never appear there.
if [ -f ".kairoi/.guards-log" ] && [ -s ".kairoi/.guards-log" ]; then
  echo "Read tool erroneously wrote to .guards-log"
  cat .kairoi/.guards-log
  exit 1
fi

# --- Grep tool with a path that maps to the module: same expectation ---
# Wipe seen-flag so Phase 1 fires again for this fresh "first touch".
rm -f .kairoi/.seen-*

INPUT_GREP="$(jq -n --arg cwd "$CWD" '{
  cwd: $cwd,
  tool_name: "Grep",
  tool_input: { path: "src/auth/" }
}')"

OUT_GREP="$(echo "$INPUT_GREP" | bash "$GUARD_CHECK")"
MSG_GREP="$(echo "$OUT_GREP" | jq -r '.hookSpecificOutput.additionalContext // empty')"

if ! echo "$MSG_GREP" | grep -qF "OAuth2 PKCE"; then
  echo "Grep tool did NOT receive Phase 1 orientation"
  echo "got: $MSG_GREP"
  exit 1
fi

# --- Write tool: confirms gate flips back on for write-class tools ---
rm -f .kairoi/.seen-*

INPUT_WRITE="$(jq -n --arg cwd "$CWD" '{
  cwd: $cwd,
  tool_name: "Write",
  tool_input: { file_path: "src/auth/token.ts" }
}')"

OUT_WRITE="$(echo "$INPUT_WRITE" | bash "$GUARD_CHECK")"
MSG_WRITE="$(echo "$OUT_WRITE" | jq -r '.hookSpecificOutput.additionalContext // empty')"

if ! echo "$MSG_WRITE" | grep -qF "Verify mutex lock"; then
  echo "Write tool did NOT receive Phase 2 guard scan output (gate broken)"
  echo "got: $MSG_WRITE"
  exit 1
fi

assert_contains ".kairoi/.guards-log" "fix-token-race" || exit 1

exit 0
