# Changelog

All notable changes to kairoi are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html); alpha releases may introduce breaking changes in minor versions.

## [Unreleased]

## [1.0.2-alpha] — 2026-05-02

### Fixed

- Verbose header (`KAIROI_VERBOSE=1`) now reads the plugin version from `marketplace.json` instead of `plugin.json`. `plugin.json` intentionally carries no `version` field (marketplace.json is the version authority); the old lookup always fell back to `"unknown"`, producing `=== kairoi vunknown ===`.

## [1.0.1-alpha] — 2026-05-02

### Fixed

- `state-write-guard.sh` now bypasses the hand-edit denial for subagent calls. The guard previously relied on PreToolUse hooks not firing inside subagents (Claude Code issue #34692); that assumption no longer holds — hooks now fire for subagent tool calls with `agent_id` present in the payload. Without this fix, `kairoi-reflect-module` and `kairoi-audit` would be denied when writing model files to `.kairoi/` during automated sync. The fix mirrors the same `agent_id` check used by jetbrains-router: if `agent_id` is present, the write is from kairoi's own machinery and is allowed through unconditionally.

### Added

- `tests/test_state_write_guard.sh` Case I: 4 test cases covering the subagent bypass — Write/Edit to `.kairoi/model/*.json` and `.kairoi/.reflect-result-*.json` from a subagent (agent_id present) pass through, and main-session writes to the same paths remain denied.

## [1.0.0-alpha] — 2026-04-29

### Added

- Edit-time guard system: pre-flight checks run before Claude edits trigger-matched files, surfacing known constraints before changes land
- Automatic commit capture and session sync via `sync-prepare` / `sync-finalize` scripts; manifest tracks tasks, files modified, guards fired, and test results per module
- Module reflection (`kairoi-reflect-module` subagent): updates purpose, entry points, known patterns, negative invariants, change archetypes, and dependencies after each session
- Cross-module guard awareness: guards for interface-level constraints automatically extend to dependent modules via `_index.json` semantic edges
- Churn confidence scoring on guards (confirmed / disputed counts; suspect threshold detection)
- Negative invariants on module models: absence claims that grant permission to skip audit work
- Change archetypes: recurring change patterns accumulated per module and injected at orientation
- `/kairoi:lint` skill: observation-only report on source patterns that increase Claude's re-reading cost — star imports, files over 300 lines, source files with no matching test; grounded in Claude's introspective knowledge of its own cognitive cost, not style-guide consensus
- `/kairoi:init` skill: seeds a project's `.kairoi/` state directory, writes initial rules and schemas
- `/kairoi:audit` skill: manual inspection of the current session's guards, disputes, and task coverage
- `/kairoi:show` skill: displays the current module model in readable form
- `/kairoi:doctor` skill: diagnoses stale state, schema drift, and hook configuration issues
- `kairoi-complete` orchestrator agent: hook-triggered post-session reflection and sync dispatch
- `kairoi-audit` subagent: targeted module-state audit without full sync
- Session boot banner via `session-boot.sh` hook; surfaces orientation summary at session start
- Automatic buffer tracking (`auto-buffer.sh`): appends file-write receipts to the session buffer for audit coverage
- `state-write-guard.sh`: mechanical gate preventing state file writes outside designated paths
- `validate-schema.sh`: schema conformance check for module model JSON
- `hooks/hooks.json`: PreToolUse, PostToolUse, and SessionStart hooks wiring the full lifecycle
- `docs/recovery.md`: scenario-driven troubleshooting guide for common failure modes
- Test suite: 22 tests covering guard evaluation, buffer receipts, session boot, schema validation, and sync lifecycle
