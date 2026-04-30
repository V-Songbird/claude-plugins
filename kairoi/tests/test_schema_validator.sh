#!/usr/bin/env bash
# Schema validator (validate-schema.sh).
# Covers receipt, buffer-entry, reflect-result schemas plus usage errors.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
VALIDATOR="$PLUGIN/scripts/validate-schema.sh"

[ -f "$VALIDATOR" ] || { echo "FAIL: validator missing at $VALIDATOR"; exit 1; }

# run_valid   <name> <schema> <input>
run_valid() {
  local NAME="$1" SCHEMA="$2" INPUT="$3"
  local OUTPUT RC
  OUTPUT="$(echo "$INPUT" | bash "$VALIDATOR" "$SCHEMA" 2>&1)"
  RC=$?
  if [ "$RC" -ne 0 ]; then
    echo "FAIL: $NAME — expected valid, got RC=$RC"
    echo "  input: $INPUT"
    echo "  errors: $OUTPUT"
    return 1
  fi
}

# run_invalid <name> <schema> <input> <expected-substr>
run_invalid() {
  local NAME="$1" SCHEMA="$2" INPUT="$3" EXPECT="$4"
  local OUTPUT RC
  OUTPUT="$(echo "$INPUT" | bash "$VALIDATOR" "$SCHEMA" 2>&1)"
  RC=$?
  if [ "$RC" -eq 0 ]; then
    echo "FAIL: $NAME — expected invalid, got valid"
    echo "  input: $INPUT"
    return 1
  fi
  if ! echo "$OUTPUT" | grep -qF "$EXPECT"; then
    echo "FAIL: $NAME — error output doesn't match"
    echo "  expected substring: $EXPECT"
    echo "  actual:"
    echo "$OUTPUT" | sed 's/^/    /'
    return 1
  fi
}

# run_rc <name> <schema> <input> <expected-rc>
run_rc() {
  local NAME="$1" SCHEMA="$2" INPUT="$3" EXPECT_RC="$4"
  echo "$INPUT" | bash "$VALIDATOR" "$SCHEMA" >/dev/null 2>&1
  local RC=$?
  if [ "$RC" -ne "$EXPECT_RC" ]; then
    echo "FAIL: $NAME — expected RC=$EXPECT_RC, got RC=$RC"
    return 1
  fi
}

# =========================================================================
# Receipt
# =========================================================================

# Valid: minimal required fields
run_valid "receipt/valid-minimal" receipt \
  '{"task_id":"t1","timestamp":"2026-04-17T10:00:00Z","status":"SUCCESS","modules_affected":["auth"],"modified_files":["src/auth/token.ts"],"commit_hash":"abc123","guards_fired":[],"guards_disputed":[],"blocked_diagnostics":null}' \
  || exit 1

# Valid: BLOCKED with test_results + diagnostics
run_valid "receipt/valid-blocked-with-tests" receipt \
  '{"task_id":"t2","timestamp":"2026-04-17T10:00:00Z","status":"BLOCKED","modules_affected":["api"],"modified_files":["b"],"test_results":{"total":5,"passed":3,"failed":2,"skipped":0},"commit_hash":null,"guards_fired":[],"guards_disputed":[],"guards_created":[],"model_updated":[],"edges_updated":[],"blocked_diagnostics":"tests failed: 2/5"}' \
  || exit 1

# Invalid: missing task_id
run_invalid "receipt/missing-task-id" receipt \
  '{"timestamp":"2026-04-17T10:00:00Z","status":"SUCCESS","modules_affected":[],"modified_files":[],"commit_hash":"abc","guards_fired":[],"guards_disputed":[],"blocked_diagnostics":null}' \
  "missing: task_id" || exit 1

# Invalid: empty task_id
run_invalid "receipt/empty-task-id" receipt \
  '{"task_id":"","timestamp":"2026-04-17T10:00:00Z","status":"SUCCESS","modules_affected":[],"modified_files":[],"commit_hash":"abc","guards_fired":[],"guards_disputed":[],"blocked_diagnostics":null}' \
  "task_id must be non-empty" || exit 1

# Invalid: status not SUCCESS or BLOCKED
run_invalid "receipt/bad-status" receipt \
  '{"task_id":"t","timestamp":"2026-04-17T10:00:00Z","status":"WEIRD","modules_affected":[],"modified_files":[],"commit_hash":"abc","guards_fired":[],"guards_disputed":[],"blocked_diagnostics":null}' \
  "status must be SUCCESS or BLOCKED" || exit 1

# Invalid: __PENDING__ placeholder in commit_hash (audit finding regression test)
run_invalid "receipt/__pending__-hash" receipt \
  '{"task_id":"t","timestamp":"2026-04-17T10:00:00Z","status":"SUCCESS","modules_affected":[],"modified_files":[],"commit_hash":"__PENDING__","guards_fired":[],"guards_disputed":[],"blocked_diagnostics":null}' \
  "__PENDING__" || exit 1

# Invalid: modules_affected must be array
run_invalid "receipt/modules-not-array" receipt \
  '{"task_id":"t","timestamp":"2026-04-17T10:00:00Z","status":"SUCCESS","modules_affected":"auth","modified_files":[],"commit_hash":"abc","guards_fired":[],"guards_disputed":[],"blocked_diagnostics":null}' \
  "modules_affected must be array" || exit 1

# Invalid: test_results must be object or null
run_invalid "receipt/test-results-string" receipt \
  '{"task_id":"t","timestamp":"2026-04-17T10:00:00Z","status":"SUCCESS","modules_affected":[],"modified_files":[],"test_results":"skipped","commit_hash":"abc","guards_fired":[],"guards_disputed":[],"blocked_diagnostics":null}' \
  "test_results must be object or null" || exit 1

# =========================================================================
# Buffer entry
# =========================================================================

run_valid "buffer-entry/valid" buffer-entry \
  '{"task_id":"t1","timestamp":"2026-04-17T10:00:00Z","status":"SUCCESS","summary":"fix X","modules_affected":["a"],"modified_files":["f"],"test_results":null,"commit_hash":"abc","guards_fired":[],"guards_disputed":[],"blocked_diagnostics":null}' \
  || exit 1

run_invalid "buffer-entry/missing-commit-hash" buffer-entry \
  '{"task_id":"t","timestamp":"2026-04-17T10:00:00Z","status":"SUCCESS","summary":"s","modules_affected":[],"modified_files":[],"guards_fired":[],"guards_disputed":[]}' \
  "missing: commit_hash" || exit 1

run_invalid "buffer-entry/empty-commit-hash" buffer-entry \
  '{"task_id":"t","timestamp":"2026-04-17T10:00:00Z","status":"SUCCESS","summary":"s","modules_affected":[],"modified_files":[],"commit_hash":"","guards_fired":[],"guards_disputed":[]}' \
  "commit_hash must be non-empty" || exit 1

run_invalid "buffer-entry/missing-summary" buffer-entry \
  '{"task_id":"t","timestamp":"2026-04-17T10:00:00Z","status":"SUCCESS","modules_affected":[],"modified_files":[],"commit_hash":"abc","guards_fired":[],"guards_disputed":[]}' \
  "missing: summary" || exit 1

# =========================================================================
# Reflect-result
# =========================================================================

run_valid "reflect-result/empty-object" reflect-result '{}' || exit 1

run_valid "reflect-result/full" reflect-result \
  '{"guards_created":[{"source_task":"t","check":"verify mutex"}],"semantic_edges":[{"from":"a","to":"b"}]}' \
  || exit 1

run_invalid "reflect-result/guards-created-not-array" reflect-result \
  '{"guards_created":"oops"}' \
  "guards_created must be array" || exit 1

run_invalid "reflect-result/semantic-edges-not-array" reflect-result \
  '{"semantic_edges":42}' \
  "semantic_edges must be array" || exit 1

# =========================================================================
# Usage errors
# =========================================================================

# Invalid JSON → exit 1
run_rc "usage/invalid-json" receipt 'not-json{' 1 || exit 1

# Unknown schema → exit 2
run_rc "usage/unknown-schema" "fake-schema-xyz" '{}' 2 || exit 1

echo "schema validator: all cases passed"
exit 0
