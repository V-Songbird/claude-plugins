#!/usr/bin/env bash
# Fail-open: when JETBRAINS_ROUTER_DISABLE=1, the hook exits 0 regardless of
# the tool — native Read/Grep/etc run unimpeded. This is the kill-switch
# users rely on when the WebStorm MCP server isn't available.

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

# Override the test default: force fail-open mode. Unset both the internal
# probe-bypass and the legacy public name so neither leaks past the kill
# switch.
unset JETBRAINS_ROUTER_FORCE_INTERNAL
unset JETBRAINS_ROUTER_FORCE
export JETBRAINS_ROUTER_DISABLE=1

INPUT='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/src/app.ts" }
}'

run_hook "$INPUT"

assert_eq 0 "$WSR_RC" "kill-switch must fail open (exit 0) even on a tool that would normally redirect"
assert_not_contains "$WSR_STDERR" "mcp__webstorm__" "no redirect message should be emitted"

# And confirm Bash aggressive patterns also fail open:
INPUT_CAT='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "cat src/app.ts" }
}'
run_hook "$INPUT_CAT"
assert_eq 0 "$WSR_RC" "Bash cat must fail open with kill-switch on"
