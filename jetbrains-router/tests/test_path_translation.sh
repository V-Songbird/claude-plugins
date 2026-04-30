#!/usr/bin/env bash
# Path translation: absolute paths (both Unix and Windows-style) inside the
# project root must be converted to project-relative. Paths outside the
# project must cause the hook to fail open (WebStorm can't see them).

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

# --- Unix absolute inside project -----------------------------------------
INPUT_UNIX='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/packages/ui/src/App.tsx" }
}'
run_hook "$INPUT_UNIX"
assert_eq 2 "$WSR_RC" "Unix absolute inside project should block"
assert_contains "$WSR_STDERR" 'pathInProject="packages/ui/src/App.tsx"' "Unix path must strip root"

# --- Windows absolute inside project with backslashes ---------------------
INPUT_WIN='{
  "tool_name": "Read",
  "cwd": "D:\\Projects\\Work\\DLL\\GPRICE-Unified-Pricing-Portal",
  "tool_input": { "file_path": "D:\\Projects\\Work\\DLL\\GPRICE-Unified-Pricing-Portal\\packages\\ui\\src\\App.tsx" }
}'
run_hook "$INPUT_WIN"
assert_eq 2 "$WSR_RC" "Windows absolute inside project should block"
assert_contains "$WSR_STDERR" 'pathInProject="packages/ui/src/App.tsx"' "Windows backslashes must normalize to forward slashes"

# --- Already-relative path --------------------------------------------------
INPUT_REL='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "src/app.ts" }
}'
run_hook "$INPUT_REL"
assert_eq 2 "$WSR_RC" "Already-relative path should still block"
assert_contains "$WSR_STDERR" 'pathInProject="src/app.ts"' "relative path passes through unchanged"

# --- Absolute path OUTSIDE the project root → fail open -------------------
INPUT_OUT='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/etc/hosts" }
}'
run_hook "$INPUT_OUT"
assert_eq 0 "$WSR_RC" "path outside project root must fail open (WebStorm can't see it)"
