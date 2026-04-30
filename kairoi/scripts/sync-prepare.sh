#!/usr/bin/env bash
set -euo pipefail

# kairoi sync-prepare: read buffer, aggregate per-module context,
# auto-discover new modules, write .sync-manifest.json.
# Called by the kairoi-complete orchestrator before dispatching reflection.
#
# Usage: sync-prepare.sh
#
# Reads:
#   .kairoi/buffer.jsonl
#   .kairoi/model/_index.json
#   .kairoi/overrides.json
#
# Writes:
#   .kairoi/.sync-manifest.json
#   .kairoi/model/<module>.json (seed files for newly discovered modules)
#
# Exits 0 with JSON status on stdout:
#   {"status":"ok","task_count":N} or {"status":"empty"}

command -v jq &>/dev/null || { echo '{"status":"error","message":"jq required"}'; exit 1; }

# Debug mode
_DEVNULL="/dev/null"
if [ "${KAIROI_DEBUG:-}" = "1" ]; then
  _DEVNULL="/dev/stderr"
  echo "kairoi-debug: sync-prepare starting" >&2
fi

STATE_DIR=".kairoi"
BUFFER="$STATE_DIR/buffer.jsonl"
INDEX="$STATE_DIR/model/_index.json"
OVERRIDES="$STATE_DIR/overrides.json"
MANIFEST="$STATE_DIR/.sync-manifest.json"

[ -f "$INDEX" ] || { echo '{"status":"error","message":"no _index.json"}'; exit 1; }

# --- Read buffer ---
if [ ! -f "$BUFFER" ] || [ ! -s "$BUFFER" ]; then
  echo '{"status":"empty"}'
  exit 0
fi

# Separate _deferred entries from real tasks
DEFERRED_MODULES="[]"
TASKS_JSON="[]"

while IFS= read -r LINE; do
  [ -n "$LINE" ] || continue
  TID="$(echo "$LINE" | jq -r '.task_id // empty')"
  if [ "$TID" = "_deferred" ]; then
    # Merge modules_pending into deferred set
    DEFERRED_MODULES="$(echo "$DEFERRED_MODULES" "$LINE" | jq -s '
      .[0] + (.[1].modules_pending // []) | unique
    ')"
  else
    TASKS_JSON="$(echo "$TASKS_JSON" | jq --argjson t "$LINE" '. + [$t]')"
  fi
done < "$BUFFER"

TASK_COUNT="$(echo "$TASKS_JSON" | jq 'length')"
DEFERRED_COUNT="$(echo "$DEFERRED_MODULES" | jq 'length')"

if [ "$TASK_COUNT" -eq 0 ] && [ "$DEFERRED_COUNT" -eq 0 ]; then
  echo '{"status":"empty"}'
  exit 0
fi

# --- Read supporting files ---
OVERRIDES_JSON="{}"
[ -f "$OVERRIDES" ] && OVERRIDES_JSON="$(cat "$OVERRIDES")"

# tr -d '\r' guards against Windows git-bash adding CR to jq output.
SOURCE_DIRS="$(jq -r '.source_dirs // ["src/"] | .[]' "$INDEX" 2>"$_DEVNULL" | tr -d '\r')"
MODULE_MAP="$(jq '.modules' "$INDEX" 2>"$_DEVNULL")"

# --- Aggregate per-module context ---
# Build modules_affected map from tasks
MODULES_AFFECTED="$(echo "$TASKS_JSON" | jq '
  # Collect per-module data across all tasks
  reduce .[] as $task ({};
    reduce ($task.modules_affected // [])[] as $mod (.;
      .[$mod] = (.[$mod] // {
        tasks: [],
        files_modified: [],
        guards_fired: [],
        guards_disputed: [],
        test_results: { total: 0, passed: 0, failed: 0, skipped: 0 },
        is_blocked: false,
        corrections: [],
        pinned: {},
        protected_guards: []
      }) |
      .[$mod].tasks += [$task.task_id] |
      .[$mod].files_modified = (.[$mod].files_modified + ($task.modified_files // []) | unique) |
      .[$mod].guards_fired = (.[$mod].guards_fired + ($task.guards_fired // []) | unique) |
      .[$mod].guards_disputed = (.[$mod].guards_disputed + ($task.guards_disputed // []) | unique) |
      # Sum test results (skip null)
      (if $task.test_results != null then
        .[$mod].test_results.total += ($task.test_results.total // 0) |
        .[$mod].test_results.passed += ($task.test_results.passed // 0) |
        .[$mod].test_results.failed += ($task.test_results.failed // 0) |
        .[$mod].test_results.skipped += ($task.test_results.skipped // 0)
      else . end) |
      (if $task.status == "BLOCKED" then
        .[$mod].is_blocked = true
      else . end)
    )
  )
')"

# --- Add deferred modules (from prior partial failure) ---
if [ "$DEFERRED_COUNT" -gt 0 ]; then
  MODULES_AFFECTED="$(echo "$MODULES_AFFECTED" "$DEFERRED_MODULES" | jq -s '
    .[0] as $mods | .[1] as $deferred |
    reduce $deferred[] as $mod ($mods;
      if .[$mod] then . else
        .[$mod] = {
          tasks: [],
          files_modified: [],
          guards_fired: [],
          guards_disputed: [],
          test_results: { total: 0, passed: 0, failed: 0, skipped: 0 },
          is_blocked: false,
          corrections: [],
          pinned: {},
          protected_guards: []
        }
      end
    )
  ')"
fi

# --- Slot overrides per module ---
MODULES_AFFECTED="$(echo "$MODULES_AFFECTED" "$OVERRIDES_JSON" | jq -s '
  .[0] as $mods | .[1] as $ov |
  $mods | to_entries | map(
    .key as $mod |
    ($ov.modules[$mod] // {}) as $mov |
    .value.corrections = ($mov.corrections // []) |
    .value.pinned = ($mov.pinned // {}) |
    .value.protected_guards = ($mov.protected_guards // [])
  ) | from_entries
')"

# --- Surface unmapped files (no heuristic module creation) ---
# Unmapped files are reported in the manifest; the human or a future agent
# flow decides whether they warrant a new module, belong in an existing
# one, or should be ignored entirely. Nothing in .kairoi/ mutates silently.
# Heuristic auto-module-creation from filesystem layout is rejected by the
# philosophy filter (structure-prescription).
ALL_MODIFIED="$(echo "$TASKS_JSON" | jq -r '.[].modified_files // [] | .[]' | tr -d '\r' | sort -u)"

UNMAPPED_FILES="[]"
while IFS= read -r FILE; do
  [ -n "$FILE" ] || continue

  # Under a declared source_dir?
  IN_SOURCE=false
  while IFS= read -r SD; do
    case "$FILE" in "$SD"*) IN_SOURCE=true; break ;; esac
  done <<< "$SOURCE_DIRS"
  $IN_SOURCE || continue

  # Already mapped to a module?
  MAPPED="$(echo "$MODULE_MAP" | jq -r --arg f "$FILE" '
    to_entries[] |
    select(.value.source_paths[] as $sp | $f | startswith($sp)) |
    .key
  ' | head -1)"

  [ -n "$MAPPED" ] && continue

  UNMAPPED_FILES="$(echo "$UNMAPPED_FILES" | jq --arg f "$FILE" '. + [$f]')"
done <<< "$ALL_MODIFIED"

# --- Count blocked ---
BLOCKED_COUNT="$(echo "$TASKS_JSON" | jq '[.[] | select(.status == "BLOCKED")] | length')"

# --- Write manifest ---
# Use temp files + --slurpfile to avoid "Argument list too long" when the
# accumulated TASKS_JSON or MODULES_AFFECTED JSON blows past ARG_MAX.
_TMP_TASKS="$(mktemp)"
_TMP_MODS="$(mktemp)"
_TMP_UNMAPPED="$(mktemp)"
printf '%s' "$TASKS_JSON"      > "$_TMP_TASKS"
printf '%s' "$MODULES_AFFECTED" > "$_TMP_MODS"
printf '%s' "$UNMAPPED_FILES"   > "$_TMP_UNMAPPED"

jq -n \
  --argjson task_count "$TASK_COUNT" \
  --slurpfile tasks "$_TMP_TASKS" \
  --slurpfile modules_affected "$_TMP_MODS" \
  --slurpfile unmapped_files "$_TMP_UNMAPPED" \
  --argjson blocked_count "$BLOCKED_COUNT" \
  '{
    task_count: $task_count,
    tasks: $tasks[0],
    modules_affected: $modules_affected[0],
    unmapped_files: $unmapped_files[0],
    blocked_count: $blocked_count
  }' > "$MANIFEST"

rm -f "$_TMP_TASKS" "$_TMP_MODS" "$_TMP_UNMAPPED"

# --- Snapshot affected model files before reflection ---
# These pre-reflection copies let sync-finalize enforce `protected_guards` —
# if reflection removed a protected guard, we can restore the exact object
# from the snapshot. `pinned` fields are enforced without snapshots (overrides
# is authoritative). Snapshots are cleaned up by sync-finalize.
SNAPSHOT_DIR="$STATE_DIR/.pre-sync"
mkdir -p "$SNAPSHOT_DIR"
rm -f "$SNAPSHOT_DIR"/*.json 2>"$_DEVNULL" || true

while IFS= read -r SNAP_MOD; do
  SNAP_MOD="${SNAP_MOD%$'\r'}"
  [ -n "$SNAP_MOD" ] || continue
  SRC_MF="$STATE_DIR/model/$SNAP_MOD.json"
  [ -f "$SRC_MF" ] && cp "$SRC_MF" "$SNAPSHOT_DIR/$SNAP_MOD.json"
done < <(echo "$MODULES_AFFECTED" | jq -r 'keys[]' | tr -d '\r')

echo "{\"status\":\"ok\",\"task_count\":$TASK_COUNT,\"modules\":$(echo "$MODULES_AFFECTED" | jq 'keys'),\"deferred\":$DEFERRED_COUNT,\"unmapped\":$(echo "$UNMAPPED_FILES" | jq 'length')}"
