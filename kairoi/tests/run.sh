#!/usr/bin/env bash
# kairoi test runner. Discovers test_*.sh files in this directory, runs each
# in an isolated tmpdir, reports pass/fail tally. No external test framework.
#
# Usage: bash kairoi/tests/run.sh
# Exit code: 0 if all pass, 1 if any fail.

set -u

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$TESTS_DIR/.." && pwd)"

export KAIROI_TEST_PLUGIN_ROOT="$PLUGIN_ROOT"
export KAIROI_TEST_HELPERS="$TESTS_DIR/helpers.sh"

PASS=0
FAIL=0
FAILED_TESTS=()

echo "kairoi tests (plugin: $PLUGIN_ROOT)"
echo ""

for TEST_FILE in "$TESTS_DIR"/test_*.sh; do
  [ -f "$TEST_FILE" ] || continue
  TEST_NAME="$(basename "$TEST_FILE" .sh)"

  TMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t kairoi_test.XXXXXX)"

  # Run in subshell so cd doesn't leak; isolate stdout/stderr unless failure.
  OUTPUT="$(cd "$TMP_DIR" && bash "$TEST_FILE" 2>&1)"
  RC=$?

  if [ "$RC" -eq 0 ]; then
    PASS=$((PASS + 1))
    echo "  PASS  $TEST_NAME"
  else
    FAIL=$((FAIL + 1))
    FAILED_TESTS+=("$TEST_NAME")
    echo "  FAIL  $TEST_NAME"
    echo "$OUTPUT" | sed 's/^/        /'
  fi

  rm -rf "$TMP_DIR"
done

echo ""
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
  echo "$PASS/$TOTAL tests passed."
  exit 0
else
  echo "$PASS/$TOTAL passed, $FAIL failed:"
  for T in "${FAILED_TESTS[@]}"; do
    echo "  - $T"
  done
  exit 1
fi
