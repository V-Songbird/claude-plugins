#!/usr/bin/env bash
# Flow 7: /kairoi:show renders a human-readable model dump. Not a formatting
# lock-in — just verifies the critical pieces (purpose, confidence glyph,
# guard rendering, edges, buffer status) are present in output.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
SHOW="$PLUGIN/scripts/show.sh"

setup_kairoi_state "auth" "OAuth2 PKCE token lifecycle" 3
add_guard "auth" "fix-token-race" "Verify mutex lock" "src/auth/token.ts"

# Add an edge + a receipt + a buffered task for full coverage
jq '.edges = [{from: "api", to: "auth", type: "calls", label: "token validation", weight: 1, last_seen: "2026-04-10"}] |
    .modules.api = {source_paths: ["src/api/"]}' .kairoi/model/_index.json > /tmp/idx.json && mv /tmp/idx.json .kairoi/model/_index.json

jq -n '{purpose: "REST endpoints", entry_points: [], guards: [], known_patterns: [], dependencies: [], _meta: {confidence: "medium", last_validated: "2026-04-01", tasks_since_validation: 15}}' > .kairoi/model/api.json

jq -c -n '{task_id: "r1", timestamp: "2026-04-15T00:00:00Z", status: "SUCCESS", modules_affected: ["auth"], commit_hash: "abc", guards_fired: [], guards_disputed: []}' > .kairoi/receipts.jsonl

buffer_append_raw "pending" "SUCCESS" "auth"

OUT="$(bash "$SHOW" 2>&1)"

# Headline bits
for needle in \
  "=== kairoi model ===" \
  "auth" \
  "OAuth2 PKCE token lifecycle" \
  "● high" \
  "fix-token-race" \
  "Verify mutex lock" \
  "EDGES" \
  "api → auth" \
  "token validation" \
  "RECENT ACTIVITY" \
  "BUFFER" \
  "pending [SUCCESS]"; do
  if ! echo "$OUT" | grep -qF "$needle"; then
    echo "show output missing expected content: '$needle'"
    echo "full output:"
    echo "$OUT" | sed 's/^/  /'
    exit 1
  fi
done

# Filtered output
OUT2="$(bash "$SHOW" auth 2>&1)"
if ! echo "$OUT2" | grep -qF "OAuth2 PKCE"; then
  echo "filtered show did not render target module"
  exit 1
fi
if echo "$OUT2" | grep -qF "EDGES"; then
  echo "filtered show should not render the EDGES block"
  exit 1
fi

# Unknown module should error
if bash "$SHOW" nonexistent >/dev/null 2>&1; then
  echo "show should exit non-zero for unknown module"
  exit 1
fi

exit 0
