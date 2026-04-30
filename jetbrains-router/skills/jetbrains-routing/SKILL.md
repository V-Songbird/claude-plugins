---
name: jetbrains-routing
description: Route Claude Code file-ops tools through a JetBrains IDE MCP server (WebStorm, Rider, IntelliJ IDEA). Use this when about to call Read, Grep, Glob, Edit, Write, or a project-file Bash command in a session where mcp__webstorm__*, mcp__rider__*, or mcp__idea__* tools are registered. IDE reads reflect the editor's in-memory buffer so unsaved edits are visible; searches are scoped by the project index (skip node_modules, build outputs, .gitignore'd paths); and get_file_problems returns IDE inspection results for a file without launching tsc, gradle, or a language-server cold-start. A PreToolUse hook enforces routing and exits 2 on a native call — following this skill up front avoids the redirect round-trip.
user-invocable: false
---

# jetbrains-routing

## When this applies

A `mcp__webstorm__*`, `mcp__rider__*`, or `mcp__idea__*` tool is listed in the session's available tools. Check once per session — if none are present, the JetBrains MCP server isn't connected and this skill's guidance doesn't apply (use native tools; the hook will fail open).

## Prefix configuration

JetBrains IDEs register their MCP tools under the key name from `mcpServers` in `.claude.json`. The auto-configure button produces canonical defaults:

| IDE | Default prefix |
|-----|---------------|
| WebStorm | `mcp__webstorm__*` |
| Rider | `mcp__rider__*` |
| IntelliJ IDEA | `mcp__idea__*` |

If you renamed your `mcpServers` entry, set `JETBRAINS_MCP_PREFIX=<your-name>` in your shell before launching Claude Code so the hook redirects to the right prefix.

Only one IDE is active per session. If multiple IDEs are running, `JETBRAINS_MCP_PREFIX` determines which one receives routed calls.

## Tool mapping

**Always use the JetBrains replacement whenever a `mcp__<ide>__*` tool is registered.** The `PreToolUse` hook exits 2 on a native call with a stderr redirect naming the IDE tool and the pre-translated project-relative path — going native first incurs the round-trip for nothing.

For the full native-to-IDE mapping (required parameters, usage notes, when to pick `search_symbol` over `search_text`, when `get_file_problems` replaces a build run), see [references/tool-map.md](references/tool-map.md). Load it before the first routed call in a session.

## Path translation

JetBrains tools take **project-relative** paths via `pathInProject` / `file_path` / `path`, not absolute paths.

Translation rule: strip the project root prefix and convert backslashes to forward slashes.

- `D:\Projects\Work\DLL\GPRICE-Unified-Pricing-Portal\packages\ui\src\app.ts` → `packages/ui/src/app.ts`
- `D:/Projects/Work/DLL/GPRICE-Unified-Pricing-Portal/README.md` → `README.md`
- Already relative (`src/app.ts`) → leave as-is.

Pass `projectPath` explicitly when the session cwd is not the project root, using the absolute path of the project root.

## Stay on native tools for

- **`Bash` with pipes, heredocs, or output over 2000 lines.** `execute_terminal_command` caps output at 2000 lines and prompts the user in the IDE unless "Brave Mode" is enabled.
- **`Bash git status` / `git log` / `git diff` / `git blame`** and other git commands. `get_repositories` only surfaces basic state and doesn't replace `git status`'s detail.
- **Binary files.** `read_file` errors on binaries; use native `Read` or a `Bash` probe for binary inspection.
- **Paths outside the project root.** The IDE MCP can only see files inside the open project. Redirect does not apply.
- **Non-code paths.** The hook passes these through automatically — no action required:
  - Dotfiles and dotfolders: `.claude/`, `.idea/`, `.gradle/`, `.kotlin/`, `.git/`, `.gitignore`, etc.
  - Markdown files: `CLAUDE.md`, `README.md`, `docs/guide.md`, etc.
  - JSON / JSONL files: `package.json`, `tsconfig.json`, etc.
  - `docs/` directory.
  - Config/settings extensions: `.yml`, `.yaml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.properties`, `.lock`, `.env`.
  - For `Grep` / `Glob`: if the `path` parameter points to one of these areas, native tools are used; whole-project searches still redirect.
- **Interactive or long-running commands** — dev servers, watchers, REPLs.
- **Linked git worktrees.** When cwd is under a linked worktree (not the main checkout), the hook fails open automatically — the IDE's open project is almost never the worktree itself, and routed paths would miss. No action required from the skill; just expect native tools to run through.
- **Kotlin / Java in WebStorm or Rider.** If `get_project_modules` returns all modules as `WEB_MODULE` (WebStorm) or `PROJECT` for non-C# files (Rider) and the project contains `.kt` or `.java` files, the Kotlin/Java symbol index is not populated — `search_symbol` and `get_file_problems` will return empty. Use native tools. Kotlin/Java require IntelliJ IDEA (`JAVA_MODULE` type) for semantic indexing.
- **C# in WebStorm or IDEA.** C# symbol indexing requires Rider (`PROJECT` type modules). `search_symbol` will return empty for `.cs` files in other IDEs.

## IDE-specific capabilities

Some tools are only available on certain IDEs. Check which prefix is registered before using these:

**WebStorm + Rider only** — database tools + IntelliJ inspection scripting:
`cancel_sql_query`, `execute_sql_query`, `generate_inspection_kts_api`, `generate_inspection_kts_examples`, `generate_psi_tree`, `get_database_object_description`, `list_database_connections`, `list_database_schemas`, `list_recent_sql_queries`, `list_schema_object_kinds`, `list_schema_objects`, `preview_table_data`, `run_inspection_kts`, `test_database_connection`

**IDEA only** — debugger session control + Jupyter notebooks:
`runNotebookCell`, `xdebug_control_session`, `xdebug_evaluate_expression`, `xdebug_get_debugger_status`, `xdebug_get_frame_values`, `xdebug_get_stack`, `xdebug_get_threads`, `xdebug_get_value_by_path`, `xdebug_list_breakpoints`, `xdebug_remove_breakpoint`, `xdebug_run_to_line`, `xdebug_set_breakpoint`, `xdebug_set_variable`, `xdebug_start_debugger_session`

**Rider only**: `permission_prompt` — pass through without interception.

## Escape hatches

These are **session-level** controls — set by the human in their shell before launching Claude Code, or by a project-scoped `.envrc`. They are NOT for command-prefix use.

- `JETBRAINS_ROUTER_BYPASS=Read,Edit,Write` (comma-separated, no spaces) leaves those specific native tools alone while the rest still redirect. Use when you know the IDE's open project doesn't match this session's cwd for a subset of operations.
- `JETBRAINS_ROUTER_DISABLE=1` kill-switches every redirect for the session.

**Anti-bypass:** the hook explicitly blocks any `Bash` command that prefixes itself with `JETBRAINS_ROUTER_*=…` (e.g. `JETBRAINS_ROUTER_DISABLE=1 cat foo`). Setting these in a command does not actually disable the hook — the hook reads its own process env, not the inner command's — and pattern-bypassing through env-prefix tricks is treated as a bypass attempt. If a redirect is genuinely wrong (binary file mistakenly matched, exotic flag combo), surface that to the user; do not work around it.

## Ordering heuristic

1. Before the first `Read` / `Grep` / `Glob` / `Edit` / `Write` of a session, verify `mcp__webstorm__*`, `mcp__rider__*`, or `mcp__idea__*` tools are listed. If yes, use the IDE replacement; if no, use native.
2. For the first JetBrains call in a session, call `get_project_modules` once to confirm the project is what you expect. If all modules report as `WEB_MODULE` and the project has `.kt` or `.java` files, fall back to native tools for the session — see "Stay on native tools for".
3. Translate paths to project-relative form before the call — the hook's stderr redirect message already contains this hint if you ever get one, but getting it right first saves the round-trip.
4. When `search_symbol` returns a result, check `lineText` first — it often contains the full implementation body (reliable in WebStorm and IDEA; Rider resolves the file but `lineText` contains only the first line). Only call `read_file` if you need more context than `lineText` provides.
5. If `search_symbol` returns empty for a symbol you can confirm exists in a source file, the language is not indexed by this IDE — switch to `search_in_files_by_text` for the rest of the session and do not retry `search_symbol`.

## Additional resources

- For the full native-to-IDE tool mapping, required parameters, and usage notes, see [references/tool-map.md](references/tool-map.md)