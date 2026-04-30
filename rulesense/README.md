# rulesense

Audit and author CLAUDE.md rule files for Claude Code.

Rulesense makes Claude more effective at following your rules by improving the rules themselves. It scores rules for structural clarity — specificity of triggers, presence of action directives, framing, redundancy — and either suggests rewrites or authors new rules interactively.

> **Scores measure what authors control: rule structure. Claude's actual compliance depends on baseline behavior beyond rule text.**

> **Version:** 1.0.0-alpha — interfaces may change between minor releases.

## Skills

| Skill | Description |
|-------|-------------|
| `/rulesense:assay` | Structural audit of CLAUDE.md and `.claude/rules/` files. Scores each rule against eight factors and returns a graded report with rewrite suggestions. Use `--fix` to apply rewrites interactively. |
| `/rulesense:forge` | Interactive rule authoring with real-time structural scoring. Multi-rule brainstorm mode with a 3-checkpoint review flow (draft → score → post-write). |
| `/rulesense:file` | Reformats rule files for readability — one concept per bullet, blank-line separation, 80-char wrap. Never changes rule content; produces a before/after diff for confirmation before writing. |

## Scoring factors

Rules are scored against eight structural factors:

- **F1** — Trigger specificity: does the rule fire on a clear, identifiable condition?
- **F2** — Conditional coverage: are all relevant cases handled?
- **F3** — Claude compliance judgment: is the rule phrased so Claude can decide compliance without ambiguity?
- **F4** — Action presence: does the rule specify what to do, not just what not to do?
- **F7** — Framing: is the directive phrased in active, imperative form?
- **F8** — Redundancy: does the rule duplicate intent expressed elsewhere?

## Requirements

Python 3.11+ is required for the scoring pipeline scripts.

## Installation

Clone this repository and register the `rulesense/` directory as a Claude Code plugin.

## License

MIT — see [LICENSE](./LICENSE).
