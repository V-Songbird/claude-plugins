# Rewrite pipeline mechanics (Steps A–D)

Called from Phase 3c Step 5b when `selected_changes.rewrite == true`. Load on-demand when Step 5b fires. Steps A–D generate and score rewrites; the text-based apply step lives in SKILL.md Step 5b so it honours the fixed `promote → rewrite → reorganize` execution order.

## Step A — Select qualifying rules

Invoke `Bash` with `description: "Select rules qualifying for rewrite"`:

```bash
$PYTHON_CMD "$SCRIPTS/run_audit.py" --prepare-fix
```

Outputs mandate rules scoring below 0.50 with their dominant weakness and suggested action. If none qualify (possible if Step 5a promoted every weak rule), tell the user no rewrites remain and return to Phase 3c Step 5c (or Step 6 if no reorganize).

## Step B — Generate rewrites

For each qualifying rule, generate a single rewrite targeting the dominant weakness without changing intent. Read `references/rewrite-guide.md` for extractor compatibility (avoiding re-fragmentation by `extract.py`) and the pattern taxonomy.

### Extractor self-check — required before writing each rewrite

The extractor splits compound directives on specific patterns. Rewrites containing those patterns get fragmented into multiple scored "rules", wasting the rewrite and re-injecting low-quality orphans into the audit. Before committing a rewrite, verify:

- [ ] No `, and ` or ` and ` between two clauses that each have their own imperative verb. Use `or`, a comma + participle, or split into the single most important directive.
- [ ] No `;` outside a code span.
- [ ] No ` — ` (em-dash + space) followed by an independent clause with its own imperative verb. Em-dash attached to a parenthetical / example / adjective phrase is fine.
- [ ] The rewrite reads as exactly one directive when read aloud.

Failing any check, revise BEFORE writing to the rewrites JSON. `--score-rewrites` cannot catch this; by then the rewrite has already fragmented.

Invoke `Write` to create `.rulesense-tmp/_gen_rewrites.py`:

```python
# .rulesense-tmp/_gen_rewrites.py
import json
rewrites = [
    {"rule_id": "R001", "original_text": "...", "suggested_rewrite": "...",
     "file": "CLAUDE.md", "line_start": 15, "old_score": 0.03,
     "old_dominant_weakness": "F4", "projected_score": 0.75},
]
with open(".rulesense-tmp/rewrites_input.json", "w", encoding="utf-8") as f:
    json.dump(rewrites, f, indent=2, ensure_ascii=False)
```

Invoke `Bash` with `description: "Write rewrites JSON; remove temp script"`:

```bash
$PYTHON_CMD .rulesense-tmp/_gen_rewrites.py && rm -f .rulesense-tmp/_gen_rewrites.py
```

## Step C — Score rewrites

Invoke `Bash` with `description: "Score proposed rewrites mechanically"`:

```bash
$PYTHON_CMD "$SCRIPTS/run_audit.py" --score-rewrites
```

Scores all rewrites mechanically and builds judgment prompts. Output shape matches Phase 1 metadata. Read the prompt file(s) and score F3/F8 — same flow as Phase 2. Write to `.rulesense-tmp/rewrite_judgments.json` using the batched format.

**Fragmentation check.** The scorer emits `WARNING: <rule_id> rewrite would fragment into N rules` on stderr for any rewrite containing a splitter pattern. The scored JSON also includes `_rewrite_meta.would_fragment: true` and a `fragments_preview`. If any warnings fire, revise those rewrites in `.rulesense-tmp/rewrites_input.json` (use `or` instead of `, and`, drop semicolons, collapse to one directive) and re-run `--score-rewrites`. Applying a fragmenting rewrite injects orphan F-grade fragments into the next audit.

## Step D — Finalize rewrites

Invoke `Bash` with `description: "Finalize rewrites and render report"`:

```bash
$PYTHON_CMD "$SCRIPTS/run_audit.py" --finalize-fix
```

Pass `--verbose` or `--json` if requested. Parses judgments, applies safety gates (regression, volatility, self-verification), composes scores, renders the report. Present the output.

Return to SKILL.md Phase 3c Step 5b for the text-based apply step. Do NOT ask another "apply?" question — the user already consented at the Phase 3c fix menu.
