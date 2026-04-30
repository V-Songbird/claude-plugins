#!/usr/bin/env bash
# Flow 13: session-boot CHRONIC block.
# When receipt history is deeper than the 30-task recent window, session-boot
# surfaces long-lived patterns (modules repeatedly BLOCKED, guards chronically
# disputed, test-failure-prone modules). This is B1 — the within-project
# memory-compounding foundation.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
SESSION_BOOT="$PLUGIN/scripts/session-boot.sh"

setup_kairoi_state "parser" "Parser module" 0

# Generate 40 receipts. 4 of them are BLOCKED on "parser" spread across time;
# the "fix-tz-silent-fail" guard is disputed on 6 distinct tasks. That puts
# parser over the 3-blocked threshold and the guard over the 5-disputed
# threshold — both chronic.
RECEIPTS=".kairoi/receipts.jsonl"
: > "$RECEIPTS"

emit_receipt() {
  local task_id="$1"
  local status="$2"
  local ts="$3"
  local disputed_json="${4:-[]}"
  local test_failed="${5:-0}"

  jq -c -n \
    --arg t "$task_id" --arg s "$status" --arg ts "$ts" \
    --argjson d "$disputed_json" --argjson fail "$test_failed" \
    '{
      task_id: $t, timestamp: $ts, status: $s,
      modules_affected: ["parser"], modified_files: ["src/parser/dates.ts"],
      test_results: (if $fail > 0 then {total: 1, passed: 0, failed: $fail, skipped: 0} else null end),
      commit_hash: "abc1234", guards_fired: [], guards_disputed: $d,
      guards_created: [], model_updated: [], edges_updated: [],
      blocked_diagnostics: null
    }' >> "$RECEIPTS"
}

# 36 SUCCESS tasks, spread across the first 36 slots
for i in $(seq 1 36); do
  emit_receipt "task-$i" "SUCCESS" "2026-04-$(printf '%02d' $((i % 28 + 1)))T00:00:00Z"
done

# 4 BLOCKED tasks interspersed
emit_receipt "task-b1" "BLOCKED" "2026-03-15T00:00:00Z"
emit_receipt "task-b2" "BLOCKED" "2026-03-20T00:00:00Z"
emit_receipt "task-b3" "BLOCKED" "2026-04-01T00:00:00Z"
emit_receipt "task-b4" "BLOCKED" "2026-04-10T00:00:00Z"

# Add 6 receipts that dispute the same guard source_task
for i in 1 2 3 4 5 6; do
  emit_receipt "disputed-$i" "SUCCESS" "2026-04-$(printf '%02d' $i)T12:00:00Z" '["fix-tz-silent-fail"]'
done

# Add 3 receipts with test failures on the same module
for i in 1 2 3; do
  emit_receipt "testfail-$i" "SUCCESS" "2026-04-$(printf '%02d' $((10 + i)))T06:00:00Z" '[]' 2
done

RC="$(wc -l < "$RECEIPTS" | tr -d ' ')"
if [ "$RC" -le 30 ]; then
  echo "fixture setup error: expected >30 receipts, got $RC"
  exit 1
fi

CWD="$(pwd)"
INPUT="$(jq -n --arg cwd "$CWD" '{cwd: $cwd}')"

# CHRONIC / DIAGNOSTICS / UNRESOLVED live behind KAIROI_VERBOSE=1.
# Default session-boot output is a one-line banner — this test is specifically
# verifying the verbose analytic block, so we opt in.
OUT="$(echo "$INPUT" | KAIROI_VERBOSE=1 bash "$SESSION_BOOT" 2>&1)"

# ---- CHRONIC block must appear ----
if ! echo "$OUT" | grep -qF "CHRONIC"; then
  echo "CHRONIC section missing from session-boot output"
  echo "full output:"
  echo "$OUT" | sed 's/^/  /'
  exit 1
fi

# ---- repeat-blocked parser ----
if ! echo "$OUT" | grep -qE "repeat-blocked.*parser×4"; then
  echo "CHRONIC did not surface parser as repeat-blocked"
  echo "$OUT" | sed 's/^/  /'
  exit 1
fi

# ---- chronically disputed guard ----
if ! echo "$OUT" | grep -qE "chronically disputed.*fix-tz-silent-fail×6"; then
  echo "CHRONIC did not surface fix-tz-silent-fail as chronically disputed"
  echo "$OUT" | sed 's/^/  /'
  exit 1
fi

# ---- test-failure-prone modules ----
if ! echo "$OUT" | grep -qE "test-failure-prone.*parser×3"; then
  echo "CHRONIC did not surface parser as test-failure-prone"
  echo "$OUT" | sed 's/^/  /'
  exit 1
fi

# ---- When history is <= 30 receipts, CHRONIC must NOT appear ----
# (regression check: the section is gated on RC > 30 to avoid duplicating DIAGNOSTICS)
: > "$RECEIPTS"
for i in 1 2 3 4 5; do
  emit_receipt "t-$i" "SUCCESS" "2026-04-01T0$i:00:00Z"
done

OUT_SMALL="$(echo "$INPUT" | KAIROI_VERBOSE=1 bash "$SESSION_BOOT" 2>&1)"
if echo "$OUT_SMALL" | grep -qF "CHRONIC"; then
  echo "CHRONIC should not appear when receipts count <= 30"
  echo "$OUT_SMALL" | sed 's/^/  /'
  exit 1
fi

exit 0
