#!/usr/bin/env bash
# Flow 2: confidence formula — churn_since_validation determines the tier.
#   churn_since_validation in [0, 10]  → high
#   churn_since_validation in (11, 25] → medium
#   churn_since_validation > 25        → low
#
# churn_since_validation is the sum of modified_files.length across all tasks
# since last validation. buffer_append_raw uses 1 modified file per task, so
# churn = task_count in tests (same numeric behavior as the old tsv formula).
#
# Test runs sync-prepare + sync-finalize against synthesized buffers of
# different sizes and asserts the final confidence on the module file.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
SYNC_PREPARE="$PLUGIN/scripts/sync-prepare.sh"
SYNC_FINALIZE="$PLUGIN/scripts/sync-finalize.sh"

run_case() {
  local initial_tsv="$1"
  local task_count="$2"
  local expected_conf="$3"

  # Isolated sub-tmpdir so each case starts clean
  local sub
  sub="$(mktemp -d 2>/dev/null || mktemp -d -t kairoi_conf.XXXXXX)"
  (
    cd "$sub"
    init_git_repo
    setup_kairoi_state "auth" "Auth module" "$initial_tsv"

    local i
    for i in $(seq 1 "$task_count"); do
      buffer_append_raw "task-$i" "SUCCESS" "auth"
    done

    bash "$SYNC_PREPARE" >/dev/null 2>&1
    bash "$SYNC_FINALIZE" --reflected "auth" >/dev/null 2>&1

    # Confidence is derived at read time from churn_since_validation.
    # Nothing is stored — we compute it here exactly like consumers do.
    local actual
    actual="$(jq -r '
      if .purpose == null then "low"
      elif (._meta.churn_since_validation // 0) <= 10 then "high"
      elif (._meta.churn_since_validation // 0) <= 25 then "medium"
      else "low" end
    ' .kairoi/model/auth.json)"

    if [ "$actual" != "$expected_conf" ]; then
      echo "case tsv=$initial_tsv + $task_count tasks:"
      echo "  expected confidence=$expected_conf"
      echo "  actual   confidence=$actual"
      echo "  final churn=$(jq -r '._meta.churn_since_validation' .kairoi/model/auth.json)"
      exit 1
    fi

    # Verify stored confidence is truly absent (no drift risk).
    local stored
    stored="$(jq -r '._meta | has("confidence")' .kairoi/model/auth.json)"
    if [ "$stored" != "false" ]; then
      echo "case tsv=$initial_tsv + $task_count tasks:"
      echo "  _meta.confidence should NOT be persisted (derived at read)"
      exit 1
    fi

    # Verify churn_since_validation is present and correct.
    # buffer_append_raw uses 1 file per task, so churn = initial_tsv + task_count.
    local expected_churn=$(( initial_tsv + task_count ))
    local actual_churn
    actual_churn="$(jq -r '._meta.churn_since_validation // "null"' .kairoi/model/auth.json)"
    if [ "$actual_churn" = "null" ]; then
      echo "case tsv=$initial_tsv + $task_count tasks:"
      echo "  _meta.churn_since_validation missing from model"
      exit 1
    fi
    if [ "$actual_churn" != "$expected_churn" ]; then
      echo "case tsv=$initial_tsv + $task_count tasks:"
      echo "  expected churn=$expected_churn"
      echo "  actual   churn=$actual_churn"
      exit 1
    fi
  )
  local rc=$?
  rm -rf "$sub"
  return $rc
}

# Boundary cases: formula tiers are <=10, <=25, else
run_case 0 5  "high"   || exit 1  # tsv=5, high
run_case 0 10 "high"   || exit 1  # tsv=10, still high
run_case 0 11 "medium" || exit 1  # tsv=11, crosses to medium
run_case 0 25 "medium" || exit 1  # tsv=25, still medium
run_case 0 26 "low"    || exit 1  # tsv=26, crosses to low

# Continuation from an already-stale model
run_case 20 10 "low"   || exit 1  # tsv=30, low

exit 0
