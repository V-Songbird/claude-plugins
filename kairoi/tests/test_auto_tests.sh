#!/usr/bin/env bash
# Test-result auto-capture driven by build-adapter.json.
# Tests auto-run on every commit if `.test` is configured in
# build-adapter.json; otherwise test_results is null. No user flag
# required.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
AUTO_BUFFER="$PLUGIN/scripts/auto-buffer.sh"

init_git_repo
setup_kairoi_state "auth" "Auth module" 0

CWD="$(pwd)"
INPUT="$(jq -n --arg cwd "$CWD" '{cwd: $cwd, tool_name: "Bash", tool_input: {command: "git commit -m feat"}}')"

# --- Case 1: build-adapter.json has no .test configured → test_results null ---
# setup_kairoi_state writes a build-adapter.json without `.test`, so this
# is the default state.
commit_file "src/auth/token.ts" "// token" "feat(auth): add token"

echo "$INPUT" | CLAUDE_PLUGIN_ROOT="$PLUGIN" bash "$AUTO_BUFFER"

assert_line_count ".kairoi/buffer.jsonl" 1 || exit 1

TR_UNSET="$(jq -c '.test_results' .kairoi/buffer.jsonl)"
if [ "$TR_UNSET" != "null" ]; then
  echo "expected test_results=null when build-adapter.json.test is unset"
  echo "got: $TR_UNSET"
  exit 1
fi

# --- Case 2: build-adapter.json.test set → test_results populated ---
# Install a deterministic fake test command. The output must contain
# "N passed", "M failed", "K skipped" for buffer-append's parser.
FAKE_OUTPUT="Running fake tests... 3 passed, 2 failed, 1 skipped"
FAKE_EXIT=1
jq --arg cmd "echo '$FAKE_OUTPUT'; exit $FAKE_EXIT" \
   '.test = $cmd' \
   .kairoi/build-adapter.json > /tmp/ba.json && mv /tmp/ba.json .kairoi/build-adapter.json

# Reset buffer and make another commit so auto-buffer has something new.
: > .kairoi/buffer.jsonl
commit_file "src/auth/helper.ts" "// helper" "feat(auth): add helper"

echo "$INPUT" | CLAUDE_PLUGIN_ROOT="$PLUGIN" bash "$AUTO_BUFFER"

assert_line_count ".kairoi/buffer.jsonl" 1 || exit 1

TR_SET="$(jq -c '.test_results' .kairoi/buffer.jsonl)"
if [ "$TR_SET" = "null" ]; then
  echo "expected test_results to be populated when build-adapter.json.test is set"
  echo "full buffer entry:"
  jq . .kairoi/buffer.jsonl
  exit 1
fi

assert_jq ".kairoi/buffer.jsonl" '.test_results.passed' "3" || exit 1
assert_jq ".kairoi/buffer.jsonl" '.test_results.failed' "2" || exit 1
assert_jq ".kairoi/buffer.jsonl" '.test_results.skipped' "1" || exit 1
assert_jq ".kairoi/buffer.jsonl" '.test_results.total' "6" || exit 1

exit 0
