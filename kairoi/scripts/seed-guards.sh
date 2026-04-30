#!/usr/bin/env bash
# kairoi seed-guards: scan source files for invariant comments and emit them
# as candidate guards. Invoked by /kairoi:init step 5.5 to close the
# "invisible for 3 sessions" bootstrap gap — so day-one kairoi already fires
# on something the author already wrote as explicit intent.
#
# Detection rule: a comment marker (// or #) followed by whitespace and an
# invariant keyword (NEVER, MUST NOT, WARNING:, DO NOT, IMPORTANT:, SECURITY:)
# at the start of the comment content. This catches:
#   - leading comments:   // NEVER remove X
#   - trailing comments:  const T = 3600; // IMPORTANT: rotate the key
# and rejects:
#   - keywords in string literals (no comment marker on the line)
#   - commented-out code (keyword not right after the marker)
#   - Python/Ruby docstrings (no #/// prefix, just """)
#   - C-family block comments (/* ... */ — wrong marker)
#
# The scanner is conservative on purpose. Its quality gate is a deliberate-
# gotcha fixture; false-positive rate must stay ≤ 25% or the whole seed-
# guards flow is deferred.
#
# Usage:
#   seed-guards.sh <source_dir>
#
# Output (stdout, JSON):
#   {"candidates": [{"file": "...", "line": N, "keyword": "...", "check": "..."}]}

set -euo pipefail

command -v jq >/dev/null || { echo "kairoi seed-guards: jq required" >&2; exit 1; }

SOURCE_DIR="${1:-}"
if [ -z "$SOURCE_DIR" ] || [ ! -d "$SOURCE_DIR" ]; then
  echo "kairoi seed-guards: usage: seed-guards.sh <source_dir>" >&2
  exit 1
fi
SOURCE_DIR="${SOURCE_DIR%/}"

_DEVNULL="/dev/null"
if [ "${KAIROI_DEBUG:-}" = "1" ]; then
  _DEVNULL="/dev/stderr"
  echo "kairoi-debug: seed-guards scanning $SOURCE_DIR" >&2
fi

# Extension → comment style. Kept small on purpose — add more as we encounter
# real projects in a language we don't cover.
SLASH_EXTS=(ts tsx js jsx mjs cjs rs go java kt kts scala cs c cpp h hpp swift dart)
HASH_EXTS=(py rb sh bash yml yaml toml)
# php accepts both // and #; scan it twice.

# Keyword alternation for the initial grep filter.
KEYWORDS='NEVER|MUST NOT|WARNING:|DO NOT|IMPORTANT:|SECURITY:'

TMPFILE="$(mktemp 2>"$_DEVNULL" || mktemp -t seed_guards.XXXXXX)"
trap 'rm -f "$TMPFILE"' EXIT

# Extract the keyword at the start of a stripped comment-content string.
# Longer keywords first so "MUST NOT" wins over "MUST" (we don't match bare MUST anyway).
extract_keyword() {
  local content="$1"
  case "$content" in
    "MUST NOT "*|"MUST NOT:"*)   echo "MUST NOT"; return 0 ;;
    "DO NOT "*|"DO NOT:"*)       echo "DO NOT";   return 0 ;;
    "NEVER "*|"NEVER:"*)         echo "NEVER";    return 0 ;;
    "WARNING:"*)                  echo "WARNING";  return 0 ;;
    "IMPORTANT:"*)                echo "IMPORTANT"; return 0 ;;
    "SECURITY:"*)                 echo "SECURITY"; return 0 ;;
  esac
  return 1
}

# Trim leading and trailing whitespace (portable, no bashisms).
trim() {
  printf '%s' "$1" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//'
}

# Scan one file with one marker. Writes JSON objects to $TMPFILE (one per line).
scan_file() {
  local file="$1" marker="$2"
  local mre rel
  case "$marker" in
    '//') mre='\/\/' ;;
    '#')  mre='#'    ;;
    *)    return 0 ;;
  esac
  rel="${file#$SOURCE_DIR/}"

  local matches
  matches="$(grep -nE "${mre}[[:space:]]+(${KEYWORDS})" "$file" 2>"$_DEVNULL" || true)"
  [ -n "$matches" ] || return 0

  local IFS_save="$IFS"
  IFS=$'\n'
  local match
  for match in $matches; do
    [ -n "$match" ] || continue
    local line_num rest after kw
    # grep -n output: "<line>:<content>"
    line_num="${match%%:*}"
    rest="${match#*:}"
    # Everything from the marker onward.
    after="${rest#*${marker}}"
    after="$(trim "$after")"
    kw="$(extract_keyword "$after" 2>/dev/null)" || continue

    jq -c -n \
      --arg f "$rel" \
      --argjson l "$line_num" \
      --arg k "$kw" \
      --arg c "$after" \
      '{file: $f, line: $l, keyword: $k, check: $c}' >> "$TMPFILE"
  done
  IFS="$IFS_save"
}

# Walk the tree and scan.
for ext in "${SLASH_EXTS[@]}"; do
  while IFS= read -r -d '' file; do
    scan_file "$file" '//'
  done < <(find "$SOURCE_DIR" -type f -name "*.$ext" -print0 2>"$_DEVNULL")
done

for ext in "${HASH_EXTS[@]}"; do
  while IFS= read -r -d '' file; do
    scan_file "$file" '#'
  done < <(find "$SOURCE_DIR" -type f -name "*.$ext" -print0 2>"$_DEVNULL")
done

# PHP: both styles.
while IFS= read -r -d '' file; do
  scan_file "$file" '//'
  scan_file "$file" '#'
done < <(find "$SOURCE_DIR" -type f -name "*.php" -print0 2>"$_DEVNULL")

# Emit final JSON. jq -s on an empty file returns [].
if [ -s "$TMPFILE" ]; then
  CANDIDATES="$(jq -s '.' "$TMPFILE")"
else
  CANDIDATES='[]'
fi

jq -n --argjson cs "$CANDIDATES" '{candidates: $cs}'
