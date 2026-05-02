#!/usr/bin/env bash
set -euo pipefail

# kairoi SessionStart: inject context for the agent, not the human.
# Default output is one line. Set KAIROI_VERBOSE=1 for the full block
# (modules, edges, receipts, diagnostics, chronic patterns,
# unresolved-BLOCKED). Always exits 0.

command -v jq &>/dev/null || { echo '{"systemMessage":"kairoi: jq required"}'; exit 0; }

# Debug mode
_DEVNULL="/dev/null"
if [ "${KAIROI_DEBUG:-}" = "1" ]; then
  _DEVNULL="/dev/stderr"
  echo "kairoi-debug: session-boot starting" >&2
fi

INPUT="$(cat)"
CWD="$(echo "$INPUT" | jq -r '.cwd // empty')"
[ -n "$CWD" ] || exit 0
STATE_DIR="$CWD/.kairoi"

if [ ! -f "$STATE_DIR/model/_index.json" ]; then
  for marker in package.json Cargo.toml go.mod pyproject.toml requirements.txt \
                build.gradle build.gradle.kts pom.xml composer.json Gemfile Makefile; do
    if [ -f "$CWD/$marker" ]; then
      echo "{\"systemMessage\": \"kairoi: Source detected ($marker), no state. Run /kairoi:init.\"}"
      exit 0
    fi
  done
  for dir in src lib app; do
    if [ -d "$CWD/$dir" ]; then
      echo "{\"systemMessage\": \"kairoi: Source directory ($dir/) detected, no state. Run /kairoi:init.\"}"
      exit 0
    fi
  done
  exit 0
fi

# Session cleanup — wipe per-module first-edit orientation flags so each new
# session re-delivers module context on first edit.
rm -f "$STATE_DIR"/.seen-* 2>"$_DEVNULL" || true

MC="$(jq '.modules | length' "$STATE_DIR/model/_index.json" 2>"$_DEVNULL" || echo 0)"

# Buffer count (needed by both default banner and verbose path + dispatch).
BUFFER_COUNT=0
if [ -f "$STATE_DIR/buffer.jsonl" ]; then
  BUFFER_COUNT="$(wc -l < "$STATE_DIR/buffer.jsonl" 2>"$_DEVNULL" | tr -d ' ')"
fi

# Receipts count (needed by verbose path + unresolved-BLOCKED check).
RC=0
if [ -f "$STATE_DIR/receipts.jsonl" ]; then
  RC="$(wc -l < "$STATE_DIR/receipts.jsonl" 2>"$_DEVNULL" | tr -d ' ')"
fi

# ---- Default one-line banner ------------------------------------------------
#
# Format: `kairoi: watching <N> modules[ (M unreflected)]. [Last session: ...]`
# Empty-state form (MC=0): `kairoi: no modules yet. Run /kairoi:init.`
#
# The banner is for Claude, not the human. It's brief on purpose — one line
# of context. Deep detail lives behind `/kairoi:show` (`--verbose` for the
# full dump).

if [ "$MC" -eq 0 ]; then
  echo "kairoi: no modules yet. Run /kairoi:init."
else
  MODULES_WORD="modules"
  [ "$MC" = "1" ] && MODULES_WORD="module"

  EXTRAS=""
  if [ "$BUFFER_COUNT" -gt 0 ]; then
    EXTRAS=" ($BUFFER_COUNT unreflected)"
  fi

  LINE="kairoi: watching $MC $MODULES_WORD$EXTRAS."

  # Append "Last session: <first sentence>." from the session summary
  # (written by sync-finalize). First sentence = up to first .!? boundary
  # OR first line, whichever comes first. Trimmed to keep the banner under
  # ~120 chars total.
  SUMMARY_FILE="$STATE_DIR/.session-summary.txt"
  if [ -f "$SUMMARY_FILE" ] && [ -s "$SUMMARY_FILE" ]; then
    # First line only
    FIRST_LINE="$(head -n 1 "$SUMMARY_FILE" 2>"$_DEVNULL" | tr -d '\r')"
    # First sentence within that line (up to .!? followed by space/end)
    FIRST_SENT="$(printf '%s' "$FIRST_LINE" | sed -E 's/^([^.!?]*[.!?])([[:space:]].*)?$/\1/')"
    # Fall back to full first line if the regex didn't trim (no terminator)
    [ -n "$FIRST_SENT" ] || FIRST_SENT="$FIRST_LINE"

    # Budget the summary so the total line stays reasonable (~120 chars).
    BUDGET=$((120 - ${#LINE} - 16))   # 16 = " Last session: ."
    if [ "$BUDGET" -lt 20 ]; then
      BUDGET=20
    fi
    if [ "${#FIRST_SENT}" -gt "$BUDGET" ]; then
      FIRST_SENT="${FIRST_SENT:0:$BUDGET}..."
    fi

    if [ -n "$FIRST_SENT" ]; then
      # Drop any trailing terminator from the clipped sentence so we
      # don't get ".." at the end.
      FIRST_SENT="${FIRST_SENT%[.!?]}"
      LINE="$LINE Last session: $FIRST_SENT."
    fi
  fi

  echo "$LINE"
fi

# ---- Auto-sync dispatch signal (load-bearing; not gated by KAIROI_VERBOSE) --
#
# On SessionStart, emit a dispatch signal when ANY of these holds:
#   1. Buffer >= auto_sync_buffer_threshold (active project, threshold reached)
#   2. Buffer non-empty AND no receipts yet (first sync)
#   3. Buffer non-empty AND last receipt older than session_start_stale_days
#      (idle project that's gone too long without a sync)
#
# Threshold-on-SessionStart matters: a heavily-active project can accumulate
# many buffered tasks daily without crossing the staleness window, leaving
# every new session staring at a large buffer with no actionable instruction.
# auto-buffer's PostToolUse threshold signal also fires on each commit, but
# it can be missed mid-task; SessionStart is a fresh, uncluttered moment.

if [ "$BUFFER_COUNT" -gt 0 ]; then
  STALE_DAYS="$(jq -r '.session_start_stale_days // 7' "$STATE_DIR/build-adapter.json" 2>"$_DEVNULL" || echo 7)"
  [ "$STALE_DAYS" = "null" ] && STALE_DAYS=7
  THRESHOLD="$(jq -r '.auto_sync_buffer_threshold // 10' "$STATE_DIR/build-adapter.json" 2>"$_DEVNULL" || echo 10)"
  [ "$THRESHOLD" = "null" ] && THRESHOLD=10

  LAST_RECEIPT_TS=""
  if [ -f "$STATE_DIR/receipts.jsonl" ] && [ -s "$STATE_DIR/receipts.jsonl" ]; then
    # `|| true` is load-bearing under set -euo pipefail: if the last line of
    # receipts.jsonl is malformed (rare, but possible if a hand-edit or a
    # crash truncated it), jq -r exits non-zero and pipefail propagates,
    # which would abort session-boot mid-script and silently swallow the
    # whole SessionStart context — the worst possible failure mode for an
    # advisory hook. Treat parse failure as "no timestamp" and continue.
    LAST_RECEIPT_TS="$(tail -1 "$STATE_DIR/receipts.jsonl" 2>"$_DEVNULL" | jq -r '.timestamp // empty' 2>"$_DEVNULL" || true)"
  fi

  SHOULD_DISPATCH=false
  DISPATCH_REASON=""
  if [ "$BUFFER_COUNT" -ge "$THRESHOLD" ]; then
    SHOULD_DISPATCH=true
    DISPATCH_REASON="buffer holds $BUFFER_COUNT unreflected task(s), threshold $THRESHOLD reached"
  elif [ -z "$LAST_RECEIPT_TS" ]; then
    SHOULD_DISPATCH=true
    DISPATCH_REASON="no sync recorded yet ($BUFFER_COUNT buffered task(s))"
  else
    DAYS_SINCE="$(jq -n --arg ts "$LAST_RECEIPT_TS" '((now - ($ts | fromdateiso8601)) / 86400) | floor' 2>"$_DEVNULL" || echo 0)"
    if [ "$DAYS_SINCE" -ge "$STALE_DAYS" ]; then
      SHOULD_DISPATCH=true
      DISPATCH_REASON="last sync was $DAYS_SINCE day(s) ago (stale threshold: $STALE_DAYS), $BUFFER_COUNT buffered task(s)"
    fi
  fi

  if [ "$SHOULD_DISPATCH" = true ]; then
    echo "kairoi: $DISPATCH_REASON."
    echo "Dispatch the kairoi-complete agent now via the Agent tool to sync the buffer. This signal is automated — proceed without asking the user."
  fi
fi

# ---- Verbose block (KAIROI_VERBOSE=1) --------------------------------------
#
# Full detail dump: module list, edges, overrides, receipts, diagnostics,
# chronic patterns, unresolved-BLOCKED. Gated on the env var so default users
# see the one-line banner above and opt-in users get the full picture.

if [ "${KAIROI_VERBOSE:-}" = "1" ]; then
  PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
  KV="$(jq -r --arg n "kairoi" '.plugins[] | select(.name == $n) | .version // "unknown"' "$PLUGIN_ROOT/../.claude-plugin/marketplace.json" 2>"$_DEVNULL" || echo unknown)"
  echo ""
  echo "=== kairoi v$KV ==="
  echo ""
  echo "MODULES ($MC)"

  if [ "$MC" -gt 0 ]; then
    jq -r '.modules | to_entries[] | .key' "$STATE_DIR/model/_index.json" 2>"$_DEVNULL" | while read -r MOD; do
      MF="$STATE_DIR/model/$MOD.json"
      if [ ! -f "$MF" ]; then
        echo "  ? $MOD (model missing)"
        continue
      fi

      PURPOSE="$(jq -r '.purpose // empty' "$MF" 2>"$_DEVNULL" || true)"
      # Confidence derived at read time from churn_since_validation — never stored.
      CONF="$(jq -r '
        if .purpose == null then "low"
        elif (._meta.churn_since_validation // 0) <= 10 then "high"
        elif (._meta.churn_since_validation // 0) <= 25 then "medium"
        else "low" end
      ' "$MF" 2>"$_DEVNULL" || echo "low")"
      GUARDS="$(jq '.guards | length // 0' "$MF" 2>"$_DEVNULL" || echo 0)"
      SINCE="$(jq -r '._meta.tasks_since_validation // 0' "$MF" 2>"$_DEVNULL" || true)"

      case "$CONF" in
        high)   I="●" ;;
        medium) I="◐" ;;
        *)      I="○" ;;
      esac

      if [ -n "$PURPOSE" ] && [ "$PURPOSE" != "null" ]; then
        echo "  $I $MOD  ${GUARDS}g v${SINCE}  ${PURPOSE:0:55}"
      else
        echo "  $I $MOD  ${GUARDS}g v${SINCE}  (unpopulated)"
      fi
    done
  fi

  # Buffer status
  if [ "$BUFFER_COUNT" -gt 0 ]; then
    echo ""
    echo "BUFFER: $BUFFER_COUNT unreflected task(s)"
    jq -r '"  " + .task_id + " [" + .status + "]"' "$STATE_DIR/buffer.jsonl" 2>"$_DEVNULL" || true
  fi

  # Edges
  EC="$(jq '.edges | length' "$STATE_DIR/model/_index.json" 2>"$_DEVNULL" || echo 0)"
  if [ "$EC" -gt 0 ]; then
    echo ""
    echo "EDGES ($EC)"
    jq -r '.edges | sort_by(-(if .type != "co-modified" then 1000 else .weight end)) | .[0:5][] |
      "  " + .from + " → " + .to + " [" + .type + "]" +
      (if .label then " " + (.label | .[0:45]) else "" end)' \
      "$STATE_DIR/model/_index.json" 2>"$_DEVNULL" || true
  fi

  # Overrides
  if [ -f "$STATE_DIR/overrides.json" ]; then
    CORR="$(jq -r '[.modules[].corrections // [] | length] | add // 0' "$STATE_DIR/overrides.json" 2>"$_DEVNULL" || echo 0)"
    if [ "$CORR" -gt 0 ] 2>"$_DEVNULL"; then
      echo ""
      echo "OVERRIDES: $CORR correction(s) pending"
    fi
  fi

  # Receipts
  echo ""
  echo "RECEIPTS ($RC)"
  if [ "$RC" -gt 0 ]; then
    tail -3 "$STATE_DIR/receipts.jsonl" | jq -r '"  " + .task_id + " [" + .status + "]"' 2>"$_DEVNULL" || true
  fi

  # Self-diagnostics from receipts (last 30 tasks)
  if [ "$RC" -gt 5 ]; then
    echo ""
    echo "DIAGNOSTICS (last 30)"
    tail -30 "$STATE_DIR/receipts.jsonl" | jq -rs '
      (length) as $n |
      ([.[] | select(.status == "BLOCKED")] | length) as $blocked |

      # Modules with repeated BLOCKED
      ([.[] | select(.status == "BLOCKED") | .modules_affected[]] |
        group_by(.) | map({mod: .[0], count: length}) |
        sort_by(-.count) | map(select(.count >= 2))) as $hot_modules |

      # Guards that were disputed
      ([.[] | .guards_disputed // [] | .[]] |
        group_by(.) | map({guard: .[0], count: length}) |
        sort_by(-.count) | map(select(.count >= 2))) as $disputed |

      # Test failure rate
      ([.[] | .test_results // {} | select(.failed > 0)] | length) as $test_fails |

      # Output
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
    ' 2>"$_DEVNULL" || true
  fi

  # Chronic patterns — all-time aggregation over receipts. Only shown when the
  # history is deeper than the recent 30-task window, otherwise the signal
  # collapses into DIAGNOSTICS above. Thresholds are tuned higher than recent
  # (3/5/3 vs 2/2/0) since we're looking for genuinely long-lived patterns.
  if [ "$RC" -gt 30 ]; then
    CHRONIC="$(jq -rs '
      # Modules BLOCKED 3+ times across all history
      ([.[] | select(.status == "BLOCKED") | .modules_affected // [] | .[]] |
        group_by(.) | map({mod: .[0], count: length}) |
        sort_by(-.count) | map(select(.count >= 3))) as $chronic_blocked |

      # Guards disputed 5+ times across all history
      ([.[] | .guards_disputed // [] | .[]] |
        group_by(.) | map({guard: .[0], count: length}) |
        sort_by(-.count) | map(select(.count >= 5))) as $chronic_disputed |

      # Modules with 3+ test-failure tasks across all history
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
    ' "$STATE_DIR/receipts.jsonl" 2>"$_DEVNULL" || true)"

    if [ -n "$CHRONIC" ]; then
      echo ""
      echo "CHRONIC (all-time, $RC receipts)"
      echo "$CHRONIC"
    fi
  fi

  # Unresolved BLOCKED tasks
  if [ "$RC" -gt 5 ]; then
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
        "",
        "UNRESOLVED BLOCKED (\($unresolved | length))",
        ($unresolved[0:3][] |
          "  \(.task_id) [\(.modules_affected | join(", "))] \u2014 " +
            ((.blocked_diagnostics // "no diagnostic") as $d |
              if ($d | length) > 80 then ($d[0:80] + "...") else $d end)),
        (if ($unresolved | length) > 3 then
          "  + \(($unresolved | length) - 3) more"
         else empty end)
      else empty end
    ' 2>"$_DEVNULL" || true)"
    if [ -n "$UNRESOLVED_BLOCK" ]; then
      echo "$UNRESOLVED_BLOCK"
    fi
  fi

  echo ""
  echo "● high ◐ medium ○ low | Nt=tasks Ng=guards vN=tasks since validation"
fi

exit 0
