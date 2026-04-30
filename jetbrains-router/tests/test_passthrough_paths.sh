#!/usr/bin/env bash
# Non-code paths must pass through on native tools (exit 0).
# The hook's _is_passthrough_path() guards these categories:
#   - Dotfiles / dotfolders (.claude, .idea, .gradle, .gitignore, etc.)
#   - Markdown files (CLAUDE.md, README.md, docs/guide.md)
#   - JSON / JSONL (package.json, tsconfig.json)
#   - docs/ directory
#   - Config/settings extensions (.yml, .yaml, .toml, .lock, .env, etc.)
# Source-code files (src/*.ts, etc.) must still redirect.

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

# ---------------------------------------------------------------------------
# Read — dotfolders
# ---------------------------------------------------------------------------

INPUT_READ_CLAUDE='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/.claude/settings.json" }
}'
run_hook "$INPUT_READ_CLAUDE"
assert_eq 0 "$WSR_RC" "Read on .claude/ must pass through (dotfolder)"

INPUT_READ_IDEA='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/.idea/workspace.xml" }
}'
run_hook "$INPUT_READ_IDEA"
assert_eq 0 "$WSR_RC" "Read on .idea/ must pass through (dotfolder)"

INPUT_READ_GRADLE='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/.gradle/settings.gradle" }
}'
run_hook "$INPUT_READ_GRADLE"
assert_eq 0 "$WSR_RC" "Read on .gradle/ must pass through (dotfolder)"

INPUT_READ_GITIGNORE='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/.gitignore" }
}'
run_hook "$INPUT_READ_GITIGNORE"
assert_eq 0 "$WSR_RC" "Read on .gitignore must pass through (dotfile)"

# ---------------------------------------------------------------------------
# Read — markdown
# ---------------------------------------------------------------------------

INPUT_READ_CLAUDE_MD='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/CLAUDE.md" }
}'
run_hook "$INPUT_READ_CLAUDE_MD"
assert_eq 0 "$WSR_RC" "Read on CLAUDE.md must pass through (markdown)"

INPUT_READ_README='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/README.md" }
}'
run_hook "$INPUT_READ_README"
assert_eq 0 "$WSR_RC" "Read on README.md must pass through (markdown)"

INPUT_READ_DOCS_MD='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/docs/guide.md" }
}'
run_hook "$INPUT_READ_DOCS_MD"
assert_eq 0 "$WSR_RC" "Read on docs/guide.md must pass through (markdown)"

# ---------------------------------------------------------------------------
# Read — JSON / JSONL
# ---------------------------------------------------------------------------

INPUT_READ_PKG='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/package.json" }
}'
run_hook "$INPUT_READ_PKG"
assert_eq 0 "$WSR_RC" "Read on package.json must pass through (JSON)"

INPUT_READ_TSCONFIG='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/tsconfig.json" }
}'
run_hook "$INPUT_READ_TSCONFIG"
assert_eq 0 "$WSR_RC" "Read on tsconfig.json must pass through (JSON)"

INPUT_READ_JSONL='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/data/records.jsonl" }
}'
run_hook "$INPUT_READ_JSONL"
assert_eq 0 "$WSR_RC" "Read on .jsonl must pass through (JSONL)"

# ---------------------------------------------------------------------------
# Read — docs directory
# ---------------------------------------------------------------------------

INPUT_READ_DOCS_HTML='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/docs/index.html" }
}'
run_hook "$INPUT_READ_DOCS_HTML"
assert_eq 0 "$WSR_RC" "Read on docs/index.html must pass through (docs dir)"

# ---------------------------------------------------------------------------
# Read — config/settings extensions
# ---------------------------------------------------------------------------

INPUT_READ_YML='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/.github/workflows/ci.yml" }
}'
run_hook "$INPUT_READ_YML"
assert_eq 0 "$WSR_RC" "Read on .yml must pass through (config extension)"

INPUT_READ_TOML='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/Cargo.toml" }
}'
run_hook "$INPUT_READ_TOML"
assert_eq 0 "$WSR_RC" "Read on .toml must pass through (config extension)"

INPUT_READ_LOCK='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/package-lock.json" }
}'
run_hook "$INPUT_READ_LOCK"
assert_eq 0 "$WSR_RC" "Read on package-lock.json must pass through (JSON)"

INPUT_READ_ENV='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/.env" }
}'
run_hook "$INPUT_READ_ENV"
assert_eq 0 "$WSR_RC" "Read on .env must pass through (dotfile + config)"

# ---------------------------------------------------------------------------
# Read — source code must still redirect
# ---------------------------------------------------------------------------

INPUT_READ_SRC='{
  "tool_name": "Read",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/src/app.ts" }
}'
run_hook "$INPUT_READ_SRC"
assert_eq 2 "$WSR_RC" "Read on src/app.ts must still redirect to IDE"
assert_contains "$WSR_STDERR" "mcp__webstorm__read_file" "redirect must name read_file"

# ---------------------------------------------------------------------------
# Edit — passthrough on dotfolder (file-existence check is bypassed)
# ---------------------------------------------------------------------------

INPUT_EDIT_CLAUDE='{
  "tool_name": "Edit",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/.claude/settings.json" }
}'
run_hook "$INPUT_EDIT_CLAUDE"
assert_eq 0 "$WSR_RC" "Edit on .claude/settings.json must pass through"

INPUT_EDIT_MD='{
  "tool_name": "Edit",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/CLAUDE.md" }
}'
run_hook "$INPUT_EDIT_MD"
assert_eq 0 "$WSR_RC" "Edit on CLAUDE.md must pass through"

# ---------------------------------------------------------------------------
# Write — passthrough on dotfolder
# ---------------------------------------------------------------------------

INPUT_WRITE_CLAUDE='{
  "tool_name": "Write",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/.claude/hooks/my-hook.sh" }
}'
run_hook "$INPUT_WRITE_CLAUDE"
assert_eq 0 "$WSR_RC" "Write on .claude/ must pass through"

INPUT_WRITE_PKG='{
  "tool_name": "Write",
  "cwd": "/home/proj/my-app",
  "tool_input": { "file_path": "/home/proj/my-app/package.json" }
}'
run_hook "$INPUT_WRITE_PKG"
assert_eq 0 "$WSR_RC" "Write on package.json must pass through"

# ---------------------------------------------------------------------------
# Grep — path parameter to passthrough area
# ---------------------------------------------------------------------------

INPUT_GREP_CLAUDE_PATH='{
  "tool_name": "Grep",
  "cwd": "/home/proj/my-app",
  "tool_input": { "pattern": "hooks", "path": "/home/proj/my-app/.claude" }
}'
run_hook "$INPUT_GREP_CLAUDE_PATH"
assert_eq 0 "$WSR_RC" "Grep scoped to .claude/ must pass through"

INPUT_GREP_DOCS_PATH='{
  "tool_name": "Grep",
  "cwd": "/home/proj/my-app",
  "tool_input": { "pattern": "usage", "path": "/home/proj/my-app/docs" }
}'
run_hook "$INPUT_GREP_DOCS_PATH"
assert_eq 0 "$WSR_RC" "Grep scoped to docs/ must pass through"

# Grep with no path must still redirect (whole-project search)
INPUT_GREP_NO_PATH='{
  "tool_name": "Grep",
  "cwd": "/home/proj/my-app",
  "tool_input": { "pattern": "useState" }
}'
run_hook "$INPUT_GREP_NO_PATH"
assert_eq 2 "$WSR_RC" "Grep with no path must still redirect to IDE"
assert_contains "$WSR_STDERR" "search_regex" "redirect must name search_regex"

# ---------------------------------------------------------------------------
# Glob — path parameter to passthrough area
# ---------------------------------------------------------------------------

INPUT_GLOB_IDEA_PATH='{
  "tool_name": "Glob",
  "cwd": "/home/proj/my-app",
  "tool_input": { "pattern": "**/*.xml", "path": "/home/proj/my-app/.idea" }
}'
run_hook "$INPUT_GLOB_IDEA_PATH"
assert_eq 0 "$WSR_RC" "Glob scoped to .idea/ must pass through"

# Glob with no path must still redirect
INPUT_GLOB_NO_PATH='{
  "tool_name": "Glob",
  "cwd": "/home/proj/my-app",
  "tool_input": { "pattern": "**/*.ts" }
}'
run_hook "$INPUT_GLOB_NO_PATH"
assert_eq 2 "$WSR_RC" "Glob with no path must still redirect to IDE"
assert_contains "$WSR_STDERR" "search_file" "redirect must name search_file"

# ---------------------------------------------------------------------------
# Bash cat — passthrough on dotfolder / markdown
# ---------------------------------------------------------------------------

INPUT_CAT_CLAUDE='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "cat .claude/settings.json" }
}'
run_hook "$INPUT_CAT_CLAUDE"
assert_eq 0 "$WSR_RC" "Bash cat on .claude/ must pass through"

INPUT_CAT_MD='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "cat CLAUDE.md" }
}'
run_hook "$INPUT_CAT_MD"
assert_eq 0 "$WSR_RC" "Bash cat on CLAUDE.md must pass through"

# Bash cat on a source file must still redirect
INPUT_CAT_SRC='{
  "tool_name": "Bash",
  "cwd": "/home/proj/my-app",
  "tool_input": { "command": "cat src/app.ts" }
}'
run_hook "$INPUT_CAT_SRC"
assert_eq 2 "$WSR_RC" "Bash cat on src/app.ts must still redirect"
assert_contains "$WSR_STDERR" "read_file" "redirect must name read_file"
