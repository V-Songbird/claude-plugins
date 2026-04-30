# Changelog

All notable changes to forge are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html); alpha releases may introduce breaking changes in minor versions.

## [Unreleased]

## [1.0.0-alpha] — 2026-04-29

### Added

- `/forge:forge` orchestrator skill: 10-step pre-code feature review pipeline — understand requirements → structural search → reality-check spike → parallel expert analysis → master plan → adversarial critic → plan revise → user approval → implementation → build + report
- Entry guard: skips the full pipeline for trivial localized changes (typo fixes, single-method bugs); enters forge only when the feature crosses ≥ 2 architectural areas or touches a trust boundary
- Reality-check spike (Step 2.5): targeted ≤ 30-line probe against the single riskiest assumption before any planning begins; surfaces refutations to the user rather than silently re-scoping
- `/forge:expert-analysis` skill + `forge-expert` subagent: parallel domain expert analysis (architecture, security, performance, testing, UX); each expert reads actual code and returns a scoped report
- `/forge:master-plan` skill: synthesizes expert reports into a single-layer implementation plan (Feature, Steps with W-prefixed IDs, `Files touched`, `Done when` criteria, Risks, Open questions)
- `/forge:critic-review` skill + `adversarial-critic` subagent: ground-truths the master plan against the codebase; emits a structured critique organized as Blocking / High-priority gap / Open question; includes self-doubt rule for Blocking findings to reduce false positives
- `/forge:plan-revise` skill: incorporates critic findings and user feedback into a revised plan before approval
- User approval gate (Step 8): `AskUserQuestion` halt — the pipeline does not proceed to implementation without explicit approval
- `/forge:dispatch-implementation` skill + `forge-implementer` subagent: optional parallel worktree dispatch for plans with parallel-friendly steps
- `/forge:build-and-report` skill: optional stack-specific build and verify step after implementation; defers build commands to the consuming project's CLAUDE.md
- Color and effort metadata on all skills and agents for session-context visibility
- Stack-agnostic design: no hardcoded build commands; all stack-specific behavior deferred to the project's own CLAUDE.md
