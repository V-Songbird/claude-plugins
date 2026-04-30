#!/usr/bin/env bash
# Native Read on a project file → blocked and redirected to
# mcp__webstorm__read_file with the project-relative path.

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

INPUT='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/src/components/App.tsx" }
}'

run_hook "$INPUT"

assert_eq 2 "$WSR_RC" "Read on a project file should block with exit 2"
assert_contains "$WSR_STDERR" "mcp__webstorm__read_file" "stderr must name the replacement tool"
assert_contains "$WSR_STDERR" 'pathInProject="src/components/App.tsx"' "stderr must carry the translated project-relative path"
assert_contains "$WSR_STDERR" "jetbrains-router:" "stderr must be namespaced"
