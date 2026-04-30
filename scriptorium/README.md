# scriptorium

Reference guide and proofreader for Claude Code instruction artifacts.

Scriptorium makes Claude more effective at authoring the instruction files that drive Claude Code: SKILL.md files, CLAUDE.md rule files, plan files, subagent definitions, slash commands, and hook scripts. The scribe skill documents every tool parameter, phrasing pattern, frontmatter field, and decomposition shape that Claude Code parses and executes reliably. The proofreader audits drafts against a 13-item checklist so nothing downstream falls back to prose placeholders or bare tool calls.

> **Version:** 1.0.0-alpha — interfaces may change between minor releases.

## Skills

| Skill | Description |
|-------|-------------|
| `/scriptorium:scribe` | Comprehensive authoring guide for Claude Code instruction artifacts. Covers tools, frontmatter, phrasing patterns, decomposition shapes, and dynamic-injection safety. |

## Proofreader

The `proofreader` subagent audits any instruction artifact against a 13-item checklist:

1. `AskUserQuestion` full shape
2. `TodoWrite` / `TaskCreate` + `TaskUpdate` lifecycle
3. `Bash` description field
4. `Agent` dispatch parameters
5. Plan-gate `ExitPlanMode` usage
6. No `AskUserQuestion` inside subagents
7. Literal tool names with strong directive verbs
8. SKILL.md body shape and token budget
9. File reference resolution
10. User-facing output phrasing
11. Frontmatter validity
12. Decomposition opportunity (SUGGEST-only)
13. Dynamic-injection safety

Returns a structured PASS/FAIL/N/A/SUGGEST report per item with line-anchored evidence and concrete revision text. In directory mode, repeating failures across three or more files are surfaced as a single systemic entry.

## Installation

Clone this repository and register the `scriptorium/` directory as a Claude Code plugin.

## License

MIT — see [LICENSE](./LICENSE).
