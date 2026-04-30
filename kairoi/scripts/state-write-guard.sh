#!/usr/bin/env bash
set -euo pipefail

# kairoi PreToolUse hook: deny hand-edits to .kairoi/ state.
#
# Fires on Edit / Write / MultiEdit. Denies the tool call when the target
# path is under .kairoi/ — except .kairoi/overrides.json (the user-correction
# surface, deliberately editable).
#
# Three classes of legitimate writer all bypass this hook automatically:
#   1. Subagents (kairoi-complete, kairoi-audit, kairoi-reflect-module) —
#      PreToolUse hooks do not fire for tool calls inside subagents (Claude
#      Code anthropics/claude-code#34692). Verified by the end-to-end
#      kairoi-complete fixture in test_state_write_guard.sh.
#   2. Hook scripts (auto-buffer.sh, buffer-append.sh, sync-finalize.sh,
#      seed-guards.sh) — they write via shell redirection, not Edit/Write
#      tool calls, so they are not matched.
#   3. The init skill — bracketed by a `.kairoi/.write-guard-disabled`
#      sentinel that init creates before its first Write tool call and
#      removes after its last one. The sentinel is a transient dotfile
#      (gitignored under .kairoi/.* in Team mode, the whole .kairoi/ in
#      Solo mode).
#
# Deny mechanism: emit hookSpecificOutput with permissionDecision: "deny"
# and exit 0. Exit non-zero is reserved for hook errors that should fail
# open (jq missing, malformed input).

command -v jq &>/dev/null || exit 0

INPUT="$(cat)"
CWD="$(echo "$INPUT" | jq -r '.cwd // empty')"
[ -n "$CWD" ] || exit 0

STATE_DIR="$CWD/.kairoi"

# Pre-init: no _index.json means kairoi has not been bootstrapped in this
# project. Allow all writes — the deny would otherwise block /kairoi:init's
# own Write tool calls in the very first run.
[ -f "$STATE_DIR/model/_index.json" ] || exit 0

# Sentinel: init / re-discover create this before their Write tool calls
# and remove it after. The script that toggles it uses shell I/O, which is
# not subject to this hook.
[ -f "$STATE_DIR/.write-guard-disabled" ] && exit 0

TOOL_NAME="$(echo "$INPUT" | jq -r '.tool_name // empty')"
case "$TOOL_NAME" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

# Both Edit and Write put the path at .tool_input.file_path. MultiEdit also
# uses .tool_input.file_path (single file, multiple edits). One JSON path
# covers all three matchers.
FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')"
[ -n "$FILE_PATH" ] || exit 0

# Normalize: tool inputs may be absolute (Write) or relative (Edit on a
# previously-read file). Strip the cwd prefix if present so the match logic
# only sees project-relative paths.
REL_PATH="${FILE_PATH#$CWD/}"
REL_PATH="${REL_PATH#./}"

# Off-target: not under .kairoi/. Allow.
case "$REL_PATH" in
  .kairoi|.kairoi/*) ;;
  *) exit 0 ;;
esac

# Allowlist: overrides.json is the documented user-correction surface.
# Exact match only — we do not allowlist .kairoi/overrides.json.bak or
# similar shapes.
if [ "$REL_PATH" = ".kairoi/overrides.json" ]; then
  exit 0
fi

# Deny. The reason text routes the agent to the right primitive for what it
# was probably trying to do.
REASON="kairoi blocks hand-edits to $REL_PATH. Use \`/kairoi:audit <module>\` to rebuild guards from source, \`/kairoi:show <module>\` for a read-only view, or write to \`.kairoi/overrides.json\` to correct kairoi's understanding."

jq -n --arg reason "$REASON" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $reason
  }
}'

exit 0
