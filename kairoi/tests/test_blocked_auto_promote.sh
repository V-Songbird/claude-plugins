#!/usr/bin/env bash
# buffer-append.sh auto-promotes SUCCESS → BLOCKED based on three mechanical
# signals: test failures, test-disablement in the diff, and revert commits.
# This is the load-bearing piece that closes the user-reported gap: Claude
# Code sessions can't be relied on to self-report stuck-ness, so kairoi has
# to detect it from observable post-commit state.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
BUFFER_APPEND="$PLUGIN/scripts/buffer-append.sh"

init_git_repo
setup_kairoi_state "auth" "Auth module" 0

# --- Case 1: explicit failed-tests CSV promotes to BLOCKED ---
commit_file "src/auth/token.ts" "// stub" "feat(auth): stub token"

bash "$BUFFER_APPEND" \
  --task "case1-tests-failed" \
  --status "SUCCESS" \
  --summary "stub token" \
  --tests "10,7,3,0" >/dev/null

assert_jq ".kairoi/buffer.jsonl" '.status' "BLOCKED" || exit 1
assert_jq ".kairoi/buffer.jsonl" '.blocked_diagnostics | test("tests failing: 3 of 10")' "true" || exit 1

# --- Case 2: explicit --status BLOCKED with custom diag is preserved ---
> .kairoi/buffer.jsonl
commit_file "src/auth/refresh.ts" "// stub" "feat(auth): refresh stub"

bash "$BUFFER_APPEND" \
  --task "case2-explicit-blocked" \
  --status "BLOCKED" \
  --summary "refresh stub" \
  --tests "5,5,0,0" \
  --blocked-diag "agent self-reported: integration with provider X failed" >/dev/null

assert_jq ".kairoi/buffer.jsonl" '.status' "BLOCKED" || exit 1
assert_jq ".kairoi/buffer.jsonl" '.blocked_diagnostics' "agent self-reported: integration with provider X failed" || exit 1

# --- Case 3: clean commit with passing tests stays SUCCESS ---
> .kairoi/buffer.jsonl
commit_file "src/auth/clean.ts" "// works" "feat(auth): clean impl"

bash "$BUFFER_APPEND" \
  --task "case3-clean" \
  --status "SUCCESS" \
  --summary "clean impl" \
  --tests "5,5,0,0" >/dev/null

assert_jq ".kairoi/buffer.jsonl" '.status' "SUCCESS" || exit 1
assert_jq ".kairoi/buffer.jsonl" '.blocked_diagnostics' "null" || exit 1

# --- Case 4: test-disablement in the diff promotes to BLOCKED ---
# Add a Jest .skip annotation as a new line in the commit's diff. The grep
# patterns in buffer-append target the major framework conventions across
# JVM/JS/Python.
> .kairoi/buffer.jsonl
mkdir -p src/auth
cat > src/auth/test_thing.test.ts <<'EOF'
describe.skip("auth flow", () => {
  it("works", () => {});
});
EOF
git add src/auth/test_thing.test.ts
git commit -q -m "test(auth): skip flaky suite"

bash "$BUFFER_APPEND" \
  --task "case4-disabled-tests" \
  --status "SUCCESS" \
  --summary "skip flaky suite" \
  --skip-tests >/dev/null

assert_jq ".kairoi/buffer.jsonl" '.status' "BLOCKED" || exit 1
assert_jq ".kairoi/buffer.jsonl" '.blocked_diagnostics | test("test-disablement detected")' "true" || exit 1

# --- Case 5: revert commit promotes to BLOCKED ---
> .kairoi/buffer.jsonl
commit_file "src/auth/oops.ts" "// rolled back" 'Revert "feat(auth): broken thing"'

bash "$BUFFER_APPEND" \
  --task "case5-revert" \
  --status "SUCCESS" \
  --summary "rollback" \
  --skip-tests >/dev/null

assert_jq ".kairoi/buffer.jsonl" '.status' "BLOCKED" || exit 1
assert_jq ".kairoi/buffer.jsonl" '.blocked_diagnostics | test("revert commit")' "true" || exit 1

# --- Case 6: raw_exit non-zero with no parsed counts still promotes ---
# This covers the "tests ran, output format not recognized, but exit was
# non-zero" branch in buffer-append's auto-run path.
> .kairoi/buffer.jsonl
commit_file "src/auth/exit.ts" "// stub" "feat(auth): exit-only fail"

bash "$BUFFER_APPEND" \
  --task "case6-raw-exit" \
  --status "SUCCESS" \
  --summary "exit only" \
  --tests "1,0,1,0" >/dev/null

assert_jq ".kairoi/buffer.jsonl" '.status' "BLOCKED" || exit 1

exit 0
