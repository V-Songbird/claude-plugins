#!/usr/bin/env bash
# Anti-bypass: an agent must not be able to dodge a redirect by prefixing the
# Bash command with env-var assignments. The `JETBRAINS_ROUTER_*` family in
# particular is the user's session-level control surface (kill switch,
# force-on, per-tool bypass list); setting it via command prefix would let
# an agent silently disable the plugin on a per-call basis.
#
# Two behaviors verified here:
#   1. A neutral env prefix (e.g. `FOO=1 cat …`) gets stripped — the same
#      redirect the unprefixed command would emit fires.
#   2. A JETBRAINS_ROUTER_* env prefix gets blocked outright with an
#      explanatory message naming the variable.

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

CWD="/home/proj/my-app"

# --- Neutral env prefix is stripped, dispatch still fires -----------------
INPUT_FOO="{
  \"tool_name\": \"Bash\",
  \"cwd\": \"$CWD\",
  \"tool_input\": { \"command\": \"FOO=1 cat src/app.ts\" }
}"
run_hook "$INPUT_FOO"
assert_eq 2 "$WSR_RC" "FOO=1 prefix must not bypass cat redirect"
assert_contains "$WSR_STDERR" "mcp__webstorm__read_file" "stripped FOO=1 cat still names read_file"
assert_contains "$WSR_STDERR" "src/app.ts" "redirect carries the right file path after env strip"

# --- Multi-prefix env strip ----------------------------------------------
INPUT_MULTI="{
  \"tool_name\": \"Bash\",
  \"cwd\": \"$CWD\",
  \"tool_input\": { \"command\": \"FOO=1 BAR=2 cat src/app.ts\" }
}"
run_hook "$INPUT_MULTI"
assert_eq 2 "$WSR_RC" "FOO=1 BAR=2 prefix must not bypass cat redirect"
assert_contains "$WSR_STDERR" "mcp__webstorm__read_file" "multi-prefix stripped, redirect fires"

# --- Leading `env` is stripped --------------------------------------------
INPUT_ENV="{
  \"tool_name\": \"Bash\",
  \"cwd\": \"$CWD\",
  \"tool_input\": { \"command\": \"env FOO=1 cat src/app.ts\" }
}"
run_hook "$INPUT_ENV"
assert_eq 2 "$WSR_RC" "leading 'env' must not bypass cat redirect"
assert_contains "$WSR_STDERR" "mcp__webstorm__read_file" "stripped 'env FOO=1 cat' still redirects"

# --- JETBRAINS_ROUTER_DISABLE prefix is blocked with anti-bypass message ---
INPUT_DISABLE="{
  \"tool_name\": \"Bash\",
  \"cwd\": \"$CWD\",
  \"tool_input\": { \"command\": \"JETBRAINS_ROUTER_DISABLE=1 cat src/app.ts\" }
}"
run_hook "$INPUT_DISABLE"
assert_eq 2 "$WSR_RC" "JETBRAINS_ROUTER_DISABLE prefix must be blocked"
assert_contains "$WSR_STDERR" "JETBRAINS_ROUTER_" "anti-bypass message names the variable family"
assert_contains "$WSR_STDERR" "do not set" "anti-bypass message tells agent not to set it"
assert_not_contains "$WSR_STDERR" "mcp__webstorm__read_file" "anti-bypass takes precedence over the cat redirect"

# --- JETBRAINS_ROUTER_FORCE_INTERNAL prefix is blocked too -----------------
INPUT_FORCE="{
  \"tool_name\": \"Bash\",
  \"cwd\": \"$CWD\",
  \"tool_input\": { \"command\": \"JETBRAINS_ROUTER_FORCE_INTERNAL=1 cat src/app.ts\" }
}"
run_hook "$INPUT_FORCE"
assert_eq 2 "$WSR_RC" "JETBRAINS_ROUTER_FORCE_INTERNAL prefix must be blocked"
assert_contains "$WSR_STDERR" "JETBRAINS_ROUTER_" "anti-bypass message fires for FORCE_INTERNAL too"

# --- JETBRAINS_ROUTER_BYPASS prefix is blocked too -------------------------
INPUT_BYPASS="{
  \"tool_name\": \"Bash\",
  \"cwd\": \"$CWD\",
  \"tool_input\": { \"command\": \"JETBRAINS_ROUTER_BYPASS=Read,Edit cat src/app.ts\" }
}"
run_hook "$INPUT_BYPASS"
assert_eq 2 "$WSR_RC" "JETBRAINS_ROUTER_BYPASS prefix must be blocked"
assert_contains "$WSR_STDERR" "JETBRAINS_ROUTER_" "anti-bypass message fires for BYPASS too"

# --- Mixed: neutral prefix BEFORE plugin var still triggers anti-bypass ---
INPUT_MIXED="{
  \"tool_name\": \"Bash\",
  \"cwd\": \"$CWD\",
  \"tool_input\": { \"command\": \"FOO=1 JETBRAINS_ROUTER_DISABLE=1 cat src/app.ts\" }
}"
run_hook "$INPUT_MIXED"
assert_eq 2 "$WSR_RC" "JETBRAINS_ROUTER_ check must run for any peeled token, not just the first"
assert_contains "$WSR_STDERR" "JETBRAINS_ROUTER_" "anti-bypass fires when plugin var is the second prefix"

# --- ls dispatch survives env prefix --------------------------------------
INPUT_LS="{
  \"tool_name\": \"Bash\",
  \"cwd\": \"$CWD\",
  \"tool_input\": { \"command\": \"FOO=1 ls src\" }
}"
run_hook "$INPUT_LS"
assert_eq 2 "$WSR_RC" "FOO=1 ls must redirect after env strip"
assert_contains "$WSR_STDERR" "mcp__webstorm__list_directory_tree" "ls operand extraction works post-strip"
assert_contains "$WSR_STDERR" "directoryPath=\"src\"" "ls picked the right directory after strip"

# --- find dispatch survives env prefix ------------------------------------
INPUT_FIND="{
  \"tool_name\": \"Bash\",
  \"cwd\": \"$CWD\",
  \"tool_input\": { \"command\": \"FOO=1 find . -name foo.ts\" }
}"
run_hook "$INPUT_FIND"
assert_eq 2 "$WSR_RC" "FOO=1 find -name must redirect after env strip"
assert_contains "$WSR_STDERR" "mcp__webstorm__find_files_by_name_keyword" "find pattern matched post-strip"
