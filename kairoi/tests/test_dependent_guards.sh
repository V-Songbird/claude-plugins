#!/usr/bin/env bash
# Flow 8: dependent-module guard triggering.
# A guard whose trigger_files includes a dependent module's source_path prefix
# (e.g., "src/api/") must fire when ANY file under that prefix is edited.
# This is the mechanical infrastructure that makes B1 (dependent-guard
# generation during reflection) actually bite: once reflection extends a
# guard's trigger_files, guard-check must honor the cross-module trigger.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
GUARD_CHECK="$PLUGIN/scripts/guard-check.sh"

init_git_repo
setup_kairoi_state "auth" "Auth module" 0

# Add a second module (api, dependent on auth) to _index
jq '.modules.api = {source_paths: ["src/api/"]} |
    .edges = [{from: "api", to: "auth", type: "calls", label: "token validation", weight: 1, last_seen: "2026-04-10"}]' \
    .kairoi/model/_index.json > /tmp/idx.json && mv /tmp/idx.json .kairoi/model/_index.json

jq -n '{purpose: "REST endpoints", entry_points: ["src/api/index.ts"], guards: [], known_patterns: [], dependencies: ["auth"], _meta: {confidence: "high", last_validated: "2026-04-01", tasks_since_validation: 0}}' > .kairoi/model/api.json

# Guard lives on auth, but its trigger_files include a cross-module prefix
# (src/api/) — this is what reflection would produce for an interface-level
# guard per the new B1 logic.
jq --arg today "$(date -u +%Y-%m-%d)" \
   '.guards += [{
     trigger_files: ["src/auth/token.ts", "src/api/"],
     check: "Verify token signature contract with callers",
     rationale: "Refresh-token format changed in fix-token-race; callers in api depend on the exact shape",
     source_task: "fix-token-race",
     created: $today,
     confirmed: 0,
     disputed: 0
   }]' .kairoi/model/auth.json > /tmp/auth.json && mv /tmp/auth.json .kairoi/model/auth.json

CWD="$(pwd)"

assert_fires() {
  local file="$1"
  local label="$2"
  local input
  input="$(jq -n --arg cwd "$CWD" --arg f "$file" '{cwd: $cwd, tool_name: "Write", tool_input: {file_path: $f}}')"
  local out
  out="$(echo "$input" | bash "$GUARD_CHECK")"
  local msg
  msg="$(echo "$out" | jq -r '.hookSpecificOutput.additionalContext // empty')"
  if ! echo "$msg" | grep -qF "Verify token signature"; then
    echo "[$label] edit to $file did NOT fire the cross-module guard"
    echo "  additionalContext: $msg"
    return 1
  fi
  return 0
}

assert_does_not_fire() {
  local file="$1"
  local label="$2"
  local input
  input="$(jq -n --arg cwd "$CWD" --arg f "$file" '{cwd: $cwd, tool_name: "Write", tool_input: {file_path: $f}}')"
  local out
  out="$(echo "$input" | bash "$GUARD_CHECK")"
  local msg
  msg="$(echo "$out" | jq -r '.hookSpecificOutput.additionalContext // empty')"
  if echo "$msg" | grep -qF "Verify token signature"; then
    echo "[$label] edit to $file erroneously fired the guard"
    echo "  additionalContext: $msg"
    return 1
  fi
  return 0
}

# Direct file in auth module: original trigger. Must fire.
assert_fires "src/auth/token.ts" "direct auth file" || exit 1

# Any file under dependent module api (prefix match via "src/api/"). Must fire.
assert_fires "src/api/middleware.ts" "dependent api file" || exit 1
assert_fires "src/api/routes/users.ts" "deep dependent api file" || exit 1

# File in auth but not in trigger_files list. Must NOT fire this guard.
# (It might still fire orientation on first edit, but not THIS guard's check text.)
assert_does_not_fire "src/auth/unrelated.ts" "unrelated auth file" || exit 1

# The guard's source_task must still be logged to .guards-log on every match
# (so dispute/confirmation tracking still works across modules).
LOG_LINES="$(sort -u .kairoi/.guards-log | wc -l | tr -d ' ')"
# Three fires so far (token.ts + 2 api files), dedup → 1 unique source_task.
if [ "$LOG_LINES" != "1" ]; then
  echo "expected 1 unique source_task in .guards-log, got $LOG_LINES"
  cat .kairoi/.guards-log
  exit 1
fi

exit 0
