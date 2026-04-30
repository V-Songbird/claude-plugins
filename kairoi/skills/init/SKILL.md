---
name: init
description: Initializes kairoi on any project — detects tech stack, discovers modules, bootstraps model files from source scan. Supports Node (vitest/jest), JVM (gradle), Rust (cargo), Go, Python (pytest), and generic stacks. Triggers on initialize kairoi, set up kairoi, add kairoi.
disable-model-invocation: true
argument-hint: [project-root]
effort: high
shell: bash
---

# Initialize kairoi

Set up kairoi with bootstrapped models from source. Run once per project.

Project root: $ARGUMENTS (defaults to current directory if not specified)

## Pre-Check

- If `.kairoi/model/_index.json` exists: report the existing modules
  (one line per module: id + purpose if populated). Then MUST invoke
  `AskUserQuestion` with:

  ```
  questions: [{
    question: "kairoi is already initialized in this project. What would you like to do?",
    header: "Re-init",
    multiSelect: false,
    options: [
      {
        label: "Re-discover",
        description: "Run module discovery again, overwriting .kairoi/model/*.json from fresh source scans. Preserves receipts.jsonl and overrides.json."
      },
      {
        label: "Skip",
        description: "Leave the existing .kairoi/ state as-is and exit init. Nothing changes."
      }
    ]
  }]
  ```

  `header` is "Re-init" (7 chars, within the ≤12-char cap).
  `multiSelect: false` renders radio buttons (exactly one answer).
  If the user picks "Skip", stop immediately without proceeding to
  Step 1.
- If `.kairoi/receipts.jsonl` exists: NEVER delete.
- If `.kairoi/overrides.json` exists: NEVER delete.

## What This Creates

```
.kairoi/
├── build-adapter.json
├── receipts.jsonl
├── buffer.jsonl
├── overrides.json
└── model/
    ├── _index.json
    └── <module>.json  (one per module, bootstrapped from source)
```

## Progress tracking

Before starting Step 1, MUST invoke `TaskCreate` once per step below
(10 calls, matching the 10 numbered Steps in this skill — Step 8.5
"Write behavioral rules" rolls into the Step 8 task because it
shares the same commit). Each call pairs `content` (imperative) with
`activeForm` (progressive):

1. `{ content: "Detect stack", activeForm: "Detecting stack" }`
2. `{ content: "Create build-adapter.json", activeForm: "Creating build-adapter.json" }`
3. `{ content: "Discover modules", activeForm: "Discovering modules" }`
4. `{ content: "Create _index.json", activeForm: "Creating _index.json" }`
5. `{ content: "Bootstrap models from source", activeForm: "Bootstrapping models from source" }`
6. `{ content: "Seed candidate guards from invariant comments", activeForm: "Seeding candidate guards" }`
7. `{ content: "Create overrides.json and empty JSONL files", activeForm: "Creating overrides and empty JSONL files" }`
8. `{ content: "Choose mode, configure .gitignore, install rules", activeForm: "Configuring mode, gitignore, and rules" }`
9. `{ content: "Commit init artifacts", activeForm: "Committing init artifacts" }`
10. `{ content: "Summarize init outcome", activeForm: "Summarizing init outcome" }`

Before starting each numbered Step below, MUST invoke `TaskUpdate` to
mark the matching task `in_progress`. After the Step completes, MUST
invoke `TaskUpdate` again to mark it `completed`. NEVER batch
completions. Pre-Check is intentionally NOT a task — it is the
preamble that happens before tracking begins.

## Step 1: Detect Stack

Reference [schemas/build-adapters.md](schemas/build-adapters.md) for detection rules.

## Step 2: Create build-adapter.json

Read plugin version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`.

```json
{
  "kairoi_version": "<version>",
  "stack": "<detected>",
  "test": "<test-command or null>",
  "source_dirs": ["src/"],
  "test_dirs": ["tests/"],
  "exclude_dirs": [],
  "edge_prune_min_weight": 2,
  "edge_prune_max_age_days": 30
}
```

## Step 3: Discover Modules

Scan `source_dirs`. A module = a directory directly under a source dir.

- **Node / JVM / Rust**: directories under source_dirs
- **Go**: packages (directories with `.go` files)
- **Python**: directories with `__init__.py`

If fewer than 2 directories, treat entire source tree as one module.

## Step 4: Create _index.json

MUST invoke `Bash` with:
- `command: 'mkdir -p .kairoi/model && touch .kairoi/.write-guard-disabled'`
- `description: 'Creating model directory and disarming write-guard for init writes'`

The `.kairoi/.write-guard-disabled` sentinel disarms the PreToolUse
deny hook (`scripts/state-write-guard.sh`) for the duration of init's
own Write tool calls in Steps 4–6 / 5.5. Step 7 removes the sentinel as
its last act, re-arming the guard before Step 8 configures `.gitignore`.
The sentinel is a transient dotfile (covered by the `.kairoi/.*`
gitignore patterns set in Step 8). Do not commit it.

Then MUST invoke `Write` with `file_path: '.kairoi/model/_index.json'` and `content` matching this shape:

```json
{
  "source_dirs": ["src/"],
  "modules": {
    "<id>": { "source_paths": ["src/<id>/"] }
  },
  "edges": []
}
```

## Step 5: Bootstrap Models from Source

For each discovered module, read up to 3 entry-point files (skipping
any >500 lines) and create a POPULATED model file (not an empty seed).
This is the critical difference from previous versions — the first
real task starts with a usable model.

For each module:

5a. Find entry point files. Check in order:
- `index.ts`, `index.js`, `mod.rs`, `__init__.py`, `main.go` in the module dir
- If none found, use the first 3 files alphabetically

5b. Read the entry point files (up to 3 files, skip files >500 lines).

5c. Scan for imports/requires referencing other discovered modules. These
become initial `dependencies`.

5d. MUST invoke `Write` with `file_path: '.kairoi/model/<module>.json'` and `content` matching this shape:

```json
{
  "purpose": "<derived from entry point: one sentence describing what this module does>",
  "entry_points": ["<detected entry files>"],
  "guards": [],
  "known_patterns": [],
  "dependencies": ["<modules referenced in imports>"],
  "_meta": {
    "last_validated": "<today ISO>",
    "tasks_since_validation": 0
  }
}
```

Do NOT persist `_meta.confidence`. Confidence is derived on read from
`tasks_since_validation` + `purpose` nullity. Storing it creates drift
risk between writers. `tasks_since_validation: 0` after bootstrap means
readers will compute `high` confidence on the next read.

If a module's entry point is too complex to summarize in one sentence, write
purpose as: "Entry point: <filename>. Exports: <list of main exports>."
This is more useful than null.

5e. Create initial edges from import analysis:
- If module A imports from module B, create a `calls` edge with a label
  describing the import (e.g., "imports validateToken from auth").

## Step 5.5: Seed candidate guards from explicit invariant comments

Before bootstrap is complete, scan each module's source for comments the
author has already written as invariants — `NEVER`, `MUST NOT`,
`WARNING:`, `DO NOT`, `IMPORTANT:`, `SECURITY:`. Each becomes a *candidate*
guard. This closes the "invisible for 3 sessions" gap: day-one kairoi
fires on something the human already wrote as explicit intent.

**This is NOT ingestion of human style preferences.** The filter allows
this because the text is explicit authored intent — the human wrote
`NEVER` knowing what they meant. kairoi is just delivering that
intent at the right moment mechanically.

For each module in `_index.json`, MUST invoke `Bash` with:
- `command: '${CLAUDE_PLUGIN_ROOT}/scripts/seed-guards.sh <module's source_paths[0]>'`
- `description: 'Scanning module source for invariant-comment candidate guards'`

The script outputs JSON:

```json
{
  "candidates": [
    { "file": "src/auth/token.ts", "line": 1, "keyword": "NEVER",
      "check": "NEVER remove the mutex lock below — concurrent refresh corrupts tokens" }
  ]
}
```

For each candidate, append a guard to the module's `.kairoi/model/<module>.json`:

```json
{
  "trigger_files": ["<candidate.file>"],
  "check": "<candidate.check>",
  "rationale": "Seeded from source comment on init. Promote or remove during first /kairoi:audit.",
  "source_task": "init-seed:<kebab-case summary of check, max 40 chars>",
  "created": "<today ISO>",
  "confirmed": 0,
  "disputed": 0,
  "status": "candidate"
}
```

The `status: "candidate"` field distinguishes seeded guards from
reflection-created ones. `/kairoi:audit` promotes candidates it confirms
(removes the `status` field) or removes those it can't justify.

If the scanner detects zero candidates, just skip — not every project
has explicit invariant comments, and that's fine.

Report in the final summary how many candidate guards were seeded per
module.

## Step 6: Create overrides.json

MUST invoke `Write` with `file_path: '.kairoi/overrides.json'` and `content`:

```json
{
  "modules": {}
}
```

See [schemas/state-files.md](schemas/state-files.md) for the per-module override fields (`pinned`,
`corrections`, `protected_guards`).

## Step 7: Create empty files and re-arm write-guard

MUST invoke `Bash` with:
- `command: 'touch .kairoi/receipts.jsonl .kairoi/buffer.jsonl && rm -f .kairoi/.write-guard-disabled'`
- `description: 'Creating empty append-only state files and re-arming write-guard'`

Removing `.kairoi/.write-guard-disabled` here re-arms the PreToolUse
deny hook for the rest of the session. From this point on, any Edit /
Write / MultiEdit on `.kairoi/**` (other than `.kairoi/overrides.json`)
will be blocked, redirecting hand-edits to `/kairoi:audit` /
`/kairoi:show` / overrides.

## Step 8: Choose collaboration mode & configure .gitignore

Kairoi needs to know how the project is developed so it can decide which
parts of `.kairoi/` belong in git (shared with teammates) and which stay
local-per-developer. There are two modes: Team and Solo.

### Idempotency check first

If the project's `.gitignore` already contains any kairoi entry (either
the solo-style `.kairoi/` whole-directory rule, or any team-style
individual entry like `.kairoi/buffer.jsonl`), the mode has already been
chosen on a prior init. Skip the prompt and the append — report
`"mode already configured, leaving .gitignore untouched"` in the
summary.

### Ask the user

MUST invoke `AskUserQuestion` with:

```
questions: [{
  question: "How is this project being developed?",
  header: "Mode",
  multiSelect: false,
  options: [
    {
      label: "Team",
      description: "Multiple developers. Commit model files, overrides, and stack config so teammates share the same understanding. Local work-in-progress (buffer, receipts, session log) stays on my machine."
    },
    {
      label: "Solo",
      description: "Just me. The entire .kairoi/ directory stays local to my machine — nothing kairoi-related goes into git."
    }
  ]
}]
```

`header` is "Mode" (4 chars, within the ≤12-char cap).
`multiSelect: false` renders a radio-button UI (exactly one answer).
The per-option `description` is what the user sees when hovering the
button — full sentences, not fragments.

### Append to `.gitignore` based on the answer

Create `.gitignore` if it doesn't exist. Append the appropriate block.

#### If Team

```
# kairoi — local per-developer work-in-progress (Team mode)
.kairoi/buffer.jsonl
.kairoi/receipts.jsonl
.kairoi/session.log

# kairoi — transient hook scratch state
.kairoi/.guards-log
.kairoi/.guard-disputes
.kairoi/.sync-manifest.json
.kairoi/.reflect-result-*.json
.kairoi/.seen-*
.kairoi/.session-summary.txt
.kairoi/.pre-sync/
.kairoi/.write-guard-disabled
```

In Team mode, `.kairoi/model/`, `.kairoi/overrides.json`, and
`.kairoi/build-adapter.json` ARE committed — the shared trust surface
teammates pull from.

#### If Solo

```
# kairoi — entire directory is local-per-developer (Solo mode)
.kairoi/
```

In Solo mode nothing kairoi writes is tracked by git.

### Mode inference on subsequent reads

No `mode.json` file records the choice — that would be schema
prescription for something the filesystem already encodes. Any reader
that needs to know the mode infers it by grepping `.gitignore`:

- Line matching `^\.kairoi/\s*$` → Solo mode.
- Line matching `^\.kairoi/buffer\.jsonl\s*$` (or any other individual
  entry) → Team mode.
- Neither → mode not configured (fresh init state).

### Keep in sync

The Team transient-files list above must stay in sync with `doctor.sh`'s
transient-file audit. Adding a new transient here requires updating the
doctor's `TRANSIENTS` variable.

## Step 8.5: Write behavioral rules

Write three rulesense-format rule files so Claude has ambient
orientation about kairoi state ownership, command routing, and the
project's writing stance. This runs before the commit step so the new
files land in the same init commit. No CLAUDE.md breadcrumb is
installed — the rule files carry the load on their own loading
discipline, so duplicating their content into the always-loaded
CLAUDE.md would just fire on every session regardless of relevance.

Track which artifacts were written vs. skipped so Step 10's summary
can report accurately. Each `Bash` tool call is a fresh subshell —
shell variables do NOT survive between invocations. Persist outcomes
to a transient file inside `.kairoi/`, then read it back in Step 10:

```bash
INIT_LOG=".kairoi/.init-summary"
mkdir -p .kairoi
: > "$INIT_LOG"   # truncate any prior partial run
```

Every command below appends one `key=value` line per outcome to
`$INIT_LOG`. Step 10 parses it; the file is gitignored (already
covered by the `.kairoi/.*` transient pattern set in Step 8) and may
be deleted after the summary renders.

### Copy rule files (skip-if-exists)

For each of `kairoi.md`, `kairoi-state-files.md`, and
`kairoi-writing.md`, copy from the skill's `rules/` directory into
`<project>/.claude/rules/`. If the destination already exists, leave
it untouched — the user may have customized it.

MUST invoke `Bash` with:
- `command: (the copy loop below, passed as a single command string)`
- `description: 'Installing kairoi behavioral rules under .claude/rules/'`

```bash
for RULE in kairoi.md kairoi-state-files.md kairoi-writing.md; do
  DST=".claude/rules/$RULE"
  SRC="${CLAUDE_SKILL_DIR}/rules/$RULE"
  if [ -e "$DST" ]; then
    echo "rule_skipped=$RULE" >> .kairoi/.init-summary
  else
    mkdir -p .claude/rules
    cp "$SRC" "$DST"
    echo "rule_written=$RULE" >> .kairoi/.init-summary
  fi
done
```

## Step 9: Commit

Stage only the paths init actually produced or modified this run.
Don't `git add -A` — the user's working tree may have unrelated
changes that shouldn't land in this commit.

MUST invoke `Bash` twice in sequence.

First call — stage:
- `command: 'git add .kairoi/ .gitignore && [ -e .claude/rules/kairoi.md ] && git add .claude/rules/kairoi.md; [ -e .claude/rules/kairoi-state-files.md ] && git add .claude/rules/kairoi-state-files.md; [ -e .claude/rules/kairoi-writing.md ] && git add .claude/rules/kairoi-writing.md; true'`
- `description: 'Staging init artifacts'`

Second call — commit:
- `command: 'git commit -m "chore: init kairoi"'`
- `description: 'Committing kairoi init'`

## Step 10: Summary

After all 10 tasks have been marked completed via `TaskUpdate`,
present this exact format (do NOT paraphrase or restructure):

- Stack detected
- Modules discovered (count + list with bootstrapped purposes)
- Initial edges found
- Collaboration mode from Step 8: `Team` or `Solo`, or `already
  configured (mode unchanged)` if `.gitignore` already contained a
  kairoi entry from a prior init.
- For each of `.claude/rules/kairoi.md`, `.claude/rules/kairoi-state-files.md`,
  and `.claude/rules/kairoi-writing.md`, one line reporting
  `wrote <file>` or `skipped <file> — already exists`. Read from
  `.kairoi/.init-summary` (the file written across Step 8.5's Bash
  invocations — shell variables don't survive between Bash tool calls,
  so the file is the only reliable source). Parse with:
  `grep '^rule_written=' .kairoi/.init-summary | cut -d= -f2-` and
  `grep '^rule_skipped=' .kairoi/.init-summary | cut -d= -f2-`.
- "Models were built from a source scan and are ready to use. Guards are
  empty — they grow from task reflection as I encounter surprises.
  Start the first task."
- "Edit `.kairoi/overrides.json` to correct my understanding at any time."

## Additional resources

- For stack detection rules and build-adapter field definitions, see [schemas/build-adapters.md](schemas/build-adapters.md)
- For per-module override fields (`pinned`, `corrections`, `protected_guards`), see [schemas/state-files.md](schemas/state-files.md)
- For the behavioral rule installed into the project on init, see [rules/kairoi.md](rules/kairoi.md)
- For the state-file behavioral rule installed into the project on init, see [rules/kairoi-state-files.md](rules/kairoi-state-files.md)
- For the writing-stance behavioral rule installed into the project on init (Pillar 2 code-tier), see [rules/kairoi-writing.md](rules/kairoi-writing.md)
