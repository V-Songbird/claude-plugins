#!/usr/bin/env bash
# state-write-guard PreToolUse hook: deny hand-edits to .kairoi/ paths.
#
# Verifies:
#   - Edit / Write / MultiEdit to .kairoi/model/*.json is denied with a reason
#   - Edit / Write to .kairoi/overrides.json is allowed (allowlist)
#   - Edit / Write to a non-kairoi path is allowed
#   - Pre-init (no _index.json) writes pass through (init bootstrap)
#   - .kairoi/.write-guard-disabled sentinel suppresses denial
#   - Other tool names (Bash, Read, Grep) pass through silently
#   - Absolute paths normalize correctly against cwd

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
GUARD="$PLUGIN/scripts/state-write-guard.sh"

# Helper: run the guard with a constructed input. Echoes stdout.
# Usage: run_guard <tool_name> <file_path>
run_guard() {
  local tool="$1"
  local fp="$2"
  jq -n --arg cwd "$PWD" --arg tn "$tool" --arg f "$fp" \
    '{cwd: $cwd, tool_name: $tn, tool_input: {file_path: $f}}' | bash "$GUARD"
}

# Helper: assert the output denies (permissionDecision == "deny").
assert_deny() {
  local out="$1"
  local label="$2"
  local decision
  decision="$(echo "$out" | jq -r '.hookSpecificOutput.permissionDecision // empty' 2>/dev/null)"
  if [ "$decision" != "deny" ]; then
    echo "FAIL [$label]: expected deny, got: $out"
    return 1
  fi
  local reason
  reason="$(echo "$out" | jq -r '.hookSpecificOutput.permissionDecisionReason // empty' 2>/dev/null)"
  if [ -z "$reason" ]; then
    echo "FAIL [$label]: deny without a permissionDecisionReason"
    return 1
  fi
  return 0
}

# Helper: assert the output allows (empty stdout — fall-open).
assert_allow() {
  local out="$1"
  local label="$2"
  if [ -n "$out" ]; then
    echo "FAIL [$label]: expected fall-open (empty stdout), got: $out"
    return 1
  fi
  return 0
}

# =========================================================================
# Case A: pre-init — no .kairoi/model/_index.json yet. All writes allowed.
# =========================================================================
mkdir -p caseA && cd caseA || exit 1

OUT="$(run_guard Write ".kairoi/model/auth.json")"
assert_allow "$OUT" "A1: Write .kairoi/model/auth.json pre-init" || exit 1

OUT="$(run_guard Edit ".kairoi/buffer.jsonl")"
assert_allow "$OUT" "A2: Edit .kairoi/buffer.jsonl pre-init" || exit 1

cd .. || exit 1

# =========================================================================
# Case B: post-init — _index.json exists, sentinel absent. Deny .kairoi/**.
# =========================================================================
mkdir -p caseB && cd caseB || exit 1
setup_kairoi_state "auth" "Auth module" 0

# B1: Edit on a model file is denied.
OUT="$(run_guard Edit ".kairoi/model/auth.json")"
assert_deny "$OUT" "B1: Edit .kairoi/model/auth.json" || exit 1

# B2: Write on a model file is denied.
OUT="$(run_guard Write ".kairoi/model/auth.json")"
assert_deny "$OUT" "B2: Write .kairoi/model/auth.json" || exit 1

# B3: MultiEdit on a model file is denied.
OUT="$(run_guard MultiEdit ".kairoi/model/auth.json")"
assert_deny "$OUT" "B3: MultiEdit .kairoi/model/auth.json" || exit 1

# B4: Write on _index.json itself is denied.
OUT="$(run_guard Write ".kairoi/model/_index.json")"
assert_deny "$OUT" "B4: Write .kairoi/model/_index.json" || exit 1

# B5: Write on buffer.jsonl is denied (append-only hook-owned).
OUT="$(run_guard Write ".kairoi/buffer.jsonl")"
assert_deny "$OUT" "B5: Write .kairoi/buffer.jsonl" || exit 1

# B6: Write on a transient dotfile is denied.
OUT="$(run_guard Write ".kairoi/.guards-log")"
assert_deny "$OUT" "B6: Write .kairoi/.guards-log" || exit 1

# B7: Write on build-adapter.json is denied.
OUT="$(run_guard Write ".kairoi/build-adapter.json")"
assert_deny "$OUT" "B7: Write .kairoi/build-adapter.json" || exit 1

# B8: Reason text mentions /kairoi:audit, /kairoi:show, or overrides.json.
OUT="$(run_guard Write ".kairoi/model/auth.json")"
REASON="$(echo "$OUT" | jq -r '.hookSpecificOutput.permissionDecisionReason')"
echo "$REASON" | grep -q '/kairoi:audit' \
  || { echo "FAIL B8: reason missing /kairoi:audit hint"; echo "$REASON"; exit 1; }
echo "$REASON" | grep -q 'overrides.json' \
  || { echo "FAIL B8b: reason missing overrides.json hint"; echo "$REASON"; exit 1; }

cd .. || exit 1

# =========================================================================
# Case C: allowlist — .kairoi/overrides.json is editable.
# =========================================================================
mkdir -p caseC && cd caseC || exit 1
setup_kairoi_state "auth" "Auth module" 0

OUT="$(run_guard Edit ".kairoi/overrides.json")"
assert_allow "$OUT" "C1: Edit .kairoi/overrides.json (allowlisted)" || exit 1

OUT="$(run_guard Write ".kairoi/overrides.json")"
assert_allow "$OUT" "C2: Write .kairoi/overrides.json (allowlisted)" || exit 1

# C3: paths that LOOK like overrides.json but aren't an exact match are denied.
OUT="$(run_guard Write ".kairoi/overrides.json.bak")"
assert_deny "$OUT" "C3: Write .kairoi/overrides.json.bak (not allowlisted)" || exit 1

cd .. || exit 1

# =========================================================================
# Case D: off-target — paths outside .kairoi/ pass through.
# =========================================================================
mkdir -p caseD && cd caseD || exit 1
setup_kairoi_state "auth" "Auth module" 0

OUT="$(run_guard Write "src/auth/token.ts")"
assert_allow "$OUT" "D1: Write src/auth/token.ts" || exit 1

OUT="$(run_guard Edit "README.md")"
assert_allow "$OUT" "D2: Edit README.md" || exit 1

# D3: a file that starts with .kairoi but isn't actually under .kairoi/.
OUT="$(run_guard Write ".kairoi-notes.txt")"
assert_allow "$OUT" "D3: Write .kairoi-notes.txt (not under .kairoi/)" || exit 1

cd .. || exit 1

# =========================================================================
# Case E: sentinel — .kairoi/.write-guard-disabled suppresses denial.
# =========================================================================
mkdir -p caseE && cd caseE || exit 1
setup_kairoi_state "auth" "Auth module" 0
touch .kairoi/.write-guard-disabled

# Even Writes that would normally be denied pass through.
OUT="$(run_guard Write ".kairoi/model/auth.json")"
assert_allow "$OUT" "E1: Write blocked path with sentinel present" || exit 1

OUT="$(run_guard Write ".kairoi/model/_index.json")"
assert_allow "$OUT" "E2: Write _index.json with sentinel present (re-init path)" || exit 1

# Removing the sentinel re-arms the guard.
rm -f .kairoi/.write-guard-disabled
OUT="$(run_guard Write ".kairoi/model/auth.json")"
assert_deny "$OUT" "E3: Write blocked path after sentinel removed" || exit 1

cd .. || exit 1

# =========================================================================
# Case F: tool-name filter — non-write tools pass through.
# =========================================================================
mkdir -p caseF && cd caseF || exit 1
setup_kairoi_state "auth" "Auth module" 0

# Read on a model file is allowed (the tool-name doesn't match).
OUT="$(run_guard Read ".kairoi/model/auth.json")"
assert_allow "$OUT" "F1: Read .kairoi/model/auth.json" || exit 1

# Bash on a model file is allowed (Bash subprocess writes are how kairoi's
# own scripts and subagents work — they must not be blocked here).
OUT="$(run_guard Bash ".kairoi/model/auth.json")"
assert_allow "$OUT" "F2: Bash matcher pass-through" || exit 1

cd .. || exit 1

# =========================================================================
# Case G: absolute path — input may carry an absolute file_path. The script
# must normalize against cwd before matching.
# =========================================================================
mkdir -p caseG && cd caseG || exit 1
setup_kairoi_state "auth" "Auth module" 0

ABS=".kairoi/model/auth.json"
ABS="$PWD/$ABS"
OUT="$(run_guard Write "$ABS")"
assert_deny "$OUT" "G1: Write with absolute path under cwd/.kairoi/" || exit 1

ABS_OK="$PWD/.kairoi/overrides.json"
OUT="$(run_guard Write "$ABS_OK")"
assert_allow "$OUT" "G2: Write absolute overrides.json (allowlist via normalized path)" || exit 1

cd .. || exit 1

# =========================================================================
# Case H: no cwd in input — fall open silently. (Defensive: malformed input
# should never block.)
# =========================================================================
EMPTY_INPUT='{"tool_name": "Write", "tool_input": {"file_path": ".kairoi/model/auth.json"}}'
OUT="$(echo "$EMPTY_INPUT" | bash "$GUARD")"
assert_allow "$OUT" "H1: empty cwd falls open" || exit 1

exit 0
