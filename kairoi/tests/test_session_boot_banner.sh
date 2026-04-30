#!/usr/bin/env bash
# session-boot default output is a one-line banner.
#
# The multi-block dump (MODULES / BUFFER / EDGES / RECEIPTS /
# DIAGNOSTICS / CHRONIC / UNRESOLVED / legend) is opt-in via
# KAIROI_VERBOSE=1. This test locks in the default-is-minimal contract
# and the KAIROI_VERBOSE=1 escape hatch.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
SESSION_BOOT="$PLUGIN/scripts/session-boot.sh"

setup_kairoi_state "auth" "Auth module" 3

CWD="$(pwd)"
INPUT="$(jq -n --arg cwd "$CWD" '{cwd: $cwd}')"

# ---- Default output: one line, starts with "kairoi:" ----------------------
OUT="$(echo "$INPUT" | bash "$SESSION_BOOT" 2>&1)"

# Non-empty-line count must be exactly 1 (banner only; no buffer → no
# dispatch signal fires in this fixture).
LINE_COUNT="$(echo "$OUT" | grep -c . || true)"
if [ "$LINE_COUNT" != "1" ]; then
  echo "default session-boot emitted $LINE_COUNT lines, expected 1"
  echo "full output:"
  echo "$OUT" | sed 's/^/  /'
  exit 1
fi

# Banner format check: "kairoi: watching N modules." variants.
if ! echo "$OUT" | grep -qE '^kairoi: watching 1 module\.'; then
  echo "default banner wrong format (expected 'kairoi: watching 1 module.')"
  echo "$OUT" | sed 's/^/  /'
  exit 1
fi

# None of the verbose-block headers must leak into default output.
for leak in "=== kairoi" "MODULES (" "RECEIPTS (" "EDGES (" "BUFFER:" "DIAGNOSTICS" "CHRONIC" "UNRESOLVED" "● high ◐ medium ○ low"; do
  if echo "$OUT" | grep -qF "$leak"; then
    echo "default output leaked verbose content: '$leak'"
    echo "$OUT" | sed 's/^/  /'
    exit 1
  fi
done

# ---- KAIROI_VERBOSE=1: full dump ------------------------------------------
OUT_V="$(echo "$INPUT" | KAIROI_VERBOSE=1 bash "$SESSION_BOOT" 2>&1)"

# Verbose must still include the banner (first line), plus the old-style
# dump beneath it.
if ! echo "$OUT_V" | head -1 | grep -qE '^kairoi: watching 1 module'; then
  echo "verbose output missing banner on first line"
  echo "$OUT_V" | sed 's/^/  /'
  exit 1
fi

for needle in "=== kairoi v" "MODULES (1)" "auth" "● high ◐ medium ○ low"; do
  if ! echo "$OUT_V" | grep -qF "$needle"; then
    echo "verbose output missing expected content: '$needle'"
    echo "$OUT_V" | sed 's/^/  /'
    exit 1
  fi
done

# Verbose header must carry the real plugin version from plugin.json,
# not a hard-coded literal.
if echo "$OUT_V" | grep -qF "=== kairoi vunknown ==="; then
  echo "verbose header fell back to 'unknown' — plugin.json read failed"
  echo "$OUT_V" | sed 's/^/  /'
  exit 1
fi

# ---- Last-session snippet: appears when .session-summary.txt exists -------
mkdir -p .kairoi
cat > .kairoi/.session-summary.txt <<'EOF'
Caught a near-regression in token refresh. Details follow.
Second line should be ignored entirely.
EOF

OUT_LS="$(echo "$INPUT" | bash "$SESSION_BOOT" 2>&1)"

if ! echo "$OUT_LS" | grep -qF "Last session:"; then
  echo "banner missing 'Last session:' snippet when summary file exists"
  echo "$OUT_LS" | sed 's/^/  /'
  exit 1
fi

# Must pick up first sentence, not the trailing "Details follow." or the
# second-line "Second line should be ignored."
if ! echo "$OUT_LS" | grep -qF "Caught a near-regression in token refresh"; then
  echo "banner didn't include first sentence of summary"
  echo "$OUT_LS" | sed 's/^/  /'
  exit 1
fi
if echo "$OUT_LS" | grep -qF "Second line should be ignored"; then
  echo "banner leaked second line of summary"
  echo "$OUT_LS" | sed 's/^/  /'
  exit 1
fi

# Still exactly one line of output.
LC_LS="$(echo "$OUT_LS" | grep -c . || true)"
if [ "$LC_LS" != "1" ]; then
  echo "banner-with-summary emitted $LC_LS lines, expected 1"
  echo "$OUT_LS" | sed 's/^/  /'
  exit 1
fi

# ---- Empty summary file: no "Last session:" suffix ------------------------
: > .kairoi/.session-summary.txt
OUT_EMPTY="$(echo "$INPUT" | bash "$SESSION_BOOT" 2>&1)"
if echo "$OUT_EMPTY" | grep -qF "Last session:"; then
  echo "empty summary file should not produce 'Last session:' text"
  echo "$OUT_EMPTY" | sed 's/^/  /'
  exit 1
fi

# ---- Zero modules: init-prompt form ---------------------------------------
rm .kairoi/.session-summary.txt
jq '.modules = {}' .kairoi/model/_index.json > /tmp/idx.json && mv /tmp/idx.json .kairoi/model/_index.json

OUT_ZERO="$(echo "$INPUT" | bash "$SESSION_BOOT" 2>&1)"
if ! echo "$OUT_ZERO" | grep -qF "kairoi: no modules yet"; then
  echo "zero-module banner wrong"
  echo "$OUT_ZERO" | sed 's/^/  /'
  exit 1
fi

# ---- Dispatch signal fires on stale buffer regardless of verbose mode ----
# Rebuild fixture: one module, one buffered task, no receipts (stale by
# definition → SHOULD_DISPATCH). The dispatch signal is load-bearing
# and must not be muted by KAIROI_VERBOSE gating.
setup_kairoi_state "auth" "Auth module" 3
buffer_append_raw "pending" "SUCCESS" "auth"

OUT_DISPATCH="$(echo "$INPUT" | bash "$SESSION_BOOT" 2>&1)"
if ! echo "$OUT_DISPATCH" | grep -qF "Dispatch the kairoi-complete agent"; then
  echo "dispatch signal missing in default mode when state is stale"
  echo "$OUT_DISPATCH" | sed 's/^/  /'
  exit 1
fi

# With dispatch, stdout is banner + dispatch reason + dispatch instruction
# = 3 non-empty lines. Anything more than that means the verbose block
# bled through.
LC_DISP="$(echo "$OUT_DISPATCH" | grep -c . || true)"
if [ "$LC_DISP" -gt 3 ]; then
  echo "default+dispatch stdout got $LC_DISP lines, expected <=3"
  echo "$OUT_DISPATCH" | sed 's/^/  /'
  exit 1
fi

# ---- Threshold-only dispatch: fresh receipt but buffer >= threshold -------
# An active project can pile commits faster than the staleness window. Even
# when the last receipt is recent (well below session_start_stale_days), a
# buffer >= threshold must trigger dispatch. This is what closes the
# user-reported gap: with a recent sync 6 days ago and 64 buffered tasks,
# the previous design said "not stale yet" and emitted no dispatch
# instruction; the new design says "threshold crossed, dispatch now."
setup_kairoi_state "auth" "Auth module" 3
# Recent receipt: today, well within the 7-day stale window.
RECENT_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
jq -nc --arg ts "$RECENT_TS" '{
  task_id: "recent-sync",
  timestamp: $ts,
  status: "SUCCESS",
  modules_affected: ["auth"],
  modified_files: [],
  test_results: null,
  commit_hash: "0000000",
  guards_fired: [],
  guards_disputed: [],
  blocked_diagnostics: null
}' > .kairoi/receipts.jsonl
# Pile up enough to cross default threshold of 10.
for i in 1 2 3 4 5 6 7 8 9 10; do
  buffer_append_raw "task-$i" "SUCCESS" "auth"
done

OUT_THRESH="$(echo "$INPUT" | bash "$SESSION_BOOT" 2>&1)"
if ! echo "$OUT_THRESH" | grep -qF "Dispatch the kairoi-complete agent"; then
  echo "threshold-based dispatch missing when buffer >= threshold but receipts fresh"
  echo "$OUT_THRESH" | sed 's/^/  /'
  exit 1
fi
if ! echo "$OUT_THRESH" | grep -qF "threshold"; then
  echo "expected dispatch reason to mention threshold"
  echo "$OUT_THRESH" | sed 's/^/  /'
  exit 1
fi

# ---- Below threshold AND fresh receipt: no dispatch -----------------------
# Counter-case: must NOT dispatch when both checks pass. Otherwise we'd be
# nagging Claude on every session-start of an active project mid-cycle.
setup_kairoi_state "auth" "Auth module" 3
jq -nc --arg ts "$RECENT_TS" '{
  task_id: "recent-sync",
  timestamp: $ts,
  status: "SUCCESS",
  modules_affected: ["auth"],
  modified_files: [],
  test_results: null,
  commit_hash: "0000000",
  guards_fired: [],
  guards_disputed: [],
  blocked_diagnostics: null
}' > .kairoi/receipts.jsonl
# Only 2 buffered tasks — well below threshold of 10.
buffer_append_raw "task-a" "SUCCESS" "auth"
buffer_append_raw "task-b" "SUCCESS" "auth"

OUT_QUIET="$(echo "$INPUT" | bash "$SESSION_BOOT" 2>&1)"
if echo "$OUT_QUIET" | grep -qF "Dispatch the kairoi-complete agent"; then
  echo "dispatch fired when buffer below threshold and receipt fresh — false positive"
  echo "$OUT_QUIET" | sed 's/^/  /'
  exit 1
fi

exit 0
