#!/usr/bin/env bash
# auto-buffer PostToolUse hook.
# After ANY git commit, the hook auto-invokes buffer-append.sh, derives
# task_id from the commit subject, and appends a buffer entry without the
# agent needing to remember. Every commit is buffered unconditionally;
# duplicate commits are deduped by hash.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
AUTO_BUFFER="$PLUGIN/scripts/auto-buffer.sh"

init_git_repo
setup_kairoi_state "auth" "Auth module" 0

CWD="$(pwd)"

# --- Stage 1: SUCCESS commit triggers auto-buffer ---
commit_file "src/auth/token.ts" "// token" "feat(auth): add refresh token"

INPUT="$(jq -n --arg cwd "$CWD" '{cwd: $cwd, tool_name: "Bash", tool_input: {command: "git commit -m feat"}}')"
echo "$INPUT" | CLAUDE_PLUGIN_ROOT="$PLUGIN" bash "$AUTO_BUFFER"

assert_line_count ".kairoi/buffer.jsonl" 1 || exit 1
assert_jq ".kairoi/buffer.jsonl" '.task_id' "add-refresh-token" || exit 1
assert_jq ".kairoi/buffer.jsonl" '.status' "SUCCESS" || exit 1
assert_jq ".kairoi/buffer.jsonl" '.modules_affected[0]' "auth" || exit 1

# --- Stage 2: Running the hook again on the same commit is idempotent ---
echo "$INPUT" | CLAUDE_PLUGIN_ROOT="$PLUGIN" bash "$AUTO_BUFFER"
assert_line_count ".kairoi/buffer.jsonl" 1 || exit 1

# --- Stage 3: every commit is buffered regardless of subject shape ---
commit_file "src/auth/other.ts" "// other" "chore: regular commit"
echo "$INPUT" | CLAUDE_PLUGIN_ROOT="$PLUGIN" bash "$AUTO_BUFFER"
assert_line_count ".kairoi/buffer.jsonl" 2 || exit 1
LATEST_S3="$(tail -1 .kairoi/buffer.jsonl)"
if [ "$(echo "$LATEST_S3" | jq -r '.task_id')" != "regular-commit" ]; then
  echo "expected task_id=regular-commit, got: $(echo "$LATEST_S3" | jq -r '.task_id')"
  exit 1
fi
if [ "$(echo "$LATEST_S3" | jq -r '.status')" != "SUCCESS" ]; then
  echo "expected status=SUCCESS, got: $(echo "$LATEST_S3" | jq -r '.status')"
  exit 1
fi

# --- Stage 4: a clean commit (no test failures, no skip annotations, not a
#               revert) stays SUCCESS. Buffer-append's auto-promotion to
#               BLOCKED is mechanical — it fires only when one of the three
#               signals trips (see test_blocked_auto_promote.sh for the
#               positive cases).  ---
commit_file "src/auth/lock.ts" "// lock" "fix(auth): lock race"
echo "$INPUT" | CLAUDE_PLUGIN_ROOT="$PLUGIN" bash "$AUTO_BUFFER"

assert_line_count ".kairoi/buffer.jsonl" 3 || exit 1
LATEST="$(tail -1 .kairoi/buffer.jsonl)"
if [ "$(echo "$LATEST" | jq -r '.status')" != "SUCCESS" ]; then
  echo "expected status=SUCCESS, got: $(echo "$LATEST" | jq -r '.status')"
  exit 1
fi
if [ "$(echo "$LATEST" | jq -r '.blocked_diagnostics')" != "null" ]; then
  echo "expected blocked_diagnostics=null, got: $(echo "$LATEST" | jq -r '.blocked_diagnostics')"
  exit 1
fi

# --- Stage 5: buffer at threshold emits JSON dispatch signal ---
# Seed buffer to threshold-1, then commit + run hook. The post-commit count
# reaches default threshold (10), triggering dispatch JSON on stdout.
# hookSpecificOutput MUST carry the required `hookEventName` field — without
# it, Claude Code's hook validator rejects the output and the dispatch
# signal is dropped silently.
for i in 1 2 3 4 5 6; do
  buffer_append_raw "seed-task-$i" "SUCCESS" "auth"
done
commit_file "src/auth/cross-threshold.ts" "// threshold" "feat(auth): push to threshold"
HOOK_OUT="$(echo "$INPUT" | CLAUDE_PLUGIN_ROOT="$PLUGIN" bash "$AUTO_BUFFER" 2>/dev/null)"

# stdout must be valid JSON
echo "$HOOK_OUT" > .kairoi/.dispatch-output.json
if ! jq empty .kairoi/.dispatch-output.json 2>/dev/null; then
  echo "expected valid JSON on stdout at threshold, got: $HOOK_OUT"
  exit 1
fi
# hookEventName is REQUIRED by Claude Code's schema — missing it drops the signal
assert_jq ".kairoi/.dispatch-output.json" '.hookSpecificOutput.hookEventName' "PostToolUse" || exit 1
# additionalContext must carry the dispatch instruction Claude is supposed to follow
if ! jq -r '.hookSpecificOutput.additionalContext' .kairoi/.dispatch-output.json 2>/dev/null | grep -qF "Dispatch the kairoi-complete agent"; then
  echo "expected dispatch instruction in additionalContext"
  cat .kairoi/.dispatch-output.json
  exit 1
fi
rm -f .kairoi/.dispatch-output.json

# --- Stage 6: BLOCKED commit surfaces failure as system-reminder ---
# When buffer-append auto-promotes the just-written entry to BLOCKED (here
# via a test-disablement diff), auto-buffer must detect the BLOCKED status
# on the tail entry and emit a hookSpecificOutput.additionalContext warning
# that includes the diagnostic. The user explicitly cannot rely on Claude
# to read buffer.jsonl after every commit — the signal has to come back
# through the hook envelope, in the same response cycle as the commit's
# Bash tool call.
> .kairoi/buffer.jsonl
mkdir -p src/auth
cat > src/auth/skip.test.ts <<'EOF'
it.skip("flaky", () => {});
EOF
git add src/auth/skip.test.ts
git commit -q -m "test(auth): skip flaky"
echo "$INPUT" | CLAUDE_PLUGIN_ROOT="$PLUGIN" bash "$AUTO_BUFFER" 2>/dev/null > .kairoi/.blocked-output.json

# stdout must be valid JSON containing the BLOCKED warning
if ! jq empty .kairoi/.blocked-output.json 2>/dev/null; then
  echo "expected valid JSON when commit is BLOCKED, got:"
  cat .kairoi/.blocked-output.json
  exit 1
fi
assert_jq ".kairoi/.blocked-output.json" '.hookSpecificOutput.hookEventName' "PostToolUse" || exit 1
if ! jq -r '.hookSpecificOutput.additionalContext' .kairoi/.blocked-output.json 2>/dev/null | grep -qF "BLOCKED"; then
  echo "expected BLOCKED warning in additionalContext"
  cat .kairoi/.blocked-output.json
  exit 1
fi
if ! jq -r '.hookSpecificOutput.additionalContext' .kairoi/.blocked-output.json 2>/dev/null | grep -qF "test-disablement"; then
  echo "expected test-disablement diagnostic in additionalContext"
  cat .kairoi/.blocked-output.json
  exit 1
fi
# Buffer entry must also reflect the promotion
assert_jq ".kairoi/buffer.jsonl" '.status' "BLOCKED" || exit 1
rm -f .kairoi/.blocked-output.json

exit 0
