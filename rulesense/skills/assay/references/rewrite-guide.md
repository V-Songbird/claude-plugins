# Rewrite Generation Guide

Reference for generating quality rewrites during Phase 3.5 (--fix mode).

## Extractor Compatibility

`extract.py::_try_split` splits compound directives on `;` and on `, and` / ` and ` when both sides have independent imperative verbs (via `_has_own_verb`). This is correct for real rule files, but forces rewrites to produce single-directive text to avoid re-fragmentation during re-scoring.

### Connective guidance

- **Use `or` instead of `and`** between independent clauses — `or` doesn't trigger the splitter
- **Avoid semicolons outside code spans.** Semicolons inside backticks are typically safe because surrounding clauses don't have independent verbs, but avoid when possible
- **Prefer a single sentence with embedded code spans** over multiple sentences joined by punctuation

### Examples

Good — extracts as one rule:
```
**All user-facing strings** use react-intl with `<FormattedMessage id="..." />` referencing IDs in `messages.json`.
```

Bad — splits into three:
```
**All user-facing strings** must use react-intl. Example: `<FormattedMessage id="..." />`. Reference `messages.json` for IDs.
```

### Verification

If a rewrite is complex, dry-run through `extract.py` first. A rewrite that extracts as N rules will have scores computed per-fragment, making re-scoring meaningless.

## Rewrite Strategy

1. **Target the dominant weakness** — the factor that contributes most to the low score
2. **Preserve intent** — rewrites change structural clarity, not the rule's meaning
3. **Single pass** — one attempt per rule per invocation
4. **Single directive** — produce one extractable rule, not a compound statement

## Pattern Taxonomy

Use these patterns to classify rewrites for the Step F teaching summary:

| Pattern | What was wrong | What the fix does |
|---|---|---|
| **Description → Directive** | States what exists ("Components use X") instead of instructing | Adds "When [trigger], [action]" structure |
| **Fragment → Complete sentence** | List item orphaned from heading, no verb or context | Inlines the parent's verb + enough context to stand alone |
| **Principle → Concrete** | Abstract maxim with no examples or file paths | Adds examples, file paths, before/after comparisons |
| **Prohibition → Positive alternative** | Says what not to do without saying what to do | Adds the positive action alongside the prohibition |
| **Global → Scoped** | Rule about specific files loaded globally in CLAUDE.md | Adds file/directory scope or suggests moving to .claude/rules/ with paths: |
| **CLAUDE.md → Scoped rule file** | Rule in CLAUDE.md only applies to specific files/directories | Move to .claude/rules/ with paths: frontmatter |

Most rewrites fit one pattern. If a rewrite combines two (e.g., fragment + concrete), pick the primary one.

## When to include intent

Rules can be unambiguous about trigger and action but still fail on edge cases the rule's literal wording doesn't cover. Adding a brief "because X" clause lets Claude extrapolate.

Without intent:
> "Use functional components for all new React files."

With intent:
> "Use functional components for all new React files — the team standardized on hooks for consistent code-review patterns."

If Claude encounters a class component that's being renamed (not new, not a rewrite), the intent-bearing version gives Claude a principle to apply ("hooks for consistency"). The intent-free version leaves Claude guessing.

**When to add intent**:
- The rule could be ambiguous in edge cases (most non-trivial rules)
- The rule is one of several competing conventions and Claude needs to know which one wins
- The rule contradicts a common pattern Claude might otherwise default to

**When to skip intent**:
- The rule is mechanically enforced elsewhere (hook, linter) and Claude never actually acts on it
- The rule's action is atomic enough that no extrapolation is possible

## Safety Gates

The orchestrator's `--finalize-fix` mode applies three safety gates automatically:

1. **Regression gate**: If `new_score < old_score`, the rewrite is dropped
2. **Judgment-volatility gate**: If F3 or F8 delta exceeds 0.20, a warning is shown (rewrite still presented)
3. **Self-verification gate**: If `|new_score - projected_score|` exceeds 0.05, a warning is shown (rewrite still presented)

These are handled by `rewrite_scorer.py --finalize` and don't require manual implementation.

## rewrites_input.json Schema

Each entry in the rewrites array:

```json
{
  "rule_id": "R001",
  "original_text": "Components use X",
  "suggested_rewrite": "When building components, use X with `<Component />` syntax",
  "file": "CLAUDE.md",
  "line_start": 15,
  "old_score": 0.03,
  "old_dominant_weakness": "F4",
  "projected_score": 0.75
}
```

The `projected_score` is your estimate of the rewrite's final score based on the targeted factor improvement. The self-verification gate compares this to the actual score.
