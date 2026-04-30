#!/usr/bin/env bash
# Flow 9: mechanical enforcement of overrides.pinned and overrides.protected_guards.
# The reflection agent is instructed to respect them, but that's honor-system.
# sync-finalize enforces both at the file level: pinned values always win over
# whatever reflection wrote; protected guards are restored from the pre-sync
# snapshot if reflection removed them.

set -u
. "$KAIROI_TEST_HELPERS"

PLUGIN="$KAIROI_TEST_PLUGIN_ROOT"
SYNC_PREPARE="$PLUGIN/scripts/sync-prepare.sh"
SYNC_FINALIZE="$PLUGIN/scripts/sync-finalize.sh"

init_git_repo
setup_kairoi_state "auth" "Auth module" 0
add_guard "auth" "fix-token-race" "Verify mutex lock" "src/auth/token.ts"
add_guard "auth" "other-guard" "Other check" "src/auth/other.ts"

# Write overrides: pin purpose, protect fix-token-race.
jq -n '{
  modules: {
    auth: {
      pinned: { purpose: "PINNED PURPOSE — must not change" },
      protected_guards: ["fix-token-race"]
    }
  }
}' > .kairoi/overrides.json

buffer_append_raw "some-task" "SUCCESS" "auth"

# Run sync-prepare (creates manifest + snapshots)
bash "$SYNC_PREPARE" >/dev/null 2>&1

# Verify snapshot exists
if [ ! -f ".kairoi/.pre-sync/auth.json" ]; then
  echo "snapshot not created by sync-prepare"
  exit 1
fi

# Simulate a malicious/buggy reflection agent:
#   - Rewrites purpose to something the user didn't want.
#   - Deletes the protected guard fix-token-race.
#   - Leaves other-guard alone.
jq '.purpose = "WRONG PURPOSE written by reflection" |
    .guards = (.guards | map(select(.source_task != "fix-token-race")))' \
  .kairoi/model/auth.json > /tmp/auth.json && mv /tmp/auth.json .kairoi/model/auth.json

# Also write a minimal reflect-result so sync-finalize has something to work with
jq -n '{module: "auth", guards_created: [], guards_removed: ["fix-token-race"], semantic_edges: [], purpose_changed: true, first_population: false}' \
  > .kairoi/.reflect-result-auth.json

# Sanity check pre-enforcement state: purpose is the wrong one, guard removed
assert_jq ".kairoi/model/auth.json" '.purpose' "WRONG PURPOSE written by reflection" || exit 1
GCOUNT_PRE="$(jq '.guards | length' .kairoi/model/auth.json)"
if [ "$GCOUNT_PRE" != "1" ]; then
  echo "expected 1 guard before sync-finalize (other-guard only), got $GCOUNT_PRE"
  exit 1
fi

# Run sync-finalize — must enforce overrides
bash "$SYNC_FINALIZE" --reflected "auth" >/dev/null 2>&1

# --- Post-enforcement: pinned purpose restored ---
assert_jq ".kairoi/model/auth.json" '.purpose' "PINNED PURPOSE — must not change" || exit 1

# --- Protected guard restored in full ---
GCOUNT_POST="$(jq '.guards | length' .kairoi/model/auth.json)"
if [ "$GCOUNT_POST" != "2" ]; then
  echo "expected 2 guards after sync-finalize (both restored), got $GCOUNT_POST"
  jq '.guards' .kairoi/model/auth.json
  exit 1
fi

assert_jq ".kairoi/model/auth.json" '[.guards[] | select(.source_task == "fix-token-race")] | length' "1" || exit 1
assert_jq ".kairoi/model/auth.json" '[.guards[] | select(.source_task == "fix-token-race") | .check] | .[0]' "Verify mutex lock" || exit 1

# --- Snapshot cleaned up ---
if [ -d ".kairoi/.pre-sync" ]; then
  echo ".pre-sync/ directory should be removed after sync-finalize"
  exit 1
fi

exit 0
