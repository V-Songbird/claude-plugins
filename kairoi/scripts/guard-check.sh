#!/usr/bin/env bash
set -euo pipefail

# Optional hook-fire trace for debugging dispatch.
# Enable by exporting KAIROI_TRACE=/path/to/log. Appends a timestamp + pid.
# More reliable than KAIROI_DEBUG stderr for diagnosing Windows PreToolUse
# Write/Edit dispatch issues, where stderr may be suppressed (see GitHub
# anthropics/claude-code issues #6305, #18527, #22449).
if [ -n "${KAIROI_TRACE:-}" ]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] guard-check pid=$$ cwd=${PWD}" >> "${KAIROI_TRACE}" 2>/dev/null || true
fi

# kairoi PreToolUse hook: file-touch checkpoint.
# Fires on Read/Grep/Glob/Write/Edit AND on the WebStorm MCP equivalents so
# kairoi context still reaches the agent when webstorm-router has redirected
# native calls. Three phases:
#   1. First-touch module orientation (fires on read OR write)
#   2. File-level guard injection (write-only)
#   3. Downstream edge warnings (write-only)
# Phase 1 runs unconditionally so a session that goes "straight to source via
# Read/Grep" still gets the model context pushed — the user's contract is
# `/kairoi:init` once, not "remember to read .kairoi/model/<mod>.json before
# you Read source." Phases 2-3 stay write-only because they're about edit
# safety, and firing them on every Read/Grep would flood the context.
# All phases compose into one hookSpecificOutput.additionalContext payload —
# the only PreToolUse stdout shape empirically delivered to the model.
# Exit 0 always — advisory only.

command -v jq &>/dev/null || exit 0

# Debug mode
_DEVNULL="/dev/null"
if [ "${KAIROI_DEBUG:-}" = "1" ]; then
  _DEVNULL="/dev/stderr"
  echo "kairoi-debug: guard-check starting" >&2
fi

INPUT="$(cat)"
CWD="$(echo "$INPUT" | jq -r '.cwd // empty')"

[ -n "$CWD" ] || exit 0
STATE_DIR="$CWD/.kairoi"
[ -f "$STATE_DIR/model/_index.json" ] || exit 0

# Cache _index.json — one read, reused across all phases
INDEX_DATA="$(cat "$STATE_DIR/model/_index.json")"

# Tool classification: write-class tools get all three phases; read-class
# tools get Phase 1 only. The classification matches the matcher set in
# hooks.json — mirror them here so a misconfigured matcher doesn't silently
# enable guard scanning on a pure read.
TOOL_NAME="$(echo "$INPUT" | jq -r '.tool_name // empty')"
IS_WRITE_OP=false
case "$TOOL_NAME" in
  Write|Edit|\
  mcp__webstorm__replace_text_in_file|\
  mcp__webstorm__create_new_file|\
  mcp__webstorm__rename_refactoring)
    IS_WRITE_OP=true
    ;;
esac

# Extract file path from tool input. Native Read/Write/Edit use .file_path;
# Grep/Glob use .path (a directory or repo-relative path); WebStorm MCP tools
# use .pathInProject (already project-relative). For Grep/Glob with no .path
# (default = repo root), no module match exists and we exit silently — the
# orientation push is meaningful only when a single module owns the touch.
FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // .tool_input.pathInProject // empty')"
[ -n "$FILE_PATH" ] || exit 0

# Make path relative to CWD if absolute. .pathInProject is already relative
# so the prefix-strip is a no-op for it.
FILE_PATH="${FILE_PATH#$CWD/}"

# Find which module owns this file
MODULE=""
MODULE_FILE=""
while IFS= read -r MOD; do
  MOD="${MOD%$'\r'}"
  PATHS="$(echo "$INDEX_DATA" | jq -r --arg m "$MOD" '.modules[$m].source_paths[]' 2>"$_DEVNULL" | tr -d '\r' || true)"
  while IFS= read -r SP; do
    [ -n "$SP" ] || continue
    if [[ "$FILE_PATH" == "$SP"* ]]; then
      MODULE="$MOD"
      MODULE_FILE="$STATE_DIR/model/$MOD.json"
      break 2
    fi
  done <<< "$PATHS"
done < <(echo "$INDEX_DATA" | jq -r '.modules | keys[]' 2>"$_DEVNULL" | tr -d '\r')

[ -n "$MODULE" ] || exit 0

# --- Build output across all phases ---
# Use actual newlines throughout; jq handles JSON escaping at the end.
OUTPUT=""

# ============================================================
# Phase 1: First-edit-per-module orientation (pushed, not pulled)
# ============================================================
# On the first edit within a module during this session, inject the module's
# orientation context — purpose, confidence, guard count. This replaces the
# old voluntary pre-flight step: delivery at the moment of edit, never "please
# remember to run X." The .seen-<module> flag is wiped at SessionStart.

ORIENT_FLAG="$STATE_DIR/.seen-$MODULE"
if [ ! -f "$ORIENT_FLAG" ] && [ -f "$MODULE_FILE" ]; then
  touch "$ORIENT_FLAG"

  PURPOSE="$(jq -r '.purpose // "(unpopulated)"' "$MODULE_FILE" 2>"$_DEVNULL" | tr -d '\r')"
  # Confidence derived at read time from churn_since_validation — never stored.
  CONF="$(jq -r '
    if .purpose == null then "low"
    elif (._meta.churn_since_validation // 0) <= 10 then "high"
    elif (._meta.churn_since_validation // 0) <= 25 then "medium"
    else "low" end
  ' "$MODULE_FILE" 2>"$_DEVNULL" | tr -d '\r')"
  TSV="$(jq -r '._meta.tasks_since_validation // 0' "$MODULE_FILE" 2>"$_DEVNULL" | tr -d '\r')"
  CHURN="$(jq -r '._meta.churn_since_validation // empty' "$MODULE_FILE" 2>"$_DEVNULL" | tr -d '\r' || true)"
  GCOUNT="$(jq '.guards | length' "$MODULE_FILE" 2>"$_DEVNULL" || echo 0)"

  CHURN_INFO=""
  [ -n "$CHURN" ] && CHURN_INFO=" ch=$CHURN"
  OUTPUT="${OUTPUT}[$MODULE] $PURPOSE"$'\n'
  OUTPUT="${OUTPUT}  confidence=$CONF (tsv=$TSV${CHURN_INFO}, $GCOUNT guard(s))"$'\n'

  case "$CONF" in
    high)   OUTPUT="${OUTPUT}  → trust model, work from it"$'\n' ;;
    medium) OUTPUT="${OUTPUT}  → cross-check source files before editing"$'\n' ;;
    *)      OUTPUT="${OUTPUT}  → LOW confidence: read all source in module before changes"$'\n' ;;
  esac

  CPCOUNT="$(jq '.change_patterns | length' "$MODULE_FILE" 2>"$_DEVNULL" || echo 0)"
  if [ "$CPCOUNT" -gt 0 ] 2>/dev/null; then
    OUTPUT="${OUTPUT}  known change archetypes:"$'\n'
    while IFS= read -r CP_LINE; do
      [ -n "$CP_LINE" ] || continue
      OUTPUT="${OUTPUT}${CP_LINE}"$'\n'
    done < <(jq -r '.change_patterns[] | "    · " + .archetype + ": " + .check' "$MODULE_FILE" 2>"$_DEVNULL" || true)
  fi
fi

# ============================================================
# Phase 2: File-level guards (across all modules) — WRITE-ONLY
# ============================================================
# Scan ALL modules' guards — not just the owning module's — so a guard whose
# trigger_files includes a cross-module prefix (e.g., a dependent module's
# source_path) fires correctly. This is what makes dependent-guard generation
# from reflection actually bite at edit time.
#
# Read/Grep/Glob bypass this — guards are about edit safety, not orientation,
# and firing them on every read would drown out signal.

if [ "$IS_WRITE_OP" = true ]; then
while IFS= read -r SCAN_MOD; do
  SCAN_MOD="${SCAN_MOD%$'\r'}"
  [ -n "$SCAN_MOD" ] || continue
  SCAN_FILE="$STATE_DIR/model/$SCAN_MOD.json"
  [ -f "$SCAN_FILE" ] || continue

  GUARD_COUNT="$(jq '.guards | length' "$SCAN_FILE" 2>"$_DEVNULL" || echo 0)"
  [ "$GUARD_COUNT" -gt 0 ] || continue

  for i in $(seq 0 $((GUARD_COUNT - 1))); do
    TRIGGERS="$(jq -r --argjson i "$i" '.guards[$i].trigger_files[]' "$SCAN_FILE" 2>"$_DEVNULL" | tr -d '\r' || true)"
    MATCHED=false

    while IFS= read -r TRIGGER; do
      [ -n "$TRIGGER" ] || continue
      if [[ "$TRIGGER" == */ ]]; then
        [[ "$FILE_PATH" == "$TRIGGER"* ]] && MATCHED=true && break
      else
        [[ "$FILE_PATH" == "$TRIGGER" ]] && MATCHED=true && break
      fi
    done <<< "$TRIGGERS"

    if [ "$MATCHED" = true ]; then
      CHECK="$(jq -r --argjson i "$i" '.guards[$i].check' "$SCAN_FILE" 2>"$_DEVNULL" | tr -d '\r' || true)"
      RATIONALE="$(jq -r --argjson i "$i" '.guards[$i].rationale // empty' "$SCAN_FILE" 2>"$_DEVNULL" | tr -d '\r' || true)"
      SOURCE_TASK="$(jq -r --argjson i "$i" '.guards[$i].source_task' "$SCAN_FILE" 2>"$_DEVNULL" | tr -d '\r' || true)"
      if [ -n "$CHECK" ]; then
        # When the fire is from a guard owned by a DIFFERENT module than the
        # one being edited, surface the source module so the agent knows
        # which contract it's crossing.
        if [ "$SCAN_MOD" != "$MODULE" ]; then
          OUTPUT="${OUTPUT}⚠ GUARD [$SOURCE_TASK] (from $SCAN_MOD): $CHECK"$'\n'
        else
          OUTPUT="${OUTPUT}⚠ GUARD [$SOURCE_TASK]: $CHECK"$'\n'
        fi
        if [ -n "$RATIONALE" ]; then
          OUTPUT="${OUTPUT}  ↳ WHY: $RATIONALE"$'\n'
        fi
        # .guards-log is transient (cleared by buffer-append).
        echo "$SOURCE_TASK" >> "$STATE_DIR/.guards-log"
        # session.log is persistent — the user-visible record that kairoi
        # caught something. Humans who can't audit the code can still see
        # that protection is happening.
        TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "$TIMESTAMP  [$SCAN_MOD/$SOURCE_TASK] fired on $FILE_PATH" \
          >> "$STATE_DIR/session.log"
      fi
    fi
  done
done < <(echo "$INDEX_DATA" | jq -r '.modules | keys[]' 2>"$_DEVNULL" | tr -d '\r')

# ============================================================
# Phase 3: Downstream edge warnings (semantic dependents) — WRITE-ONLY
# ============================================================
# Same write-only gate as Phase 2 — dependents matter when the contract is
# about to change, not when source is being read.

EDGE_OUTPUT="$(echo "$INDEX_DATA" | jq -r --arg mod "$MODULE" '
  [.edges // [] | .[] |
   select(.to == $mod and (.type == "calls" or .type == "shares-state" or .type == "co-configured"))] |
  if length > 0 then
    "DEPENDENTS of \($mod):",
    (.[:5][] | "  \(.from): \(.label // .type)"),
    (if length > 5 then "  + \(length - 5) more dependents" else empty end)
  else empty end
' 2>"$_DEVNULL" || true)"

if [ -n "$EDGE_OUTPUT" ]; then
  OUTPUT="${OUTPUT}${EDGE_OUTPUT}"$'\n'
fi
fi  # end IS_WRITE_OP gate (Phases 2 + 3)

# ============================================================
# Emit hookSpecificOutput payload if any phase produced output
# ============================================================
# PreToolUse hooks must emit `hookSpecificOutput` with both `hookEventName`
# and `additionalContext` for the message to reach Claude's context. Bare
# `{ systemMessage }` shapes are silently dropped from PreToolUse stdout
# (they only deliver from SessionStart). Same envelope contract as
# auto-buffer.sh's PostToolUse path — just the event name differs.

if [ -n "$OUTPUT" ]; then
  # Use jq to build valid JSON — handles all escaping (newlines, quotes, unicode)
  jq -n --arg msg "kairoi context for $FILE_PATH in module [$MODULE]:
$OUTPUT" '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: $msg}}'
fi

exit 0
