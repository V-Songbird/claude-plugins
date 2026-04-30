# SKILL.md authoring reference

Skills follow the [Agent Skills](https://agentskills.io) open standard. Claude Code extends it with invocation control, subagent execution, and dynamic context injection.

## 1. Frontmatter reference

YAML between `---` markers at the top of `SKILL.md`. All fields optional; `description` is recommended.

| Field | Required | Values | Notes |
|---|---|---|---|
| `name` | No | string, lowercase letters/numbers/hyphens, max 64 chars | Becomes the `/slash-command`. If omitted, uses the directory name. |
| `description` | Recommended | string | What the skill does and when to use it. If omitted, uses first paragraph of body. Front-load the key use case — combined `description` + `when_to_use` truncated at **1,536 chars** in the skill listing. |
| `when_to_use` | No | string | Trigger phrases or example requests. Appended to `description` in listing; counts toward 1,536-char cap. |
| `argument-hint` | No | string, e.g. `[issue-number]` | Shown during autocomplete. |
| `arguments` | No | space-separated string OR YAML list of names | Named positional arguments for `$name` substitution in the body. Names map to argument positions in order — `arguments: [issue, branch]` makes `$issue` expand to the first argument and `$branch` to the second. |
| `disable-model-invocation` | No | `true` \| `false` (default `false`) | `true` blocks Claude from auto-loading; only user-invoked. |
| `user-invocable` | No | `true` \| `false` (default `true`) | `false` hides from `/` menu; only Claude can invoke. |
| `allowed-tools` | No | space-separated string OR YAML list | Pre-approves tools while skill is active. Supports `Bash(git add *)` patterns. |
| `model` | No | same values as [`/model`](https://code.claude.com/docs/en/model-config) (`opus`/`sonnet`/`haiku`/full id) OR `inherit` | Model to use while this skill is active. The override applies for the rest of the **current turn only** and is not saved to settings; the session model resumes on the next prompt. `inherit` keeps the active model. |
| `effort` | No | `low` \| `medium` \| `high` \| `xhigh` \| `max` | Available levels depend on model. Overrides session effort. |
| `context` | No | `fork` | Run skill in a forked subagent context. |
| `agent` | No | `Explore` \| `Plan` \| `general-purpose` \| custom agent name | Subagent type when `context: fork` is set. **Silently ignored without `context: fork`.** Defaults to `general-purpose`. |
| `hooks` | No | hooks config object | Hooks scoped to this skill's lifecycle (see references/hooks.md). |
| `paths` | No | comma-separated string OR YAML list of globs | Limits auto-activation to matching files. Same syntax as path-specific rules. |
| `shell` | No | `bash` (default) \| `powershell` | Shell for `` !`cmd` `` injection. PowerShell requires `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`. |

Example:

```yaml
---
name: my-skill
description: What this skill does and when to use it.
when_to_use: Trigger when user says "do the thing" or asks about X.
disable-model-invocation: false
allowed-tools: Read Grep Bash(git status *)
paths: src/**/*.ts, src/**/*.tsx
---
```

## 2. Skill content lifecycle

- When invoked, the rendered `SKILL.md` enters the conversation as a **single message and stays there for the rest of the session**.
- Claude Code does **not re-read** the file on later turns. Edits to `SKILL.md` after invocation do not retroactively apply.
- Write guidance as **standing instructions** that apply throughout the task, not one-time steps the model must remember to repeat.
- **Auto-compaction** carries invoked skills forward within a token budget. After summarization, Claude Code re-attaches the most recent invocation of each skill, keeping the **first 5,000 tokens** of each. Re-attached skills share a **combined budget of 25,000 tokens**, filled from most-recently-invoked first; older skills can be dropped entirely.
- If a skill stops influencing behavior, content is usually still present — strengthen `description` and instructions, use hooks for deterministic enforcement, or re-invoke after compaction to restore full content.

## 3. Char budgets and cap thresholds

| Limit | Value | Scope |
|---|---|---|
| Per-entry description | 1,536 chars | Combined `description` + `when_to_use` in skill listing. Overflow truncated. |
| Global skill listing | 1% of context window, fallback **8,000 chars** | All skill descriptions combined. Override with `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var. |
| Per-skill on compaction | 5,000 tokens | First N tokens of each re-attached skill. |
| Combined re-attached | 25,000 tokens | Total across all re-attached skills after compaction. |
| Body length tip | < 500 lines | Soft tip; move detail to supporting files. |

## 4. Supporting files pattern

Each skill is a directory; `SKILL.md` is the entrypoint. Other files load only when referenced.

```
my-skill/
├── SKILL.md           # required; main instructions
├── reference.md       # detailed reference; loaded when needed
├── examples.md        # examples; loaded when needed
└── scripts/
    └── helper.py      # executed, not loaded into context
```

Reference from `SKILL.md` so Claude knows what each file holds and when to load it:

```markdown
## Additional resources
- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

Supporting files are **not auto-loaded** — Claude reads them with the `Read` tool when the SKILL.md instructs.

## 5. String substitutions

Replaced when the skill is rendered into the conversation.

| Variable | Expands to |
|---|---|
| `$ARGUMENTS` | Full argument string as typed. If absent from body, runtime appends `ARGUMENTS: <value>`. |
| `$ARGUMENTS[N]` | Nth argument by 0-based index, shell-style quoted. |
| `$N` | Shorthand for `$ARGUMENTS[N]`. `$0` = first, `$1` = second. |
| `$name` | Named argument declared in the `arguments` frontmatter list. Names map to positions in order: with `arguments: [issue, branch]`, `$issue` is the first argument and `$branch` is the second. |
| `${CLAUDE_SESSION_ID}` | Current session ID. |
| `${CLAUDE_SKILL_DIR}` | Directory containing this `SKILL.md`. For plugin skills this is the skill's subdirectory, not the plugin root. Use in injection commands to reference bundled scripts regardless of cwd. |

Multi-word indexed args require quotes: `/my-skill "hello world" second` → `$0` = `hello world`, `$1` = `second`.

Example:

```yaml
---
name: session-logger
description: Log activity for this session
---

Log to logs/${CLAUDE_SESSION_ID}.log:

$ARGUMENTS
```

## 6. Dynamic context injection

Runs **before** the skill content reaches Claude. Output replaces the placeholder; Claude only sees the final result, not the command.

Inline:

```markdown
- PR diff: !`gh pr diff`
- Changed files: !`gh pr diff --name-only`
```

Fenced (multi-line) — open with ` ```! `:

````markdown
```!
node --version
npm --version
git status --short
```
````

Disable globally with `"disableSkillShellExecution": true` in settings — each command is replaced with `[shell command execution disabled by policy]`. Bundled and managed skills are not affected. Most useful in managed settings where users cannot override.

Tip: include the literal word **`ultrathink`** anywhere in skill content to enable extended thinking.

## 7. Invocation control

Three patterns control who invokes and when full content loads:

| Frontmatter | User invokes | Claude invokes | Description in context | Full skill loads |
|---|---|---|---|---|
| (default) | Yes | Yes | Always | When invoked |
| `disable-model-invocation: true` | Yes | No | Not in context | When user invokes |
| `user-invocable: false` | No | Yes | Always | When invoked |

Notes:
- `user-invocable: false` only hides from `/` menu; does **not** block programmatic Skill-tool access. Use `disable-model-invocation: true` to block model invocation.
- Subagents preloaded with skills get the **full skill content injected at startup**, not just the description.

## 8. Pre-approved tools via `allowed-tools`

Grants permission while the skill is active so Claude doesn't prompt per use. Does **not** restrict which tools are available — every tool remains callable; non-listed tools fall back to permission settings.

Space-separated string:

```yaml
allowed-tools: Read Grep Bash(git add *) Bash(git commit *) Bash(git status *)
```

YAML list:

```yaml
allowed-tools:
  - Read
  - Grep
  - Bash(git add *)
  - Bash(git commit *)
```

To **deny** tools to a skill, add deny rules in permission settings.

## 9. Running skills in a subagent

Add `context: fork` to run the skill in an isolated subagent. The skill content becomes the prompt. The subagent has **no access to the main conversation history**.

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:
1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

`agent` field picks the execution environment (model, tools, permissions): built-in `Explore`, `Plan`, `general-purpose`, or any custom agent under `.claude/agents/`. If omitted, uses `general-purpose`. Without `context: fork`, the `agent` field is ignored.

**Warning:** `context: fork` only makes sense for skills with **explicit task instructions**. A skill that contains only guidelines like "use these API conventions" gives the subagent no actionable prompt and returns no meaningful output.

## 10. Skill locations and naming

Priority order (higher wins on name conflict):

| Location | Path | Scope |
|---|---|---|
| Enterprise | Managed settings | All org users |
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` | All your projects |
| Project | `.claude/skills/<skill-name>/SKILL.md` | This project |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md` | Where plugin enabled |

Plugin skills use a `plugin-name:skill-name` namespace and cannot collide with other levels. If a skill and a `.claude/commands/` file share a name, the skill wins.

`name` constraint: lowercase letters, numbers, hyphens; max 64 chars.

Live change detection watches `~/.claude/skills/`, project `.claude/skills/`, and `.claude/skills/` inside `--add-dir` directories — edits take effect within the session. Creating a top-level skills directory that did not exist at session start requires a restart.

Nested discovery: when working with files under `packages/frontend/`, Claude Code also loads skills from `packages/frontend/.claude/skills/` (monorepo support).

## 11. Troubleshooting

**Skill not triggering**
1. Check `description` includes keywords users would naturally say.
2. Verify it appears in "What skills are available?".
3. Rephrase the request to match the description.
4. Invoke directly with `/skill-name` if user-invocable.

**Skill triggers too often**
1. Make `description` more specific.
2. Add `disable-model-invocation: true` if only manual invocation is wanted.

**Descriptions cut short**
- All skill **names** are always included; descriptions get shortened to fit the global budget.
- Raise the budget with `SLASH_COMMAND_TOOL_CHAR_BUDGET`, or trim `description` + `when_to_use` (front-load key use case — capped at 1,536 chars per entry regardless of global budget).

Source: https://code.claude.com/docs/en/skills (fetched 2026-04-26).
