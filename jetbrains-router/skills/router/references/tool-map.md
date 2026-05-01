# Native-to-JetBrains IDE tool mapping

Load this reference from the `jetbrains-routing` skill when Claude is about to call `Read`, `Grep`, `Glob`, `Edit`, `Write`, or a project-file `Bash` command and a `mcp__webstorm__*`, `mcp__rider__*`, or `mcp__idea__*` tool is registered in the session.

**Prefix:** JetBrains auto-configure produces `webstorm`, `rider`, or `idea` as the `mcpServers` key — that becomes the tool prefix. Tool names below use `mcp__<ide>__` as the placeholder; substitute the prefix matching the IDE registered in this session. If you renamed your `mcpServers` entry, use the value of `JETBRAINS_MCP_PREFIX` instead.

## Core tools — available in all three IDEs

| Native | IDE replacement | Notes |
|---|---|---|
| `Read` | `mcp__<ide>__read_file` | Reflects the IDE's in-memory buffer, so unsaved edits the user is actively making are visible (native `Read` returns stale disk content). This is the primary reason to route `Read` — raw token cost vs native is roughly tied. Supports `mode: "lines"` / `"slice"` / `"offsets"` / `"line_columns"` / `"indentation"`; use partial modes for any file over a few hundred lines. |
| `Grep` (literal) | `mcp__<ide>__search_text` | Required: `q`. Returns snippet + 1-based line/column. |
| `Grep` (regex) | `mcp__<ide>__search_regex` | Required: `q`. Same output shape, regex input. |
| `Grep` for a symbol name | `mcp__<ide>__search_symbol` | Required: `q`. Semantic — resolves classes/methods/fields to their definition. Prefer over text/regex search when looking for an identifier definition. The result includes a `lineText` field that often contains the full implementation body — inspect it before issuing `read_file` (reliable in WebStorm and IDEA; Rider resolves the file but `lineText` contains only the first line of the file, not the symbol body). If `search_symbol` returns empty for a symbol you can confirm exists in a source file, the language is not indexed by this IDE; switch to `search_in_files_by_text` for the rest of the session and do not retry `search_symbol`. |
| `Glob` | `mcp__<ide>__search_file` | Required: `q`. Supports excludes + `limit`. |
| `Glob` by filename substring | `mcp__<ide>__find_files_by_name_keyword` | Required: `nameKeyword`. Index-backed — fastest for "find the file called X". |
| `Glob` by exact pattern | `mcp__<ide>__find_files_by_glob` | Required: `globPattern`. |
| Directory listing / `ls` | `mcp__<ide>__list_directory_tree` | Required: `directoryPath`. |
| `Edit` | `mcp__<ide>__replace_text_in_file` | Required: `pathInProject`, `oldText`, `newText`. Auto-saves. |
| `Edit` — rename symbol | `mcp__<ide>__rename_refactoring` | Required: `pathInProject`, `symbolName`, `newName`. Updates every reference — prefer over text Edit for identifier renames. |
| `Write` (new file) | `mcp__<ide>__create_new_file` | Required: `pathInProject`. Auto-creates parent directories. |
| Format file | `mcp__<ide>__reformat_file` | Required: `path`. |
| `Bash npm run build` / `tsc` | `mcp__<ide>__build_project` | Returns compile errors as structured output. |
| `Bash npm test` / custom runner | `mcp__<ide>__execute_run_configuration` | Required: `configurationName`. Use `mcp__<ide>__get_run_configurations` first to list available configs. |
| `Bash cat FILE` / `head` / `tail` | `mcp__<ide>__read_file` | With appropriate `mode`. |
| `Bash grep ...` / `rg ...` | `mcp__<ide>__search_text` or `search_regex` | |
| `Bash find -name ...` | `mcp__<ide>__find_files_by_name_keyword` | |
| `Bash ls DIR` | `mcp__<ide>__list_directory_tree` | |
| Inspect problems in a file | `mcp__<ide>__get_file_problems` | Required: `filePath`. Returns the IDE's inspection results — compile errors, unresolved symbols, deprecation warnings — without launching `tsc` / `gradle` / a fresh language-server run. Prefer this over `Bash tsc` / `Bash npm run build` / `Bash gradle check` whenever the question is "does this file have errors?" Use `errorsOnly=true` to skip warnings. Effectiveness depends on the IDE's language support for the file type. No native equivalent. |
| Lookup docs / signature | `mcp__<ide>__get_symbol_info` | Required: `filePath`, `line`, `column`. No native equivalent. |

## WebStorm + Rider only — database tools

Available in WebStorm (`mcp__webstorm__*`) and Rider (`mcp__rider__*`). Not present in IDEA.

| Tool | Purpose |
|---|---|
| `list_database_connections` | List configured data sources |
| `test_database_connection` | Verify connection status |
| `list_database_schemas` | List schemas for a connection |
| `list_schema_object_kinds` | List supported object kinds for a connection |
| `list_schema_objects` | List objects within a schema |
| `get_database_object_description` | Describe a database object |
| `execute_sql_query` | Run a SQL query, returns CSV |
| `cancel_sql_query` | Cancel a running query by session ID |
| `list_recent_sql_queries` | Recent and running queries |
| `preview_table_data` | Preview rows from a table or view |

## WebStorm + Rider only — IntelliJ inspection scripting

| Tool | Purpose |
|---|---|
| `generate_psi_tree` | Generate PSI tree for a file (plugin development) |
| `generate_inspection_kts_api` | Generate inspection API scaffolding |
| `generate_inspection_kts_examples` | Generate inspection examples |
| `run_inspection_kts` | Run a custom inspection script |

## IDEA only — debugger session control

Available as `mcp__idea__*` only.

| Tool | Purpose |
|---|---|
| `xdebug_start_debugger_session` | Start a debug session |
| `xdebug_get_debugger_status` | Check current debugger state |
| `xdebug_get_stack` | Get current call stack |
| `xdebug_get_threads` | List active threads |
| `xdebug_get_frame_values` | Get variable values for a stack frame |
| `xdebug_get_value_by_path` | Inspect a nested value by path |
| `xdebug_evaluate_expression` | Evaluate an expression in the debugger |
| `xdebug_set_breakpoint` | Set a breakpoint |
| `xdebug_remove_breakpoint` | Remove a breakpoint |
| `xdebug_list_breakpoints` | List all breakpoints |
| `xdebug_run_to_line` | Run to a specific line |
| `xdebug_set_variable` | Modify a variable value |
| `xdebug_control_session` | Step over / into / out / resume / stop |

## IDEA only — notebooks

| Tool | Purpose |
|---|---|
| `runNotebookCell` | Execute a Jupyter notebook cell |

## Rider only

| Tool | Purpose |
|---|---|
| `permission_prompt` | Rider security gate — pass through, do not intercept |