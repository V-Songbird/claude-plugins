#!/usr/bin/env bash
# BLOCKED reclassification logic.
# Verifies sync-finalize.sh's receipt-emission jq correctly reclassifies
# buffer entries as BLOCKED based on test_results.failed (primary,
# mechanical) and a commit-message keyword heuristic (secondary). Also
# verifies false-positive rejection via the [^A-Za-z] flankers (no
# "unbroken" → BLOCKED, no "wipro" → BLOCKED).
#
# Testing approach: the reclassification jq is duplicated here from
# sync-finalize.sh's receipt-emission loop and fed fixture task entries.
# This tests the LOGIC in isolation.
#
# IF YOU CHANGE THE JQ IN sync-finalize.sh: keep this file in sync.

set -u
. "$KAIROI_TEST_HELPERS"

# Keep this jq exactly in sync with sync-finalize.sh's receipt-emission block.
RECLASSIFY='. as $t | (
  if (($t.test_results // {}) | (if type == "object" then (.failed // 0) else 0 end)) > 0 then
    { status: "BLOCKED",
      reason: "tests failed: \(($t.test_results.failed // 0))/\(($t.test_results.total // 0))" }
  elif (($t.summary // "") | test("(^|[^A-Za-z])(WIP|broken|stuck|giving up|gave up)([^A-Za-z]|$)"; "i")) then
    { status: "BLOCKED",
      reason: "commit-message blocker keyword in: \"\($t.summary // "")\"" }
  else
    { status: ($t.status // "SUCCESS"), reason: null }
  end
)'

# run_case <name> <input-json> <expected-status> [<reason-contains>]
# Asserts output status and optionally that reason contains a substring.
run_case() {
  local NAME="$1"
  local INPUT="$2"
  local EXPECTED_STATUS="$3"
  local EXPECTED_REASON_MATCH="${4:-}"

  local OUT
  OUT="$(echo "$INPUT" | jq -c "$RECLASSIFY" 2>&1)"
  local RC=$?
  if [ "$RC" -ne 0 ]; then
    echo "FAIL: $NAME — jq errored (rc=$RC)"
    echo "  input:  $INPUT"
    echo "  output: $OUT"
    return 1
  fi

  local STATUS
  STATUS="$(echo "$OUT" | jq -r '.status')"
  if [ "$STATUS" != "$EXPECTED_STATUS" ]; then
    echo "FAIL: $NAME — expected status=$EXPECTED_STATUS, got $STATUS"
    echo "  input:  $INPUT"
    echo "  output: $OUT"
    return 1
  fi

  if [ -n "$EXPECTED_REASON_MATCH" ]; then
    local REASON
    REASON="$(echo "$OUT" | jq -r '.reason // "null"')"
    if ! echo "$REASON" | grep -qF "$EXPECTED_REASON_MATCH"; then
      echo "FAIL: $NAME — reason doesn't contain expected substring"
      echo "  expected substring: $EXPECTED_REASON_MATCH"
      echo "  actual reason:      $REASON"
      return 1
    fi
  fi

  return 0
}

# --- Primary (mechanical): test_results.failed > 0 → BLOCKED with reason ---
run_case "test_failure_primary" \
  '{"task_id":"t1","status":"SUCCESS","summary":"fix date parser","test_results":{"total":10,"passed":8,"failed":2,"skipped":0}}' \
  "BLOCKED" "tests failed: 2/10" || exit 1

# --- Secondary (heuristic): commit-message keywords → BLOCKED ---
run_case "keyword_WIP" \
  '{"task_id":"t2","status":"SUCCESS","summary":"WIP refactor auth","test_results":null}' \
  "BLOCKED" "WIP refactor auth" || exit 1

run_case "keyword_gave_up" \
  '{"task_id":"t3","status":"SUCCESS","summary":"gave up on X","test_results":null}' \
  "BLOCKED" "gave up on X" || exit 1

run_case "keyword_broken" \
  '{"task_id":"t4","status":"SUCCESS","summary":"fix broken lock","test_results":null}' \
  "BLOCKED" "fix broken lock" || exit 1

run_case "keyword_stuck" \
  '{"task_id":"t5","status":"SUCCESS","summary":"stuck on deploy","test_results":null}' \
  "BLOCKED" "stuck on deploy" || exit 1

run_case "keyword_giving_up" \
  '{"task_id":"t6","status":"SUCCESS","summary":"giving up on refactor","test_results":null}' \
  "BLOCKED" "giving up on refactor" || exit 1

# --- False-positive rejection via [^A-Za-z] flankers ---
run_case "no_match_unbroken" \
  '{"task_id":"t7","status":"SUCCESS","summary":"restore unbroken state","test_results":null}' \
  "SUCCESS" "" || exit 1

run_case "no_match_wipro" \
  '{"task_id":"t8","status":"SUCCESS","summary":"bump WIPRO library version","test_results":null}' \
  "SUCCESS" "" || exit 1

# --- Clean commits → SUCCESS ---
run_case "clean_feat" \
  '{"task_id":"t9","status":"SUCCESS","summary":"feat(x): add new thing","test_results":null}' \
  "SUCCESS" "" || exit 1

# --- Defensive paths ---
# Missing test_results and summary → preserve input status.
run_case "empty_fields_preserves_status" \
  '{"task_id":"t10","status":"SUCCESS"}' \
  "SUCCESS" "" || exit 1

# Non-object test_results (would crash without the type-check guard).
run_case "test_results_non_object_string" \
  '{"task_id":"t11","status":"SUCCESS","summary":"fix x","test_results":"skipped"}' \
  "SUCCESS" "" || exit 1

# Pre-set BLOCKED status is preserved if no reclassification triggered.
run_case "preserve_preset_blocked" \
  '{"task_id":"t12","status":"BLOCKED","summary":"fix x","test_results":null}' \
  "BLOCKED" "" || exit 1

# Test-failure takes precedence over keyword match (primary over secondary).
run_case "test_failure_wins_over_keyword" \
  '{"task_id":"t13","status":"SUCCESS","summary":"fix broken auth","test_results":{"total":5,"passed":3,"failed":2,"skipped":0}}' \
  "BLOCKED" "tests failed: 2/5" || exit 1

echo "C3 BLOCKED reclassification: 13/13 cases passed"
exit 0
