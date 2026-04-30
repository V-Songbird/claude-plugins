#!/usr/bin/env bash
# /kairoi:show --verbose flag parsing + extra analytic blocks.
#
# `--verbose` (or `-v`) prints DIAGNOSTICS / CHRONIC / UNRESOLVED BLOCKED
# in addition to the default output. Module filter still works, and
# `--verbose <module>` is accepted in either order.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
SHOW="$PLUGIN/scripts/show.sh"

setup_kairoi_state "auth" "OAuth2 PKCE token lifecycle" 3

# ---- --verbose no longer errors out --------------------------------------
if ! bash "$SHOW" --verbose >/tmp/show_verbose.out 2>&1; then
  echo "show --verbose exited non-zero"
  sed 's/^/  /' /tmp/show_verbose.out
  exit 1
fi
if grep -qF "no module named '--verbose'" /tmp/show_verbose.out; then
  echo "show --verbose still treats the flag as a module filter"
  sed 's/^/  /' /tmp/show_verbose.out
  exit 1
fi

if ! bash "$SHOW" -v >/tmp/show_v.out 2>&1; then
  echo "show -v exited non-zero"
  sed 's/^/  /' /tmp/show_v.out
  exit 1
fi

# ---- --verbose adds DIAGNOSTICS once history is deep enough --------------
# Need >5 receipts for DIAGNOSTICS, >30 for CHRONIC. Generate 35 receipts
# including some BLOCKED and some disputed guards so the analytic sections
# actually have something to render.
RECEIPTS=".kairoi/receipts.jsonl"
: > "$RECEIPTS"

emit_receipt() {
  local task_id="$1"
  local status="$2"
  local ts="$3"
  local disputed_json="${4:-[]}"
  jq -c -n \
    --arg t "$task_id" --arg s "$status" --arg ts "$ts" \
    --argjson d "$disputed_json" \
    '{
      task_id: $t, timestamp: $ts, status: $s,
      modules_affected: ["auth"], modified_files: ["src/auth/token.ts"],
      test_results: null, commit_hash: "abc1234",
      guards_fired: [], guards_disputed: $d, guards_created: [],
      model_updated: [], edges_updated: [], blocked_diagnostics: "stale diag"
    }' >> "$RECEIPTS"
}

# Ordering matters for UNRESOLVED detection: a BLOCKED is "unresolved" when no
# later SUCCESS on the same module follows it. Put the SUCCESS + disputed
# tasks FIRST (early timestamps) and the BLOCKED tasks LAST (late timestamps).
for i in 1 2 3 4 5; do
  emit_receipt "disp-$i" "SUCCESS" "2026-03-$(printf '%02d' $i)T12:00:00Z" '["some-guard"]'
done
for i in $(seq 1 28); do
  emit_receipt "task-$i" "SUCCESS" "2026-03-$(printf '%02d' $((i % 28 + 5)))T00:00:00Z"
done
emit_receipt "task-b1" "BLOCKED" "2026-04-20T00:00:00Z"
emit_receipt "task-b2" "BLOCKED" "2026-04-22T00:00:00Z"
emit_receipt "task-b3" "BLOCKED" "2026-04-25T00:00:00Z"

# Default (no --verbose) must NOT print DIAGNOSTICS / CHRONIC / UNRESOLVED.
OUT_DEFAULT="$(bash "$SHOW" 2>&1)"
for leak in "DIAGNOSTICS" "CHRONIC" "UNRESOLVED"; do
  if echo "$OUT_DEFAULT" | grep -qF "$leak"; then
    echo "default show leaked verbose-only block: '$leak'"
    echo "$OUT_DEFAULT" | sed 's/^/  /'
    exit 1
  fi
done

# --verbose must include DIAGNOSTICS; CHRONIC when >30 receipts;
# UNRESOLVED whenever there's an unresolved BLOCKED in the last 30.
OUT_V="$(bash "$SHOW" --verbose 2>&1)"
for needle in "DIAGNOSTICS (last 30)" "repeat-blocked modules" "chronically disputed" "UNRESOLVED BLOCKED"; do
  if ! echo "$OUT_V" | grep -qF "$needle"; then
    echo "show --verbose missing expected section: '$needle'"
    echo "$OUT_V" | sed 's/^/  /'
    exit 1
  fi
done

# --verbose also keeps all the default content that was already there.
for needle in "=== kairoi model ===" "OAuth2 PKCE token lifecycle"; do
  if ! echo "$OUT_V" | grep -qF "$needle"; then
    echo "show --verbose dropped default content: '$needle'"
    echo "$OUT_V" | sed 's/^/  /'
    exit 1
  fi
done

# ---- Flag + module filter: both orders accepted --------------------------
OUT_VF1="$(bash "$SHOW" --verbose auth 2>&1)"
OUT_VF2="$(bash "$SHOW" auth --verbose 2>&1)"

for OUT in "$OUT_VF1" "$OUT_VF2"; do
  if ! echo "$OUT" | grep -qF "OAuth2 PKCE"; then
    echo "show --verbose <module> dropped module detail"
    echo "$OUT" | sed 's/^/  /'
    exit 1
  fi
  # Filtered view exits before system-wide sections, verbose or not.
  if echo "$OUT" | grep -qF "DIAGNOSTICS"; then
    echo "show --verbose <module> should not render system-wide DIAGNOSTICS"
    echo "$OUT" | sed 's/^/  /'
    exit 1
  fi
done

# ---- Unknown flag must error cleanly -------------------------------------
if bash "$SHOW" --nonsense >/tmp/show_bad.out 2>&1; then
  echo "show --nonsense should have exited non-zero"
  sed 's/^/  /' /tmp/show_bad.out
  exit 1
fi
if ! grep -qF "unknown flag" /tmp/show_bad.out; then
  echo "show --nonsense didn't report unknown-flag error"
  sed 's/^/  /' /tmp/show_bad.out
  exit 1
fi

exit 0
