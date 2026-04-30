#!/usr/bin/env bash
# Flow 5: first-edit-per-module orientation.
# On the first Write/Edit within a module during a session, guard-check injects
# the module's purpose, confidence, and guard count as a system message.
# Subsequent edits within the same module do not repeat the orientation.
# SessionStart wipes the .seen-<module> flag so orientation re-fires on the
# next session.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
GUARD_CHECK="$PLUGIN/scripts/guard-check.sh"

init_git_repo
setup_kairoi_state "auth" "OAuth2 PKCE token lifecycle" 0

CWD="$(pwd)"
INPUT_TOKEN="$(jq -n --arg cwd "$CWD" '{cwd: $cwd, tool_input: {file_path: "src/auth/token.ts"}}')"
INPUT_OTHER="$(jq -n --arg cwd "$CWD" '{cwd: $cwd, tool_input: {file_path: "src/auth/other.ts"}}')"

# --- First edit in module: orientation fires ---
OUTPUT1="$(echo "$INPUT_TOKEN" | bash "$GUARD_CHECK")"
MSG1="$(echo "$OUTPUT1" | jq -r '.hookSpecificOutput.additionalContext // empty')"

if ! echo "$MSG1" | grep -qF "OAuth2 PKCE"; then
  echo "first-edit orientation missing module purpose"
  echo "got: $MSG1"
  exit 1
fi

if ! echo "$MSG1" | grep -qF "confidence=high"; then
  echo "first-edit orientation missing confidence line"
  echo "got: $MSG1"
  exit 1
fi

# Seen flag must exist
if [ ! -f ".kairoi/.seen-auth" ]; then
  echo ".seen-auth flag not created after first edit"
  exit 1
fi

# --- Second edit in the same module during the same session: no repeat ---
OUTPUT2="$(echo "$INPUT_OTHER" | bash "$GUARD_CHECK")"
MSG2="$(echo "$OUTPUT2" | jq -r '.hookSpecificOutput.additionalContext // empty')"

if echo "$MSG2" | grep -qF "OAuth2 PKCE"; then
  echo "orientation repeated on second edit within same session"
  echo "got: $MSG2"
  exit 1
fi

# --- Session restart (simulated by wiping .seen-* flags) ---
rm -f .kairoi/.seen-*

OUTPUT3="$(echo "$INPUT_TOKEN" | bash "$GUARD_CHECK")"
MSG3="$(echo "$OUTPUT3" | jq -r '.hookSpecificOutput.additionalContext // empty')"

if ! echo "$MSG3" | grep -qF "OAuth2 PKCE"; then
  echo "orientation did not re-fire after seen-flag wipe"
  echo "got: $MSG3"
  exit 1
fi

exit 0
