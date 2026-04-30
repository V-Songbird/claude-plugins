# Example: a strong subagent definition

A `dependency-auditor` subagent shipped from inside a plugin (`<plugin_root>/agents/dependency-auditor.md`). It scans a Node project for outdated and vulnerable dependencies and returns a structured, actionable summary. The design is strong because: (1) the frontmatter uses only fields permitted to plugin-shipped agents — `hooks`, `mcpServers`, and `permissionMode` are deliberately absent; (2) the prompt body resolves ambiguity up-front rather than delegating to `AskUserQuestion`; (3) the tool allowlist is tight (read + shell only — no `Edit` / `Write`); (4) `maxTurns` provides an explicit hard stop; and (5) the return-channel format is specified literally so the dispatching session can act on it without re-parsing.

## The strong example

```markdown
---
name: dependency-auditor
description: Use proactively after package.json or lockfile changes to audit outdated and vulnerable npm dependencies. Returns a structured findings report. Read-only — does not modify files.
model: haiku
maxTurns: 8
tools: Read, Grep, Glob, Bash
skills:
  - npm-audit-conventions
isolation: worktree
---

# Dependency Auditor

## When this agent is dispatched

Dispatched by the main session when ALL hold:

- The repo root contains `package.json` AND a lockfile (`package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml`).
- The dispatcher has already resolved which package manager to invoke (passed in the prompt as `pkg_manager: npm|yarn|pnpm`) and which severity floor to report (`severity_floor: low|moderate|high|critical`).
- The dispatcher has passed the absolute path to the project root as `project_root`.

If any of the three inputs is missing from the dispatch prompt, terminate on turn 1 with the literal string `MISSING_INPUT: <field>` and stop. Do NOT attempt to discover them yourself — the dispatcher is responsible for resolution.

## Capability constraints

- This subagent MUST NOT invoke `AskUserQuestion`. Foreground passthrough is unreliable (Ctrl+B can background the run mid-turn) and `isolation: worktree` strengthens the case for self-contained operation. All ambiguity is resolved by the dispatcher before this agent runs.
- This subagent CANNOT spawn other subagents. Do not invoke `Agent`.
- This subagent CANNOT invoke `EnterWorktree` / `ExitWorktree`. Worktree isolation is provided by the `isolation: "worktree"` frontmatter field at dispatch time.
- This subagent CANNOT modify files. The `tools` allowlist excludes `Edit`, `Write`, and `NotebookEdit` by omission.
- Bash `cd` does not persist across calls in a subagent. Always pass absolute paths.

## Workflow

1. Validate inputs. Confirm `project_root`, `pkg_manager`, and `severity_floor` are present in the dispatch prompt. If not, emit `MISSING_INPUT: <field>` and stop.

2. Locate the manifest. Invoke `Read` with `file_path: "<project_root>/package.json"`. If the file does not exist, emit `MISSING_FILE: package.json` and stop.

3. Locate the lockfile. Invoke `Glob` with `pattern: "{package-lock.json,yarn.lock,pnpm-lock.yaml}"` and `path: "<project_root>"`. If zero matches, emit `MISSING_FILE: lockfile` and stop.

4. Run the outdated check. Invoke `Bash` with:
   - `command: "cd <project_root> && <pkg_manager> outdated --json"` (substitute `pkg_manager`)
   - `description: "Listing outdated dependencies"`
   - `timeout: 60000`
   Capture stdout. Non-zero exit codes are expected when outdated deps exist — treat exit 1 as success if stdout is valid JSON.

5. Run the vulnerability audit. Invoke `Bash` with:
   - `command: "cd <project_root> && <pkg_manager> audit --json"`
   - `description: "Auditing dependencies for vulnerabilities"`
   - `timeout: 90000`
   Capture stdout.

6. Filter and shape. Drop vulnerabilities below `severity_floor`. Drop outdated entries where `current == wanted` (already at the satisfiable max).

7. Emit the return summary in the exact format below. Do NOT recap files read or commands invoked.

## Return format

The dispatching session sees ONLY your final assistant message. Return EXACTLY this shape, in this order, no preamble:

```
## Dependency Audit

### Vulnerabilities (severity >= <severity_floor>)
- <package>@<version> — <severity> — <advisory_title> — fix: <fixed_in or "no fix available">

### Outdated (current < wanted)
- <package>: <current> -> <wanted> (latest: <latest>)

### Summary
- vulnerabilities_total: <int>
- outdated_total: <int>
- recommended_action: <one sentence: "run <pkg_manager> audit fix" | "manual review needed for <N> packages" | "no action required">
```

If both lists are empty, return only the `### Summary` block with `recommended_action: "no action required"`.
```

## What to notice

1. **Frontmatter fields used:** `name`, `description` (required pair), plus `model: haiku` (cheap, sufficient for parsing JSON output), `maxTurns: 8` (hard ceiling — six numbered workflow steps fit comfortably), `tools` (tight read-only allowlist), `skills` (preloads `npm-audit-conventions` because subagents do not inherit parent skills), `isolation: worktree` (the audit runs inside a temporary clone — safe even if a future workflow step adds writes).

2. **Frontmatter fields deliberately omitted:** `hooks`, `mcpServers`, and `permissionMode` are excluded because plugin-shipped agents reject them silently. `effort`, `disallowedTools`, `memory`, `background`, `color`, and `initialPrompt` are omitted because no requirement justifies them — extra fields are noise that distracts the dispatcher model.

3. **Ambiguity handled without `AskUserQuestion`:** The "When this agent is dispatched" section names every required input (`project_root`, `pkg_manager`, `severity_floor`) and defines a deterministic failure mode (`MISSING_INPUT: <field>`) when any is absent. The dispatcher — running in the main session — is the one responsible for collecting these via `AskUserQuestion` BEFORE invoking `Agent`. This is the correct division of labor per the foreground-to-background conversion risk noted in `references/subagents.md` §5.

4. **No subagent spawning:** "Capability constraints" states explicitly that `Agent` is not to be invoked. The constraint is reinforced by omitting `Agent` from the `tools` allowlist would also work, but stating the rule in prose protects against the model attempting it via inheritance.

5. **Return-channel discipline:** The "Return format" block specifies the literal output shape — headings, bullet structure, key names, and the empty-state contract. The dispatching session can grep the return for `vulnerabilities_total:` without re-parsing prose. Forbidding recap ("do NOT recap files read or commands invoked") prevents the agent from padding the return with intermediate exploration the main session does not need.

6. **Hard stop:** `maxTurns: 8` plus a numbered seven-step workflow guarantees termination even if a Bash call hangs and recovers. Without `maxTurns`, a confused subagent can burn arbitrary tokens before the main session notices.
