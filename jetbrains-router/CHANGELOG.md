# Changelog

All notable changes to jetbrains-router are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html); alpha releases may introduce breaking changes in minor versions.

## [Unreleased]

## [1.0.0-alpha] — 2026-04-29

### Added

- PreToolUse hook routing Claude Code's Read, Grep, Glob, Edit, Write, and Bash invocations through a JetBrains IDE MCP server (WebStorm, Rider, IntelliJ IDEA) when available
- `get_file_problems` integration: replaces local `tsc`/`gradle`/`mypy` runs with the IDE's live diagnostic index for in-editor diagnostics
- Fail-open behavior: when no JetBrains IDE is connected or the MCP server is unreachable, all tool calls pass through to native Claude Code behavior without error
- `JETBRAINS_ROUTER_DISABLE=1` environment variable: disables routing unconditionally for worktree sessions or contexts where native tools are required
- `JETBRAINS_ROUTER_BYPASS` environment variable: selectively disables routing for specific tools (comma-separated, e.g. `Read,Edit,Write`)
- Worktree fall-through: detects git worktree paths and bypasses routing to prevent cross-project IDE state contamination
- `/jetbrains-router:jetbrains-routing` skill: reference guide for the native-to-IDE tool mapping and bypass conditions
- `references/tool-map.md`: detailed mapping of each Claude Code native tool to its JetBrains IDE MCP equivalent with parameter translations
- `commands/jetbrains-status.md` slash command: checks whether JetBrains routing is active and reports the current bypass state
- `pre-tool-use-redirect.sh`: hook implementation with platform-aware path handling (Windows/Unix)
- `jetbrains-detect.sh`: IDE presence probe used by the redirect hook
- Requires a JetBrains IDE 2025.2+ with MCP Server plugin enabled
- Test suite: 10 tests covering redirect behavior, bypass conditions, worktree detection, and fail-open paths
