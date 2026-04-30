# Teaching-summary patterns

Reference for Phase 3c Step 6. Load on-demand when Step 6 fires.

## Pattern table

For each applied change (rewrite, reorganize-move, or placement promotion), pick the best-fitting pattern. One change = one pattern; if several could apply, choose the one that most visibly changed in the before/after diff.

| Pattern | What changed | Why Claude needs this |
|---|---|---|
| Description → Directive | Added "When [trigger], [action]" structure | Descriptions describe state — "Components use X" has no firing moment. Directives tell Claude when to act. |
| Fragment → Complete sentence | Inlined parent verb + context | Claude reads each extracted rule in isolation. Fragments lack the heading context that made them legible to a human reader. |
| Principle → Concrete | Added examples, file paths, before/after | Abstract principles ("write clean code") give Claude no pattern to match. Concrete anchors turn the rule into something Claude can check against. |
| Prohibition → Positive alternative | Added positive action alongside prohibition | Claude is more reliable executing "do X" than "don't do Y". Prohibitions require Claude to recognize an action it's about to take and interrupt; positive imperatives bind trigger and action together. |
| Global → Scoped | Added file/directory scope or `paths:` | Unscoped rules load every session, consuming Claude's attention budget even when irrelevant. Scoped rules only load when the glob matches. |
| CLAUDE.md → Scoped rule file | Moved to `.claude/rules/` with `paths:` | Same principle as Global → Scoped, at file level — frees the always-loaded CLAUDE.md for rules that genuinely apply everywhere. |
| Rule → Primitive promotion | Moved to a hook / skill / subagent via `.rulesense/PROMOTIONS.md` | A deterministic gate or isolated worker enforces the behavior without consuming Claude's context on every session — the rule was in the wrong primitive. |

## Rendering rules

1. **Group the applied changes by pattern.** Drop any pattern with zero applied changes. Pick one before/after example per non-empty group — choose the clearest contrast.
2. **Render each non-empty pattern section in 4–6 lines.** Structure: pattern name, the before/after example you picked, a one-sentence explanation tied to that example.

## Structural patterns — prioritize when applied

The two most impactful structural changes reduce context-window load on every future session. Whenever reorganization or promotion ran, include these patterns with the count of moved rules and the core principle:

- **CLAUDE.md → Scoped rule file** — CLAUDE.md = core conventions loaded every session; `.claude/rules/` = focused guidelines loaded on demand.
- **Rule → Primitive promotion** — hooks / skills / subagents enforce behavior outside Claude's prompt entirely.

## Weak rewrites that survived

If any rewrites stayed below the quality floor after apply, note them separately with structural suggestions: before/after code examples, splitting into focused rules, adding specific triggers.
