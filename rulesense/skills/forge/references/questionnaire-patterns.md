# Phase 2b — Questionnaire option sets by topic

Per-topic `AskUserQuestion` patterns. Adapt to the topic — do not use the option labels verbatim. Substitute concrete labels drawn from the project analysis in Phase 2 (real directories, real frameworks).

Every question whose answer space is a fixed enumerable set MUST be asked via `AskUserQuestion`. Only genuinely open-ended questions ("Is there a style guide or reference project I should match?", "Which directories are the focus?") may stay as plain text.

## Testing topic

Invoke `AskUserQuestion` for each of these (up to 3 total per session):

- **question**: `"What are you testing?"` · **header**: `"Test scope"` · **multiSelect**: `true` · options drawn from project analysis (e.g. `"API endpoints"`, `"React components"`, `"Database / data layer"`, `"End-to-end flows"`).
- **question**: `"What's the biggest pain point?"` · **header**: `"Pain point"` · **multiSelect**: `false` · options: `"No tests"`, `"Flaky tests"`, `"Slow tests"`, `"Too many mocks"`.
- **question**: `"How strict should these rules be?"` · **header**: `"Strictness"` · **multiSelect**: `false` · options: `"Hard requirements that block PRs"`, `"Guidelines Claude follows when writing new code"`.

## Code style topic

Invoke `AskUserQuestion` for the option-shaped questions and prose for the rest:

- **question**: `"Which aspects?"` · **header**: `"Style aspects"` · **multiSelect**: `true` · options: `"Naming"`, `"File organization"`, `"Imports"`, `"Error handling"`.
- Prose (open): "Is there a style guide or reference project I should match?"
- **question**: `"Where should these rules apply?"` · **header**: `"Rule scope"` · **multiSelect**: `false` · options: `"Everywhere (CLAUDE.md)"`, `"Specific directories (.claude/rules/ with paths:)"`.

## Architecture topic

Invoke `AskUserQuestion` for the option-shaped questions and prose for the rest:

- **question**: `"What boundaries matter most?"` · **header**: `"Boundaries"` · **multiSelect**: `true` · options: `"Layer separation"`, `"Module isolation"`, `"API contracts"`.
- **question**: `"Codify existing patterns or enforce new ones?"` · **header**: `"Direction"` · **multiSelect**: `false` · options: `"Codify existing patterns"`, `"Enforce new patterns"`.
- Prose (open): "Which directories are the focus?"
