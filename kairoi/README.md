# kairoi

Session safety for Claude Code in unfamiliar codebases.

Kairoi keeps Claude in sync with your project across long sessions. It fires warnings before risky edits, captures what changed after each session, and reflects on module state so context doesn't drift. Cross-module aware: guards for interface-level constraints automatically extend to dependent modules.

> **Version:** 1.0.0-alpha — interfaces may change between minor releases.

## What it does

**Edit-time guards** — pre-flight checks run before Claude edits trigger-matched files. Guards encode known constraints and fire before changes land, not after.

**Automatic session sync** — `sync-prepare` and `sync-finalize` scripts capture a manifest of tasks, files modified, guards fired, and test results per module after each session.

**Module reflection** — the `kairoi-reflect-module` subagent updates each module's purpose, entry points, known patterns, negative invariants, and change archetypes after a session, keeping Claude's understanding of the codebase accurate over time.

**Churn confidence** — guards accumulate confirmed and disputed counts. Guards with high dispute rates are flagged as suspect so you can review or retire them.

## Skills

| Skill | Description |
|-------|-------------|
| `/kairoi:init` | Seeds a project's `.kairoi/` state directory, writes initial rules and schemas |
| `/kairoi:kairoi` | Main session orchestrator: orientation, guard evaluation, and sync dispatch |
| `/kairoi:audit` | Manual inspection of guards, disputes, and task coverage for the current session |
| `/kairoi:show` | Displays the current module model in readable form |
| `/kairoi:lint` | Observation-only report on source patterns that increase Claude's re-reading cost |
| `/kairoi:doctor` | Diagnoses stale state, schema drift, and hook configuration issues |

## Setup

Run `/kairoi:init` in a new project to seed the `.kairoi/` state directory. The `hooks/hooks.json` file wires `PreToolUse`, `PostToolUse`, and `SessionStart` hooks automatically.

See `docs/recovery.md` for troubleshooting common failure modes.

## Installation

Clone this repository and register the `kairoi/` directory as a Claude Code plugin.

## License

MIT — see [LICENSE](./LICENSE).
