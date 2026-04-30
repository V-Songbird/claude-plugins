#!/usr/bin/env bash
# Native Grep → blocked and redirected to mcp__webstorm__search_regex.

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

INPUT='{
  "tool_name": "Grep",
  "cwd": "/home/proj/my-app",
  "tool_input": { "pattern": "TODO\\(.*\\)" }
}'

run_hook "$INPUT"

assert_eq 2 "$WSR_RC" "Grep should block with exit 2"
assert_contains "$WSR_STDERR" "mcp__webstorm__search_regex" "stderr must name the regex replacement tool"
assert_contains "$WSR_STDERR" "mcp__webstorm__search_text" "stderr must also mention search_text as the literal alternative"
