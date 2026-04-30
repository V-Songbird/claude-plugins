#!/usr/bin/env bash
# Flow: sync-finalize actually writes edges to _index.json.
#
# Regression guard for a silent bug where the big edge-update jq filter
# in sync-finalize.sh contained `reduce ... as $v (init; body) as $name`
# WITHOUT parens around the reduce expression. jq 1.6 accepted this;
# jq 1.7+ rejects it with:
#   syntax error, unexpected as, expecting end of file
#     (Windows cmd shell quoting issues?)
# Because the jq call was chained via `> tmp && mv`, a jq failure left
# `_index.json` untouched (.tmp emptied, mv skipped). The script still
# printed "N receipt(s) emitted, M module(s) finalized" so the failure
# read as cosmetic — but edges silently stopped updating on any jq 1.7+
# install (Windows git-bash being the canonical case, since that's the
# version msys2 ships).
#
# This test exercises the edge-update path end-to-end and asserts that
# both co-modified AND semantic edges land in _index.json. Future edit
# to sync-finalize that breaks the filter parse fails this test.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
SYNC_PREPARE="$PLUGIN/scripts/sync-prepare.sh"
SYNC_FINALIZE="$PLUGIN/scripts/sync-finalize.sh"

init_git_repo
setup_kairoi_state "auth" "Auth module" 0

# Add a second module so co-modified edges have something to connect.
jq -n '{
  source_dirs: ["src/"],
  modules: {
    auth:  { source_paths: ["src/auth/"]  },
    users: { source_paths: ["src/users/"] }
  },
  edges: []
}' > .kairoi/model/_index.json

jq -n '{
  purpose: "Users module",
  entry_points: ["src/users/index.ts"],
  guards: [],
  known_patterns: [],
  dependencies: [],
  _meta: { last_validated: "2026-04-01", tasks_since_validation: 0 }
}' > .kairoi/model/users.json

# Buffer a task that touches BOTH modules — drives co-modified edge.
buffer_append_raw "multi-module-task" "SUCCESS" "auth" "src/auth/t.ts"
jq -c '.modules_affected = ["auth","users"] |
       .modified_files  = ["src/auth/t.ts","src/users/t.ts"]' \
  .kairoi/buffer.jsonl > .kairoi/buffer.jsonl.tmp
mv .kairoi/buffer.jsonl.tmp .kairoi/buffer.jsonl

bash "$SYNC_PREPARE" > /dev/null

# Seed reflect-result for auth with a semantic edge to users.
jq -n '{
  module: "auth",
  guards_created: [],
  guards_removed: [],
  semantic_edges: [{ from: "auth", to: "users", type: "calls", label: "imports validateUser" }],
  first_population: false
}' > .kairoi/.reflect-result-auth.json

# Empty reflect-result for users (no guards, no outgoing edges).
jq -n '{
  module: "users",
  guards_created: [],
  guards_removed: [],
  semantic_edges: [],
  first_population: false
}' > .kairoi/.reflect-result-users.json

# Capture stderr: any "syntax error" here is the regression.
FINALIZE_ERR="$(bash "$SYNC_FINALIZE" --reflected "auth,users" 2>&1 >/dev/null)"

if echo "$FINALIZE_ERR" | grep -qi 'syntax error\|compile error'; then
  echo "FAIL: sync-finalize jq filter failed to parse"
  echo "$FINALIZE_ERR" | sed 's/^/  /'
  exit 1
fi

# Co-modified edge: auth <-> users, weight 1.
CO_COUNT="$(jq '[.edges[] | select(.type == "co-modified" and .from == "auth" and .to == "users")] | length' .kairoi/model/_index.json)"
if [ "$CO_COUNT" != "1" ]; then
  echo "FAIL: expected 1 co-modified edge auth→users, got $CO_COUNT"
  jq '.edges' .kairoi/model/_index.json | sed 's/^/  /'
  exit 1
fi

# Semantic edge: auth -> users, type "calls".
SEM_COUNT="$(jq '[.edges[] | select(.type == "calls" and .from == "auth" and .to == "users")] | length' .kairoi/model/_index.json)"
if [ "$SEM_COUNT" != "1" ]; then
  echo "FAIL: expected 1 semantic calls edge auth→users, got $SEM_COUNT"
  jq '.edges' .kairoi/model/_index.json | sed 's/^/  /'
  exit 1
fi

# Edge weights + last_seen stamped today.
TODAY="$(date -u +%Y-%m-%d)"
STAMPED="$(jq --arg today "$TODAY" '[.edges[] | select(.last_seen == $today)] | length' .kairoi/model/_index.json)"
if [ "$STAMPED" != "2" ]; then
  echo "FAIL: expected both edges stamped last_seen=$TODAY, got $STAMPED"
  jq '.edges' .kairoi/model/_index.json | sed 's/^/  /'
  exit 1
fi

exit 0
