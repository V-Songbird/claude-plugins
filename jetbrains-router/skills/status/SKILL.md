---
name: status
description: Probe whether a JetBrains IDE MCP server is connected to this session and report the project modules it sees.
user-invocable: true
---

# jetbrains-status

Gather and report the current jetbrains-router state. Do all three probes before replying.

1. **MCP connectivity** — identify which JetBrains prefix is registered in this session (`mcp__webstorm__*`, `mcp__rider__*`, or `mcp__idea__*`), then call `get_project_modules` on that prefix (no arguments required; optionally pass `projectPath` if you know the absolute project root). If no JetBrains tool is registered, note "MCP tool unavailable". If the call errors, note "MCP call failed" with the error text.

2. **Hook availability** — invoke `Bash` with `description: "Probe jetbrains-router availability"` and `command`:
   ```
   bash ${CLAUDE_PLUGIN_ROOT}/scripts/jetbrains-detect.sh; echo exit=$?
   ```
   Exit 0 = hook will enforce routing. Exit 1 with stderr `disabled via JETBRAINS_ROUTER_DISABLE=1` = kill-switched. Exit 1 with no stderr = no JetBrains process detected.

3. **Report** — under 10 lines, covering:
   - **Status** — one of "connected" / "not connected (no MCP tool)" / "not connected (MCP call failed)" / "kill-switched".
   - **Active IDE + prefix** — which of `webstorm`, `rider`, `idea` (or custom via `JETBRAINS_MCP_PREFIX`) is live.
   - **Project root** — if the MCP response includes it.
   - **Module count + names** — from the MCP response.
   - **Routing state** — cross-reference the two probes:
     - MCP connected + detect exit 0 → `routing active (hook will redirect Read/Grep/Glob/Edit/Write/Bash)`
     - MCP connected + detect exit 1 → `routing kill-switched (MCP reachable but hook is disabled — unset JETBRAINS_ROUTER_DISABLE to re-enable)`
     - MCP unavailable + detect exit 0 → `routing will misfire (hook enforces but MCP tools are missing — check IDE → Settings → Tools → MCP Server)`
     - MCP unavailable + detect exit 1 → `routing inactive (hook fails open, native tools in use)`

No recommendations beyond the mismatch hints above. The user runs this to verify the plugin is live.
