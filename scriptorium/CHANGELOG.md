# Changelog

All notable changes to scriptorium are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html); alpha releases may introduce breaking changes in minor versions.

## [Unreleased]

## [1.0.0-alpha] — 2026-04-29

### Added

- `/scriptorium:scribe` skill: comprehensive authoring guide for Claude Code instruction artifacts (SKILL.md, CLAUDE.md, plan files, subagent definitions, slash commands, hook scripts); covers every tool parameter, phrasing pattern, frontmatter field, and decomposition shape that Claude Code parses and executes reliably
- 13-item authoring checklist covering: `AskUserQuestion` full shape, `TodoWrite`/`TaskCreate`+`TaskUpdate` lifecycle, `Bash` description field, `Agent` dispatch parameters, plan-gate `ExitPlanMode` usage, no `AskUserQuestion` inside subagents, literal tool names with strong directive verbs, `SKILL.md` body shape and token budget, file reference resolution, user-facing output phrasing, frontmatter validity, decomposition opportunity (SUGGEST-only), and dynamic-injection safety
- `proofreader` subagent: audits any instruction artifact against the 13-item checklist; returns a structured PASS/FAIL/N/A/SUGGEST report per item with line-anchored evidence and concrete revision text
- Directory-mode cross-file pattern detection: flags the same checklist failure repeated across ≥ 3 files as a single systemic entry
- Decomposition guidance: identifies SKILL.md files that should be split into orchestrator + subagents; provides proposed file-tree output
- Dynamic-injection safety check: flags write-shaped commands in `` !`cmd` `` and ` ```! ` blocks that run unconditionally
- 12 reference files covering tools, workflow shapes, plans, hooks, permissions, dynamic context, agent frontmatter, key bindings, and decomposition patterns
- 6 worked examples: strong CLAUDE.md, plan file, SKILL.md, subagent definition, workflow decomposition, and a full worked example walkthrough
