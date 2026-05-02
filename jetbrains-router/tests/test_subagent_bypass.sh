#!/usr/bin/env bash
# Subagent bypass: when agent_id is present in the hook payload, the hook
# must fail open (exit 0) regardless of tool or path, because subagents may
# not have the JetBrains MCP tools in their allowed set.

set -u
. "$WSR_TEST_PLUGIN_ROOT/tests/helpers.sh"

AGENT_PAYLOAD_READ='{"tool_name":"Read","cwd":"/proj","tool_input":{"file_path":"/proj/src/app.ts"},"agent_id":"abc123","agent_type":"general-purpose"}'
AGENT_PAYLOAD_GREP='{"tool_name":"Grep","cwd":"/proj","tool_input":{"pattern":"foo"},"agent_id":"abc123","agent_type":"Explore"}'
AGENT_PAYLOAD_EDIT='{"tool_name":"Edit","cwd":"/proj","tool_input":{"file_path":"/proj/src/app.ts","old_string":"a","new_string":"b"},"agent_id":"abc123"}'

run_hook "$AGENT_PAYLOAD_READ"
assert_eq 0 "$WSR_RC" "Read from subagent (agent_id present) must pass through"

run_hook "$AGENT_PAYLOAD_GREP"
assert_eq 0 "$WSR_RC" "Grep from subagent (agent_id present) must pass through"

# Edit check: the file existence guard runs before the block — supply a
# non-existent path so the hook's own guard would fail open anyway, but
# ensure it's the agent_id check firing first (both exit 0, so the result
# is the same; the test verifies the path is not blocked).
run_hook "$AGENT_PAYLOAD_EDIT"
assert_eq 0 "$WSR_RC" "Edit from subagent (agent_id present) must pass through"

# Main-session call (no agent_id) with the same Read path SHOULD be blocked.
MAIN_PAYLOAD_READ='{"tool_name":"Read","cwd":"/proj","tool_input":{"file_path":"/proj/src/app.ts"}}'
run_hook "$MAIN_PAYLOAD_READ"
assert_eq 2 "$WSR_RC" "Read from main session (no agent_id) must still be blocked"

echo "PASS: subagent bypass"
