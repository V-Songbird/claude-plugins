# Hooks reference

## What hooks are

Hooks are user-defined shell commands (or HTTP endpoints, or model evaluations) that Claude Code's harness runs at specific lifecycle points. They are configured in `settings.json` (or in plugin `hooks/hooks.json`, or in skill/agent frontmatter), not invoked by Claude. The harness fires them; Claude has no decision over whether they run. This is what makes hooks deterministic — Claude cannot skip a hook by deciding not to call it. Use hooks for behavior that must always happen (formatters, audit logs, permission gates, env reloads).

## Configuration format

All hooks live under a top-level `hooks` object. Each key is an event name; each value is an array of matcher groups, and each group has a list of handler objects.

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "Bash|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/script.sh",
            "timeout": 60,
            "shell": "bash"
          }
        ]
      }
    ]
  },
  "disableAllHooks": false
}
```

Handler `type` values: `command` (shell), `http` (POST to URL), `prompt` (single LLM call), `agent` (multi-turn subagent).

Matcher rules:
- `"*"`, `""`, or omitted = match everything for that event
- Only letters, digits, `_`, `|` = exact tool name or pipe-separated alternation (`Edit|Write`)
- Anything else = JavaScript regex (e.g., `mcp__github__.*`, `^Notebook`)
- Some events take no matcher (see catalog below); the `matcher` field is ignored for those

Handler fields shared across types: `timeout` (seconds, default 600), `statusMessage`, `if` (permission-rule syntax for tool-event filtering, e.g., `"Bash(git *)"`), `once` (skill frontmatter only).

Command-only fields: `command`, `shell` (`"bash"` default, or `"powershell"`), `async`, `asyncRewake`.

Path env vars usable inside `command`: `$CLAUDE_PROJECT_DIR`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, and `$CLAUDE_ENV_FILE` (for `SessionStart` / `CwdChanged` / `FileChanged` only).

## Event catalog (verified against docs)

### SessionStart
Fires when a session begins or resumes. Matcher: `startup | resume | clear | compact`. Use to load env vars, inject context, restore state.
```json
{ "SessionStart": [{ "matcher": "compact", "hooks": [{ "type": "command", "command": "echo 'Reminder: use bun, not npm.'" }] }] }
```

### SessionEnd
Fires when a session terminates. Matcher: `clear | resume | logout | prompt_input_exit | bypass_permissions_disabled | other`. Use for cleanup.

### UserPromptSubmit
Fires when the user submits a prompt, before Claude processes it. No matcher. Receives `prompt`. Stdout text is added to context; `decision: "block"` rejects the prompt.

### PreToolUse
Fires after Claude builds tool arguments, before the tool runs. Matcher = tool name (`Bash`, `Edit|Write`, `mcp__memory__.*`). The only event that can deny a tool call before execution.
```json
{ "PreToolUse": [{ "matcher": "Edit|Write", "hooks": [{ "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/protect.sh" }] }] }
```
Output JSON: `hookSpecificOutput.permissionDecision` = `allow | deny | ask | defer`.

### PostToolUse
Fires after a tool succeeds. Matcher = tool name. Use for formatters, linters, logging. Cannot undo the tool call.
```json
{ "PostToolUse": [{ "matcher": "Edit|Write", "hooks": [{ "type": "command", "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write" }] }] }
```

### PostToolUseFailure
Fires after a tool execution fails. Matcher = tool name. Receives `error`, `is_interrupt`. Logging only; no block control.

### PermissionRequest
Fires when a permission dialog is about to appear. Matcher = tool name. Output `hookSpecificOutput.decision.behavior = "allow" | "deny"` to answer the dialog automatically. Does not fire in `-p` non-interactive mode.

### PermissionDenied
Fires when auto-mode classifier denies a tool call. Matcher = tool name. Return `{ "hookSpecificOutput": { "retry": true } }` to let Claude retry.

### Notification
Fires when Claude Code emits a notification (waiting on input, etc.). Matcher = `permission_prompt | idle_prompt | auth_success | elicitation_dialog`.
```json
{ "Notification": [{ "matcher": "", "hooks": [{ "type": "command", "command": "notify-send 'Claude' 'needs attention'" }] }] }
```

### Stop
Fires when Claude finishes responding. No matcher. `decision: "block"` keeps Claude working. Must check `stop_hook_active` to avoid infinite loops.

### StopFailure
Fires when the turn ends due to API error. Matcher = `rate_limit | authentication_failed | billing_error | invalid_request | server_error | max_output_tokens | unknown`. Logging only.

### SubagentStart
Fires when a subagent is spawned. Matcher = agent type (`Bash`, `Explore`, `Plan`, custom names). Output `additionalContext` to inject into the subagent.

### SubagentStop
Fires when a subagent finishes. Matcher = agent type. Same decision-control format as `Stop`. Note: `Stop` hooks declared in subagent frontmatter auto-convert to `SubagentStop`.

### TaskCreated
Fires when a task is created via `TaskCreate`. No matcher. Exit 2 blocks creation. Use for naming/description policy.

### TaskCompleted
Fires when a task is marked complete. No matcher. Exit 2 or `decision: "block"` prevents completion. Use to gate "done" on validation.

### TeammateIdle
Fires when an agent-team teammate is about to go idle. No matcher. Exit 2 or `continue: false` keeps them working.

### InstructionsLoaded
Fires when `CLAUDE.md` or `.claude/rules/*.md` loads into context (session start or lazy load). Matcher = `session_start | nested_traversal | path_glob_match | include | compact`. Receives `file_path`, `memory_type`, `load_reason`. No decision control — observability only.

### ConfigChange
Fires when a settings file changes during a session. Matcher = `user_settings | project_settings | local_settings | policy_settings | skills`. Exit 2 or `decision: "block"` blocks the change (except `policy_settings`, which cannot be blocked).

### CwdChanged
Fires when the working directory changes (e.g., `cd`). No matcher. Receives `cwd`. Can append to `$CLAUDE_ENV_FILE` for direnv-style reloads.
```json
{ "CwdChanged": [{ "hooks": [{ "type": "command", "command": "direnv export bash >> \"$CLAUDE_ENV_FILE\"" }] }] }
```

### FileChanged
Fires when a watched file changes on disk. Matcher = literal `|`-separated filenames (NOT a regex), e.g., `.envrc|.env`. Receives `file_path`. Can write to `$CLAUDE_ENV_FILE`.

### WorktreeCreate
Fires when a worktree is created via `--worktree` or `isolation: "worktree"`. No matcher. Replaces default git behavior. Print path to stdout (command hook) or return `hookSpecificOutput.worktreePath` (HTTP). Non-zero exit fails creation.

### WorktreeRemove
Fires when a worktree is removed (session exit or subagent finish). No matcher. No decision control.

### PreCompact
Fires before context compaction. Matcher = `manual | auto`. Exit 2 or `decision: "block"` blocks compaction.

### PostCompact
Fires after context compaction completes. Matcher = `manual | auto`. No decision control.

### Elicitation
Fires when an MCP server requests user input during a tool call. Matcher = MCP server name. Output `hookSpecificOutput.action` = `accept | decline | cancel` plus `content`.

### ElicitationResult
Fires after the user responds to an MCP elicitation, before the response goes back to the server. Matcher = MCP server name. Can override the user's answer.

## Events listed in prior drafts that are NOT documented

Cross-reference of the prior `SKILL.md` draft list against the live docs:

VERIFIED (exist in docs):
`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `SessionStart`, `SessionEnd`, `Stop`, `SubagentStart`, `SubagentStop`, `PreCompact`, `PermissionRequest`, `TaskCompleted`, `ConfigChange`, `WorktreeCreate`, `WorktreeRemove`, `Notification`, `TeammateIdle`.

Also from the older prose mention — VERIFIED:
`PostCompact`, `PermissionDenied`, `TaskCreated`, `InstructionsLoaded`, `CwdChanged`, `FileChanged`.

NOT DOCUMENTED — do not rely on these event names:
- `Setup` — no such event. Use `SessionStart` (matcher `startup`) for one-time setup behavior.

Additional events present in the docs that the prior draft missed (worth knowing):
`StopFailure`, `Elicitation`, `ElicitationResult`.

If you encounter a citation to `Setup` in any artifact, treat it as a fabrication and replace with `SessionStart` + the correct matcher.

## Hooks in skills and agents

Anchor: https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents

Skills and subagents may declare hooks in their YAML frontmatter using the same shape as `settings.json`. Scope is the component's lifetime; the harness cleans them up when the skill/agent finishes.

```yaml
---
name: secure-ops
description: Operations with security checks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
---
```

Notes:
- `Stop` hooks declared in subagent frontmatter auto-convert to `SubagentStop`.
- `once: true` is honored only in skill frontmatter (runs once per session, then removed).
- Skill/agent hooks are listed in `/hooks` with a `[Session]` source label.

## Plugin-provided hooks

Plugins declare hooks at `<plugin-root>/hooks/hooks.json` using the same `hooks` object shape. They activate when the plugin is enabled and show as `[Plugin]` in `/hooks`.

```json
{
  "description": "Auto-format on edit",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh", "timeout": 30 }
        ]
      }
    ]
  }
}
```

Use `${CLAUDE_PLUGIN_ROOT}` for plugin-bundled scripts and `${CLAUDE_PLUGIN_DATA}` for persistent plugin state.

## Referencing hooks in CLAUDE.md / SKILL.md

When an instruction artifact relies on a hook, cite it precisely so Claude can verify it exists and degrade gracefully if it doesn't. Pattern:

> This project has a `SessionStart` hook at `.claude/hooks/load_env.sh` that exports DB credentials into `$CLAUDE_ENV_FILE`. If the hook is missing or fails, run `source .envrc` manually before any Bash tool call that touches the database.

Required pieces:
1. **Event name** (verified against the catalog above).
2. **Hook script path** (relative to `$CLAUDE_PROJECT_DIR` or `${CLAUDE_PLUGIN_ROOT}`).
3. **Observable effect** (what the hook does that Claude can rely on).
4. **Fallback** (what Claude does when the hook is absent — never assume the hook fired).

Do not paste full hook configs into CLAUDE.md. Configs belong in `settings.json`; CLAUDE.md cites the contract.

## Anti-patterns

- **Inventing events.** Never cite an event name that isn't in the catalog above. `Setup`, `OnEdit`, `BeforeCommit` etc. do not exist; the harness silently ignores unknown event keys, which looks like the hook is "broken" when it was never registered.
- **Writing executable hook logic in `skills/` markdown as if Claude runs it.** Claude reads SKILL.md; the harness reads `hooks` blocks. A hook described in prose with no corresponding `settings.json` / frontmatter entry will never fire.
- **Omitting the matcher when one is required.** A `PreToolUse` block with no matcher fires on every tool call — including `Read`, `Glob`, `WebFetch`. This is almost never what authors intend. Set `matcher` to the specific tool names you mean to gate.
- **Treating stdout as user-facing.** Stdout from `command` hooks is parsed as JSON or injected into Claude's context (depending on event), not shown to the user. User-facing messages go to `systemMessage` in JSON output, or to stderr with exit 2 for blocking feedback.
- **Mixing exit-2 blocks with JSON output.** If your hook exits 2, stdout JSON is ignored. Pick one mode per code path.
- **Assuming hooks fired.** CLAUDE.md should always describe a fallback for when the hook is absent — users may be on a fresh checkout, the file watcher may have missed an edit, or `disableAllHooks` may be set.
- **Using regex syntax in `FileChanged` matchers.** `FileChanged` splits on `|` into literal filenames; regex characters are not interpreted.

Source: https://code.claude.com/docs/en/hooks (fetched 2026-04-18).
