#!/usr/bin/env bash
# kairoi style-check: observation-only report on source patterns known to
# make Claude's own re-reading harder. Each observation is justified by how
# Claude actually processes code — not style-guide consensus.
#
# Three observations (each item earns its place via introspective
# cognitive cost, not conventional wisdom):
#
# 1. Star imports / wildcard re-exports
#    → Symbol origin-tracing becomes 2-3× slower. Explicit imports let
#      Claude resolve a symbol in one step; with `import *`, Claude must
#      read the target module, enumerate its exports, and match.
#
# 2. Files over 300 lines
#    → Proxy for "too much surface area for one re-read pass." Claude's
#      working-memory budget for holding simultaneous invariants, mutations,
#      and branch conditions degrades past this threshold. The function-
#      level version of this observation (individual functions over 80-150
#      lines) needs an AST pass that's deferred to a future version; file-
#      level is a reliable, language-agnostic approximation.
#
# 3. Source files with no matching test
#    → Claude consults tests as executable behavioral spec when modifying
#      functions. Without them, confidence in "am I breaking the contract?"
#      drops significantly — inference from the function body alone tells
#      Claude what the code *does*, not what it *should do*.
#
# Does NOT: modify any file, write any guard, run any fixer. Pure report.
#
# Usage:
#   style-check.sh [module]
#
# With no argument, scans all modules from _index.json. With a module name,
# scans just that module.

set -uo pipefail

command -v jq >/dev/null || { echo "kairoi: jq required" >&2; exit 1; }

STATE_DIR=".kairoi"
INDEX="$STATE_DIR/model/_index.json"
ADAPTER="$STATE_DIR/build-adapter.json"

if [ ! -f "$INDEX" ]; then
  echo "kairoi: no .kairoi/ state found. Run /kairoi:init first."
  exit 1
fi

FILTER="${1:-}"

_DEVNULL="/dev/null"
if [ "${KAIROI_DEBUG:-}" = "1" ]; then
  _DEVNULL="/dev/stderr"
  echo "kairoi-debug: style-check starting" >&2
fi

# File-length threshold (Claude-introspection-grounded; see header).
LINE_THRESHOLD=300

# Test dirs from build-adapter; default to common patterns when unknown.
TEST_DIRS="$(jq -r '.test_dirs // ["tests/", "test/", "__tests__/", "spec/"] | .[]' \
  "$ADAPTER" 2>"$_DEVNULL" | tr -d '\r')"

# Resolve module list
if [ -n "$FILTER" ]; then
  MODULES="$FILTER"
else
  MODULES="$(jq -r '.modules | keys[]' "$INDEX" 2>"$_DEVNULL" | tr -d '\r')"
fi

# Extensions considered "source" for the purposes of this scan.
SOURCE_EXTS="ts tsx js jsx mjs cjs rs go java kt kts scala cs c cpp h hpp swift dart py rb php"

# ---- Observation detectors -------------------------------------------------

# 1. Star imports — language-specific patterns, each keyed by file extension.
detect_star_imports() {
  local file="$1"
  local ext="${file##*.}"
  case "$ext" in
    ts|tsx|js|jsx|mjs|cjs)
      # import * as Foo from 'bar';  OR  export * from 'bar';
      grep -nE "^\s*(import|export)\s+\*" "$file" 2>"$_DEVNULL" || true
      ;;
    py)
      # from X import *
      grep -nE "^\s*from\s+\S+\s+import\s+\*" "$file" 2>"$_DEVNULL" || true
      ;;
    rs)
      # use foo::*;
      grep -nE "^\s*(pub\s+)?use\s+.+::\*" "$file" 2>"$_DEVNULL" || true
      ;;
    go)
      # import . "foo" (dot-imports are analogous to star in Go)
      grep -nE '^\s*\.\s+"[^"]+"' "$file" 2>"$_DEVNULL" || true
      ;;
    java|kt|kts|scala)
      # import foo.bar.*;
      grep -nE "^\s*import\s+.+\.\*" "$file" 2>"$_DEVNULL" || true
      ;;
    *)
      return 0
      ;;
  esac
}

# 2. File length
detect_long_file() {
  local file="$1"
  local lines
  lines="$(wc -l < "$file" 2>"$_DEVNULL" | tr -d ' ')"
  if [ "${lines:-0}" -gt "$LINE_THRESHOLD" ]; then
    echo "$lines"
  fi
}

# 3. Untested file — does any file under any test_dir have the same stem?
has_matching_test() {
  local src_file="$1"
  local stem base
  base="$(basename "$src_file")"
  stem="${base%.*}"
  # Skip the matching check for files that look like tests themselves.
  case "$src_file" in
    *test*|*spec*|*Test*|*.test.*|*.spec.*) return 0 ;;
  esac
  # Search each test_dir for any file containing the stem.
  while IFS= read -r td; do
    td="${td%/}"
    [ -d "$td" ] || continue
    if find "$td" -type f \( -name "*${stem}*" \) -print -quit 2>"$_DEVNULL" | grep -q .; then
      return 0
    fi
  done <<< "$TEST_DIRS"
  return 1
}

# ---- Per-module scan -------------------------------------------------------

HEADER_EMITTED=false

scan_module() {
  local mod="$1"
  local paths
  paths="$(jq -r --arg m "$mod" '.modules[$m].source_paths[]?' "$INDEX" 2>"$_DEVNULL" | tr -d '\r')"
  [ -n "$paths" ] || return 0

  local findings=""

  while IFS= read -r sp; do
    [ -n "$sp" ] || continue
    [ -d "$sp" ] || continue

    # Collect files under this source path.
    while IFS= read -r -d '' file; do
      local ext="${file##*.}"
      case " $SOURCE_EXTS " in
        *" $ext "*) ;;
        *) continue ;;
      esac

      # Detect per-observation, accumulating findings.
      local si_lines
      si_lines="$(detect_star_imports "$file")"
      if [ -n "$si_lines" ]; then
        while IFS= read -r m; do
          [ -n "$m" ] || continue
          local ln="${m%%:*}"
          findings="${findings}  $file:$ln  star import — explicit import would save Claude a trace step"$'\n'
        done <<< "$si_lines"
      fi

      local long
      long="$(detect_long_file "$file")"
      if [ -n "$long" ]; then
        findings="${findings}  $file  $long lines — consider splitting (past ${LINE_THRESHOLD}-line threshold)"$'\n'
      fi

      if ! has_matching_test "$file"; then
        findings="${findings}  $file  no matching test file under ${TEST_DIRS//$'\n'/, }"$'\n'
      fi
    done < <(find "$sp" -type f -print0 2>"$_DEVNULL")
  done <<< "$paths"

  if [ -n "$findings" ]; then
    if [ "$HEADER_EMITTED" = false ]; then
      echo "=== kairoi style-check ==="
      echo ""
      echo "Observation-only. Each line is a hint grounded in Claude's re-reading"
      echo "cognitive cost — not enforcement. Use as input to your own judgment."
      echo ""
      HEADER_EMITTED=true
    fi
    echo "[$mod]"
    printf '%s' "$findings"
    echo ""
  fi
}

ANY_FINDINGS=false
while IFS= read -r MOD; do
  MOD="${MOD%$'\r'}"
  [ -n "$MOD" ] || continue
  OUTPUT_BEFORE_COUNT="$HEADER_EMITTED"
  scan_module "$MOD"
  if [ "$HEADER_EMITTED" = true ]; then
    ANY_FINDINGS=true
  fi
done <<< "$MODULES"

if [ "$ANY_FINDINGS" = false ]; then
  echo "=== kairoi style-check ==="
  echo ""
  echo "No observations. Either the code is already Claude-legible by the"
  echo "three criteria (no star imports, no files over ${LINE_THRESHOLD} lines,"
  echo "every source file has a matching test), or style-check needs better"
  echo "detectors — the observation list is intentionally conservative and"
  echo "will grow as patterns earn their place."
fi
