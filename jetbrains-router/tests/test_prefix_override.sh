#!/usr/bin/env bash
# JETBRAINS_MCP_PREFIX: overrides the auto-detected IDE prefix so the hook
# emits the correct mcp__<prefix>__* tool name for rider, idea, or any custom
# server key the user registered in their mcpServers config.

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

INPUT='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/src/app.ts" }
}'

# --- Default: no env var, FORCE_INTERNAL=1 → webstorm (probe skipped) --------
# In test mode (FORCE_INTERNAL=1 set by helpers.sh), auto-detection is skipped
# so results are deterministic regardless of which IDE is open on the machine.
unset JETBRAINS_MCP_PREFIX
run_hook "$INPUT"
assert_eq 2 "$WSR_RC" "default prefix: Read must redirect"
assert_contains "$WSR_STDERR" "mcp__webstorm__read_file" "default prefix falls back to webstorm in FORCE_INTERNAL mode"

# --- rider prefix -------------------------------------------------------------
export JETBRAINS_MCP_PREFIX=rider
run_hook "$INPUT"
assert_eq 2 "$WSR_RC" "rider prefix: Read must redirect"
assert_contains "$WSR_STDERR" "mcp__rider__read_file" "prefix=rider must emit rider tool name"
assert_not_contains "$WSR_STDERR" "mcp__webstorm__" "rider prefix must not leak webstorm in stderr"

# --- idea prefix --------------------------------------------------------------
export JETBRAINS_MCP_PREFIX=idea
run_hook "$INPUT"
assert_eq 2 "$WSR_RC" "idea prefix: Read must redirect"
assert_contains "$WSR_STDERR" "mcp__idea__read_file" "prefix=idea must emit idea tool name"
assert_not_contains "$WSR_STDERR" "mcp__webstorm__" "idea prefix must not leak webstorm in stderr"

# --- Custom renamed entry (e.g. user added -ide suffix) ----------------------
export JETBRAINS_MCP_PREFIX=webstorm-ide
run_hook "$INPUT"
assert_eq 2 "$WSR_RC" "custom prefix: Read must redirect"
assert_contains "$WSR_STDERR" "mcp__webstorm-ide__read_file" "custom prefix must be used verbatim"

unset JETBRAINS_MCP_PREFIX
