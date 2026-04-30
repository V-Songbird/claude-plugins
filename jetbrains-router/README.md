# jetbrains-router

Routes Claude Code tools through a JetBrains IDE MCP server.

When a supported JetBrains IDE is connected (WebStorm, Rider, IntelliJ IDEA), Claude Code's Read, Grep, Glob, Edit, Write, and Bash invocations are transparently routed through the IDE's MCP server. Primary benefits:

- **Live diagnostics**: `get_file_problems` replaces local `tsc`/`gradle`/`mypy` runs with the IDE's in-memory diagnostic index
- **Unsaved-buffer reads**: file reads reflect the editor's current buffer, including changes not yet saved to disk
- **Project-index search**: searches narrow past `.gitignore` and other excluded paths using the IDE's project model

**Fails open**: when no IDE is connected or the MCP server is unreachable, all tool calls pass through to native Claude Code behavior without error or interruption.

> **Version:** 1.0.0-alpha — interfaces may change between minor releases.

## Requirements

- JetBrains IDE 2025.2+ (WebStorm, Rider, or IntelliJ IDEA)
- MCP Server plugin enabled in the IDE

## Environment variables

| Variable | Effect |
|----------|--------|
| `JETBRAINS_ROUTER_DISABLE=1` | Disables all routing unconditionally |
| `JETBRAINS_ROUTER_BYPASS=Read,Edit` | Disables routing for specific tools (comma-separated) |

Worktree sessions are automatically detected and bypass routing to prevent cross-project IDE state contamination.

## Skills and commands

| Name | Description |
|------|-------------|
| `/jetbrains-router:jetbrains-routing` | Reference guide for the native-to-IDE tool mapping and bypass conditions |
| `/jetbrains-status` | Checks whether JetBrains routing is active and reports the current bypass state |

## Installation

Clone this repository and register the `jetbrains-router/` directory as a Claude Code plugin. The `hooks/hooks.json` file wires the `PreToolUse` hook automatically.

## License

MIT — see [LICENSE](./LICENSE).
