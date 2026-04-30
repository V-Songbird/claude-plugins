# Judgment-file shapes for Phase 2

Schemas and templates for writing `.rulesense-tmp/all_judgments.json`. Load on-demand when Phase 2 fires.

## Batched judgment file — canonical shape

The orchestrator handles both single-batch and multi-batch corpora through one batched format. Include every rule ID (the orchestrator validates completeness during finalization).

```python
# .rulesense-tmp/_judgment_all.py
import json
all_judgments = {
    "batches": [
        {
            "expected_ids": ["R001", "R002", "R003"],
            "judgments": [
                {"id": "R001",
                 "F3": {"value": 0.75, "level": 3, "reasoning": "..."},
                 "F8": {"value": 0.90, "level": 3, "reasoning": "..."}},
                {"id": "R002",
                 "F3": {"value": 0.40, "level": 2, "reasoning": "..."},
                 "F8": {"value": 0.55, "level": 2, "reasoning": "..."}},
            ]
        },
        # one entry per batch (single entry for small-corpus mode)
    ]
}
with open(".rulesense-tmp/all_judgments.json", "w", encoding="utf-8") as f:
    json.dump(all_judgments, f, indent=2, ensure_ascii=False)
```

Invoke `Bash` with `description: "Write judgments JSON; remove temp script"`:

```bash
$PYTHON_CMD .rulesense-tmp/_judgment_all.py && rm -f .rulesense-tmp/_judgment_all.py
```

## Unscorable rules

Use null values — 0.50 is not neutral and distorts scores:

```json
{"id": "R047",
 "F3": {"value": null, "level": null, "reasoning": "insufficient context"},
 "F8": {"value": null, "level": null, "reasoning": "insufficient context"}}
```

## F-patch shape — only when `needs_judgment: true` on the prompt entry

Some rules arrive flagged as needing an F1 or F7 patch; the mechanical score was ambiguous and the model must override it. The patch field name is `F1_patch` or `F7_patch`, and the shape MUST match the F3/F8 shape — a dict with a required `value` key (float in [0, 1] or null) and a `reasoning` string.

**Correct:**

```json
{"id": "R005",
 "F3": {"value": 0.75, "level": 3, "reasoning": "..."},
 "F8": {"value": 0.90, "level": 3, "reasoning": "..."},
 "F7_patch": {"value": 0.60, "reasoning": "mixes concrete API calls with abstract prose"}}
```

**Shapes the pipeline drops (silently or with a crash):**

- `"F7_patch": {"reasoning": "..."}` — missing `value` key → `parse_judgment` warns and drops.
- `"F7_patch": 0.60` — bare number, not a dict → dropped.
- `"F7_patch": {"value": "0.60", ...}` — string instead of number → dropped.
- `"F7_patch": {"value": 1.5, ...}` — out of range → dropped.

Only emit `F{N}_patch` for rules whose prompt entry carries `needs_judgment: true` or an explicit "patch requested" flag. NEVER volunteer patches on unflagged rules.
