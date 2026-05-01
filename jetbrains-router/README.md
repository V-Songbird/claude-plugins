# jetbrains-router

Routes Claude Code tools through a JetBrains IDE MCP server.

When a supported JetBrains IDE is connected (WebStorm, Rider, IntelliJ IDEA), Claude Code's Read, Grep, Glob, Edit, Write, and Bash invocations are transparently routed through the IDE's MCP server. Primary benefits:

- **Live diagnostics**: `get_file_problems` replaces local `tsc`/`gradle`/`mypy` runs with the IDE's in-memory diagnostic index
- **Unsaved-buffer reads**: file reads reflect the editor's current buffer, including changes not yet saved to disk
- **Project-index search**: searches narrow past `.gitignore` and other excluded paths using the IDE's project model

**Fails open**: when no IDE is connected or the MCP server is unreachable, all tool calls pass through to native Claude Code behavior without error or interruption.

## Routing scope

Routing applies to **source code files**. The following always use native tools, even when an IDE is connected:

| Category | Examples |
|----------|---------|
| Dotfiles and dotfolders | `.claude/`, `.idea/`, `.gradle/`, `.kotlin/`, `.gitignore`, `.env` |
| Markdown | `CLAUDE.md`, `README.md`, `docs/guide.md` |
| JSON / JSONL | `package.json`, `tsconfig.json`, `*.jsonl` |
| `docs/` directory | any file under `docs/` |
| Config extensions | `.yml`, `.yaml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.properties`, `.lock` |
| Binary files | images, archives, compiled artifacts |
| Paths outside the project root | the IDE can only see files inside its open project |

For `Grep` and `Glob`, native tools are used when the `path` parameter targets one of the above areas. Whole-project searches (no `path` argument) still redirect to the IDE's index-backed search.

> **Version:** 1.0.1-alpha — interfaces may change between minor releases.

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
| `/jetbrains-router:router` | Reference guide for the native-to-IDE tool mapping and bypass conditions |
| `/jetbrains-router:status` | Checks whether JetBrains routing is active and reports the current bypass state |

## Installation

Clone this repository and register the `jetbrains-router/` directory as a Claude Code plugin. The `hooks/hooks.json` file wires the `PreToolUse` hook automatically.

## License

MIT — see [LICENSE](./LICENSE).
