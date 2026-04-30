# Changelog

All notable changes to rulesense are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html); alpha releases may introduce breaking changes in minor versions.

## [Unreleased]

## [1.0.0-alpha] — 2026-04-29

### Added

- `/rulesense:assay` skill: structural audit of CLAUDE.md and `.claude/rules/` files; scores each rule against eight factors (F1 trigger specificity, F2 conditional coverage, F3 Claude compliance judgment, F4 action presence, F7 framing, F8 redundancy) and returns a graded report with rewrite suggestions; `--fix` flag suggests and applies rewrites interactively
- `/rulesense:forge` skill: interactive rule authoring with real-time structural scoring; multi-rule brainstorm mode, 3-checkpoint review flow (draft → score → post-write); creates `.claude/rules/` files scored for Claude's parsing
- `/rulesense:file` skill: reformats rule files for readability — one concept per bullet, blank-line separation, 80-char wrap; never changes rule content, produces a before/after diff for confirmation before writing
- `run_audit.py` orchestrator: single entry point handling all pipeline mechanics; modes `--prepare`, `--finalize`, `--prepare-fix`, `--score-rewrites`, `--finalize-fix`, `--score-draft`, `--finalize-draft`, `--build-analysis`, `--cleanup`
- Failure-class diagnostics: distinguishes structural, framing, and coverage failure classes for targeted fix guidance
- Conflict detection: identifies rules that contradict each other within the same rule file
- Bright-line threshold system: mechanical pass/fail gates calibrated to Claude's actual parsing behavior
- High-stakes rule scaffold: templates for rules that govern irreversible or high-blast-radius actions
- Heading-context extraction: section headings propagate through chunking so conditional blocks merge with their parent directive
- Description-bullet prose filter: architecture descriptions classified as prose, not rules, preventing false positives
- JSX classifier fix: `<FormattedMessage />` patterns no longer misclassified as file paths
- 61-verb scoring vocabulary with noun-verb disambiguation
- 16 reference files covering scoring factors, rule organization, placement guidance, and report schema (assay skill)
- 5 reference files for the forge authoring workflow (brainstorm templates, scoring rubric, review checkpoints)
- Test suite: 514 tests covering extraction, scoring, composition, report rendering, and orchestrator modes
