#!/usr/bin/env bash
# Flow 3: every buffered task produces exactly one receipt after sync-finalize.
# Buffer is cleared (no _deferred entries when all modules reflected).

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
SYNC_PREPARE="$PLUGIN/scripts/sync-prepare.sh"
SYNC_FINALIZE="$PLUGIN/scripts/sync-finalize.sh"

init_git_repo
setup_kairoi_state "auth" "Auth module" 0

for i in 1 2 3; do
  buffer_append_raw "task-$i" "SUCCESS" "auth"
done

bash "$SYNC_PREPARE" >/dev/null 2>&1
bash "$SYNC_FINALIZE" --reflected "auth" >/dev/null 2>&1

# Three receipts, one per buffered task
assert_line_count ".kairoi/receipts.jsonl" 3 || exit 1

for i in 1 2 3; do
  if ! grep -qF "\"task-$i\"" .kairoi/receipts.jsonl; then
    echo "receipt for task-$i missing"
    sed 's/^/  /' .kairoi/receipts.jsonl
    exit 1
  fi
done

# Buffer cleared
assert_empty_or_missing ".kairoi/buffer.jsonl" || exit 1

# Each receipt has the required fields
FIRST="$(head -1 .kairoi/receipts.jsonl)"
for field in task_id timestamp status modules_affected commit_hash guards_fired guards_disputed; do
  if ! echo "$FIRST" | jq -e ".$field" >/dev/null 2>&1; then
    echo "receipt missing required field: $field"
    echo "first receipt: $FIRST"
    exit 1
  fi
done

exit 0
