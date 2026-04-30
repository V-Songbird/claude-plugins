# settings.json reference (instruction-author scope)

## Scope of this file

This is the *instruction-author-relevant subset* of `settings.json` — only the keys that change how a CLAUDE.md, skill, command, agent, or plugin instruction artifact actually runs. For the full settings surface (model selection, telemetry, attribution, sandbox, marketplaces, plugin trust, etc.), see the `update-config` skill that ships with Claude Code, or the official reference at https://code.claude.com/docs/en/settings.

If your instruction depends on a settings value being a particular thing, document the dependency here and tell the reader to set it via `update-config`. Do not instruct Claude to edit `settings.json` directly inline.

## File locations and precedence

Higher precedence overrides lower. Arrays merge across scopes (concatenated and deduplicated); scalars are replaced.

| Rank | Scope | Path |
| :--- | :--- | :--- |
| 1 (highest) | Managed | `managed-settings.json` (system dir, MDM, registry, or server-managed) |
| 2 | Command-line flags | e.g. `--add-dir`, `--permission-mode` |
| 3 | Local | `.claude/settings.local.json` (gitignored) |
| 4 | Project | `.claude/settings.json` (committed) |
| 5 (lowest) | User | `~/.claude/settings.json` |

Run `/status` inside Claude Code to see which sources are active.

## settings.json keys that affect instruction artifacts

| Key | Type | Purpose | Why instruction authors care |
| :--- | :--- | :--- | :--- |
| `hooks` | object | Register commands to run at lifecycle events | Any "always do X before/after Y" behavior must live here, not in prose. See `references/hooks.md`. |
| `permissions.allow` / `ask` / `deny` | string[] | Tool-use rules in `Tool` or `Tool(specifier)` form | Determines whether the instruction's tool calls fire silently, prompt, or are blocked. See `references/permissions.md`. |
| `permissions.additionalDirectories` | string[] | Extra working directories for file access (same as `--add-dir`) | An instruction that reads/edits paths outside the project root needs these listed, or the tool will refuse. |
| `permissions.defaultMode` | string | Default permission mode at startup (`default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`) | Affects whether your instruction's edits land without prompting. |
| `env` | object<string,string> | Environment variables loaded into Claude Code's process | The only stable way to ship an env var to every session for your team. Subset of vars below. |
| `defaultShell` | `"bash"` \| `"powershell"` | Shell for input-box `!` commands | If your instruction uses `` !`cmd` `` preprocessing on Windows, this and `CLAUDE_CODE_USE_POWERSHELL_TOOL` decide which shell runs it. |
| `disableSkillShellExecution` | boolean | Disables `` !`...` `` and ```` ```! ```` shell preprocessing in user/project/plugin skills and commands | If `true`, your skill's shell preamble is replaced with `[shell command execution disabled by policy]`. Bundled and managed skills are exempt. Author skills to degrade gracefully when this is set. |
| `disableAllHooks` | boolean | Disables every hook and the custom statusline | If your instruction depends on a hook firing, document this gate. |
| `includeGitInstructions` | boolean | Includes built-in commit/PR workflow text in the system prompt (default `true`) | Set `false` if your CLAUDE.md ships its own git workflow and you do not want the built-in prose competing with it. `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS` env var takes precedence. |
| `outputStyle` | string | Adjusts the system prompt with a named output style | Output styles can override tone instructions in your CLAUDE.md; mention if a style is required. |
| `agent` | string | Run the main thread as a named subagent | If your instruction assumes a particular subagent's tool list and prompt, set this. |

### Minimal JSON example

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": ["Bash(npm run lint)", "Read(~/.zshrc)"],
    "deny": ["Read(./.env)", "Read(./secrets/**)"],
    "additionalDirectories": ["../shared-docs/"],
    "defaultMode": "acceptEdits"
  },
  "env": {
    "CLAUDE_CODE_USE_POWERSHELL_TOOL": "1",
    "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": "1"
  },
  "defaultShell": "powershell",
  "disableSkillShellExecution": false,
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/audit.sh" }] }
    ]
  }
}
```

> Note on `toolConfig.askUserQuestion.previewFormat`: this key is referenced in some plugin examples to enable per-option preview rendering (`"markdown"` or `"html"`) for `AskUserQuestion`, but it is not part of the published settings reference. Treat it as experimental — verify against `--help` output of your installed Claude Code version before relying on it in shared instructions.

## Environment variables that change instruction behavior

Any of these can be set in the shell, in `env` inside `settings.json`, or in a script pointed to by `CLAUDE_ENV_FILE`.

| Variable | Values | Effect | Mention in an artifact when... |
| :--- | :--- | :--- | :--- |
| `CLAUDE_CODE_USE_POWERSHELL_TOOL` | `0` / `1` | Enables the native `PowerShell` tool. Required for `defaultShell: "powershell"` and for `shell: powershell` in skill frontmatter | The skill's shell preamble or hook expects PowerShell semantics. |
| `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` | `0` / `1` (default `0`) | When `1`, loads `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`, and `CLAUDE.local.md` from `--add-dir` directories | The instruction lives in a sibling repo that is loaded with `--add-dir` and you need its memory files picked up. |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | `0` / `1` (default `0`) | After every Bash/PowerShell command in the main session, return to the project working directory | The instruction tells Claude to run a `cd` that should not persist between commands. |
| `CLAUDE_ENV_FILE` | path to shell script | Sourced before every Bash command. Use to persist virtualenv / conda activation | The instruction depends on a shell environment (Python venv, Node version) being active. Also populated by `SessionStart` and `CwdChanged` hooks. |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | `0` / `1` (default `0`) | Enables agent-teams features and the `SendMessage`, `TeamCreate`, `TeamDelete` tools | The instruction directs Claude to coordinate with teammates or resume a stopped subagent by ID. |
| `DISABLE_TELEMETRY` | `0` / `1` | Disables telemetry collection. Also disables session quality surveys | The instruction relies on the `Monitor` tool — it is unavailable when this is set. |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | `0` / `1` | Equivalent to setting `DISABLE_AUTOUPDATER`, `DISABLE_FEEDBACK_COMMAND`, `DISABLE_ERROR_REPORTING`, and `DISABLE_TELEMETRY` together | Same as above — `Monitor` is gated off by this. |

> Note on `SLASH_COMMAND_TOOL_CHAR_BUDGET`: this variable is not present in the public env-vars reference at the time of writing. If your slash command's tool description is being truncated and you need to investigate, check `claude --help`, the changelog, or the `update-config` skill for the current knob name rather than guessing.

## How to *reference* settings from an instruction artifact

Do:
- State the dependency explicitly. ("This skill assumes `permissions.allow` includes `Bash(git status)`; otherwise the status check will prompt.")
- Tell the reader to use the `update-config` skill, the `/config` command, or `/permissions` to set it. ("Run `/permissions` and add `Bash(npm run test:*)` to the allowlist.")
- For team-scoped artifacts, recommend adding the key to `.claude/settings.json` (committed) so collaborators inherit it.
- For machine-specific tweaks (env vars with secrets, local paths), recommend `.claude/settings.local.json`.

Don't:
- Instruct Claude inline to edit `settings.json` itself. The harness reads `settings.json` at startup; mid-session edits do not always re-load. Route through `update-config`.
- Hard-code a value the user must set. State the requirement and let the user (or `update-config`) decide the value.
- Assume `additionalDirectories` makes a sibling repo's `.claude/` configuration discoverable. It grants *file access*, not configuration discovery — see `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` for the memory-file opt-in.
- Document `defaultShell: "powershell"` without also documenting the `CLAUDE_CODE_USE_POWERSHELL_TOOL=1` prerequisite.

Sources: https://code.claude.com/docs/en/settings ; https://code.claude.com/docs/en/env-vars (fetched 2026-04-18).
