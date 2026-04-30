#!/usr/bin/env bash
# Shared helpers for jetbrains-router tests. Sourced by test_*.sh files.

set -u

: "${WSR_TEST_HOOK:?WSR_TEST_HOOK must be set by run.sh}"
: "${WSR_TEST_PLUGIN_ROOT:?WSR_TEST_PLUGIN_ROOT must be set by run.sh}"

# Force the availability probe on so process detection doesn't gate tests.
# Individual tests can override by exporting JETBRAINS_ROUTER_DISABLE=1 to
# exercise the fail-open path. Uses the internal name explicitly so a user
# who exported JETBRAINS_ROUTER_FORCE in their shell rc to debug this plugin
# does not bleed that state into the test runs of other plugins.
export JETBRAINS_ROUTER_FORCE_INTERNAL=1
unset JETBRAINS_ROUTER_FORCE
unset JETBRAINS_ROUTER_DISABLE

# run_hook — pipes the given JSON to the redirect script, captures stderr
# into WSR_STDERR and the exit code into WSR_RC. Stdout is discarded.
#
# Usage:
#   INPUT='{"tool_name":"Read","cwd":"/p","tool_input":{"file_path":"/p/x"}}'
#   run_hook "$INPUT"
#   assert_eq 2 "$WSR_RC" "hook should block"
#   assert_contains "$WSR_STDERR" "read_file"
run_hook() {
  local input="$1"
  local stderr_file
  stderr_file="$(mktemp)"
  printf '%s' "$input" | bash "$WSR_TEST_HOOK" >/dev/null 2>"$stderr_file"
  WSR_RC=$?
  WSR_STDERR="$(cat "$stderr_file")"
  rm -f "$stderr_file"
}

assert_eq() {
  local expected="$1"
  local actual="$2"
  local msg="${3:-assertion failed}"
  if [ "$expected" != "$actual" ]; then
    echo "ASSERT FAIL: $msg"
    echo "  expected: $expected"
    echo "  actual:   $actual"
    exit 1
  fi
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local msg="${3:-substring missing}"
  case "$haystack" in
    *"$needle"*) return 0 ;;
  esac
  echo "ASSERT FAIL: $msg"
  echo "  expected to contain: $needle"
  echo "  actual:              $haystack"
  exit 1
}

assert_not_contains() {
  local haystack="$1"
  local needle="$2"
  local msg="${3:-substring unexpectedly present}"
  case "$haystack" in
    *"$needle"*)
      echo "ASSERT FAIL: $msg"
      echo "  should not contain: $needle"
      echo "  actual:             $haystack"
      exit 1
      ;;
  esac
}
