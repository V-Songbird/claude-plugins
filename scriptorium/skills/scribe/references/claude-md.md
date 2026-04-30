# CLAUDE.md authoring reference

CLAUDE.md is **always-in-context** instruction. It loads at session start and stays in the context window for the whole conversation. Use it for facts and conventions Claude must hold every turn — not for procedures (those go in skills, which load on demand).

## 1. What belongs in CLAUDE.md

Put in CLAUDE.md:
- Build, test, lint commands the project uses (`npm test`, `cargo build --release`).
- Naming conventions, indentation, file layout (`API handlers live in src/api/handlers/`).
- "Always do X" / "never do Y" rules that apply across the codebase.
- Architecture facts a new contributor would need to be productive.

Do NOT put in CLAUDE.md:
- Multi-step procedures → write a **skill** instead (loads on demand, no context cost when idle).
- Rules that only apply to one subtree → write a **path-scoped rule** in `.claude/rules/` instead.
- Hook configuration → that goes in `settings.json`, not CLAUDE.md (CLAUDE.md is guidance, not enforcement).

Size target: **under 200 lines per file**. Longer files consume more context and reduce adherence. Split with imports or `.claude/rules/` if growing.

## 2. Discovery and load order

CLAUDE.md is discovered by walking up the directory tree from the working directory. All discovered files are **concatenated** into context (they do not override each other). More specific locations are read after broader ones, so closer files have last word on conflicts.

| Scope | Path | Loaded |
|---|---|---|
| Managed policy (org) | macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`<br>Linux/WSL: `/etc/claude-code/CLAUDE.md`<br>Windows: `C:\Program Files\ClaudeCode\CLAUDE.md` | At launch, cannot be excluded |
| User | `~/.claude/CLAUDE.md` | At launch, every project |
| Project (team-shared) | `./CLAUDE.md` or `./.claude/CLAUDE.md` | At launch |
| Project (personal, gitignored) | `./CLAUDE.local.md` | At launch, appended after `CLAUDE.md` |
| Monorepo subdirectory | `<subdir>/CLAUDE.md` | **On demand** — only when Claude reads a file in that subdir |

Within one directory: `CLAUDE.local.md` is appended after `CLAUDE.md`, so personal notes have last word locally.

After `/compact`: project-root CLAUDE.md is re-injected automatically. Nested subdirectory CLAUDE.md files are NOT re-injected — they reload only when Claude next reads a file there.

Block-level HTML comments (`<!-- maintainer notes -->`) are stripped before injection; comments inside code blocks are preserved.

## 3. Import syntax

CLAUDE.md can pull in other files with `@path/to/file` syntax. Imported files are expanded inline at launch.

```text
See @README for project overview and @package.json for npm commands.

# Workflow
- git workflow @docs/git-instructions.md
- personal prefs @~/.claude/my-project-instructions.md
```

Rules:
- Both **relative and absolute** paths allowed.
- Relative paths resolve against the **file containing the import**, not the working directory.
- `~/...` works for the user home directory.
- Imports recurse, with a **maximum depth of five hops**.
- First time a project uses external imports, Claude Code shows an approval dialog. Decline = imports stay disabled.

Use imports to keep CLAUDE.md short while pulling in detailed reference docs (READMEs, contributor guides, project-specific instruction packs).

## 4. Path-specific rules (`.claude/rules/`)

For instructions that only apply to part of the codebase, write a rule file in `.claude/rules/<topic>.md`. Files are discovered recursively; subdirectories are fine.

Rules **without** `paths` frontmatter load at launch with same priority as `.claude/CLAUDE.md`.

Rules **with** `paths` frontmatter load only when Claude reads a matching file:

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/**/*.{ts,tsx}"
  - "tests/**/*.test.ts"
---

# API rules
- All endpoints must validate input.
- Use the standard error response format.
```

Glob patterns: `**/*.ts`, `src/**/*`, `*.md`, `src/components/*.tsx`, brace expansion `{ts,tsx}` all supported.

User-level rules in `~/.claude/rules/` apply to every project; project rules override them.

## 5. Additional directories (`--add-dir`)

By default, `--add-dir <path>` does **not** load CLAUDE.md from the added directory. To enable it, set:

```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared-config
```

With the flag set, `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`, and `CLAUDE.local.md` all load from the added directory.

## 6. CLAUDE.md inside a plugin — does NOT auto-load

The documented discovery paths are **managed policy, user (`~/.claude`), project (`./` or `./.claude`), and ancestor/subdirectory walking**. Plugin install paths are not in that list. **A `CLAUDE.md` shipped inside a plugin will not be auto-loaded into sessions.**

Implication for plugin authors: do not rely on a plugin-bundled CLAUDE.md to inject persistent instructions. Instead:
- Ship a **skill** — loaded on demand when its description matches the prompt.
- Ship a **command** — invoked explicitly by the user.
- Ship a **hook** in the plugin's `hooks.json` — fires on harness events.
- If absolutely required, instruct the user to copy/import the file from their own project `CLAUDE.md` using `@${CLAUDE_PLUGIN_ROOT}/...` syntax.

## 7. Decide: CLAUDE.md vs skill

| Question | If yes → CLAUDE.md | If yes → skill |
|---|---|---|
| Must Claude know this on every turn? | yes | no |
| Is it a multi-step procedure? | no | yes |
| Does it cost real context every session? | acceptable | avoid |
| Triggered by a specific user request? | no | yes |
| Repeatable workflow with steps? | no | yes |

Rule of thumb: **facts and standing rules → CLAUDE.md. Procedures and workflows → skills.** If something only matters when Claude touches a specific subtree, prefer a path-scoped rule over either.

## 8. Naming Claude Code tools inside CLAUDE.md

CLAUDE.md instructions that reference tools must use the same naming rules as skills. See `references/tools.md` for the full catalog and phrasing rules. Quick summary:

- Use exact tool names: `Read`, `Edit`, `Write`, `Glob`, `Grep`, `Bash`, `WebFetch`, `WebSearch`, `Task`, `TodoWrite`.
- MCP tools use the literal `mcp__server__tool` form.
- Don't paraphrase (`"use the file reader"` will not trigger Read).
- Specific verbs help: `"Read <path>"`, `"run via Bash"`, `"Grep for X"`.
- Same phrasing rules apply whether the instruction lives in CLAUDE.md, a rule file, a skill, or a command.

Source: https://code.claude.com/docs/en/memory (fetched 2026-04-18).
