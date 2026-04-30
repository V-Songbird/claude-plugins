# forge

Pre-code feature review workflow for Claude Code.

Forge stress-tests a proposed feature design against the actual codebase before any code is written. It runs a 10-step pipeline: requirements understanding → structural search → reality-check spike → parallel domain expert analysis → master plan → adversarial critic → plan revision → user approval → implementation → optional build report.

The critical gates: parallel experts surface cross-domain conflicts that a single pass misses; the adversarial critic checks the plan against real code, not assumptions; and the user-approval step is where the feature can be redirected or killed before work begins.

> **Version:** 1.0.0-alpha — interfaces may change between minor releases.

## When to use

- The feature crosses two or more architectural areas or touches a trust boundary
- You want conflicts and risks surfaced before implementation starts
- You have a design in mind but want it stress-tested by domain experts first

Forge skips the full pipeline for trivial localized changes (typo fixes, single-method bugs).

## Skills

| Skill | Description |
|-------|-------------|
| `/forge:forge` | Full pipeline orchestrator. Entry point for all feature reviews. |
| `/forge:expert-analysis` | Parallel domain expert analysis (architecture, security, performance, testing, UX). |
| `/forge:master-plan` | Synthesizes expert reports into a single-layer implementation plan. |
| `/forge:critic-review` | Adversarial critic: grounds the master plan against actual code. |
| `/forge:plan-revise` | Incorporates critic findings and user feedback into a revised plan. |
| `/forge:dispatch-implementation` | Optional: parallel worktree dispatch for multi-step plans. |
| `/forge:build-and-report` | Optional: build and verify step after implementation. |

## Design

Forge is stack-agnostic — no hardcoded build commands. All stack-specific behavior defers to the consuming project's own CLAUDE.md.

## Installation

Clone this repository and register the `forge/` directory as a Claude Code plugin.

## License

MIT — see [LICENSE](./LICENSE).
