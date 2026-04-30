#!/usr/bin/env bash
# JETBRAINS_ROUTER_BYPASS: comma-separated list of native tool names to leave
# alone. Per-tool escape hatch, finer-grained than the all-or-nothing
# JETBRAINS_ROUTER_DISABLE kill switch.

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

# --- Sanity: without BYPASS, Read redirects -------------------------------
INPUT_READ='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/src/app.ts" }
}'
unset JETBRAINS_ROUTER_BYPASS
run_hook "$INPUT_READ"
assert_eq 2 "$WSR_RC" "baseline: Read without bypass should redirect"
assert_contains "$WSR_STDERR" "mcp__webstorm__read_file" "baseline redirect names read_file"

# --- Single tool in bypass → that tool passes through ---------------------
export JETBRAINS_ROUTER_BYPASS=Read
run_hook "$INPUT_READ"
assert_eq 0 "$WSR_RC" "BYPASS=Read must let Read through"
assert_not_contains "$WSR_STDERR" "mcp__webstorm__" "no redirect msg when Read is bypassed"

# --- Other tools still redirect when only Read is bypassed ----------------
INPUT_GREP='{
  "tool_name": "Grep",
  "cwd": "/home/proj/my-app",
  "tool_input": { "pattern": "TODO" }
}'
run_hook "$INPUT_GREP"
assert_eq 2 "$WSR_RC" "BYPASS=Read must NOT affect Grep"
assert_contains "$WSR_STDERR" "search_regex" "Grep still redirects when only Read is in bypass list"

# --- Multiple tools in bypass ---------------------------------------------
export JETBRAINS_ROUTER_BYPASS=Read,Edit,Grep
run_hook "$INPUT_GREP"
assert_eq 0 "$WSR_RC" "BYPASS=Read,Edit,Grep must let Grep through"

INPUT_EDIT='{
  "tool_name": "Edit",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/src/app.ts" }
}'
run_hook "$INPUT_EDIT"
assert_eq 0 "$WSR_RC" "BYPASS=Read,Edit,Grep must let Edit through"

INPUT_WRITE='{
  "tool_name": "Write",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/src/new.ts" }
}'
run_hook "$INPUT_WRITE"
assert_eq 2 "$WSR_RC" "Write must still redirect — not in bypass list"
assert_contains "$WSR_STDERR" "create_new_file" "Write redirect still names create_new_file"

# --- Exact-name matching (no substring bleed) -----------------------------
# "Rea" should not match "Read" — the comma-delimited case must be anchored.
export JETBRAINS_ROUTER_BYPASS=Rea
run_hook "$INPUT_READ"
assert_eq 2 "$WSR_RC" "BYPASS=Rea must not match Read (substring bleed would be a bug)"

# --- Empty bypass value behaves as absent ---------------------------------
export JETBRAINS_ROUTER_BYPASS=
run_hook "$INPUT_READ"
assert_eq 2 "$WSR_RC" "empty BYPASS must behave as absent — Read redirects"

unset JETBRAINS_ROUTER_BYPASS
