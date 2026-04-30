#!/usr/bin/env bash
# kairoi show: human-readable dump of the current model.
#
# For the human sitting next to Claude, not for Claude. Peace of mind is
# invisible unless users can see what kairoi is tracking — this is the
# window. Every piece of state has to be reachable without opening JSON.
#
# Usage:
#   show.sh                     # all modules, edges, recent activity, overrides, buffer
#   show.sh <module>            # just that module's detail
#   show.sh --verbose           # default output + diagnostics, chronic, unresolved
#   show.sh --verbose <module>  # per-module detail + verbose tail

set -u

command -v jq &>/dev/null || { echo "kairoi: jq required" >&2; exit 1; }

STATE_DIR=".kairoi"
INDEX="$STATE_DIR/model/_index.json"

# --- Flag parsing ----------------------------------------------------------
# Supports: `show`, `show <module>`, `show --verbose [<module>]`,
# `show -v [<module>]`, `show <module> --verbose`. `--` ends flag parsing.
VERBOSE=0
FILTER=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --verbose|-v)
      VERBOSE=1
      shift
      ;;
    --)
      shift
      if [ "$#" -gt 0 ]; then
        FILTER="$1"
        shift
      fi
      ;;
    -*)
      echo "kairoi: unknown flag '$1' (try --verbose)" >&2
      exit 1
      ;;
    *)
      if [ -z "$FILTER" ]; then
        FILTER="$1"
      fi
      shift
      ;;
  esac
done

if [ ! -f "$INDEX" ]; then
  echo "kairoi: no .kairoi/ state found. Run /kairoi:init to bootstrap."
  exit 1
fi

echo "=== kairoi model ==="
echo ""

# Resolve module list
if [ -n "$FILTER" ]; then
  MODULES="$FILTER"
else
  MODULES="$(jq -r '.modules | keys[]' "$INDEX" 2>/dev/null | tr -d '\r')"
fi

HAS_ANY=false
while IFS= read -r MOD; do
  MOD="${MOD%$'\r'}"
  [ -n "$MOD" ] || continue

  MF="$STATE_DIR/model/$MOD.json"
  if [ ! -f "$MF" ]; then
    echo "  $MOD  (model file missing — run /kairoi:audit $MOD)"
    continue
  fi
  HAS_ANY=true

  PURPOSE="$(jq -r '.purpose // "(unpopulated)"' "$MF" | tr -d '\r')"
  # Compute confidence from staleness — never read a persisted value.
  # churn_since_validation weights by files touched per task, so a
  # 10-file refactor decays confidence faster than 10 trivial edits.
  CONF="$(jq -r '
    if .purpose == null then "low"
    elif (._meta.churn_since_validation // 0) <= 10 then "high"
    elif (._meta.churn_since_validation // 0) <= 25 then "medium"
    else "low" end
  ' "$MF" | tr -d '\r')"
  SINCE="$(jq -r '._meta.tasks_since_validation // 0' "$MF" | tr -d '\r')"
  CHURN_VAL="$(jq -r '._meta.churn_since_validation // empty' "$MF" 2>/dev/null | tr -d '\r' || true)"
  LAST_V="$(jq -r '._meta.last_validated // "never"' "$MF" | tr -d '\r')"
  GCOUNT="$(jq '.guards | length' "$MF" 2>/dev/null || echo 0)"
  PCOUNT="$(jq '.known_patterns | length' "$MF" 2>/dev/null || echo 0)"
  DCOUNT="$(jq '.dependencies | length' "$MF" 2>/dev/null || echo 0)"

  case "$CONF" in
    high)   GLYPH="●" ;;
    medium) GLYPH="◐" ;;
    *)      GLYPH="○" ;;
  esac

  GUARD_WORD="guards"
  [ "$GCOUNT" = "1" ] && GUARD_WORD="guard"

  CHURN_INFO=""
  [ -n "$CHURN_VAL" ] && CHURN_INFO=" ch=$CHURN_VAL"
  echo "$MOD  $GLYPH $CONF  (v$SINCE${CHURN_INFO} since $LAST_V, $GCOUNT $GUARD_WORD)"
  echo "  $PURPOSE"

  EP="$(jq -r '.entry_points // [] | join(", ")' "$MF" 2>/dev/null | tr -d '\r')"
  [ -n "$EP" ] && echo "  entry: $EP"

  if [ "$GCOUNT" -gt 0 ]; then
    echo "  guards:"
    jq -r '.guards[] |
      "    [\(.source_task)] \(.check)" +
      (if (.confirmed // 0) > 0 or (.disputed // 0) > 0 then
        "  (" +
        ([
          (if (.confirmed // 0) > 0 then "confirmed×\(.confirmed)" else empty end),
          (if (.disputed // 0) > 0 then "disputed×\(.disputed)" else empty end)
        ] | join(", ")) +
        ")"
      else "" end)
    ' "$MF" 2>/dev/null
  fi

  if [ "$PCOUNT" -gt 0 ]; then
    echo "  patterns:"
    jq -r '.known_patterns[] | "    - " + .' "$MF" 2>/dev/null
  fi

  NICOUNT="$(jq '.negative_invariants | length' "$MF" 2>/dev/null || echo 0)"
  if [ "$NICOUNT" -gt 0 ] 2>/dev/null; then
    echo "  not:"
    jq -r '.negative_invariants[] | "    - " + .' "$MF" 2>/dev/null
  fi

  if [ "$DCOUNT" -gt 0 ]; then
    DEPS="$(jq -r '.dependencies | join(", ")' "$MF" 2>/dev/null)"
    echo "  deps: $DEPS"
  fi

  echo ""
done <<< "$MODULES"

if [ "$HAS_ANY" = false ] && [ -n "$FILTER" ]; then
  echo "(no module named '$FILTER')"
  exit 1
fi

# The rest (edges, activity, overrides, buffer) only when not filtering.
# --verbose on a filtered view still only renders that one module's detail;
# system-wide sections below are suppressed because they're not about the
# filtered module.
if [ -n "$FILTER" ]; then
  exit 0
fi

# Edges
EDGE_COUNT="$(jq '.edges | length' "$INDEX" 2>/dev/null || echo 0)"
if [ "$EDGE_COUNT" -gt 0 ]; then
  echo "EDGES ($EDGE_COUNT)"
  jq -r '.edges |
    sort_by(-(if .type != "co-modified" then 1000 else (.weight // 0) end))[0:10][] |
    "  \(.from) → \(.to) [\(.type)" +
    (if .type == "co-modified" and (.weight // 0) > 1 then " ×\(.weight)" else "" end) +
    "]" +
    (if .label then "  " + (.label | .[0:70]) else "" end)
  ' "$INDEX" 2>/dev/null
  if [ "$EDGE_COUNT" -gt 10 ]; then
    echo "  ... + $((EDGE_COUNT - 10)) more"
  fi
  echo ""
fi

# Recent activity (receipts = completed + reflected tasks)
RC=0
if [ -f "$STATE_DIR/receipts.jsonl" ] && [ -s "$STATE_DIR/receipts.jsonl" ]; then
  RC="$(wc -l < "$STATE_DIR/receipts.jsonl" | tr -d ' ')"
  echo "RECENT ACTIVITY ($RC total, showing last 5)"
  tail -5 "$STATE_DIR/receipts.jsonl" | jq -r '
    "  \(.timestamp | .[0:10])  [\(.status)] \(.task_id) — " +
    ((.modules_affected // []) | join(", "))
  ' 2>/dev/null
  echo ""
fi

# Recent guard fires (mechanical protection the user can actually see happening)
if [ -f "$STATE_DIR/session.log" ] && [ -s "$STATE_DIR/session.log" ]; then
  GC="$(wc -l < "$STATE_DIR/session.log" | tr -d ' ')"
  echo "RECENT GUARD FIRES ($GC total, showing last 5)"
  tail -5 "$STATE_DIR/session.log" | sed 's/^/  /'
  echo ""
fi

# Overrides
if [ -f "$STATE_DIR/overrides.json" ]; then
  OV_LINES="$(jq -r '.modules // {} | to_entries[] |
    . as $e |
    ([
      ($e.value.pinned // {} | keys | if length > 0 then "pinned: \(join(", "))" else empty end),
      ($e.value.corrections // [] | if length > 0 then "\(length) correction(s) pending" else empty end),
      ($e.value.protected_guards // [] | if length > 0 then "protected: \(join(", "))" else empty end)
    ] | map(select(. != null))) as $parts |
    if ($parts | length) > 0 then
      "  [\($e.key)] " + ($parts | join("; "))
    else empty end
  ' "$STATE_DIR/overrides.json" 2>/dev/null)"

  if [ -n "$OV_LINES" ]; then
    echo "OVERRIDES"
    echo "$OV_LINES"
    echo ""
  fi
fi

# Buffer status
if [ -f "$STATE_DIR/buffer.jsonl" ] && [ -s "$STATE_DIR/buffer.jsonl" ]; then
  BCOUNT="$(wc -l < "$STATE_DIR/buffer.jsonl" | tr -d ' ')"
  BUF_LAST_SYNC=""
  if [ -f "$STATE_DIR/receipts.jsonl" ] && [ -s "$STATE_DIR/receipts.jsonl" ]; then
    BUF_LAST_SYNC="$(tail -1 "$STATE_DIR/receipts.jsonl" 2>/dev/null | jq -r '.timestamp // empty' 2>/dev/null | cut -c1-10 || true)"
  fi
  if [ -n "$BUF_LAST_SYNC" ]; then
    echo "BUFFER ($BCOUNT unreflected — last reflection: $BUF_LAST_SYNC)"
  else
    echo "BUFFER ($BCOUNT unreflected — never reflected)"
  fi
  jq -r '"  \(.task_id) [\(.status)]"' "$STATE_DIR/buffer.jsonl" 2>/dev/null
  echo ""
fi

# --- Verbose analytics (--verbose only) ------------------------------------
# DIAGNOSTICS over the last 30 receipts, CHRONIC patterns all-time,
# UNRESOLVED BLOCKED tasks. Gated on --verbose so the default output
# stays tight.
if [ "$VERBOSE" = "1" ] && [ "$RC" -gt 5 ]; then
  echo "DIAGNOSTICS (last 30)"
  tail -30 "$STATE_DIR/receipts.jsonl" | jq -rs '
    (length) as $n |
    ([.[] | select(.status == "BLOCKED")] | length) as $blocked |
    ([.[] | select(.status == "BLOCKED") | .modules_affected[]] |
      group_by(.) | map({mod: .[0], count: length}) |
      sort_by(-.count) | map(select(.count >= 2))) as $hot_modules |
    ([.[] | .guards_disputed // [] | .[]] |
      group_by(.) | map({guard: .[0], count: length}) |
      sort_by(-.count) | map(select(.count >= 2))) as $disputed |
    ([.[] | .test_results // {} | select(.failed > 0)] | length) as $test_fails |
    (if $blocked > 0 then
      "  blocked: \($blocked)/\($n) tasks (\($blocked * 100 / $n | floor)%)"
    else empty end),
    (if ($hot_modules | length) > 0 then
      "  repeat-blocked modules: " + ($hot_modules | map(.mod + "×" + (.count|tostring)) | join(", "))
    else empty end),
    (if ($disputed | length) > 0 then
      "  frequently disputed guards: " + ($disputed | map(.guard + "×" + (.count|tostring)) | join(", "))
    else empty end),
    (if $test_fails > 0 then
      "  test failures: \($test_fails)/\($n) tasks"
    else empty end),
    (if $blocked == 0 and ($disputed | length) == 0 and $test_fails == 0 then
      "  health: clean"
    else empty end)
  ' 2>/dev/null
  echo ""

  if [ "$RC" -gt 30 ]; then
    CHRONIC="$(jq -rs '
      ([.[] | select(.status == "BLOCKED") | .modules_affected // [] | .[]] |
        group_by(.) | map({mod: .[0], count: length}) |
        sort_by(-.count) | map(select(.count >= 3))) as $chronic_blocked |
      ([.[] | .guards_disputed // [] | .[]] |
        group_by(.) | map({guard: .[0], count: length}) |
        sort_by(-.count) | map(select(.count >= 5))) as $chronic_disputed |
      ([.[] | select((.test_results // {}).failed // 0 > 0) |
        .modules_affected // [] | .[]] |
        group_by(.) | map({mod: .[0], count: length}) |
        sort_by(-.count) | map(select(.count >= 3))) as $chronic_fails |
      (if ($chronic_blocked | length) > 0 then
        "  repeat-blocked (all-time): " +
          ($chronic_blocked | map(.mod + "×" + (.count|tostring)) | join(", "))
      else empty end),
      (if ($chronic_disputed | length) > 0 then
        "  chronically disputed: " +
          ($chronic_disputed | map(.guard + "×" + (.count|tostring)) | join(", ")) +
          " — review on next audit"
      else empty end),
      (if ($chronic_fails | length) > 0 then
        "  test-failure-prone: " +
          ($chronic_fails | map(.mod + "×" + (.count|tostring)) | join(", "))
      else empty end)
    ' "$STATE_DIR/receipts.jsonl" 2>/dev/null)"

    if [ -n "$CHRONIC" ]; then
      echo "CHRONIC (all-time, $RC receipts)"
      echo "$CHRONIC"
      echo ""
    fi
  fi

  UNRESOLVED_BLOCK="$(tail -30 "$STATE_DIR/receipts.jsonl" | jq -rs '
    [.[] | select(.status == "BLOCKED")] as $blocked |
    [.[] | select(.status == "SUCCESS")] as $successes |
    [$blocked[] |
      . as $b |
      ([$successes[] |
        select(.timestamp > $b.timestamp) |
        select(any(.modules_affected[]; . as $m | $b.modules_affected | any(. == $m)))
      ] | length) as $resolved |
      select($resolved == 0)
    ] | sort_by(.timestamp) | reverse | . as $unresolved |
    if ($unresolved | length) > 0 then
      "UNRESOLVED BLOCKED (\($unresolved | length))",
      ($unresolved[0:3][] |
        "  \(.task_id) [\(.modules_affected | join(", "))] \u2014 " +
          ((.blocked_diagnostics // "no diagnostic") as $d |
            if ($d | length) > 80 then ($d[0:80] + "...") else $d end)),
      (if ($unresolved | length) > 3 then
        "  + \(($unresolved | length) - 3) more"
       else empty end)
    else empty end
  ' 2>/dev/null)"
  if [ -n "$UNRESOLVED_BLOCK" ]; then
    echo "$UNRESOLVED_BLOCK"
    echo ""
  fi
fi

# Last sync's summary (regenerated each sync)
if [ -f "$STATE_DIR/.session-summary.txt" ] && [ -s "$STATE_DIR/.session-summary.txt" ]; then
  echo "LAST SYNC"
  sed 's/^/  /' "$STATE_DIR/.session-summary.txt"
  echo ""
fi

echo "● high  ◐ medium  ○ low    vN = tasks since last validation"
