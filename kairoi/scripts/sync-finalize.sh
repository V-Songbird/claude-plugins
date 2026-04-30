#!/usr/bin/env bash
set -euo pipefail

# kairoi sync-finalize: post-reflection cleanup.
# Updates _meta, co-modified edges, semantic edges, prunes stale edges,
# consumes corrections, emits receipts, clears buffer, writes _deferred
# for unreflected modules, removes transient files.
#
# Usage:
#   sync-finalize.sh --reflected <mod1,mod2,...>
#
# Reads:
#   .kairoi/.sync-manifest.json
#   .kairoi/.reflect-result-*.json
#   .kairoi/model/_index.json
#   .kairoi/model/<module>.json
#   .kairoi/build-adapter.json
#   .kairoi/overrides.json
#
# Writes:
#   .kairoi/model/<module>.json (_meta updates)
#   .kairoi/model/_index.json (edge updates)
#   .kairoi/overrides.json (consume corrections)
#   .kairoi/receipts.jsonl (append receipts)
#   .kairoi/buffer.jsonl (clear + _deferred)
#
# Removes:
#   .kairoi/.sync-manifest.json
#   .kairoi/.reflect-result-*.json

command -v jq &>/dev/null || { echo "kairoi sync-finalize: jq required" >&2; exit 1; }

# Debug mode
_DEVNULL="/dev/null"
if [ "${KAIROI_DEBUG:-}" = "1" ]; then
  _DEVNULL="/dev/stderr"
  echo "kairoi-debug: sync-finalize starting" >&2
fi

# --- Parse arguments ---
REFLECTED=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reflected) REFLECTED="$2"; shift 2 ;;
    *) echo "kairoi sync-finalize: unknown arg $1" >&2; exit 1 ;;
  esac
done

STATE_DIR=".kairoi"
MANIFEST="$STATE_DIR/.sync-manifest.json"
INDEX="$STATE_DIR/model/_index.json"
ADAPTER="$STATE_DIR/build-adapter.json"
OVERRIDES="$STATE_DIR/overrides.json"
RECEIPTS="$STATE_DIR/receipts.jsonl"
BUFFER="$STATE_DIR/buffer.jsonl"

[ -f "$MANIFEST" ] || { echo "kairoi sync-finalize: no manifest" >&2; exit 1; }

# Parse reflected modules into a JSON array
IFS=',' read -ra REFLECTED_ARR <<< "$REFLECTED"
REFLECTED_JSON="$(printf '%s\n' "${REFLECTED_ARR[@]}" | jq -R -s 'split("\n") | map(select(length > 0))')"

# All modules from manifest. tr -d '\r' guards against Windows git-bash pipes
# adding CR to jq output, which would corrupt every downstream module-key lookup.
ALL_MODULES="$(jq -r '.modules_affected | keys[]' "$MANIFEST" | tr -d '\r')"

# Unreflected modules = all - reflected
UNREFLECTED_JSON="$(echo "$ALL_MODULES" | jq -R -s --argjson ref "$REFLECTED_JSON" '
  split("\n") | map(select(length > 0)) |
  map(select(. as $m | $ref | index($m) | not))
')"

# Read manifest tasks
TASKS_JSON="$(jq '.tasks' "$MANIFEST")"

SCRIPT_DIR="$(dirname "$0")"
VALIDATE_SCHEMA="$SCRIPT_DIR/validate-schema.sh"

# --- Collect reflection results ---
# Merge all .reflect-result-*.json into one object keyed by module.
# Validate each reflect-result before merging. Invalid agent output is
# logged and skipped rather than propagating schema drift into receipts
# and model files downstream.
RESULTS="{}"
for RF in "$STATE_DIR"/.reflect-result-*.json; do
  [ -f "$RF" ] || continue

  # Validator errors go to stderr; we don't care about its stdout.
  if [ -f "$VALIDATE_SCHEMA" ]; then
    if ! bash "$VALIDATE_SCHEMA" reflect-result "$RF"; then
      echo "kairoi sync-finalize: SKIPPING invalid reflect-result: $RF" >&2
      continue
    fi
  fi

  MOD="$(jq -r '.module' "$RF" | tr -d '\r')"
  RESULTS="$(echo "$RESULTS" | jq --arg mod "$MOD" --slurpfile r "$RF" '.[$mod] = $r[0]')"
done

# --- Step 1: Update _meta ---
TODAY="$(date -u +%Y-%m-%d)"

while IFS= read -r MOD; do
  MOD="${MOD%$'\r'}"
  [ -n "$MOD" ] || continue
  MODEL_FILE="$STATE_DIR/model/${MOD}.json"
  [ -f "$MODEL_FILE" ] || continue

  # Only update _meta for reflected modules
  IS_REFLECTED="$(echo "$REFLECTED_JSON" | jq --arg m "$MOD" 'index($m) != null')"
  [ "$IS_REFLECTED" = "true" ] || continue

  # Count tasks affecting this module
  TASK_COUNT="$(jq --arg mod "$MOD" '
    .modules_affected[$mod].tasks | length
  ' "$MANIFEST")"

  # Check if this was first population (from reflect-result file)
  FIRST_POP="$(echo "$RESULTS" | jq -r --arg m "$MOD" '.[$m].first_population // false')"

  # Churn = total modified_files across all tasks that touched this module.
  # One file-touch per task = 1 churn unit; a 10-file refactor = 10 units.
  # This makes staleness sensitive to structural scope, not just task count.
  CHURN="$(jq --arg mod "$MOD" '
    [.tasks[] | select(.modules_affected | index($mod) != null) |
     .modified_files // [] | length] | add // 0
  ' "$MANIFEST")"

  # confidence is NOT persisted — derived at read time from churn_since_validation.
  # Storing it invited drift between writers that disagreed on the formula.
  if [ "$FIRST_POP" = "true" ]; then
    # First population — reset staleness
    jq --arg today "$TODAY" '
      ._meta.tasks_since_validation = 0 |
      ._meta.churn_since_validation = 0 |
      ._meta.last_validated = $today |
      del(._meta.confidence, ._meta.tasks_touched)
    ' "$MODEL_FILE" > "${MODEL_FILE}.tmp" && mv "${MODEL_FILE}.tmp" "$MODEL_FILE"
  else
    # Incremental update
    jq --argjson tc "$TASK_COUNT" --argjson churn "$CHURN" '
      ._meta.tasks_since_validation = (._meta.tasks_since_validation + $tc) |
      ._meta.churn_since_validation = ((._meta.churn_since_validation // 0) + $churn) |
      del(._meta.confidence, ._meta.tasks_touched)
    ' "$MODEL_FILE" > "${MODEL_FILE}.tmp" && mv "${MODEL_FILE}.tmp" "$MODEL_FILE"
  fi
done <<< "$ALL_MODULES"

# --- Step 1b: Mechanical enforcement of pinned + protected_guards ---
# Reflection agents are instructed to respect overrides, but that's
# honor-system. Before we continue, enforce mechanically:
#   - Any field in overrides.modules.<mod>.pinned replaces whatever the agent
#     wrote (human correction always wins).
#   - Any guard whose source_task is in overrides.modules.<mod>.protected_guards
#     must still exist; if reflection removed it, restore from the pre-sync
#     snapshot taken by sync-prepare.
SNAPSHOT_DIR="$STATE_DIR/.pre-sync"
if [ -f "$OVERRIDES" ]; then
  while IFS= read -r ENF_MOD; do
    ENF_MOD="${ENF_MOD%$'\r'}"
    [ -n "$ENF_MOD" ] || continue

    ENF_REFLECTED="$(echo "$REFLECTED_JSON" | jq --arg m "$ENF_MOD" 'index($m) != null')"
    [ "$ENF_REFLECTED" = "true" ] || continue

    ENF_MF="$STATE_DIR/model/$ENF_MOD.json"
    [ -f "$ENF_MF" ] || continue

    OV_MOD="$(jq --arg m "$ENF_MOD" '.modules[$m] // {}' "$OVERRIDES")"
    PINNED_JSON="$(echo "$OV_MOD" | jq '.pinned // {}')"
    PROTECTED_JSON="$(echo "$OV_MOD" | jq '.protected_guards // []')"

    # Apply pinned — top-level fields only. Merges overrides over current state.
    if [ "$(echo "$PINNED_JSON" | jq 'length')" -gt 0 ]; then
      jq --argjson pin "$PINNED_JSON" '. * $pin' "$ENF_MF" \
        > "${ENF_MF}.tmp" && mv "${ENF_MF}.tmp" "$ENF_MF"
    fi

    # Restore any protected guards that reflection removed.
    if [ "$(echo "$PROTECTED_JSON" | jq 'length')" -gt 0 ]; then
      SNAP_FILE="$SNAPSHOT_DIR/$ENF_MOD.json"
      if [ -f "$SNAP_FILE" ]; then
        while IFS= read -r PG_ST; do
          PG_ST="${PG_ST%$'\r'}"
          [ -n "$PG_ST" ] || continue
          PRESENT="$(jq --arg st "$PG_ST" \
            '[.guards[]? | select(.source_task == $st)] | length' "$ENF_MF")"
          [ "$PRESENT" = "0" ] || continue

          RESTORED="$(jq --arg st "$PG_ST" \
            '[.guards[]? | select(.source_task == $st)] | first // null' "$SNAP_FILE")"
          [ "$RESTORED" != "null" ] || continue

          jq --argjson g "$RESTORED" '.guards += [$g]' "$ENF_MF" \
            > "${ENF_MF}.tmp" && mv "${ENF_MF}.tmp" "$ENF_MF"
        done <<< "$(echo "$PROTECTED_JSON" | jq -r '.[]' | tr -d '\r')"
      fi
    fi
  done <<< "$ALL_MODULES"
fi

# --- Step 2: Update Edges ---

# Read pruning thresholds
PRUNE_MIN_WEIGHT="$(jq -r '.edge_prune_min_weight // 2' "$ADAPTER" 2>"$_DEVNULL" || echo 2)"
PRUNE_MAX_AGE="$(jq -r '.edge_prune_max_age_days // 30' "$ADAPTER" 2>"$_DEVNULL" || echo 30)"

# Compute threshold date for age-based pruning. Uses jq (portable) instead of
# GNU `date -d` (which fails on BSD/macOS/Windows git-bash).
PRUNE_THRESHOLD="$(jq -r -n --argjson days "$PRUNE_MAX_AGE" --arg today "$TODAY" \
  '(($today + "T00:00:00Z" | fromdateiso8601) - ($days * 86400)) | strftime("%Y-%m-%d")' \
  2>"$_DEVNULL" || echo "1970-01-01")"

# 6b: Co-modified edges — for each task, create edges between all module pairs
CO_EDGES="[]"
while IFS= read -r TASK_LINE; do
  TASK_LINE="${TASK_LINE%$'\r'}"
  [ -n "$TASK_LINE" ] || continue
  MODS="$(echo "$TASK_LINE" | jq -r '.modules_affected // [] | sort | .[]' | tr -d '\r')"
  MODS_ARR=()
  while IFS= read -r M; do
    [ -n "$M" ] || continue
    MODS_ARR+=("$M")
  done <<< "$MODS"

  # Generate all pairs (alphabetical)
  for ((i=0; i<${#MODS_ARR[@]}; i++)); do
    for ((j=i+1; j<${#MODS_ARR[@]}; j++)); do
      CO_EDGES="$(echo "$CO_EDGES" | jq \
        --arg from "${MODS_ARR[$i]}" \
        --arg to "${MODS_ARR[$j]}" \
        --arg today "$TODAY" \
        '. + [{ from: $from, to: $to, today: $today }]')"
    done
  done
done <<< "$(echo "$TASKS_JSON" | jq -c '.[]' | tr -d '\r')"

# 6c: Semantic edges from reflection results
SEMANTIC_EDGES="[]"
for RF in "$STATE_DIR"/.reflect-result-*.json; do
  [ -f "$RF" ] || continue
  SE="$(jq '.semantic_edges // []' "$RF")"
  SEMANTIC_EDGES="$(echo "$SEMANTIC_EDGES" "$SE" | jq -s '.[0] + .[1]')"
done

# Apply edge updates to _index.json.
#
# NOTE: jq 1.7+ tightened the grammar so that binding the result of
# `reduce ... as $v (init; body)` to another variable via `as $name |`
# requires parentheses around the whole reduce expression. Without them,
# jq 1.7.1 (ships on Windows git-bash) fails with:
#   syntax error, unexpected as, expecting end of file
#     (Windows cmd shell quoting issues?)
# The "Windows cmd shell quoting issues?" hint in that message is a red
# herring — it's a parse-level grammar issue, not shell quoting. jq 1.6
# accepted the un-parenthesized form, which is how this script shipped
# unnoticed until Windows dogfood surfaced it. Before the fix, edge
# updates silently no-op'd on Windows (empty .tmp file, mv skipped,
# `_index.json` unchanged). Both `reduce` expressions below are now
# wrapped.
jq --argjson co_edges "$CO_EDGES" \
   --argjson sem_edges "$SEMANTIC_EDGES" \
   --argjson prune_min "$PRUNE_MIN_WEIGHT" \
   --arg prune_threshold "$PRUNE_THRESHOLD" \
   --arg today "$TODAY" '
  # Update co-modified edges
  (reduce $co_edges[] as $ce (.edges // [];
    ($ce.from) as $f | ($ce.to) as $t |
    (map(select(.from == $f and .to == $t and .type == "co-modified")) | first) as $existing |
    if $existing then
      map(if .from == $f and .to == $t and .type == "co-modified"
        then .weight = (.weight + 1) | .last_seen = $today
        else . end)
    else
      . + [{ from: $f, to: $t, type: "co-modified", weight: 1, last_seen: $today }]
    end
  )) as $edges_after_co |

  # Add semantic edges (skip duplicates)
  (reduce $sem_edges[] as $se ($edges_after_co;
    if (map(select(.from == $se.from and .to == $se.to and .type == $se.type)) | length) > 0
    then .
    else . + [$se | . + { weight: 1, last_seen: $today }]
    end
  )) as $edges_after_sem |

  # Prune co-modified edges below weight threshold AND older than age threshold
  ($edges_after_sem | map(select(
    if .type == "co-modified" and .weight < $prune_min and (.last_seen // "1970-01-01") < $prune_threshold
    then false
    else true
    end
  ))) as $final_edges |

  .edges = $final_edges
' "$INDEX" > "${INDEX}.tmp" && mv "${INDEX}.tmp" "$INDEX"

# --- Step 3: Consume corrections ---
if [ -f "$OVERRIDES" ]; then
  jq --argjson ref "$REFLECTED_JSON" '
    .modules = (.modules // {} | to_entries | map(
      if ($ref | index(.key)) != null then
        .value.corrections = []
      else . end
    ) | from_entries)
  ' "$OVERRIDES" > "${OVERRIDES}.tmp" && mv "${OVERRIDES}.tmp" "$OVERRIDES"
fi

# --- Step 4: Emit receipts ---
while IFS= read -r TASK_LINE; do
  TASK_LINE="${TASK_LINE%$'\r'}"
  [ -n "$TASK_LINE" ] || continue

  TASK_ID="$(echo "$TASK_LINE" | jq -r '.task_id')"
  TASK_MODS="$(echo "$TASK_LINE" | jq -c '.modules_affected // []')"

  # Collect guards_created and model_updated from results for this task's modules
  GUARDS_CREATED="[]"
  MODEL_UPDATED="[]"
  EDGES_UPDATED="[]"

  while IFS= read -r TMOD; do
    TMOD="${TMOD%$'\r'}"
    [ -n "$TMOD" ] || continue
    RESULT="$(echo "$RESULTS" | jq --arg m "$TMOD" '.[$m] // null')"
    if [ "$RESULT" != "null" ]; then
      GUARDS_CREATED="$(echo "$GUARDS_CREATED" "$RESULT" | jq -s '.[0] + (.[1].guards_created // []) | unique')"
      MODEL_UPDATED="$(echo "$MODEL_UPDATED" | jq --arg m "$TMOD" '. + [$m] | unique')"
      EDGES_UPDATED="$(echo "$EDGES_UPDATED" "$RESULT" | jq -s '
        .[0] + ([.[1].semantic_edges // [] | .[] | [.from, .to]] ) | unique
      ')"
    fi
  done <<< "$(echo "$TASK_MODS" | jq -r '.[]' | tr -d '\r')"

  # Emit receipt. Status is reclassified to BLOCKED based on two signals:
  #   (primary, mechanical) test_results.failed > 0 → BLOCKED
  #   (secondary, heuristic) summary contains a blocker keyword (WIP,
  #     broken, stuck, giving up, gave up — case-insensitive, flanked
  #     by non-letter chars or string boundaries so e.g. "WIP" matches
  #     but "WIPLine" / "wipro" / "unbroken" don't). jq's `\b` handling
  #     is inconsistent between test() and match(); the POSIX-style
  #     [^A-Za-z] flankers are reliable and the false-positive rejection
  #     is actually stronger.
  # Buffer entries arrive with status="SUCCESS" by default; this
  # reclassification populates blocked_diagnostics with a brief reason so
  # session-boot's UNRESOLVED block has something meaningful to display.
  # Build the receipt, then validate its schema before appending. Invalid
  # receipts are logged and skipped rather than silently corrupting
  # receipts.jsonl. If the validator is missing (e.g. partial install),
  # fall through to append — don't block receipt emission.
  RECEIPT_JSON="$(echo "$TASK_LINE" | jq -c \
    --argjson gc "$GUARDS_CREATED" \
    --argjson mu "$MODEL_UPDATED" \
    --argjson eu "$EDGES_UPDATED" '
    . as $t |
    (
      if (($t.test_results // {}) | (if type == "object" then (.failed // 0) else 0 end)) > 0 then
        { status: "BLOCKED",
          reason: "tests failed: \(($t.test_results.failed // 0))/\(($t.test_results.total // 0))" }
      elif (($t.summary // "") | test("(^|[^A-Za-z])(WIP|broken|stuck|giving up|gave up)([^A-Za-z]|$)"; "i")) then
        { status: "BLOCKED",
          reason: "commit-message blocker keyword in: \"\($t.summary // "")\"" }
      else
        { status: ($t.status // "SUCCESS"), reason: null }
      end
    ) as $class |
    {
      task_id: $t.task_id,
      timestamp: $t.timestamp,
      status: $class.status,
      modules_affected: $t.modules_affected,
      modified_files: $t.modified_files,
      test_results: $t.test_results,
      commit_hash: $t.commit_hash,
      guards_fired: $t.guards_fired,
      guards_disputed: $t.guards_disputed,
      guards_created: $gc,
      model_updated: $mu,
      edges_updated: $eu,
      blocked_diagnostics: (
        if $class.reason != null then $class.reason
        else $t.blocked_diagnostics
        end
      )
    }
  ')"

  if [ -f "$VALIDATE_SCHEMA" ] && ! echo "$RECEIPT_JSON" | bash "$VALIDATE_SCHEMA" receipt; then
    echo "kairoi sync-finalize: SKIPPING invalid receipt for task $TASK_ID" >&2
  else
    echo "$RECEIPT_JSON" >> "$RECEIPTS"
  fi
done <<< "$(echo "$TASKS_JSON" | jq -c '.[]' | tr -d '\r')"

# Rotate receipts: >200 lines → keep last 100
if [ -f "$RECEIPTS" ]; then
  RC="$(wc -l < "$RECEIPTS" | tr -d ' ')"
  if [ "$RC" -gt 200 ]; then
    tail -100 "$RECEIPTS" > "${RECEIPTS}.tmp" && mv "${RECEIPTS}.tmp" "$RECEIPTS"
  fi
fi

# --- Step 5: Clear buffer + write _deferred ---
> "$BUFFER"

UNREFLECTED_COUNT="$(echo "$UNREFLECTED_JSON" | jq 'length')"
if [ "$UNREFLECTED_COUNT" -gt 0 ]; then
  TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  jq -n -c \
    --arg ts "$TIMESTAMP" \
    --argjson mp "$UNREFLECTED_JSON" \
    '{ task_id: "_deferred", modules_pending: $mp, timestamp: $ts }' >> "$BUFFER"
fi

# --- Human-readable session summary ---
# Written to .kairoi/.session-summary.txt so the orchestrator (or the user
# via /kairoi:show) can surface it. Peace of mind needs to be visible.
SUMMARY_FILE="$STATE_DIR/.session-summary.txt"
RECEIPT_COUNT="$(echo "$TASKS_JSON" | jq 'length')"
MODULE_COUNT="$(echo "$REFLECTED_JSON" | jq 'length')"
BLOCKED_LIST="$(echo "$TASKS_JSON" | jq -r '[.[] | select(.status == "BLOCKED") | .task_id] | join(", ")')"
BLOCKED_COUNT="$(echo "$TASKS_JSON" | jq '[.[] | select(.status == "BLOCKED")] | length')"

# Aggregate guards created across all result files (the authoritative source).
GUARDS_CREATED_ALL="[]"
GUARDS_REMOVED_ALL="[]"
for RF_SUM in "$STATE_DIR"/.reflect-result-*.json; do
  [ -f "$RF_SUM" ] || continue
  GUARDS_CREATED_ALL="$(echo "$GUARDS_CREATED_ALL" | jq --slurpfile r "$RF_SUM" '. + ($r[0].guards_created // [])')"
  GUARDS_REMOVED_ALL="$(echo "$GUARDS_REMOVED_ALL" | jq --slurpfile r "$RF_SUM" '. + ($r[0].guards_removed // [])')"
done
# (Loop runs BEFORE cleanup below so it sees the files.)

GUARDS_CREATED_COUNT="$(echo "$GUARDS_CREATED_ALL" | jq 'length')"
GUARDS_REMOVED_COUNT="$(echo "$GUARDS_REMOVED_ALL" | jq 'length')"

# Test results rollup across tasks
TEST_PASSED="$(echo "$TASKS_JSON" | jq '[.[] | .test_results // {} | .passed // 0] | add // 0')"
TEST_FAILED="$(echo "$TASKS_JSON" | jq '[.[] | .test_results // {} | .failed // 0] | add // 0')"

MODULES_LIST="$(echo "$REFLECTED_JSON" | jq -r 'join(", ")')"

{
  echo "This session: $RECEIPT_COUNT task(s) reflected across $MODULE_COUNT module(s)."
  [ -n "$MODULES_LIST" ] && echo "  modules: $MODULES_LIST"
  if [ "$BLOCKED_COUNT" -gt 0 ]; then
    echo "  BLOCKED ($BLOCKED_COUNT): $BLOCKED_LIST"
  fi
  if [ "$GUARDS_CREATED_COUNT" -gt 0 ] || [ "$GUARDS_REMOVED_COUNT" -gt 0 ]; then
    echo "  guards: +$GUARDS_CREATED_COUNT created, -$GUARDS_REMOVED_COUNT removed"
  fi
  if [ "$TEST_PASSED" -gt 0 ] || [ "$TEST_FAILED" -gt 0 ]; then
    echo "  tests: ${TEST_PASSED} passed, ${TEST_FAILED} failed"
  fi
  if [ "$UNREFLECTED_COUNT" -gt 0 ]; then
    echo "  deferred (retry next sync): $(echo "$UNREFLECTED_JSON" | jq -r 'join(", ")')"
  fi
} > "$SUMMARY_FILE"

# --- Cleanup transient files ---
rm -f "$MANIFEST"
rm -f "$STATE_DIR"/.reflect-result-*.json
rm -rf "$STATE_DIR/.pre-sync"

# --- Output ---
echo "kairoi sync-finalize: $RECEIPT_COUNT receipt(s) emitted, $MODULE_COUNT module(s) finalized"
if [ "$UNREFLECTED_COUNT" -gt 0 ]; then
  echo "  deferred: $(echo "$UNREFLECTED_JSON" | jq -r 'join(", ")') (will retry next sync)"
fi
echo ""
cat "$SUMMARY_FILE"
