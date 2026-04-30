#!/usr/bin/env bash
# Flow 4: .guard-disputes contents are captured into buffer entries as
# guards_disputed, then the log is cleared. This is the mechanical half of the
# dispute pipeline — the disputed++ counter bump happens during reflection
# (agent-driven) and is not tested here.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
BUFFER_APPEND="$PLUGIN/scripts/buffer-append.sh"

init_git_repo
setup_kairoi_state "auth" "Auth module" 0
add_guard "auth" "fix-token-race" "Verify mutex lock" "src/auth/token.ts"

# Simulate the agent disputing the guard during work
echo "fix-token-race" > .kairoi/.guard-disputes

commit_file "src/auth/token.ts" "// changed" "fix(auth): change [State: BUFFERED]"

bash "$BUFFER_APPEND" \
  --task "some-task" \
  --status "SUCCESS" \
  --summary "work" \
  --skip-tests >/dev/null

# guards_disputed in buffer entry contains the source_task
assert_jq ".kairoi/buffer.jsonl" '.guards_disputed[0]' "fix-token-race" || exit 1

# .guard-disputes cleared
assert_empty_or_missing ".kairoi/.guard-disputes" || exit 1

# Also verify: multiple disputes dedupe
echo "fix-token-race" > .kairoi/.guard-disputes
echo "fix-token-race" >> .kairoi/.guard-disputes
echo "other-task" >> .kairoi/.guard-disputes

commit_file "src/auth/token.ts" "// changed2" "fix(auth): change2 [State: BUFFERED]"

bash "$BUFFER_APPEND" \
  --task "other-task" \
  --status "SUCCESS" \
  --summary "work2" \
  --skip-tests >/dev/null

# Second buffer entry should have both disputed IDs (deduped)
SECOND_LINE="$(tail -1 .kairoi/buffer.jsonl)"
COUNT="$(echo "$SECOND_LINE" | jq '.guards_disputed | length')"
if [ "$COUNT" != "2" ]; then
  echo "expected 2 deduped disputes, got $COUNT"
  echo "entry: $SECOND_LINE"
  exit 1
fi

exit 0
