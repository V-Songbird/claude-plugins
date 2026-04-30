#!/usr/bin/env bash
set -euo pipefail

# kairoi doctor: validate .kairoi/ state file integrity.
# Structural checks only — no semantic analysis (use kairoi-audit for that).
# Exits 0 with summary on stdout.

command -v jq &>/dev/null || { echo "kairoi: jq required" >&2; exit 1; }

# Debug mode
_DEVNULL="/dev/null"
if [ "${KAIROI_DEBUG:-}" = "1" ]; then
  _DEVNULL="/dev/stderr"
  echo "kairoi-debug: doctor starting" >&2
fi

STATE_DIR=".kairoi"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      cat <<'EOF'
Usage: doctor.sh

Run structural integrity checks on .kairoi/ state files.
EOF
      exit 0
      ;;
    *) echo "kairoi doctor: unknown arg '$1' (try --help)" >&2; exit 1 ;;
  esac
done

PASS=0
FAIL=0

ok() {
  echo "kairoi: ✓ $1"
  PASS=$((PASS + 1))
}

problem() {
  echo "kairoi: ✗ $1"
  FAIL=$((FAIL + 1))
}

# --- Pre-check: does .kairoi/ exist? ---
if [ ! -d "$STATE_DIR" ]; then
  problem "no .kairoi/ directory — run /kairoi:init first"
  echo ""
  echo "0/1 checks passed, 1 problem found."
  exit 0
fi

# --- Check 1: build-adapter.json ---
BA="$STATE_DIR/build-adapter.json"
if [ ! -f "$BA" ]; then
  problem "build-adapter.json missing — run /kairoi:init"
else
  if ! jq . "$BA" > /dev/null 2>"$_DEVNULL"; then
    problem "build-adapter.json is invalid JSON — fix syntax or re-run /kairoi:init"
  else
    BA_ERRS=""
    [ "$(jq 'has("kairoi_version")' "$BA")" = "true" ] || BA_ERRS="${BA_ERRS}kairoi_version, "
    [ "$(jq 'has("stack")' "$BA")" = "true" ] || BA_ERRS="${BA_ERRS}stack, "
    [ "$(jq 'has("source_dirs")' "$BA")" = "true" ] || BA_ERRS="${BA_ERRS}source_dirs, "
    if [ -n "$BA_ERRS" ]; then
      problem "build-adapter.json missing fields: ${BA_ERRS%, } — re-run /kairoi:init"
    else
      ok "build-adapter.json valid"
    fi
  fi
fi

# --- Check 2: test command exists ---
if [ -f "$BA" ] && jq . "$BA" > /dev/null 2>"$_DEVNULL"; then
  TEST_CMD="$(jq -r '.test // empty' "$BA" 2>"$_DEVNULL")"
  if [ -n "$TEST_CMD" ]; then
    # Extract the first word (the executable)
    TEST_BIN="$(echo "$TEST_CMD" | awk '{print $1}')"
    if command -v "$TEST_BIN" &>/dev/null || [ -f "node_modules/.bin/$TEST_BIN" ]; then
      ok "test command exists ($TEST_CMD)"
    else
      problem "test command '$TEST_CMD' — '$TEST_BIN' not found in PATH — fix build-adapter.json test field or install the tool"
    fi
  else
    ok "test command not configured (optional)"
  fi
fi

# --- Check 3: _index.json ---
INDEX="$STATE_DIR/model/_index.json"
INDEX_VALID=false
if [ ! -f "$INDEX" ]; then
  problem "_index.json missing — run /kairoi:init"
else
  if ! jq . "$INDEX" > /dev/null 2>"$_DEVNULL"; then
    problem "_index.json is invalid JSON — fix syntax or re-run /kairoi:init"
  else
    IDX_ERRS=""
    [ "$(jq 'has("modules")' "$INDEX")" = "true" ] || IDX_ERRS="${IDX_ERRS}modules, "
    [ "$(jq 'has("edges")' "$INDEX")" = "true" ] || IDX_ERRS="${IDX_ERRS}edges, "
    if [ -n "$IDX_ERRS" ]; then
      problem "_index.json missing fields: ${IDX_ERRS%, }"
    else
      ok "_index.json valid"
      INDEX_VALID=true
    fi
  fi
fi

# --- Check 4: module file consistency ---
if [ "$INDEX_VALID" = true ]; then
  CONSISTENCY_OK=true

  # Every key in _index.json should have a model file
  while IFS= read -r MOD; do
    [ -n "$MOD" ] || continue
    if [ ! -f "$STATE_DIR/model/${MOD}.json" ]; then
      problem "module '$MOD' in _index.json but model/${MOD}.json missing — run /kairoi:audit $MOD"
      CONSISTENCY_OK=false
    fi
  done < <(jq -r '.modules | keys[]' "$INDEX" 2>"$_DEVNULL" | tr -d '\r')

  # Every model file should have an _index entry
  for MF in "$STATE_DIR"/model/*.json; do
    [ -f "$MF" ] || continue
    BASENAME="$(basename "$MF" .json)"
    [ "$BASENAME" = "_index" ] && continue
    HAS="$(jq --arg m "$BASENAME" 'has("modules") and (.modules | has($m))' "$INDEX" 2>"$_DEVNULL")"
    if [ "$HAS" != "true" ]; then
      problem "model/${BASENAME}.json exists but not in _index.json — add to _index or remove the file"
      CONSISTENCY_OK=false
    fi
  done

  [ "$CONSISTENCY_OK" = true ] && ok "module files match _index.json"
fi

# --- Check 5: module file validity + Check 6: guard validity ---
if [ "$INDEX_VALID" = true ]; then
  while IFS= read -r MOD; do
    [ -n "$MOD" ] || continue
    MF="$STATE_DIR/model/${MOD}.json"
    [ -f "$MF" ] || continue

    if ! jq . "$MF" > /dev/null 2>"$_DEVNULL"; then
      problem "model/${MOD}.json is invalid JSON — fix syntax or run /kairoi:audit $MOD"
      continue
    fi

    # _meta checks
    META_ERRS=""
    HAS_GUARDS="$(jq 'has("guards") and (.guards | type == "array")' "$MF" 2>"$_DEVNULL")"
    [ "$HAS_GUARDS" = "true" ] || META_ERRS="${META_ERRS}guards (missing or not array), "

    HAS_META="$(jq 'has("_meta")' "$MF" 2>"$_DEVNULL")"
    if [ "$HAS_META" = "true" ]; then
      # Confidence is derived at read time from tasks_since_validation,
      # never persisted.

      VALIDATED="$(jq -r '._meta.last_validated // "null"' "$MF" 2>"$_DEVNULL")"
      if [ "$VALIDATED" != "null" ]; then
        if ! echo "$VALIDATED" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
          META_ERRS="${META_ERRS}_meta.last_validated is '$VALIDATED' (expected YYYY-MM-DD), "
        fi
      fi

      TSV="$(jq '._meta.tasks_since_validation // -1' "$MF" 2>"$_DEVNULL")"
      if [ "$TSV" -lt 0 ] 2>"$_DEVNULL"; then
        META_ERRS="${META_ERRS}_meta.tasks_since_validation is negative or missing, "
      fi
    else
      META_ERRS="${META_ERRS}_meta missing, "
    fi

    if [ -n "$META_ERRS" ]; then
      problem "model/${MOD}.json: ${META_ERRS%, } — edit .kairoi/model/${MOD}.json or run /kairoi:audit $MOD"
    else
      ok "model/${MOD}.json valid"
    fi

    # Guard checks
    if [ "$HAS_GUARDS" = "true" ]; then
      GCOUNT="$(jq '.guards | length' "$MF" 2>"$_DEVNULL" || echo 0)"
      GUARD_ERRS=0
      for i in $(seq 0 $((GCOUNT - 1))); do
        GERR=""
        TF="$(jq -r --argjson i "$i" '.guards[$i].trigger_files // [] | length' "$MF" 2>"$_DEVNULL")"
        [ "$TF" -gt 0 ] 2>"$_DEVNULL" || GERR="empty trigger_files"

        ST="$(jq -r --argjson i "$i" '.guards[$i].source_task // ""' "$MF" 2>"$_DEVNULL")"
        [ -n "$ST" ] || GERR="${GERR}${GERR:+, }empty source_task"

        CK="$(jq -r --argjson i "$i" '.guards[$i].check // ""' "$MF" 2>"$_DEVNULL")"
        [ -n "$CK" ] || GERR="${GERR}${GERR:+, }empty check"

        if [ -n "$GERR" ]; then
          problem "model/${MOD}.json guard[$i]: $GERR — edit .kairoi/model/${MOD}.json"
          GUARD_ERRS=$((GUARD_ERRS + 1))
        fi
      done
      [ "$GUARD_ERRS" -eq 0 ] && [ "$GCOUNT" -gt 0 ] && ok "model/${MOD}.json $GCOUNT guard(s) valid"
    fi
  done < <(jq -r '.modules | keys[]' "$INDEX" 2>"$_DEVNULL" | tr -d '\r')
fi

# --- Check 7: edge validity ---
if [ "$INDEX_VALID" = true ]; then
  EDGE_COUNT="$(jq '.edges | length' "$INDEX" 2>"$_DEVNULL" || echo 0)"
  EDGE_ERRS=0
  for i in $(seq 0 $((EDGE_COUNT - 1))); do
    FROM="$(jq -r --argjson i "$i" '.edges[$i].from // ""' "$INDEX" 2>"$_DEVNULL")"
    TO="$(jq -r --argjson i "$i" '.edges[$i].to // ""' "$INDEX" 2>"$_DEVNULL")"
    TYPE="$(jq -r --argjson i "$i" '.edges[$i].type // ""' "$INDEX" 2>"$_DEVNULL")"

    EERR=""
    if [ -n "$FROM" ]; then
      HAS_FROM="$(jq --arg m "$FROM" '.modules | has($m)' "$INDEX" 2>"$_DEVNULL")"
      [ "$HAS_FROM" = "true" ] || EERR="from '$FROM' not in modules"
    else
      EERR="missing from"
    fi

    if [ -n "$TO" ]; then
      HAS_TO="$(jq --arg m "$TO" '.modules | has($m)' "$INDEX" 2>"$_DEVNULL")"
      [ "$HAS_TO" = "true" ] || EERR="${EERR}${EERR:+, }to '$TO' not in modules"
    else
      EERR="${EERR}${EERR:+, }missing to"
    fi

    case "$TYPE" in
      calls|shares-state|co-configured|co-modified) ;;
      "") EERR="${EERR}${EERR:+, }missing type" ;;
      *)  EERR="${EERR}${EERR:+, }unknown type '$TYPE'" ;;
    esac

    if [ -n "$EERR" ]; then
      problem "edge[$i] ($FROM → $TO): $EERR — edit .kairoi/model/_index.json"
      EDGE_ERRS=$((EDGE_ERRS + 1))
    fi
  done
  [ "$EDGE_ERRS" -eq 0 ] && ok "edges valid ($EDGE_COUNT)"
fi

# --- Check 8: JSONL files ---
for JFILE in buffer.jsonl receipts.jsonl; do
  FPATH="$STATE_DIR/$JFILE"
  if [ ! -f "$FPATH" ]; then
    ok "$JFILE not present (ok if no tasks yet)"
    continue
  fi

  LINES="$(wc -l < "$FPATH" | tr -d ' ')"
  if [ "$LINES" -eq 0 ]; then
    ok "$JFILE empty"
    continue
  fi

  BAD=0
  LINENUM=0
  while IFS= read -r LINE; do
    LINENUM=$((LINENUM + 1))
    [ -n "$LINE" ] || continue
    if ! echo "$LINE" | jq . > /dev/null 2>"$_DEVNULL"; then
      BAD=$((BAD + 1))
      if [ "$BAD" -le 3 ]; then
        problem "$JFILE line $LINENUM is invalid JSON — edit or remove the line"
      fi
    fi
  done < "$FPATH"

  if [ "$BAD" -eq 0 ]; then
    ok "$JFILE valid ($LINES entries)"
  elif [ "$BAD" -gt 3 ]; then
    problem "$JFILE has $BAD total invalid lines"
  fi
done

# --- Check 9: transient files in .gitignore (mode-aware) ---
# Solo mode uses a whole-directory `.kairoi/` rule which covers every
# transient implicitly; Team mode lists them individually. Detect mode
# from .gitignore content (mode is not persisted in a dedicated file).
TRANSIENTS=".guards-log .guard-disputes .sync-manifest.json .session-summary.txt .write-guard-disabled"
TRANSIENT_GLOBS=".reflect-result-*.json .seen-* .pre-sync/"

GITIGNORE=""
if [ -f ".gitignore" ]; then
  GITIGNORE="$(cat .gitignore)"
fi

# Solo mode: `.kairoi/` (with optional trailing slash) covers everything.
# Skip the individual-entry check; the whole-directory rule is sufficient.
if echo "$GITIGNORE" | grep -qE '^\s*\.kairoi/?\s*$' 2>"$_DEVNULL"; then
  ok "transient files covered by .gitignore (Solo mode — \`.kairoi/\` whole-directory rule)"
else
  # Team mode (or unconfigured): each transient must be listed.
  MISSING_IGNORE=""
  for TF in $TRANSIENTS; do
    if ! echo "$GITIGNORE" | grep -qF ".kairoi/$TF" 2>"$_DEVNULL" && \
       ! echo "$GITIGNORE" | grep -qF ".kairoi/.$TF" 2>"$_DEVNULL"; then
      MISSING_IGNORE="${MISSING_IGNORE}${MISSING_IGNORE:+, }$TF"
    fi
  done

  if ! echo "$GITIGNORE" | grep -qE '\.kairoi/\.reflect-result' 2>"$_DEVNULL"; then
    MISSING_IGNORE="${MISSING_IGNORE}${MISSING_IGNORE:+, }.reflect-result-*.json"
  fi
  if ! echo "$GITIGNORE" | grep -qE '\.kairoi/\.seen-' 2>"$_DEVNULL"; then
    MISSING_IGNORE="${MISSING_IGNORE}${MISSING_IGNORE:+, }.seen-*"
  fi
  if ! echo "$GITIGNORE" | grep -qE '\.kairoi/\.pre-sync' 2>"$_DEVNULL"; then
    MISSING_IGNORE="${MISSING_IGNORE}${MISSING_IGNORE:+, }.pre-sync/"
  fi

  if [ -n "$MISSING_IGNORE" ]; then
    problem "transient files not in .gitignore: $MISSING_IGNORE — add \`.kairoi/\` transient patterns, or switch to Solo mode by setting \`.kairoi/\` as the sole rule"
  else
    ok "transient files covered by .gitignore (Team mode)"
  fi
fi

# --- Summary ---
TOTAL=$((PASS + FAIL))
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "kairoi doctor: all checks passed ($TOTAL checks)."
else
  echo "$PASS/$TOTAL checks passed, $FAIL problem(s) found."
fi
