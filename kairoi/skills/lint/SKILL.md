---
name: lint
description: Observation-only report on source patterns that make Claude's own re-reading harder — star imports, files over 300 lines, source files with no matching test. Grounded in Claude's introspective knowledge of its own cognitive cost, not style-guide consensus. Triggers on kairoi style check, kairoi style report, check claude-legibility.
argument-hint: [module-name]
shell: bash
---

# kairoi lint

Report source patterns that slow down or confuse Claude's own re-reading.
The list is intentionally short and each item is justified by how Claude
actually processes code — not by what a conventional linter would flag.

MUST invoke `Bash` with:
- `command: '${CLAUDE_PLUGIN_ROOT}/scripts/style-check.sh $ARGUMENTS'`
- `description: 'Scanning for Claude-legibility issues'`

With no argument, the scanner checks every module. With a module name,
it scans just that one.

On first surfacing, present the script's stdout to the user without
paraphrasing, summarizing, or reformatting — echo each line as it was
emitted. The §"What it explicitly does NOT do" section below already
forbids source modifications and guard writes; that guidance extends
to this surfacing step — do NOT propose edits unless the user
explicitly asks.

## What it observes (and why)

- **Star imports / wildcard re-exports.** Tracing a symbol's origin
  through `import *` forces Claude to read the target module, enumerate
  its exports, and match — 2–3× the effort of following an explicit
  named import.

- **Files over 300 lines.** Above this threshold Claude's working
  memory for simultaneous invariants, mutations, and branch conditions
  gets lossy. Error-of-omission rate rises sharply; Claude starts
  missing branches it saw earlier in the file.

- **Source files with no matching test file.** Claude consults tests
  as executable behavioral spec when modifying code. Without them,
  confidence in "am I breaking the contract?" drops — Claude can
  only reason from the function body (what it *does*), not from the
  tests (what it *should do*).

## What it explicitly does NOT do

- Modify any source code.
- Write or remove any guard.
- Run as part of a hook. `lint` is a user-invoked skill, not a
  mechanical enforcement. Any move from "observation" to "enforcement"
  requires a separate philosophy-filter pass — surfacing nudges and
  blocking edits are different products.

## How the list grows

New observations require **two conditions**, both satisfied:

1. **Cognitive-cost justification**: Claude must explain *why this pattern costs Claude* — specific to how Claude processes code, not human readability conventions. "Forces Claude to trace N layers to resolve a symbol" qualifies. "Everyone knows this is bad" does not.

2. **Receipt evidence**: At least one task in `receipts.jsonl` where the pattern contributed to a BLOCKED outcome or demonstrably elevated re-reading effort. A principled cognitive-cost argument on its own is a *candidate*, not an observation. It waits until actual project history confirms the cost.

This gate keeps kairoi:lint anchored to evidence from the project it lives in, not style conventions borrowed from elsewhere. The three current observations each have real cognitive-cost justification AND would accumulate receipt evidence in any active project — they stay. New candidates that pass only condition 1 are noted mentally but not added until condition 2 is met.
