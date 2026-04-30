#!/usr/bin/env bash
# Aggressive Bash redirect: cat/head/tail/ls/grep/rg/find -name on project
# files should redirect to WebStorm equivalents. Piped commands must NOT
# redirect (composition → native Bash).

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

# --- cat FILE → read_file --------------------------------------------------
INPUT_CAT='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "cat src/app.ts" }
}'
run_hook "$INPUT_CAT"
assert_eq 2 "$WSR_RC" "cat should block"
assert_contains "$WSR_STDERR" "mcp__webstorm__read_file" "cat must redirect to read_file"
assert_contains "$WSR_STDERR" 'pathInProject="src/app.ts"' "cat must carry project-relative path"

# --- grep ... → search_text/search_regex -----------------------------------
INPUT_GREP='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "grep -r TODO src/" }
}'
run_hook "$INPUT_GREP"
assert_eq 2 "$WSR_RC" "grep should block"
assert_contains "$WSR_STDERR" "search_text" "grep must mention search_text"

# --- rg ... → search_text/search_regex ------------------------------------
INPUT_RG='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "rg --files-with-matches TODO" }
}'
run_hook "$INPUT_RG"
assert_eq 2 "$WSR_RC" "rg should block"
assert_contains "$WSR_STDERR" "search_text" "rg must mention search_text"

# --- find -name → find_files_by_name_keyword ------------------------------
INPUT_FIND='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "find . -name *.ts" }
}'
run_hook "$INPUT_FIND"
assert_eq 2 "$WSR_RC" "find -name should block"
assert_contains "$WSR_STDERR" "find_files_by_name_keyword" "find -name must redirect to find_files_by_name_keyword"

# --- find -exec → NOT redirected (complex expression) --------------------
INPUT_FIND_EXEC='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "find . -name *.log -exec rm {} ;" }
}'
run_hook "$INPUT_FIND_EXEC"
assert_eq 0 "$WSR_RC" "find with -exec must stay on native Bash"

# --- Piped composition → NOT redirected ----------------------------------
INPUT_PIPE='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "cat src/app.ts | wc -l" }
}'
run_hook "$INPUT_PIPE"
assert_eq 0 "$WSR_RC" "piped commands must stay on native Bash (WebStorm can't compose)"
