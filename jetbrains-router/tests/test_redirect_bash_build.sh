#!/usr/bin/env bash
# Bash "npm run build" → blocked and redirected to mcp__webstorm__build_project.
# Bash "git log --oneline" → allowed (rich-history command stays native).

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

# --- Case 1: npm run build is redirected ----------------------------------
INPUT_BUILD='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "npm run build" }
}'

run_hook "$INPUT_BUILD"
assert_eq 2 "$WSR_RC" "npm run build should block"
assert_contains "$WSR_STDERR" "mcp__webstorm__build_project" "build redirect must name build_project"

# --- Case 2: git log is NOT redirected ------------------------------------
INPUT_GITLOG='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "git log --oneline -5" }
}'

run_hook "$INPUT_GITLOG"
assert_eq 0 "$WSR_RC" "git log must stay on native Bash (no WebStorm equivalent)"
assert_not_contains "$WSR_STDERR" "jetbrains-router:" "no redirect message for allowed commands"

# --- Case 3: git status stays on native ------------------------------------
# get_repositories only surfaces basic state and doesn't replace the detail
# of `git status`. Routing was more friction than value, so it stays native.
INPUT_GITSTATUS='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "git status" }
}'

run_hook "$INPUT_GITSTATUS"
assert_eq 0 "$WSR_RC" "git status must stay on native Bash"
assert_not_contains "$WSR_STDERR" "jetbrains-router:" "no redirect message for git status"
