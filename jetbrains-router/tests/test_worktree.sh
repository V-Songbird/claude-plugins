#!/usr/bin/env bash
# Worktree guard: when cwd is a linked git worktree (not the main checkout),
# the hook fails open — WebStorm's open project is almost certainly the main
# checkout, so routed project-relative paths would miss. Tests are skipped
# cleanly if `git` or `git worktree` isn't available.

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

if ! command -v git >/dev/null 2>&1; then
  echo "SKIP: git not installed"
  exit 0
fi

# run.sh cd's us into a fresh $TMP_DIR before running. Build a real repo +
# linked worktree under $PWD; run.sh cleans the whole tmpdir.
MAIN="$PWD/main"
WT="$PWD/wt"
mkdir -p "$MAIN"

(
  cd "$MAIN" || exit 1
  git init -q
  git config user.email test@test
  git config user.name test
  git commit -q --allow-empty -m init
) || { echo "SKIP: git init failed"; exit 0; }

(cd "$MAIN" && git worktree add -q "$WT" HEAD -b wt-feat) \
  || { echo "SKIP: git worktree add failed"; exit 0; }

# --- Main checkout cwd → redirect still fires ----------------------------
# Use a source file (.ts) so the worktree guard is what's under test,
# not the file-type passthrough (README.md / *.md bypass the hook by design).
INPUT_MAIN="{
  \"tool_name\": \"Read\",
  \"cwd\": \"$MAIN\",
  \"tool_input\": { \"file_path\": \"$MAIN/src/app.ts\" }
}"
run_hook "$INPUT_MAIN"
assert_eq 2 "$WSR_RC" "main checkout cwd must still redirect"
assert_contains "$WSR_STDERR" "mcp__webstorm__read_file" "main-checkout redirect names read_file"

# --- Linked worktree cwd → fail open -------------------------------------
INPUT_WT="{
  \"tool_name\": \"Read\",
  \"cwd\": \"$WT\",
  \"tool_input\": { \"file_path\": \"$WT/src/app.ts\" }
}"
run_hook "$INPUT_WT"
assert_eq 0 "$WSR_RC" "linked worktree cwd must fail open (IDE likely has main open)"
assert_not_contains "$WSR_STDERR" "mcp__webstorm__" "no redirect message in worktree"

# --- Worktree cwd also fails open for Bash redirects ---------------------
INPUT_WT_BASH="{
  \"tool_name\": \"Bash\",
  \"cwd\": \"$WT\",
  \"tool_input\": { \"command\": \"cat src/app.ts\" }
}"
run_hook "$INPUT_WT_BASH"
assert_eq 0 "$WSR_RC" "worktree must fail open for Bash too — guard runs before the dispatch"

# --- Non-git cwd is unaffected (guard is silent on non-repo paths) -------
# Use a tmp path that's provably not git-tracked.
NONGIT="$PWD/not-a-repo"
mkdir -p "$NONGIT"
INPUT_NONGIT="{
  \"tool_name\": \"Read\",
  \"cwd\": \"$NONGIT\",
  \"tool_input\": { \"file_path\": \"$NONGIT/src/app.ts\" }
}"
run_hook "$INPUT_NONGIT"
assert_eq 2 "$WSR_RC" "non-git cwd must still redirect — guard only triggers on linked worktrees"

# --- Subdirectory of main checkout → still redirects ---------------------
# Regression guard for commit 84257b8: a subdir cwd in the main checkout
# used to be misclassified as a worktree because git's --git-dir returns
# absolute and --git-common-dir returns relative when invoked from a
# subdirectory. Anchoring both rev-parse calls to --show-toplevel made the
# comparison consistent. Without that fix, this test would fail-open.
MAIN_SUBDIR="$MAIN/src"
mkdir -p "$MAIN_SUBDIR"
INPUT_MAIN_SUBDIR="{
  \"tool_name\": \"Read\",
  \"cwd\": \"$MAIN_SUBDIR\",
  \"tool_input\": { \"file_path\": \"$MAIN_SUBDIR/app.ts\" }
}"
run_hook "$INPUT_MAIN_SUBDIR"
assert_eq 2 "$WSR_RC" "main-checkout subdirectory cwd must still redirect (regression: 84257b8)"
assert_contains "$WSR_STDERR" "mcp__webstorm__read_file" "main-subdir redirect names read_file"

# --- Subdirectory of linked worktree → still fails open ------------------
# Symmetrical regression guard: a subdir cwd inside a linked worktree must
# resolve to the same worktree-vs-main decision as the worktree root.
WT_SUBDIR="$WT/src"
mkdir -p "$WT_SUBDIR"
INPUT_WT_SUBDIR="{
  \"tool_name\": \"Read\",
  \"cwd\": \"$WT_SUBDIR\",
  \"tool_input\": { \"file_path\": \"$WT_SUBDIR/app.ts\" }
}"
run_hook "$INPUT_WT_SUBDIR"
assert_eq 0 "$WSR_RC" "worktree subdirectory cwd must fail open (same as worktree root)"
assert_not_contains "$WSR_STDERR" "mcp__webstorm__" "no redirect from worktree subdir"
