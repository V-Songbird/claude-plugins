#!/usr/bin/env bash
set -euo pipefail

# kairoi buffer-append: serialize a task entry to buffer.jsonl.
# Derives modified_files from HEAD commit, maps files to modules via
# _index.json, captures guards_fired from .guards-log, captures
# guards_disputed from .guard-disputes, auto-runs tests from
# build-adapter.json when --tests is omitted. Handles all JSON.
#
# Usage:
#   buffer-append.sh --task <id> --status <SUCCESS|BLOCKED> --summary "<text>"
#                    [--tests <total,passed,failed,skipped>]
#                    [--skip-tests]
#                    [--blocked-diag "<text>"]
#
# Must be called AFTER any git commit. Reads HEAD for hash and modified
# files.
#
# Test behavior:
#   --tests <csv>     Use provided test results (override auto-run)
#   --skip-tests      Skip test execution entirely (tests = null)
#   (neither)         Auto-run tests from build-adapter.json test command
#
# Guard disputes:
#   If .kairoi/.guard-disputes exists, its contents (source_task IDs, one
#   per line) are captured as guards_disputed. Written by the agent when
#   a fired guard was deemed irrelevant. Same pattern as .guards-log.

command -v jq &>/dev/null || { echo "kairoi: jq required" >&2; exit 1; }

# Debug mode
_DEVNULL="/dev/null"
if [ "${KAIROI_DEBUG:-}" = "1" ]; then
  _DEVNULL="/dev/stderr"
  echo "kairoi-debug: buffer-append starting" >&2
fi

# --- Parse arguments ---
TASK_ID=""
STATUS="SUCCESS"
SUMMARY=""
TESTS=""
SKIP_TESTS=false
BLOCKED_DIAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task)         TASK_ID="$2"; shift 2 ;;
    --status)       STATUS="$2"; shift 2 ;;
    --summary)      SUMMARY="$2"; shift 2 ;;
    --tests)        TESTS="$2"; shift 2 ;;
    --skip-tests)   SKIP_TESTS=true; shift ;;
    --blocked-diag) BLOCKED_DIAG="$2"; shift 2 ;;
    *) echo "kairoi buffer-append: unknown arg $1" >&2; exit 1 ;;
  esac
done

if [ -z "$TASK_ID" ] || [ -z "$SUMMARY" ]; then
  echo "kairoi buffer-append: --task and --summary are required" >&2
  exit 1
fi

# --- Derive context ---
STATE_DIR=".kairoi"
[ -f "$STATE_DIR/model/_index.json" ] || { echo "kairoi: no _index.json" >&2; exit 1; }

# Commit hash from HEAD
COMMIT_HASH="$(git rev-parse HEAD 2>"$_DEVNULL" || echo "")"

# Modified files from the HEAD commit. --root handles the initial commit case,
# where HEAD has no parent — without it, diff-tree returns nothing and
# modules_affected/modified_files are silently empty.
MODIFIED_FILES="$(git diff-tree --no-commit-id --name-only -r --root HEAD 2>"$_DEVNULL" || true)"

# Map modified files to modules. tr -d '\r' guards against Windows git-bash
# adding CR to jq output that would corrupt the module keys downstream.
MODULES_AFFECTED="$(echo "$MODIFIED_FILES" | while IFS= read -r FILE; do
  FILE="${FILE%$'\r'}"
  [ -n "$FILE" ] || continue
  jq -r --arg f "$FILE" '
    .modules | to_entries[] |
    select(.value.source_paths[] as $sp | $f | startswith($sp)) |
    .key
  ' "$STATE_DIR/model/_index.json" 2>"$_DEVNULL" | tr -d '\r'
done | sort -u)"

# Convert to JSON arrays
FILES_JSON="$(echo "$MODIFIED_FILES" | jq -R -s 'split("\n") | map(select(length > 0))')"
MODULES_JSON="$(echo "$MODULES_AFFECTED" | jq -R -s 'split("\n") | map(select(length > 0))')"

# --- Test results ---
TESTS_JSON="null"
if [ -n "$TESTS" ]; then
  # Explicit --tests provided: use as-is
  IFS=',' read -r T_TOTAL T_PASSED T_FAILED T_SKIPPED <<< "$TESTS"
  TESTS_JSON="{\"total\":${T_TOTAL:-0},\"passed\":${T_PASSED:-0},\"failed\":${T_FAILED:-0},\"skipped\":${T_SKIPPED:-0}}"
elif [ "$SKIP_TESTS" = false ]; then
  # Auto-run tests from build-adapter.json
  TEST_CMD="$(jq -r '.test // empty' "$STATE_DIR/build-adapter.json" 2>"$_DEVNULL" || true)"
  if [ -n "$TEST_CMD" ]; then
    echo "kairoi: auto-running tests — $TEST_CMD"
    TEST_OUTPUT=""
    TEST_EXIT=0
    TEST_OUTPUT="$(eval "$TEST_CMD" 2>&1)" || TEST_EXIT=$?

    # Parse test counts from common framework output formats
    T_PASSED="$(echo "$TEST_OUTPUT" | grep -oiE '[0-9]+ passed' | tail -1 | grep -oE '[0-9]+')" || T_PASSED=0
    T_FAILED="$(echo "$TEST_OUTPUT" | grep -oiE '[0-9]+ failed' | tail -1 | grep -oE '[0-9]+')" || T_FAILED=0
    T_SKIPPED="$(echo "$TEST_OUTPUT" | grep -oiE '[0-9]+ (skipped|pending|todo)' | tail -1 | grep -oE '[0-9]+')" || T_SKIPPED=0
    T_TOTAL=$((T_PASSED + T_FAILED + T_SKIPPED))

    # If parsing found nothing but tests ran, use exit code
    if [ "$T_TOTAL" -eq 0 ]; then
      if [ "$TEST_EXIT" -eq 0 ]; then
        TESTS_JSON="{\"total\":0,\"passed\":0,\"failed\":0,\"skipped\":0,\"raw_exit\":0,\"parse_note\":\"tests passed but output format not recognized\"}"
      else
        TESTS_JSON="{\"total\":1,\"passed\":0,\"failed\":1,\"skipped\":0,\"raw_exit\":$TEST_EXIT,\"parse_note\":\"tests failed but output format not recognized\"}"
      fi
    else
      TESTS_JSON="{\"total\":$T_TOTAL,\"passed\":$T_PASSED,\"failed\":$T_FAILED,\"skipped\":$T_SKIPPED,\"raw_exit\":$TEST_EXIT}"
    fi
  fi
fi

# --- Guards fired — read and clear the log ---
GUARDS_FIRED_JSON="[]"
if [ -f "$STATE_DIR/.guards-log" ]; then
  GUARDS_FIRED_JSON="$(sort -u "$STATE_DIR/.guards-log" | jq -R -s 'split("\n") | map(select(length > 0))')"
  > "$STATE_DIR/.guards-log"
fi

# --- Guards disputed — read and clear ---
GUARDS_DISPUTED_JSON="[]"
if [ -f "$STATE_DIR/.guard-disputes" ]; then
  GUARDS_DISPUTED_JSON="$(sort -u "$STATE_DIR/.guard-disputes" | jq -R -s 'split("\n") | map(select(length > 0))')"
  > "$STATE_DIR/.guard-disputes"
fi

# --- Auto-promote SUCCESS → BLOCKED on mechanical signals ---
# Three observable signals can promote the entry without trusting the agent's
# self-report (the user pointed out we cannot rely on the agent to declare its
# own stuck-ness — Claude defaults to optimism and workarounds):
#   1. Test failures: test_results.failed > 0 or non-zero raw_exit
#   2. Test-disablement detected in this commit's diff (new @Ignore /
#      @Disabled / .skip / xit / @pytest.mark.skip / @unittest.skip lines)
#   3. Revert commit (subject begins with "Revert ")
# An explicit `--status BLOCKED` already passed in stays BLOCKED; we only
# upgrade SUCCESS, never downgrade.
if [ "$STATUS" = "SUCCESS" ]; then
  PROMOTE_REASON=""

  # Signal 1: test failures
  if [ "$TESTS_JSON" != "null" ]; then
    T_F_PROMOTE="$(echo "$TESTS_JSON" | jq -r '.failed // 0' 2>"$_DEVNULL" || echo 0)"
    T_RAW_PROMOTE="$(echo "$TESTS_JSON" | jq -r '.raw_exit // 0' 2>"$_DEVNULL" || echo 0)"
    T_T_PROMOTE="$(echo "$TESTS_JSON" | jq -r '.total // 0' 2>"$_DEVNULL" || echo 0)"
    if [ "${T_F_PROMOTE:-0}" -gt 0 ] 2>/dev/null || [ "${T_RAW_PROMOTE:-0}" -ne 0 ] 2>/dev/null; then
      PROMOTE_REASON="tests failing: $T_F_PROMOTE of $T_T_PROMOTE failed (raw_exit=$T_RAW_PROMOTE)"
    fi
  fi

  # Signal 2: test-disablement in the diff. Scan only added lines (^\+) so
  # pre-existing skips and removed skips don't count. The pattern set covers
  # the major test frameworks across stacks kairoi targets — JVM (@Ignore /
  # @Disabled), JS (xit / xdescribe / .skip / .only), Python (@pytest.mark.skip,
  # @unittest.skip / skipIf / skipUnless). Lint suppressors (// @ts-ignore,
  # # noqa, # type: ignore) are excluded — they're sometimes legitimate.
  if [ -z "$PROMOTE_REASON" ] && [ -n "$COMMIT_HASH" ]; then
    DISABLED_HITS="$(git diff-tree --no-commit-id -p --root HEAD 2>"$_DEVNULL" \
      | grep -E '^\+' \
      | grep -cE '@(Ignore|Disabled)\b|@pytest\.mark\.skip|@unittest\.(skip|skipIf|skipUnless)|\bxit\(|\bxdescribe\(|(it|describe|test)\.(skip|only)\(' \
      2>"$_DEVNULL" || echo 0)"
    if [ "${DISABLED_HITS:-0}" -gt 0 ] 2>/dev/null; then
      PROMOTE_REASON="test-disablement detected: $DISABLED_HITS new skip/ignore annotation(s) in diff — silencing tests instead of fixing them is a BLOCKED signal"
    fi
  fi

  # Signal 3: revert commit. git's default subject for `git revert` starts
  # with `Revert "...`. A revert is the agent rolling back prior work — by
  # definition something didn't land cleanly.
  if [ -z "$PROMOTE_REASON" ] && [ -n "$COMMIT_HASH" ]; then
    COMMIT_SUBJECT="$(git log -1 --pretty=%s 2>"$_DEVNULL" || echo "")"
    case "$COMMIT_SUBJECT" in
      Revert\ *|revert\ *)
        PROMOTE_REASON="revert commit — prior work was rolled back: $COMMIT_SUBJECT"
        ;;
    esac
  fi

  if [ -n "$PROMOTE_REASON" ]; then
    STATUS="BLOCKED"
    if [ -z "$BLOCKED_DIAG" ]; then
      BLOCKED_DIAG="$PROMOTE_REASON"
    fi
  fi
fi

# Blocked diagnostics
BLOCKED_JSON="null"
if [ -n "$BLOCKED_DIAG" ]; then
  BLOCKED_JSON="$(echo "$BLOCKED_DIAG" | jq -R -s '.')"
fi

# Timestamp. Format invariant: this must stay exactly `%Y-%m-%dT%H:%M:%SZ`
# (no fractional seconds, no numeric offset) because `session-boot.sh`
# consumes it via jq's `fromdateiso8601`, which only accepts the ISO
# profile `YYYY-MM-DDTHH:MM:SSZ`. If this format changes, the C2
# staleness detection in session-boot.sh silently falls back to "no
# staleness" via its `|| echo 0` fallback — no error, just broken logic.
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# --- Write buffer entry (validated) ---
# Build the entry, validate it against the buffer-entry schema BEFORE
# appending — this is the same gate sync-finalize uses for receipts. Without
# it, a malformed entry (missing field, bad type, __PENDING__ commit_hash)
# silently lands in buffer.jsonl and breaks sync-prepare's aggregation
# downstream.
ENTRY="$(jq -n -c \
  --arg task_id "$TASK_ID" \
  --arg timestamp "$TIMESTAMP" \
  --arg status "$STATUS" \
  --arg summary "$SUMMARY" \
  --arg commit_hash "$COMMIT_HASH" \
  --argjson modules_affected "$MODULES_JSON" \
  --argjson modified_files "$FILES_JSON" \
  --argjson test_results "$TESTS_JSON" \
  --argjson guards_fired "$GUARDS_FIRED_JSON" \
  --argjson guards_disputed "$GUARDS_DISPUTED_JSON" \
  --argjson blocked_diagnostics "$BLOCKED_JSON" \
  '{
    task_id: $task_id,
    timestamp: $timestamp,
    status: $status,
    summary: $summary,
    modules_affected: $modules_affected,
    modified_files: $modified_files,
    test_results: $test_results,
    commit_hash: $commit_hash,
    guards_fired: $guards_fired,
    guards_disputed: $guards_disputed,
    blocked_diagnostics: $blocked_diagnostics
  }')"

# Resolve plugin root for the validator (handles direct CLI invocation too).
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
VALIDATOR="$PLUGIN_ROOT/scripts/validate-schema.sh"
if [ -f "$VALIDATOR" ]; then
  if ! printf '%s' "$ENTRY" | bash "$VALIDATOR" buffer-entry >&2; then
    echo "kairoi: buffer entry rejected by schema validator — refusing to append" >&2
    exit 1
  fi
fi

printf '%s\n' "$ENTRY" >> "$STATE_DIR/buffer.jsonl"

# Test failure alert — data first, notification second
if [ "$TESTS_JSON" != "null" ]; then
  T_F_CHECK="$(echo "$TESTS_JSON" | jq '.failed // 0')"
  T_T_CHECK="$(echo "$TESTS_JSON" | jq '.total // 0')"
  if [ "$T_F_CHECK" -gt 0 ]; then
    echo "kairoi: ⚠ TESTS FAILING — $T_F_CHECK of $T_T_CHECK tests broke after commit ${COMMIT_HASH:0:7}. Fix before continuing."
  fi
fi

FIRED_COUNT="$(echo "$GUARDS_FIRED_JSON" | jq 'length')"
DISPUTED_COUNT="$(echo "$GUARDS_DISPUTED_JSON" | jq 'length')"
TEST_SUMMARY=""
if [ "$TESTS_JSON" != "null" ]; then
  T_P="$(echo "$TESTS_JSON" | jq '.passed // 0')"
  T_F="$(echo "$TESTS_JSON" | jq '.failed // 0')"
  TEST_SUMMARY=" — tests: ${T_P}✓ ${T_F}✗"
fi

echo "kairoi: buffered $TASK_ID [$STATUS] — $(echo "$MODULES_JSON" | jq -r 'join(", ")') — ${FIRED_COUNT} guard(s) fired, ${DISPUTED_COUNT} disputed${TEST_SUMMARY}"
