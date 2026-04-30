#!/usr/bin/env bash
# Flow 11: A3a source-comment scanner with the 25% false-positive quality gate.
# Scans a deliberate-gotcha fixture (8 real invariants, 4 gotchas) and asserts:
#   - every real invariant is detected
#   - total false positives keep FP rate ≤ 25% of total detections
# If this test fails, A3a (seed guards from source comments) does not ship
# as-is — see plan section A3a for the contingency.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
SCANNER="$PLUGIN/scripts/seed-guards.sh"
FIXTURE="$PLUGIN/tests/fixtures/seed-project/src"

if [ ! -d "$FIXTURE" ]; then
  echo "fixture missing at $FIXTURE"
  exit 1
fi

OUT="$(bash "$SCANNER" "$FIXTURE")"

# Validate JSON shape
if ! echo "$OUT" | jq -e '.candidates | type == "array"' >/dev/null; then
  echo "scanner output is not the expected shape"
  echo "$OUT"
  exit 1
fi

TOTAL="$(echo "$OUT" | jq '.candidates | length')"

# ---- every real invariant must be detected ----
# Keyed as "file:line:keyword". Any miss fails the test.
REAL_INVARIANTS=(
  "auth/token.ts:1:NEVER"
  "auth/token.ts:5:MUST NOT"
  "auth/token.ts:11:IMPORTANT"
  "parser/dates.rs:1:DO NOT"
  "parser/dates.rs:6:NEVER"
  "utils/helpers.go:3:MUST NOT"
  "api/routes.py:1:WARNING"
  "api/routes.py:6:SECURITY"
)

REAL_COUNT=${#REAL_INVARIANTS[@]}
MISSED=0

for key in "${REAL_INVARIANTS[@]}"; do
  f="${key%%:*}"
  rest="${key#*:}"
  ln="${rest%%:*}"
  kw="${rest#*:}"

  present="$(echo "$OUT" | jq --arg f "$f" --argjson l "$ln" --arg k "$kw" \
    '[.candidates[] | select(.file == $f and .line == $l and .keyword == $k)] | length')"

  if [ "$present" != "1" ]; then
    echo "missing real invariant: $key (detected $present times)"
    MISSED=$((MISSED + 1))
  fi
done

if [ "$MISSED" -gt 0 ]; then
  echo "FAIL: $MISSED real invariant(s) not detected"
  echo "full output:"
  echo "$OUT" | jq .
  exit 1
fi

# ---- false-positive gate: FP count = total - 8 reals ----
# The gotcha fixtures (gotchas.ts, the Python docstring) are the ONLY other
# potential matches. Any match outside the 8 real ones is a false positive.
FP_COUNT=$((TOTAL - REAL_COUNT))

if [ "$FP_COUNT" -lt 0 ]; then
  echo "FAIL: total detections ($TOTAL) less than expected reals ($REAL_COUNT)"
  exit 1
fi

# FP rate = FP / total. Must be < 25%, i.e., FP * 4 < total (integer math).
if [ "$((FP_COUNT * 4))" -ge "$TOTAL" ]; then
  echo "FAIL: false-positive rate exceeds 25%"
  echo "  total detections: $TOTAL"
  echo "  real: $REAL_COUNT"
  echo "  false positives: $FP_COUNT"
  echo "  rate: $((FP_COUNT * 100 / TOTAL))%"
  echo "full output:"
  echo "$OUT" | jq .
  exit 1
fi

# ---- every candidate has the required fields ----
MALFORMED="$(echo "$OUT" | jq '[.candidates[] |
  select(.file == null or .line == null or .keyword == null or .check == null)
] | length')"

if [ "$MALFORMED" != "0" ]; then
  echo "FAIL: $MALFORMED candidate(s) missing required fields"
  exit 1
fi

exit 0
