# Permissions reference

How permission flow gates tool firing in instruction artifacts (skills, agents, commands, hooks). Rules + modes determine whether a tool call proceeds, prompts, or is denied.

## 1. Permission system overview

Claude Code evaluates each tool call against three rule lists (`deny`, `ask`, `allow`) and a session **mode**. Rules live in `settings.json` at user / project / managed scopes; the mode is per session (or per-dispatch via the Agent tool's `mode` param). Precedence: **deny -> ask -> allow** — first matching rule wins, deny always trumps. Mode determines what happens when no rule matches (prompt, auto-accept, auto-deny, etc.).

Tiered defaults (built into the harness, not overridable by allow rules):

| Tool type | Example | Default behavior |
| :-- | :-- | :-- |
| Read-only | Read, Grep, Glob, `ls`, `cat` | No prompt, ever |
| Bash (write/exec) | shell commands | Prompt; "yes don't ask again" persists per-project |
| File modification | Edit, Write | Prompt; "yes don't ask again" until session end |

## 2. Permission modes

| Mode | Behavior | When to use |
| :-- | :-- | :-- |
| `default` | Prompts on first use of each tool | Interactive dev |
| `acceptEdits` | Auto-accepts file edits + common fs cmds (`mkdir`, `touch`, `mv`, `cp`) for paths in cwd / `additionalDirectories` | Trusted edit-heavy work |
| `plan` | Read-only; cannot modify files or execute commands | Plan Mode (see references/plans.md) |
| `auto` | Auto-approves with classifier-based safety checks (research preview) | Long unattended runs |
| `dontAsk` | Auto-denies anything not pre-approved via `permissions.allow` or `/permissions` | Strict allowlist environments |
| `bypassPermissions` | Skips prompts entirely, except writes to `.git`, `.claude` (with carve-outs), `.vscode`, `.idea`, `.husky` | Sandboxed containers/VMs only |

Set `defaultMode` in any settings file. `bypassPermissions` and `auto` can be locked off via `permissions.disableBypassPermissionsMode` / `disableAutoMode` set to `"disable"`.

## 3. Setting the mode

| Surface | How |
| :-- | :-- |
| Persistent (session default) | `"defaultMode": "<mode>"` in settings.json (user / project / managed) |
| Interactive (current session) | `/permissions` UI |
| Per-dispatch (subagent invocation) | Agent tool `mode` parameter |
| CLI startup | `--permission-mode <mode>` |

Skill / agent frontmatter does **not** set a session mode. `allowed-tools` in frontmatter grants per-call permission while the artifact is active (see section 7) — it does not change the mode.

## 4. Tool-specific rule syntax

Format: `Tool` (matches all uses) or `Tool(specifier)`.

| Pattern | Effect |
| :-- | :-- |
| `Bash` | Matches all Bash commands |
| `Bash(*)` | Equivalent to `Bash` |
| `Read` | Matches all file reads |
| `Edit` | Matches all built-in file edits |
| `WebFetch` | Matches all web fetches |
| `Bash(npm run build)` | Exact command match |
| `Bash(npm run *)` | Prefix; `*` requires word boundary when preceded by space |
| `Read(./.env)` | File in cwd |
| `Read(~/Documents/*.pdf)` | Home-relative |
| `Edit(/src/**/*.ts)` | Project-root-relative (single leading `/`) |
| `Read(//Users/alice/secrets/**)` | **Absolute** filesystem path (double leading `/`) |
| `WebFetch(domain:example.com)` | Per-domain |
| `mcp__server` | All tools from MCP server `server` |
| `mcp__server__*` | Same, wildcard form |
| `mcp__server__tool_name` | Specific MCP tool |
| `Agent(SubagentName)` | Specific subagent (e.g. `Agent(Explore)`) |

Storage: `permissions.allow`, `permissions.ask`, `permissions.deny` arrays in `settings.json`. Scopes (precedence high -> low): managed -> CLI args -> `.claude/settings.local.json` -> `.claude/settings.json` -> `~/.claude/settings.json`. **Deny at any scope cannot be overridden anywhere.**

## 5. Skill rules

The canonical permissions doc does **not** define a `Skill(name)` rule syntax. The Skill tool itself is governed as a tool name:

| Goal | Rule |
| :-- | :-- |
| Disable Skill tool entirely | `"deny": ["Skill"]` |
| Allow all skill invocations without prompt | `"allow": ["Skill"]` |

To control which **subagents** Claude can dispatch, use `Agent(Name)` rules — that is the documented per-callable invocation control. There is no first-class per-skill allow/deny rule; gate skills via the broader `Skill` tool name or via PreToolUse hooks that inspect the skill name.

## 6. Bash rules

Bash specifiers support glob `*` at any position. Behaviors that bite:

| Pattern | Matches | Notes |
| :-- | :-- | :-- |
| `Bash(git *)` | `git status`, `git push origin main` | Word boundary enforced by leading space |
| `Bash(git:*)` | Same as above | `:*` only recognized at end |
| `Bash(ls *)` | `ls -la` | Does NOT match `lsof` (word boundary) |
| `Bash(ls*)` | `ls -la`, `lsof` | No boundary |
| `Bash(* install)` | `npm install`, `pip install` | Trailing match |
| `Bash(git * main)` | `git checkout main`, `git push origin main` | `*` spans args |
| `Bash(npm test *)` | `npm test`, `timeout 30 npm test` | Wrappers stripped: `timeout`, `time`, `nice`, `nohup`, `stdbuf`, bare `xargs` |

Compound commands (`&&`, `||`, `;`, `|`, `|&`, `&`, newline) are split — each subcommand must match independently. `Bash(safe-cmd *)` does NOT authorize `safe-cmd && other-cmd`.

Read-only commands (built-in, not configurable): `ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `diff`, `stat`, `du`, `cd`, read-only `git`. These never prompt unless an explicit `ask`/`deny` rule overrides.

Wrapper trap: `direnv exec`, `devbox run`, `mise exec`, `npx`, `docker exec` are **not** stripped. `Bash(devbox run *)` allows `devbox run rm -rf .`. Write specific rules like `Bash(devbox run npm test)` instead.

Argument-constraint patterns are fragile (e.g. `Bash(curl http://github.com/ *)` misses `-X GET` reorderings, `https://`, redirects, env-var URLs). For URL filtering, deny `curl`/`wget` and use `WebFetch(domain:...)` instead.

## 7. `allowed-tools` in frontmatter

`allowed-tools: [Read, Edit, Bash(npm test *)]` in skill / agent / command frontmatter **grants** permission for the listed tools while the artifact is active, suppressing prompts that would otherwise appear. It does **NOT**:

- Restrict the artifact to only those tools — other tools remain callable, governed by baseline `settings.json` rules.
- Override `deny` rules — denies still win.
- Persist across the session — scope is the artifact's active window.

To **block** a tool from an artifact, add a `deny` rule in `settings.json`. Removing a tool from `allowed-tools` only removes the auto-grant; it does not prevent the tool from firing if baseline permissions allow it.

## 8. Additional directories

Extend file access beyond the launch directory:

| Surface | How |
| :-- | :-- |
| Startup | `--add-dir <path>` |
| Session | `/add-dir <path>` |
| Persistent | `additionalDirectories` array in `settings.json` |

What's loaded from `--add-dir` directories:

| Configuration | Loaded? |
| :-- | :-- |
| `.claude/skills/` | Yes (with live reload) |
| `.claude/settings.json` | Only `enabledPlugins` and `extraKnownMarketplaces` |
| `CLAUDE.md`, `.claude/rules/`, `CLAUDE.local.md` | Only if `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` |
| Subagents, commands, output styles, hooks, other settings | **No** — load only from cwd/parents, `~/.claude/`, managed |

To share non-skill config across projects: put it in `~/.claude/`, package it as a plugin, or launch from the directory containing `.claude/`.

## 9. ExitPlanMode `allowedPrompts`

Plan Mode (`plan`) blocks all writes/exec. `ExitPlanMode` accepts optional `allowedPrompts: Array<{ tool: "Bash"; prompt: string }>` to pre-approve specific `Bash` commands for the post-plan execution phase — but NOT per-plan scope: pre-approvals persist session-wide ([anthropics/claude-code#27160](https://github.com/anthropics/claude-code/issues/27160)). For narrower per-invocation gating, use `permissions.allow` rules. See **references/plans.md** for the full Plan Mode lifecycle and `ExitPlanMode` schema.

## 10. Common authoring mistakes

| Mistake | Symptom | Fix |
| :-- | :-- | :-- |
| Using `allowed-tools` to block tools | Other tools still fire | Add explicit `deny` rule in settings.json |
| Forgetting deny precedence | Allow rule appears ignored | Find the deny rule (any scope, including managed) — it wins |
| Pattern too broad | `Bash(devbox run *)` allows arbitrary commands | Pin the inner command: `Bash(devbox run npm test)` |
| Pattern too narrow on args | `Bash(curl http://github.com/ *)` misses `-X` reorderings, `https://`, redirects | Deny network bash; use `WebFetch(domain:...)` |
| Confusing `/path` with absolute | `Edit(/src/**)` matches `<project>/src/**`, not `/src/**` | Use `//` prefix for true absolute paths |
| Compound command assumption | `Bash(safe *)` thought to cover `safe && other` | Each subcommand matches independently — write rules for both |
| Read deny vs Bash bypass | `Read(./.env)` deny doesn't stop `cat .env` | Add `Bash(cat .env)` deny too, or enable sandbox |
| Symlink escape (allow side) | Symlink in allowed dir points outside, still prompts | Expected: allow rules require both symlink AND target to match |
| Expecting `.claude/` from `--add-dir` | Hooks/agents/commands don't load | Only skills auto-load; package as plugin or use `~/.claude/` |
| Replacing `autoMode.soft_deny` | All built-in safety rules vanish | Always start from `claude auto-mode defaults`, edit, then save |

Source: https://code.claude.com/docs/en/permissions (fetched 2026-04-18).
