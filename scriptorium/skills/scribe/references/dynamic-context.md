# Dynamic context injection — authoring reference

Skills can run shell commands **before** the body reaches Claude. The command output replaces the placeholder; Claude only ever sees the rendered result, not the command. This is preprocessing, not a tool call — the user has no approval surface and the model cannot decline.

For the docs source, see https://code.claude.com/docs/en/skills#inject-dynamic-context.

## 1. Two forms

### Inline — for single-line commands

```markdown
- Branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`
- Modified files: !`git status --porcelain`
```

The backtick block runs once when the skill is invoked; its stdout replaces `` !`<cmd>` `` in the rendered prompt.

### Fenced — for multi-line commands

Open with ` ```! ` (no language tag, just `!`):

````markdown
```!
node --version
npm --version
git status --short
```
````

The whole block runs as a single shell invocation; stdout replaces the block.

**Mechanical rule:** any command that contains a newline or chains via `&&` / `||` / `;` must use the fenced form. Inline `!`...`` for multi-line commands often parses unpredictably.

## 2. Path safety — always use `${CLAUDE_SKILL_DIR}`

Skills can be invoked from any cwd. Relative paths to bundled scripts break when the user is not at the skill directory.

### ❌ Relative path
```markdown
- Diagnostics: !`bash scripts/diagnose.sh`
```
Fails when the user invokes the skill from a subdirectory.

### ✅ Absolute via `${CLAUDE_SKILL_DIR}`
```markdown
- Diagnostics: !`bash ${CLAUDE_SKILL_DIR}/scripts/diagnose.sh`
```
`${CLAUDE_SKILL_DIR}` always resolves to the directory containing this `SKILL.md`, regardless of cwd. For plugin skills it points to the skill's subdirectory, not the plugin root.

## 3. Command safety — injection is unattended

Commands inside `` !`...` `` and ` ```! ` blocks run with the user's full permissions and **without per-command approval**. The user sees only the rendered output, after the command has already run.

### Hard rule: read-only or idempotent only

Anything in an injection must be safe to run unconditionally, every time the skill loads. **Never** inject:

- Mutating git operations: `git push`, `git commit`, `git reset --hard`, `git checkout` (mutates working tree)
- Filesystem writes: `rm`, `mv`, `cp <src> <dest>` writing to a destination, output redirection (`> file`), `mkdir -p` creating new state
- Network state changes: `gh pr create`, `gh issue create`, `gh release create`, `curl -X POST`, deploys
- Package installs: `npm install`, `pip install`, `cargo add`
- Anything that prompts for credentials, opens a browser, or pages

### ✅ Safe injections
- `git status --porcelain`, `git log --oneline -10`, `git branch --show-current`, `git diff --stat`
- `ls`, `find … -type f`, `wc -l`, `head -n 100`
- `gh pr view`, `gh pr diff`, `gh issue view` (read-only `gh` queries)
- `node --version`, `npm --version`, language version probes
- `cat <known small file>` (when the user has already accepted that file is in scope)

## 4. Pair with `allowed-tools` to suppress prompts

Injection commands run via the `Bash` tool under the hood. To avoid per-command approval prompts on every invocation, scope the command in `allowed-tools`:

```yaml
---
name: pr-summary
description: Summarize the current PR with diff + comments injected.
allowed-tools: Bash(gh *) Bash(git *)
---
```

Use the narrowest scoping that covers your injections (`Bash(git status*)` over `Bash(git *)` over `Bash(*)`). Wide patterns silently authorize anything the model later decides to run.

## 5. Shell selection (`shell:` frontmatter)

Default shell is `bash`. To run injections via PowerShell on Windows:

```yaml
---
shell: powershell
---
```

Requires the user's environment to set `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`. Without the env var, the `shell:` field is honored but PowerShell is not available — fall back to bash-portable commands.

## 6. Policy: `disableSkillShellExecution`

When `"disableSkillShellExecution": true` is set in [`settings.json`](https://code.claude.com/docs/en/settings), every `` !`<cmd>` `` and ` ```! ` block is replaced by the literal string `[shell command execution disabled by policy]` instead of running. Bundled and managed skills are exempt; user / project / plugin / additional-directory skills are gated.

This is most useful in [managed settings](https://code.claude.com/docs/en/permissions#managed-settings) where users cannot override it. If your skill *requires* dynamic injection to function, document that requirement in the body so the user understands why it produces empty placeholders under that policy.

## 7. When to reach for dynamic injection

Use it when **all** hold:
- The skill consumes current state of the codebase or environment.
- The state is read-only, idempotent, and cheap to compute.
- The state is needed at invocation time, not mid-flight.
- Without injection, the body would say *"first invoke `Bash` with `<cmd>` to capture Y, then …"* — a tool round-trip the user pays for on every invocation.

Skip it when:
- The state must be re-read mid-flight (use a `Bash` tool call so the model can decide when to re-fetch).
- The command may have side effects (see § 3).
- The command may fail in ways the model needs to recover from (injection failures produce empty/error output silently).
- The skill is reference content, not an action — reference skills load knowledge, not state.

## 8. Opportunity pattern — hoist a Bash round-trip

The most common authoring miss: a skill body opens with *"Start by running X to get Y, then …"* where X is read-only.

### ❌ Round-trip pattern
```markdown
1. Invoke `Bash` with `command: "git status --porcelain"`, `description: "Check working tree state"`.
2. Based on the output, …
```
Costs one tool round-trip on every invocation.

### ✅ Hoisted to injection
```markdown
## Current state
- Working tree: !`git status --porcelain`

## Steps
1. Based on the working-tree state above, …
```
Output is in the prompt the moment the skill renders. No round-trip.

## 9. Worked example — minimal PR-summary skill

```yaml
---
name: pr-summary
description: Summarize the current PR using injected diff and comments.
allowed-tools: Bash(gh *) Bash(git *)
disable-model-invocation: false
---

## Current PR state

- Branch: !`git branch --show-current`
- PR diff (file-level): !`gh pr diff --name-only`
- Open comments: !`gh pr view --comments`

## Your task

Summarize the change in 3 sections:
1. **What changed** — one sentence per file group
2. **Risk** — anything reviewers should focus on
3. **Open questions** — based on the comments above
```

The injections fire once when the skill renders. The model sees actual diff filenames and comment text, never the `gh` commands.

Source: https://code.claude.com/docs/en/skills#inject-dynamic-context (fetched 2026-04-26).
