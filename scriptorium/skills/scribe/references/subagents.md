# Subagents — authoring reference

Audience: Claude Code authoring a subagent definition (or a main-session prompt that dispatches one). Schema-forward. For the tool catalog see `tools.md`. For plan mode internals see `plans.md`.

A subagent is a Markdown file with YAML frontmatter. It runs in its own context window with its own system prompt, tool restrictions, and permission state. The main session sees only its final summary.

---

## 1. When to write a subagent

Author a subagent when ALL hold:

- The work produces verbose intermediate output (search results, logs, file dumps) the main session will not reference again.
- A scoped natural-language summary is sufficient as the return value.
- The work is self-contained — no mid-task back-and-forth with the user is required (see §5 on `AskUserQuestion`).
- Either parallelism, isolation (`worktree`), or a different model/effort is desirable.

Do NOT write a subagent for: short targeted edits, work needing iterative user feedback, work whose intermediate state the main session must inspect.

Subagents CANNOT spawn other subagents. Built-in subagents (`Explore`, `Plan`, `general-purpose`) cover most generic cases — write a custom one only when you keep dispatching the same instructions.

---

## 2. File layout & discovery

| Location                       | Scope                  | Priority    |
| :----------------------------- | :--------------------- | :---------- |
| Managed settings `.claude/agents/` | Org-wide           | 1 (highest) |
| `--agents` CLI flag (JSON)     | Current session        | 2           |
| `<project>/.claude/agents/*.md`| Current project        | 3           |
| `~/.claude/agents/*.md`        | All your projects      | 4           |
| `<plugin_root>/agents/*.md`    | Where plugin is enabled| 5 (lowest)  |

Project subagents are discovered by walking up from cwd. `--add-dir` directories are NOT scanned for subagents. Plugin subagents appear in `/agents` typeahead as `<plugin-name>:<agent-name>`.

Subagents are loaded at session start. Adding a file mid-session requires `/agents` reload or session restart.

---

## 3. Frontmatter reference

Only `name` and `description` are required.

| Field             | Required | Values / Notes                                                                                          |
| :---------------- | :------- | :------------------------------------------------------------------------------------------------------ |
| `name`            | Yes      | lowercase + hyphens, unique                                                                             |
| `description`     | Yes      | When Claude should delegate. Include "use proactively" to encourage automatic dispatch                  |
| `tools`           | No       | Allowlist (CSV). Omit to inherit all from main. `Agent(x,y)` restricts which subagents a `--agent` main can spawn (no effect inside subagents) |
| `disallowedTools` | No       | Denylist applied BEFORE `tools` resolution                                                              |
| `model`           | No       | `sonnet` \| `opus` \| `haiku` \| full ID (e.g. `claude-opus-4-7`) \| `inherit`. Default: `inherit`      |
| `effort`          | No       | `low` \| `medium` \| `high` \| `xhigh` \| `max` (model-dependent). Overrides session                    |
| `permissionMode`  | No       | `default` \| `acceptEdits` \| `auto` \| `dontAsk` \| `bypassPermissions` \| `plan`. Parent `bypassPermissions`/`acceptEdits`/`auto` overrides this |
| `maxTurns`        | No       | Hard stop on agentic turns. Set explicitly for bounded tasks. Derive per the formula in [workflow-skill-shapes.md](workflow-skill-shapes.md) § 3 — `(numbered steps × 2) + 4 safety, rounded up to nearest 5, capped at 30`. State the derivation in a comment beside the field so reviewers can question it. |
| `skills`          | No       | List of skill names. Full content injected at startup. Subagents do NOT inherit parent skills           |
| `mcpServers`      | No       | List of inline MCP server defs OR string references to already-configured servers                       |
| `hooks`           | No       | Lifecycle hooks scoped to this subagent. `Stop` auto-converts to `SubagentStop` at runtime              |
| `memory`          | No       | `user` \| `project` \| `local`. Persistent `MEMORY.md` directory; auto-enables Read/Write/Edit          |
| `background`      | No       | `true` to always run in background. Default `false`                                                     |
| `isolation`       | No       | Only valid value: `"worktree"`. Spawns subagent in a temporary git worktree; cleaned up if no changes   |
| `color`           | No       | `red` \| `blue` \| `green` \| `yellow` \| `purple` \| `orange` \| `pink` \| `cyan`                      |
| `initialPrompt`   | No       | Auto-submitted as first user turn ONLY when run as main via `--agent` / `agent` setting. Ignored when dispatched as subagent |

Body: system prompt. Subagents receive ONLY this prompt + basic env (cwd) — not Claude Code's default system prompt.

---

## 4. Plugin-shipped agent restrictions (VERIFIED)

From plugins-reference: *"For security reasons, `hooks`, `mcpServers`, and `permissionMode` are not supported for plugin-shipped agents."*

From sub-agents doc: *"plugin subagents do not support the `hooks`, `mcpServers`, or `permissionMode` frontmatter fields. These fields are ignored when loading agents from a plugin."*

Plugin agents support exactly: `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation`.

If a plugin agent needs a denied field, the user must copy the file into `.claude/agents/` or `~/.claude/agents/`. Workaround for permission needs: ship rules in `permissions.allow` of `settings.json` — but those apply session-wide, not just to the agent.

---

## 5. Capability limits (subagent CANNOT)

- **Spawn other subagents.** Hard rule. Use chained main-session dispatches or Skills instead.
- **Inherit cwd changes.** A subagent starts in the main session's cwd; `cd` inside the subagent does not persist between Bash/PowerShell calls and never leaks back to main. For an isolated repo copy use `isolation: worktree`.
- **Inherit parent skills.** Must be listed explicitly via `skills:`.
- **Use `EnterWorktree` / `ExitWorktree`.** Worktree lifecycle is controlled via `isolation: worktree`, not the runtime tools.
- **Ask the user clarifying questions when running in BACKGROUND.** From sub-agents doc: *"If a background subagent needs to ask clarifying questions, that tool call fails but the subagent continues."* QUALIFIED — foreground subagents CAN invoke `AskUserQuestion`: *"Foreground subagents block the main conversation until complete. Permission prompts and clarifying questions (like `AskUserQuestion`) are passed through to you."* Authoring rule: never rely on `AskUserQuestion` inside a subagent body unless `background: false` is guaranteed AND the dispatcher did not background it via Ctrl+B.

---

## 6. Dispatching from main session (Agent tool)

In v2.1.63 the `Task` tool was renamed to `Agent`. Existing `Task(...)` references still alias.

Common input fields (verify exact schema in `tools.md`):

| Field             | Notes                                                         |
| :---------------- | :------------------------------------------------------------ |
| `description`     | Required. Short label for the task panel                      |
| `prompt`          | Required. The actual instructions to the subagent             |
| `subagent_type`   | Required. Name of subagent (or `general-purpose`)             |
| `model`           | Optional per-invocation override                              |
| `run_in_background` | Optional. Returns an agent ID; resume / read transcript later |
| `max_turns`       | Optional. Per-invocation cap                                  |
| `mode`            | Optional                                                      |
| `isolation`       | Optional. `"worktree"` per-invocation                         |
| `resume`          | Optional. Continue a stopped subagent by ID                   |

Resolution order for model: `CLAUDE_CODE_SUBAGENT_MODEL` env > per-invocation `model` > frontmatter `model` > main session model.

---

## 7. Preload skills (`skills:`)

```yaml
---
name: api-developer
description: Implement endpoints following team conventions
skills:
  - api-conventions
  - error-handling-patterns
---
```

Full skill content is injected into the subagent's context at startup — not merely made invokable. Use when:

- The subagent needs domain knowledge before its first turn.
- You want the skill content even if the subagent never invokes the skill explicitly.

Inverse pattern: a skill with `context: fork` runs in a subagent it spawns. Same underlying mechanism — see `skill-authoring.md`.

---

## 8. Background / isolation / max_turns patterns

Long-running isolated worker:

```yaml
---
name: refactor-worker
description: Apply mechanical refactor across the repo. Run in background.
background: true
isolation: worktree
maxTurns: 40
tools: Read, Edit, Write, Bash, Grep, Glob
---
```

Bounded read-only researcher:

```yaml
---
name: api-surveyor
description: Catalog public API surface; return JSON list only.
tools: Read, Grep, Glob
maxTurns: 10
model: haiku
---
```

Scoped MCP without polluting main:

```yaml
---
name: browser-tester
description: Drive Playwright for UI verification
mcpServers:
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
---
```

Background subagents pre-prompt the user for required permissions at launch and auto-deny anything not pre-approved. Press Ctrl+B to background a foreground task mid-run. `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` disables backgrounding entirely.

---

## 9. Return-channel discipline

The main session sees only the subagent's final assistant message. Structure the dispatch prompt so that message is directly usable:

- State the EXACT shape of the return ("return a JSON array of `{file, line, issue}`", "return a bulleted list under 200 words").
- Forbid recap of intermediate exploration ("do not summarize files you read; only report findings").
- Name the file paths the main session needs as absolute paths — they will not be re-resolved.
- For multi-step chains, dispatch sequentially from main; do not try to chain inside a subagent.

Subagent transcripts persist at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl` and are unaffected by main-conversation compaction. Auto-compaction inside a subagent uses the same ~95% threshold as main; override with `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`.

To resume a stopped subagent the main session uses `SendMessage` with the agent ID (requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).

---

Sources: https://code.claude.com/docs/en/sub-agents ; https://code.claude.com/docs/en/plugins-reference (fetched 2026-04-18).
