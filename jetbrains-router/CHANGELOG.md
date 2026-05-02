# Changelog

All notable changes to jetbrains-router are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html); alpha releases may introduce breaking changes in minor versions.

## [Unreleased]

## [1.0.6-alpha] — 2026-05-02

### Fixed

- Redirect messages for `Glob`, `Grep` (Bash), and `find -name` now use function-call syntax with the exact required parameter name called out inline. Previously, messages said `with q="..."` in natural language which agents often ignored, leading to repeated failures with guessed parameter names (`glob`, `namePattern`, `regex`, `name`, `pattern`). New format: `mcp__<ide>__search_file(q="...")` with an explicit `required parameter is 'q' (not glob, pattern, namePattern…)` warning.

## [1.0.5-alpha] — 2026-05-02

### Fixed

- Subagents spawned via the Agent tool (parallel coding agents, specialized subagent types) now bypass IDE routing automatically. The hook detects the `agent_id` field in the PreToolUse payload — present only for subagent calls, absent for the main session — and exits 0, letting subagents use native tools. Previously, subagents received redirect instructions pointing to `mcp__webstorm__*` tools that are not available in all subagent contexts, causing parallel coding workflows to fail silently or loop.

### Added

- `tests/test_subagent_bypass.sh`: 4 test cases covering the subagent bypass — Read/Grep/Edit from a subagent (agent_id present) pass through, and main-session calls to the same paths are still blocked.

## [1.0.4-alpha] — 2026-04-30

- Fixed BOM errors.

## [1.0.3-alpha] — 2026-04-30

- Improved skill descriptions and triggering phase.

## [1.0.2-alpha] — 2026-04-30

### Fixed

- Routing always redirected to `mcp__webstorm__*` regardless of which IDE was actually running. The hook now auto-detects the active JetBrains IDE process (Rider, IntelliJ IDEA, or WebStorm) via the same platform dispatch used by `jetbrains-detect.sh` (tasklist on Windows, pgrep/ps on macOS/Linux) and routes to the matching prefix. `JETBRAINS_MCP_PREFIX` continues to override auto-detection for renamed mcpServers entries or java-wrapper-launched IDEs where the probe cannot see the process.

## [1.0.1-alpha] — 2026-04-30

### Fixed

- Non-code paths now pass through to native tools instead of being routed to the IDE. Routing is scoped to source code; the following always use native tools regardless of IDE state: dotfiles and dotfolders (`.claude/`, `.idea/`, `.gradle/`, `.kotlin/`, `.gitignore`, etc.), markdown files (`CLAUDE.md`, `README.md`, `docs/*.md`), JSON and JSONL files (`package.json`, `tsconfig.json`), the `docs/` directory, and common config extensions (`.yml`, `.yaml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.properties`, `.lock`, `.env`). Applies to `Read`, `Edit`, `Write`, and `Bash cat/head/tail`. For `Grep` and `Glob`, routing is bypassed when their `path` parameter targets a passthrough directory; whole-project searches still redirect.

## [1.0.0-alpha] — 2026-04-29

### Added

- PreToolUse hook routing Claude Code's Read, Grep, Glob, Edit, Write, and Bash invocations through a JetBrains IDE MCP server (WebStorm, Rider, IntelliJ IDEA) when available
- `get_file_problems` integration: replaces local `tsc`/`gradle`/`mypy` runs with the IDE's live diagnostic index for in-editor diagnostics
- Fail-open behavior: when no JetBrains IDE is connected or the MCP server is unreachable, all tool calls pass through to native Claude Code behavior without error
- `JETBRAINS_ROUTER_DISABLE=1` environment variable: disables routing unconditionally for worktree sessions or contexts where native tools are required
- `JETBRAINS_ROUTER_BYPASS` environment variable: selectively disables routing for specific tools (comma-separated, e.g. `Read,Edit,Write`)
- Worktree fall-through: detects git worktree paths and bypasses routing to prevent cross-project IDE state contamination
- `/jetbrains-router:router` skill: reference guide for the native-to-IDE tool mapping and bypass conditions
- `references/tool-map.md`: detailed mapping of each Claude Code native tool to its JetBrains IDE MCP equivalent with parameter translations
- `/jetbrains-router:status` skill: checks whether JetBrains routing is active and reports the current bypass state
- `pre-tool-use-redirect.sh`: hook implementation with platform-aware path handling (Windows/Unix)
- `jetbrains-detect.sh`: IDE presence probe used by the redirect hook
- Requires a JetBrains IDE 2025.2+ with MCP Server plugin enabled
- Test suite: 10 tests covering redirect behavior, bypass conditions, worktree detection, and fail-open paths
