#!/usr/bin/env bash
# Flow 14: /kairoi:lint observation-only report.
# Builds a minimal fixture with known-bad patterns and asserts each detector
# fires exactly where expected. Does NOT assert on format (just content), so
# future prose tweaks to the output don't break the test.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
STYLE_CHECK="$PLUGIN/scripts/style-check.sh"

setup_kairoi_state "auth" "Auth module" 0

# --- Fixture: 1 star import, 1 long file, 1 file without a test ---

# Make sure build-adapter points test_dirs somewhere we can populate.
jq '.test_dirs = ["tests/"]' .kairoi/build-adapter.json > /tmp/ba.json && mv /tmp/ba.json .kairoi/build-adapter.json

mkdir -p src/auth tests/auth

# 1) Star import — should flag on line 2
cat > src/auth/reexport.ts <<'EOF'
// re-export barrel — this is the cross-module bottleneck
export * from './token';
EOF

# 2) Long file (>300 lines) — make it deliberately verbose
{
  echo "// intentionally long file to trip the 300-line threshold"
  for i in $(seq 1 340); do
    echo "const placeholder_$i = $i;"
  done
} > src/auth/big.ts

# 3) Small file with NO matching test. Should flag as untested.
cat > src/auth/orphan.ts <<'EOF'
export const untested = () => 42;
EOF

# 4) Small file that DOES have a test — must NOT flag as untested.
cat > src/auth/covered.ts <<'EOF'
export const covered = () => 1;
EOF
cat > tests/auth/covered.test.ts <<'EOF'
import { covered } from '../../src/auth/covered';
test('covered', () => expect(covered()).toBe(1));
EOF

# Run the scanner
OUT="$(bash "$STYLE_CHECK" 2>&1)"

# ---- Star import detection ----
if ! echo "$OUT" | grep -qE "reexport\.ts:2.*star import"; then
  echo "FAIL: star-import observation missing for reexport.ts"
  echo "$OUT" | sed 's/^/  /'
  exit 1
fi

# ---- Long file detection ----
if ! echo "$OUT" | grep -qE "big\.ts.*[0-9]+ lines"; then
  echo "FAIL: long-file observation missing for big.ts"
  echo "$OUT" | sed 's/^/  /'
  exit 1
fi

# ---- Untested file detection ----
if ! echo "$OUT" | grep -qE "orphan\.ts.*no matching test"; then
  echo "FAIL: untested-file observation missing for orphan.ts"
  echo "$OUT" | sed 's/^/  /'
  exit 1
fi

# ---- covered.ts must NOT be flagged as untested ----
if echo "$OUT" | grep -qE "covered\.ts.*no matching test"; then
  echo "FAIL: covered.ts wrongly flagged as untested (it has covered.test.ts)"
  echo "$OUT" | sed 's/^/  /'
  exit 1
fi

# ---- Module filter: passing a specific module argument scopes output ----
OUT_FILTERED="$(bash "$STYLE_CHECK" auth 2>&1)"
if ! echo "$OUT_FILTERED" | grep -qE "reexport\.ts"; then
  echo "FAIL: filtered style-check for 'auth' lost the star-import finding"
  exit 1
fi

# ---- Unknown module: empty report, not an error ----
# (style-check iterates modules from _index; an unknown arg results in no
# source_paths → no findings. Still exits 0.)
if ! bash "$STYLE_CHECK" nonexistent >/dev/null 2>&1; then
  echo "FAIL: style-check on unknown module should still exit 0"
  exit 1
fi

exit 0
