# Fix-menu preamble template (Phase 3c Step 2)

The read-only snapshot rendered before the Step 3 multiSelect. Load on-demand when Step 2 fires.

## Voice

First-person ("I could fix…", "I'll write…"). Matches Step 3's `"Which of these changes should I apply?"` question. The user sees these two blocks back-to-back; voice MUST stay consistent.

## Framing rule — every section MUST name rules as the subject

Users reported that bare `"Hook candidates (N)"` / `"Subagent candidates (N)"` blocks read as *proposals to create new hooks or subagents from scratch* rather than what they actually are (existing rules that would work better expressed as those primitives). Every section NAMES "rules that look like …" or "rules that scored …" etc. as the subject, with hooks / subagents / scoped files as the proposed target — NEVER the reverse.

## Output template

Render each block only when its class has applicable content. OMIT whole sections otherwise — do NOT leave empty headers.

```
## What I could fix next

Here's a snapshot. You'll pick any combination next; nothing moves until you submit.

### Rules that would work better as a different primitive    ← block A (if any placement candidates)

These [P] rules already exist in your tree. If you pick "Promote" next, I'll write move-suggestions to `.rulesense/PROMOTIONS.md` and remove them from their source files. Nothing lands in `.claude/settings.json` or `.claude/agents/` automatically — `PROMOTIONS.md` is a hand-off doc you act on when ready.

Rules that look like hooks ([n1]) — deterministic gates that could run outside Claude's context:
- <rule_id> · <file>:<line_start> · <rule text truncated to 80 chars>
- …

Rules that look like skills ([n2]) — reference material / workflows loaded on demand:
- …

Rules that look like subagents ([n3]) — isolated workers invoked by name:
- …

Rules that split across primitives ([n4]) — halves belong to different primitives:
- …

### Existing rules that scored below the quality floor    ← block B (if any mandate rules below 0.50)

[R] mandate rules scored below 0.50 — the point where Claude starts misinterpreting or ignoring them. If you pick "Rewrite" next, I'll draft and score a proposed rewrite for each, run safety gates, and apply only the ones that improve. You'll see a before/after summary per rule.

### Rules that could load on-demand instead of every session    ← block C (if Phase 3b recommended reorganization)

Phase 3b flagged [O] rules (≈[L] lines of CLAUDE.md) that always load even on unrelated work. If you pick "Reorganize" next, I'll move them into [target file(s) Phase 3b suggested] with a `paths:` glob, so they only load when Claude works on matching files. Rule text is unchanged — this is pure relocation.

Pick any combination on the next screen, or skip every box to leave everything as-is.
```

## Substitution rules

- `[P]`, `[R]`, `[O]` — actual counts (placement total, weak-rule total, organization-move total).
- `[n1]`–`[n4]` — per-category placement counts. Omit the whole category line when its count is 0.
- `[L]` — line-count impact from Phase 3b.
- `[target file(s) Phase 3b suggested]` — concrete filename(s) and glob(s) from Phase 3b (e.g. `.claude/rules/v2-components.md with paths: dll-components-v2/src/**/*.{ts,tsx}`).
- Cap each category's rule list at 20 entries. If a category has more than 20, show the first 20 and end with one line `  …and <N-20> more`.

## Locked header wording

Use these exact phrasings — NEVER the bare `Hook candidates (N)` / `Subagent candidates (N)` form that earlier drafts produced (that wording is what users misread):

- `Rules that look like hooks (N) — deterministic gates that could run outside Claude's context`
- `Rules that look like skills (N) — reference material / workflows loaded on demand`
- `Rules that look like subagents (N) — isolated workers invoked by name`
- `Rules that split across primitives (N) — halves belong to different primitives`
