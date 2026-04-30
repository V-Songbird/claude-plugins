# Plan mode and plan files

Reference for instructing Claude Code to plan before implementing. Covers the `EnterPlanMode` / `ExitPlanMode` tools, `permissionMode: "plan"`, plan-file conventions, and exact phrasing that makes the planning tools fire.

## What plan mode is

Plan mode is a permission mode in which Claude analyzes the codebase with read-only operations and proposes a plan, but does not edit files or run state-changing commands. Reads, Grep, Glob, and exploratory Bash for inspection still work; Edit/Write and side-effecting tools are gated. Plan mode ends when Claude calls `ExitPlanMode`, which presents the plan to the user for approval before any execution begins. (Permission prompts otherwise apply the same as default mode.)

## Three ways to enter plan mode

Authors of SKILL.md / CLAUDE.md should pick the entry path that matches the lifecycle they control:

1. **Tool call inside a session** — `EnterPlanMode` is a built-in tool (no permission required, no parameters). Claude invokes it to switch the live session into plan mode. Useful when an instruction reads "before implementing, plan first."
2. **Session start config** — set `defaultMode` in `.claude/settings.json`:
   ```json
   { "permissions": { "defaultMode": "plan" } }
   ```
   Or pass `--permission-mode plan` at launch (also works with `-p` headless). Use when the project should always begin in plan mode.
3. **Subagent dispatch** — set `permissionMode: "plan"` in the subagent's frontmatter (or in the `Agent` tool's JSON config alongside `description`, `prompt`, `tools`). The field is named `permissionMode`, NOT `mode`. Note: if the parent session is in `auto`, `acceptEdits`, or `bypassPermissions`, the parent mode wins and the subagent's `permissionMode` is ignored.

User-facing alternates: `Shift+Tab` cycles into plan mode interactively; `/plan <prompt>` prefixes a single message into plan mode. Don't instruct downstream Claude to "press Shift+Tab" — that's a human gesture. Tell it to call `EnterPlanMode`.

## ExitPlanMode schema and semantics

`ExitPlanMode` requires permission (per tools-reference). It presents a plan for user approval and exits plan mode on accept. On approval the user picks how execution continues (auto / acceptEdits / manual review / keep planning / refine via Ultraplan), with an option to clear planning context first.

**`allowedPrompts` schema.** `ExitPlanMode` accepts an optional `{ allowedPrompts?: Array<{ tool: "Bash"; prompt: string }> }` to pre-approve specific `Bash` commands for the post-plan execution phase. The parameter is real — the Agent SDK tool-description sources document it and [anthropics/claude-code#27160](https://github.com/anthropics/claude-code/issues/27160) details its runtime behavior — though the canonical tools-reference table at `/en/tools-reference` does not inline its schema. **Caveat:** pre-approvals granted via `allowedPrompts` persist for the entire session, not just the plan's scope. The GitHub issue documents a case where a plan-mode pre-approval for `git rebase`-adjacent commands later auto-approved an unrelated `git push --force-with-lease`. For commands that must gate per-invocation, prefer `permissions.allow` rules in `.claude/settings.json` (e.g. `Bash(npm test)`, `Bash(git commit *)`), or have the user pick "approve and start in auto mode" at the approval prompt. When an artifact instructs use of `allowedPrompts`, require it to note the session-wide scope caveat alongside the invocation.

## Plan file structure

Claude Code does NOT define a formal plan-file format. The plan is presented inline in the `ExitPlanMode` call as free-form markdown. `Ctrl+G` opens it in the user's default editor for direct edit before approval. When the user accepts, Claude Code names the session from the plan content (unless the session already has a name).

Recommended sections for plans Claude writes (use these as defaults; nothing in the runtime requires them):

- **Problem** — one paragraph: what's broken or missing, why now.
- **Approach** — bullet list: the chosen direction and discarded alternatives.
- **Files touched** — bullet list of absolute paths with one-line per-file intent.
- **Risks** — anything reversible-but-painful, irreversible, or that crosses a trust boundary.
- **Test strategy** — exact commands to run after each phase; what passing looks like.

## When to instruct planning

Add an "enter plan mode first" instruction when the work involves:

- Multi-file changes (3+ files touched, or any cross-module refactor).
- Architectural changes (new abstractions, dependency reshuffles, API shape changes).
- Irreversible actions (schema migrations, deletions outside the session, force-pushes, deploys).
- The user explicitly said "plan first" or "draft a plan."
- Work spanning a long agentic loop where mid-stream correction is expensive.

## When NOT to instruct planning

Planning has overhead — a forced plan for trivial work wastes a turn. Skip the instruction when:

- Single-file fix with an obvious diff.
- Read-only inspection ("explain this function", "find where X is set").
- Approach already approved earlier in the conversation.
- Instruction artifact targets a hook or non-interactive flow with no user to approve `ExitPlanMode`.

## Tools available in plan mode

Plan mode is "Reads only" per the permission-modes table. Claude can use Read, Grep, Glob, LS, reasoning tools (Skill, AskUserQuestion, TodoWrite/TaskList family), and exploratory Bash. Edit, Write, NotebookEdit, and other write tools are gated. Permission prompts for any gated tool still appear the same as in default mode — plan mode does not silently auto-deny.

For deep codebase research without flooding the main context, plan mode delegates to the built-in **Plan subagent** (read-only tools, denied Write/Edit, inherits the main model). This avoids infinite nesting since subagents cannot spawn other subagents.

## Instruction patterns

Correct (fires the tool):
```
Before editing, call EnterPlanMode and draft the change as a plan with sections Problem / Approach / Files touched / Risks / Test strategy. Call ExitPlanMode to present it.
```

Correct (subagent dispatch):
```
Dispatch a subagent with permissionMode: "plan" to research the auth flow and return a migration plan.
```

Incorrect (does not fire the tool — describes a UI gesture):
```
Press Shift+Tab to enter plan mode, then write a plan.
```

Incorrect (vague — Claude may skip planning entirely):
```
Think about this carefully before changing anything.
```

Incorrect (wrong field name — frontmatter requires `permissionMode`, not `mode`):
```yaml
mode: plan
```

## Plan-mode subagents in brief

Set `permissionMode: "plan"` in subagent frontmatter or the `Agent` tool's JSON to spawn a research-only worker that returns a plan to the parent. Parent-mode precedence rules: `bypassPermissions` / `acceptEdits` / `auto` in the parent override the subagent's `permissionMode`. Plugin subagents do not honor `permissionMode` at all (the field is ignored when loaded from a plugin).

Sources: https://code.claude.com/docs/en/common-workflows ; https://code.claude.com/docs/en/tools-reference (fetched 2026-04-18).
