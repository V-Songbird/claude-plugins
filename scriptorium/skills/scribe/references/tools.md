# Tool catalog

Names are exact strings used in permission rules, subagent `tools:` lists, and hook matchers. UX-critical optional fields — those whose omission silently degrades the UI — are flagged inline with `(UX-critical)`. Schemas are TypeScript form from the Agent SDK; tools without a published schema use the doc-described shape.

---

## Clarification

### AskUserQuestion

Permission: No. Works in foreground subagents (passes the question through to the user); fails silently in background subagents. Because a foreground subagent can be backgrounded mid-run (Ctrl+B), the safest pattern is to resolve clarification in the dispatching session before `Agent` fires — don't rely on this tool from inside a subagent prompt.

```ts
type AskUserQuestionInput = {
  questions: Array<{
    question: string;                  // full question text
    header: string;                    // (UX-critical) ≤12 chars, shown as label
    options: Array<{
      label: string;
      description: string;
      preview?: string;                // markdown/HTML; only renders if previewFormat is configured
    }>;
    multiSelect: boolean;              // (UX-critical) false=radio, true=checkboxes
  }>;
};
```

Hard limits: 1–4 questions per call, 2–4 options per question.

When to instruct:
- 2–4 mutually exclusive (or multi-select) consequential choices
- The user may not know the option space without prompting
- Approach selection, scope confirmation, ambiguity resolution

When NOT to instruct:
- Free-form input is needed
- Inside a subagent prompt (background subagents fail silently; a foreground subagent may be backgrounded mid-run and start failing silently too — resolve clarification in the dispatching session before `Agent` fires)
- Binary yes/no that maps to a permission prompt

Example:

```
Invoke AskUserQuestion with:
  questions: [{
    question: "Which migration strategy should I use?",
    header: "Migration",
    multiSelect: false,
    options: [
      { label: "In-place",        description: "Mutate existing tables; faster, no rollback." },
      { label: "Parallel rewrite", description: "Build new schema alongside; safer, slower." },
      { label: "You decide",       description: "Let Claude pick based on codebase fit." }
    ]
  }]
```

---

## Progress

### TaskCreate

Permission: No. Interactive sessions only (SDK / `claude -p` use `TodoWrite` instead).

Shape (from docs): creates one task in the session task list. Fields include `content`, `activeForm`, `status` ("pending" | "in_progress" | "completed"), and optional dependency / detail fields.

When to instruct:
- ≥3 sequential steps in an interactive session
- Work spans multiple tool calls and the user benefits from visible progress

When NOT to instruct:
- Single-tool task
- Inside a subagent (subagent work returns a summary, not streamed todos)

```
Invoke TaskCreate with:
  content: "Run the test suite"
  activeForm: "Running the test suite"           // (UX-critical) shown while in_progress
  status: "pending"
```

### TaskGet

Permission: No. Returns full details for one task by ID.

When to instruct: when the model needs the current `details` blob or dependency state for one task it already created.

When NOT to instruct: as a substitute for `TaskList` when enumerating.

```
Invoke TaskGet with: { task_id: "<id from TaskCreate>" }
```

### TaskList

Permission: No. Lists all tasks with status.

When to instruct: when re-orienting after compaction, or before deciding which task to mark `in_progress`.

When NOT to instruct: when you already hold the IDs and just need to update one.

```
Invoke TaskList with: {}
```

### TaskUpdate

Permission: No. Updates status, dependencies, details, or deletes a task.

When to instruct:
- Marking a task `in_progress` immediately before starting it
- Marking `completed` immediately on finish — never batch
- Adjusting `details` mid-task with new findings

When NOT to instruct: to rewrite `content`/`activeForm` after creation — recreate instead.

```
Invoke TaskUpdate with:
  task_id: "<id>"
  status: "in_progress"
```

### TaskStop

Permission: No. Kills a running background task by ID.

```ts
type TaskStopInput = {
  task_id?: string;
  shell_id?: string;   // deprecated, prefer task_id
};
```

When to instruct:
- A backgrounded `Bash` (`run_in_background: true`) or `Monitor` is no longer needed
- A long-running build/server must be torn down before the next phase

```
Invoke TaskStop with: { task_id: "<bg task id>" }
```

### TaskOutput (DEPRECATED)

Permission: No. Do NOT instruct. Per the canonical reference, prefer `Read` on the task's output file path.

### TodoWrite

Permission: No. Available in non-interactive mode and the Agent SDK; interactive sessions use `TaskCreate`/`TaskGet`/`TaskList`/`TaskUpdate` instead.

```ts
type TodoWriteInput = {
  todos: Array<{
    content: string;                   // (UX-critical) imperative: "Read the config file"
    status: "pending" | "in_progress" | "completed";
    activeForm: string;                // (UX-critical) progressive: "Reading the config file"
  }>;
};
```

`content` and `activeForm` are a pair. `content` renders when pending/completed; `activeForm` renders while `in_progress`. They are NOT interchangeable.

When to instruct:
- ≥3 sequential steps in an SDK or non-interactive session
- The artifact must work in both interactive and SDK contexts (instruct `TodoWrite` primarily; note `TaskCreate`+`TaskUpdate` as the interactive equivalent)

When NOT to instruct: single-tool tasks; subagent inner loops.

```
Invoke TodoWrite with:
  todos: [
    { content: "Explore subsystem",  activeForm: "Exploring subsystem",  status: "pending" },
    { content: "Draft the change",   activeForm: "Drafting the change",  status: "pending" },
    { content: "Verify with tests",  activeForm: "Verifying with tests", status: "pending" }
  ]
```

---

## Planning

### EnterPlanMode

Permission: No. Switches the session to read-only tools (`Read`, `Glob`, `Grep`, reasoning) until `ExitPlanMode` fires. No parameters.

When to instruct: multi-file or architectural changes; the user explicitly asked to plan; the cost of the wrong approach is meaningful rework.

When NOT to instruct: trivial single-file fix; pure read-only inspection; the user already approved the approach.

```
Invoke EnterPlanMode with: {}
```

### ExitPlanMode

Permission: Yes. Presents the plan for approval and exits plan mode.

```ts
type ExitPlanModeInput = {
  allowedPrompts?: Array<{
    tool: "Bash";
    prompt: string;                    // (UX-critical) pre-approves specific Bash commands
  }>;
};
```

Omitting `allowedPrompts` forces a permission prompt for every non-auto-approved `Bash` call during execution.

```
Invoke ExitPlanMode with:
  allowedPrompts: [
    { tool: "Bash", prompt: "npm test" },
    { tool: "Bash", prompt: "npm run lint" },
    { tool: "Bash", prompt: "npm run typecheck" }
  ]
```

---

## Dispatch

### Agent

Permission: No. Spawns a subagent with its own context window.

```ts
type AgentInput = {
  description: string;                 // (UX-critical) REQUIRED; status-line label
  prompt: string;                      // REQUIRED; focused instruction
  subagent_type: string;               // REQUIRED; built-in options "general-purpose" | "Explore" | "Plan", or a custom agent name
  model?: "sonnet" | "opus" | "haiku";
  resume?: string;                     // agent ID to resume
  run_in_background?: boolean;
  max_turns?: number;
  name?: string;                       // (UX-critical when user-facing) custom display name
  team_name?: string;                  // experimental agent teams
  mode?: "acceptEdits" | "bypassPermissions" | "default" | "dontAsk" | "plan";
  isolation?: "worktree";
};
```

Subagent capability limits:
- `AskUserQuestion` works in foreground subagents (passes through to the user) but fails silently in background subagents. Because a foreground subagent can be backgrounded mid-run (Ctrl+B), resolve ambiguity in the dispatching session before `Agent` fires rather than from inside the subagent prompt.
- Subagents CANNOT invoke `EnterWorktree` / `ExitWorktree`
- Subagents CANNOT spawn other subagents (nested `Agent` calls fail — chain from the main session or delegate via skills)
- Bash `cd` changes never carry over into a subagent session

When to instruct:
- Subtask pulls bulky material (full docs, repo-wide scans) that would bloat main context
- Parallelizable work, or work needing isolation (`isolation: "worktree"`)
- Background fire-and-forget work (`run_in_background: true`)

When NOT to instruct:
- Small lookups where spawn cost > context savings
- Tasks needing back-and-forth with the user
- Tasks where relevant context is already loaded in main

```
Invoke Agent with:
  subagent_type: "general-purpose"
  description: "Scanning auth subsystem for token-handling sites"
  prompt: "List every file that touches JWT validation; summarize each in ≤2 lines."
  max_turns: 6
```

### SendMessage

Permission: No. Experimental; only available when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Sends a message to an agent-team teammate or resumes a subagent by ID. Stopped subagents auto-resume in the background.

When to instruct: only inside artifacts gated on the experimental flag — gate the instruction behind an availability check.

When NOT to instruct: any artifact intended to run on a default install.

```
Invoke SendMessage with: { agent_id: "<id>", message: "Continue with phase 2." }
```

---

## Shell

### Bash

Permission: Yes.

```ts
type BashInput = {
  command: string;
  timeout?: number;                    // ms
  description?: string;                // (UX-critical) status-line label
  run_in_background?: boolean;
  dangerouslyDisableSandbox?: boolean;
};
```

Behavior:
- `cd` in the main session carries to later Bash commands (within project / `--add-dir` paths). Subagents NEVER inherit `cd` changes.
- Disable carry-over with `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1`.
- Environment variables do NOT persist between Bash calls; use `CLAUDE_ENV_FILE` or a `SessionStart` hook.

When to instruct:
- Any command runnable in shell, especially anything >1s or non-obvious
- Background processes via `run_in_background: true` (servers, watchers, long builds)

When NOT to instruct:
- File reads (use `Read`), file edits (use `Edit`/`Write`), pattern search (use `Grep`/`Glob`)
- Long-running watch loops where `Monitor` is a better fit

```
Invoke Bash with:
  command: "npm test"
  description: "Running the Jest test suite"
  timeout: 120000
```

### PowerShell

Permission: Yes. Gated by `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`. Auto-detected on Windows (rolling out); opt-in on Linux/macOS/WSL (requires `pwsh` 7+ on PATH). Shares Bash's permission rules and working-directory carry-over.

Same shape as `Bash` (`command`, `timeout`, `description`, `run_in_background`).

When to instruct: artifacts targeting Windows users where Git Bash routing is undesirable; or artifacts with `defaultShell: "powershell"` in settings, `shell: powershell` in skill frontmatter, or hooks declared with `"shell": "powershell"`.

When NOT to instruct: cross-platform artifacts that must run on a default install — `Bash` is always available; `PowerShell` is not.

```
Invoke PowerShell with:
  command: "Get-ChildItem -Recurse -Filter *.ps1 | Measure-Object"
  description: "Counting PowerShell scripts"
```

### Monitor

Permission: Yes. Requires Claude Code v2.1.98+. Not available on Amazon Bedrock, Google Vertex AI, or Microsoft Foundry. Disabled when `DISABLE_TELEMETRY` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is set. Uses Bash permission rules.

```ts
type MonitorInput = {
  command: string;
  description: string;                 // (UX-critical) REQUIRED; status-line label
  timeout_ms?: number;
  persistent?: boolean;
};
```

When to instruct:
- Tail a log file and surface errors as they appear
- Poll a CI/PR status until it changes
- Watch a directory for file changes mid-conversation

When NOT to instruct:
- One-shot commands (use `Bash`)
- Artifacts that must run on Bedrock/Vertex/Foundry or with telemetry disabled
- Plugin-declared monitors (those start automatically when the plugin is active)

```
Invoke Monitor with:
  command: "tail -F build.log"
  description: "Watching build.log for errors"
```

---

## Files

### Edit

Permission: Yes.

```ts
type FileEditInput = {
  file_path: string;
  old_string: string;
  new_string: string;
  replace_all?: boolean;               // default false
};
```

When to instruct:
- Modifying any existing file (preserves structure, surfaces a diff)
- Renames within a file via `replace_all: true` after verifying uniqueness would fail otherwise

When NOT to instruct:
- Creating brand-new files (use `Write`)
- Editing Jupyter notebook cells (use `NotebookEdit`)

```
Invoke Edit with:
  file_path: "/abs/path/to/config.ts"
  old_string: "const TIMEOUT = 5000;"
  new_string: "const TIMEOUT = 30000;"
```

### NotebookEdit

Permission: Yes.

```ts
type NotebookEditInput = {
  notebook_path: string;
  cell_id?: string;                    // omit with edit_mode: "insert" at start
  new_source: string;
  cell_type?: "code" | "markdown";
  edit_mode?: "replace" | "insert" | "delete";
};
```

When to instruct: any change to `.ipynb` cells. NEVER use `Edit` on a notebook — JSON structure breaks.

```
Invoke NotebookEdit with:
  notebook_path: "/abs/path/to/analysis.ipynb"
  cell_id: "abc123"
  new_source: "import pandas as pd\ndf = pd.read_csv('data.csv')"
  cell_type: "code"
  edit_mode: "replace"
```

### Read

Permission: No.

```ts
type FileReadInput = {
  file_path: string;
  offset?: number;                     // 1-indexed start line
  limit?: number;                      // line count
  pages?: string;                      // PDF page range, e.g. "1-5,12"
};
```

When to instruct:
- Any file inspection by known path
- PDFs — always instruct `pages` when only a section is needed
- Large files — instruct `offset`/`limit` to avoid loading the full file

When NOT to instruct:
- Searching by content (use `Grep`)
- Listing files (use `Glob`)

```
Invoke Read with: { file_path: "/abs/path/to/report.pdf", pages: "1-5" }
```

### Write

Permission: Yes.

```ts
type FileWriteInput = {
  file_path: string;
  content: string;
};
```

When to instruct: creating new files; full overwrites of existing files when an `Edit` diff would be larger than a rewrite.

When NOT to instruct: targeted edits (use `Edit`); notebook cells (use `NotebookEdit`).

```
Invoke Write with: { file_path: "/abs/path/to/new.md", content: "# Heading\n..." }
```

---

## Search

### Glob

Permission: No. Sorted by modification time descending.

```ts
type GlobInput = {
  pattern: string;
  path?: string;
};
```

When to instruct: file enumeration by name pattern. Prefer specific patterns over `**/*`.

When NOT to instruct: searching file contents (use `Grep`).

```
Invoke Glob with: { pattern: "src/**/*.test.ts" }
```

### Grep

Permission: No.

```ts
type GrepInput = {
  pattern: string;
  path?: string;
  glob?: string;
  type?: string;
  output_mode?: "content" | "files_with_matches" | "count";   // (UX-critical) default "files_with_matches"
  "-i"?: boolean;
  "-n"?: boolean;
  "-B"?: number;
  "-A"?: number;
  "-C"?: number;
  context?: number;
  head_limit?: number;
  offset?: number;
  multiline?: boolean;
};
```

`output_mode` controls result shape — instruct it explicitly. Default `"files_with_matches"` surprises authors expecting matching lines.

When to instruct: any content search across files.

When NOT to instruct: single-file inspection (use `Read`); structural code navigation when `LSP` is available.

```
Invoke Grep with:
  pattern: "TODO\\(.*\\)"
  glob: "**/*.ts"
  output_mode: "content"
  "-n": true
```

---

## Web

### WebFetch

Permission: Yes.

```ts
type WebFetchInput = {
  url: string;
  prompt: string;                      // scoping: what to extract from the page
};
```

When to instruct: pulling specific information from a known URL. `prompt` scopes extraction so the whole page does not enter context.

When NOT to instruct: authenticated/private URLs (use a dedicated MCP tool); GitHub URLs (prefer `gh` via `Bash`).

```
Invoke WebFetch with:
  url: "https://example.com/changelog"
  prompt: "List entries added since version 4.2."
```

### WebSearch

Permission: Yes.

```ts
type WebSearchInput = {
  query: string;
  allowed_domains?: string[];
  blocked_domains?: string[];
};
```

When to instruct: discovery searches; pair with `allowed_domains` for authoritative-source scoping.

When NOT to instruct: when a known URL exists (use `WebFetch`).

```
Invoke WebSearch with:
  query: "TypeScript 5.5 satisfies operator changes"
  allowed_domains: ["typescriptlang.org", "github.com"]
```

---

## Scheduling

### CronCreate

Permission: No. Schedules a recurring or one-shot prompt within the current session. Tasks are session-scoped and restored on `--resume`/`--continue` if unexpired. Dies when the session ends.

When to instruct: watch-and-report patterns where the host session must stay live; periodic re-checks of an external resource.

When NOT to instruct: long-term scheduling beyond the session (out of scope for built-in tools); fire-once delays (use `Monitor` or a backgrounded `Bash`).

```
Invoke CronCreate with:
  schedule: "*/15 * * * *"
  prompt: "Check the deploy status and report any failures."
```

### CronDelete

Permission: No. Cancels a scheduled task by ID.

```
Invoke CronDelete with: { id: "<cron id>" }
```

### CronList

Permission: No. Lists all scheduled tasks in the session.

```
Invoke CronList with: {}
```

---

## Worktree

### EnterWorktree

Permission: No. NOT available to subagents. Creates an isolated git worktree and switches into it; pass `path` to switch into an existing worktree of the current repo.

```ts
type EnterWorktreeInput = {
  name?: string;
  path?: string;
};
```

When to instruct: experimental work that may be discarded; parallel exploration alongside the active branch.

When NOT to instruct: inside any subagent definition — the tool is unavailable there. For subagent-level isolation, use `Agent` with `isolation: "worktree"` from the main session.

```
Invoke EnterWorktree with: { name: "spike-redis-cache" }
```

### ExitWorktree

Permission: No. NOT available to subagents. Exits the worktree session and returns to the original directory. No parameters.

```
Invoke ExitWorktree with: {}
```

---

## Code intelligence

### LSP

Permission: No. Inactive until a code-intelligence plugin is installed for the language; the plugin bundles language-server config and the user installs the server binary separately. Auto-reports type errors after file edits.

Capabilities (no public TS schema):
- Jump to a symbol's definition
- Find all references to a symbol
- Get type information at a position
- List symbols in a file or workspace
- Find implementations of an interface
- Trace call hierarchies

When to instruct: skills targeting languages where LSP is likely installed (TypeScript, Rust, Go, Python with pyright); navigation that would otherwise rely on `Grep` heuristics.

When NOT to instruct: artifacts that must work without any plugin installed; languages without a plugin.

```
Invoke LSP to find references to the `parseConfig` symbol at src/config.ts:42.
```

---

## Meta

### Skill

Permission: Yes. Executes a skill within the main conversation — the mechanism behind `/skill-name`. Not a way to "register" new tools; skills run through this single tool entry.

When to instruct: an artifact that delegates to a sibling skill by name; a slash command that maps directly to a skill.

When NOT to instruct: when the work fits inline; never invoke a skill that is already running.

```
Invoke Skill with: { skill: "scribe" }
```

### ToolSearch

Permission: No. Searches for and loads deferred tools when MCP tool search is enabled.

When to instruct: artifacts that may need MCP tools whose schemas are not pre-loaded; the artifact should describe loading by capability ("select:`<name>`" for direct, keywords for search) before invoking.

When NOT to instruct: built-in tools (always loaded); MCP tools known to be active in the session.

```
Invoke ToolSearch with: { query: "select:WebFetch", max_results: 1 }
```

---

## MCP

### ListMcpResourcesTool

Permission: No.

```ts
type ListMcpResourcesInput = {
  server?: string;                     // omit to list across all connected servers
};
```

When to instruct: enumerating resources before reading; discovering what a connected MCP server exposes.

```
Invoke ListMcpResourcesTool with: {}
```

### ReadMcpResourceTool

Permission: No.

```ts
type ReadMcpResourceInput = {
  server: string;
  uri: string;
};
```

When to instruct: pulling a specific MCP resource by URI returned from `ListMcpResourcesTool`.

```
Invoke ReadMcpResourceTool with: { server: "docs", uri: "doc://api/v2/reference" }
```

---

## Experimental (gated)

Available only when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set. Do not depend on these in artifacts intended for default installs — gate every reference behind an availability check.

### TeamCreate

Permission: No. Creates an agent team with multiple teammates.

```
Invoke TeamCreate with:
  name: "review-board"
  teammates: [ { name: "reviewer-a", subagent_type: "general-purpose", prompt: "..." } ]
```

### TeamDelete

Permission: No. Disbands an agent team and cleans up teammate processes.

```
Invoke TeamDelete with: { team_name: "review-board" }
```

(`SendMessage` is the third experimental tool — listed under Dispatch.)

---

## Harness-specific extensions

These tools appear in specific Claude Code environments (dynamic-pacing `/loop`, Remote Control, Cowork-aware session MCP) but are NOT in the public tools reference. Do not assume availability on a default install. If an artifact relies on one, gate the reference behind an environment check or scope the artifact to the specific harness. Shapes marked "not publicly documented" are sourced from harness-exposed schemas, not the canonical reference.

### ScheduleWakeup

Permission: No. Available only inside `/loop` dynamic (self-paced) mode — the runtime fires the scheduled prompt as the next loop iteration. No other context exposes this tool.

```ts
type ScheduleWakeupInput = {
  delaySeconds: number;                // clamped to [60, 3600] by the runtime
  prompt: string;                      // the /loop input to re-fire verbatim, or the sentinel `<<autonomous-loop-dynamic>>` for autonomous /loop
  reason: string;                      // (UX-critical) one short sentence; shown to the user and in telemetry
};
```

Cache-window guidance: pick `delaySeconds` ≤ 270 (prompt cache stays warm, 5-minute TTL) or ≥ 1200 (accept the miss, amortize over a long wait). Avoid ≈ 300 s — worst-of-both. Default 1200–1800 for idle ticks.

When to instruct: artifacts that drive a `/loop` dynamic-mode session and must self-pace. Pass the same `/loop` input back verbatim each tick, or the `<<autonomous-loop-dynamic>>` sentinel for autonomous loops. Omit the call to end the loop.

When NOT to instruct: any non-loop artifact; fixed-interval `/loop 15m` (the runtime handles pacing); artifacts intended to run on default (non-loop) installs.

```
Invoke ScheduleWakeup with:
  delaySeconds: 270
  prompt: "/loop /check-deploy"
  reason: "Re-checking deploy status — build still running"
```

### PushNotification

Permission: Yes. Shape not publicly documented. Part of the Remote Control / mobile-push surface on harnesses that integrate with the mobile app. The canonical notification path on a default install is the `Notification` hook plus third-party services (ntfy, Pushover) — prefer that in portable artifacts.

When to instruct: only in artifacts scoped to a harness where the tool is confirmed available, and only for meaningful state changes (build done, long task complete).

When NOT to instruct: portable skills, subagent definitions, or any artifact distributed to default installs; routine progress updates.

### RemoteTrigger

Permission: Yes. Shape not publicly documented. Associated with Remote Control (connecting to a running session from outside the terminal) and the persistent-scheduling `/schedule` skill. Distinct from `CronCreate`, which is session-scoped.

When to instruct: artifacts driving remote-control-aware workflows that fire an existing trigger on demand.

When NOT to instruct: default-install artifacts; as a substitute for `CronCreate` (session scheduling) or a replacement for the `/schedule` skill (persistent remote scheduling).

### mcp__ccd_session__mark_chapter

Permission: No. MCP-provided by the `ccd_session` server in Cowork-aware harnesses. Marks a new chapter in the session — renders a divider plus a floating table-of-contents entry for navigation.

```ts
type MarkChapterInput = {
  title: string;                       // (UX-critical) under 40 chars; short noun phrase ("Auth bug fix")
  summary?: string;                    // hover tooltip in the TOC; one line
};
```

When to instruct: artifacts driving long sessions where coherent phase boundaries (exploration → implementation → verification) should be navigable. Typical session has 3–8 chapters. Do NOT mark the first message — session start is implicit.

When NOT to instruct: short sessions; chapter churn on every tool call; artifacts not scoped to a Cowork-aware harness.

```
Invoke mcp__ccd_session__mark_chapter with:
  title: "Test verification"
  summary: "Running the full suite after the auth fix lands."
```

### mcp__ccd_session__spawn_task

Permission: No. MCP-provided by the `ccd_session` server. Surfaces an out-of-scope follow-up as a user-dismissible chip; when clicked, the chip spins into its own session and worktree.

```ts
type SpawnTaskInput = {
  title: string;                       // (UX-critical) under 60 chars; imperative ("Fix stale README badge")
  prompt: string;                      // self-contained — the spawned session has no memory of this conversation
  tldr: string;                        // (UX-critical) 1–2 sentences; user-facing tooltip; no file paths or code
};
```

When to instruct: artifacts that routinely identify concrete, high-confidence out-of-scope fixes (dead code, stale docs, confirmed TODOs, high-confidence security issues).

When NOT to instruct: vague cleanup hunches; trivial fixes the current turn can absorb inline; anything that needs the current conversation's context to act on; artifacts not scoped to a Cowork-aware harness.

```
Invoke mcp__ccd_session__spawn_task with:
  title: "Remove dead config option"
  prompt: "In src/config.ts, the `legacyMode` flag is no longer referenced after commit abc123. Delete the field, its type, and the two tests that pin it."
  tldr: "Clean up an unused config flag left behind by the recent refactor."
```

---

Source: https://code.claude.com/docs/en/tools-reference (fetched 2026-04-18). The "Harness-specific extensions" section is not part of the canonical reference; entries there are documented from direct harness exposure.
