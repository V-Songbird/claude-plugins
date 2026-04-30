#!/usr/bin/env bash
# Edge cases pinned by 0.1.1-alpha bug fixes. Each block exercises one fix
# from the 0.1.1 CHANGELOG — group-by-fix, not by tool.

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

# --- Fix: input-redirect '<' is a composition, must bail -------------------
INPUT_LT='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "grep foo < input.txt" }
}'
run_hook "$INPUT_LT"
assert_eq 0 "$WSR_RC" "input redirect '<' must bail to native Bash"

INPUT_HERESTRING='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "grep foo <<< some-input" }
}'
run_hook "$INPUT_HERESTRING"
assert_eq 0 "$WSR_RC" "here-string '<<<' must bail to native Bash"

INPUT_BG='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "npm run build & echo done" }
}'
run_hook "$INPUT_BG"
assert_eq 0 "$WSR_RC" "backgrounding '&' must bail to native Bash"

# --- Fix: empty cwd + absolute path must fail open -------------------------
INPUT_NOCWD='{
  "tool_name": "Read",
  "cwd": "",
  "tool_input": { "file_path": "/etc/hosts" }
}'
run_hook "$INPUT_NOCWD"
assert_eq 0 "$WSR_RC" "absolute path with empty cwd must fail open (no project root to relativize against)"
assert_not_contains "$WSR_STDERR" "pathInProject=\"/etc/hosts\"" "must not leak absolute path as pathInProject"

# --- Fix: tail -f / head --follow must bail --------------------------------
INPUT_TAIL_F='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "tail -f src/app.log" }
}'
run_hook "$INPUT_TAIL_F"
assert_eq 0 "$WSR_RC" "tail -f is a follow, must bail to native Bash"

INPUT_HEAD_FOLLOW='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "tail --follow src/app.log" }
}'
run_hook "$INPUT_HEAD_FOLLOW"
assert_eq 0 "$WSR_RC" "tail --follow must bail to native Bash"

# --- Fix: Edit on nonexistent file must fail open --------------------------
INPUT_EDIT_MISSING='{
  "tool_name": "Edit",
  "cwd": "/tmp/jetbrains-router-test-nonexistent-DIR",
  "tool_input": { "file_path": "/tmp/jetbrains-router-test-nonexistent-DIR/does-not-exist.ts" }
}'
run_hook "$INPUT_EDIT_MISSING"
assert_eq 0 "$WSR_RC" "Edit on a nonexistent file must fail open (replace_text_in_file would 404)"

# --- Fix: Write on existing file must fail open ----------------------------
# Create a real file in the test tmpdir (cwd is a mktemp-d from run.sh).
EXISTING_FILE="$PWD/existing.ts"
: > "$EXISTING_FILE"
INPUT_WRITE_EXISTS="{
  \"tool_name\": \"Write\",
  \"cwd\": \"$PWD\",
  \"tool_input\": { \"file_path\": \"$EXISTING_FILE\" }
}"
run_hook "$INPUT_WRITE_EXISTS"
assert_eq 0 "$WSR_RC" "Write on an existing file must fail open (create_new_file refuses overwrite)"
rm -f "$EXISTING_FILE"

# --- Fix: Edit on existing file still redirects ----------------------------
EXISTING_SRC="$PWD/src.ts"
: > "$EXISTING_SRC"
INPUT_EDIT_EXISTS="{
  \"tool_name\": \"Edit\",
  \"cwd\": \"$PWD\",
  \"tool_input\": { \"file_path\": \"$EXISTING_SRC\" }
}"
run_hook "$INPUT_EDIT_EXISTS"
assert_eq 2 "$WSR_RC" "Edit on an existing file should still redirect"
assert_contains "$WSR_STDERR" "replace_text_in_file" "Edit redirect names replace_text_in_file"
rm -f "$EXISTING_SRC"

# --- Fix: Write on new file still redirects --------------------------------
NEW_FILE="$PWD/new-file.ts"
INPUT_WRITE_NEW="{
  \"tool_name\": \"Write\",
  \"cwd\": \"$PWD\",
  \"tool_input\": { \"file_path\": \"$NEW_FILE\" }
}"
run_hook "$INPUT_WRITE_NEW"
assert_eq 2 "$WSR_RC" "Write on a new file should still redirect"
assert_contains "$WSR_STDERR" "create_new_file" "Write redirect names create_new_file"

# --- Fix: Windows drive-letter case mismatch -------------------------------
INPUT_DRIVE_CASE='{
  "tool_name": "Read",
  "cwd": "D:\\Projects\\my-app",
  "tool_input": { "file_path": "d:\\Projects\\my-app\\src\\app.ts" }
}'
run_hook "$INPUT_DRIVE_CASE"
assert_eq 2 "$WSR_RC" "lowercase drive on file + uppercase on root should still match"
assert_contains "$WSR_STDERR" 'pathInProject="src/app.ts"' "drive-letter case must not block prefix strip"

# --- Fix: quoted paths in Bash bail ----------------------------------------
INPUT_QUOTED_SINGLE='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "cat '"'"'my file.ts'"'"'" }
}'
run_hook "$INPUT_QUOTED_SINGLE"
assert_eq 0 "$WSR_RC" "quoted path (single quotes) must bail — can'\''t safely parse with awk NF"

INPUT_QUOTED_DOUBLE='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "cat \"my file.ts\"" }
}'
run_hook "$INPUT_QUOTED_DOUBLE"
assert_eq 0 "$WSR_RC" "quoted path (double quotes) must bail"

# --- Fix: ls DIR -la parses DIR, not "." -----------------------------------
INPUT_LS_DIR_FLAG='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "ls src -la" }
}'
run_hook "$INPUT_LS_DIR_FLAG"
assert_eq 2 "$WSR_RC" "ls DIR -la should redirect"
assert_contains "$WSR_STDERR" 'directoryPath="src"' "ls DIR -la must resolve DIR to src, not ."

# --- Fix: find with -type must bail ----------------------------------------
INPUT_FIND_TYPE='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "find . -type f -name *.ts" }
}'
run_hook "$INPUT_FIND_TYPE"
assert_eq 0 "$WSR_RC" "find with -type must stay on native (find_files_by_name_keyword can't model -type)"

INPUT_FIND_MAXDEPTH='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "find src -maxdepth 2 -name *.ts" }
}'
run_hook "$INPUT_FIND_MAXDEPTH"
assert_eq 0 "$WSR_RC" "find with -maxdepth must stay on native"

INPUT_FIND_OR='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "find src -name *.ts -or -name *.tsx" }
}'
run_hook "$INPUT_FIND_OR"
assert_eq 0 "$WSR_RC" "find with -or must stay on native"

# --- Fix: binary-file guard ------------------------------------------------
for EXT in png jpg pdf zip exe dylib woff mp4; do
  INPUT_BIN="{
    \"tool_name\": \"Read\",
    \"cwd\": \"/home/proj/my-app\",
    \"tool_input\": { \"file_path\": \"/home/proj/my-app/assets/logo.$EXT\" }
  }"
  run_hook "$INPUT_BIN"
  assert_eq 0 "$WSR_RC" "Read on .$EXT must fail open (binary — WebStorm's read_file errors on binaries)"
done
