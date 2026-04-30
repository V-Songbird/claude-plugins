# Promotions payload template

Full `_write_promotions.py` template for Phase 3c Step 5a. Load only when Step 5a fires.

## Judgment-field contract (non-compound moves)

Every non-compound move MUST include all four `judgment` fields or `--write-promotions` emits a warning and the rendered `PROMOTIONS.md` entry becomes header-only:

- `why` — specific pattern that maps this rule to this primitive (tied to the rule's actual content, not a generic "this is mechanical").
- `suggested_shape` — concrete matcher / file path / tool list / command.
- `next_step` — the user's literal next action (what file to create, what command to add, which primitive file to scaffold).
- `tradeoff` — string when there's a real trade-off (slow hook, permission prompt, bias window), else `null`.

## Compound-move contract

Each compound move MUST include `compound.split_hint`, `compound.part_a`, `compound.part_b`, and `compound.glue` — `glue` is `null` unless the candidate's detection reported `compound_needs_glue: true`.

## Python payload template

Invoke `Write` to create `.rulesense-tmp/_write_promotions.py` with contents:

```python
# .rulesense-tmp/_write_promotions.py
import json
payload = {
    "schema_version": "0.1",
    "project": "<project-name>",
    "audit_grade": "<letter> (<score>)",
    "generated_at": "<ISO-8601 UTC timestamp>",
    "moves": [
        # Hook candidate — all four judgment fields required.
        {
            "rule_id": "R042",
            "primitive": "hook",
            "sub_type": "deterministic-gate",
            "rule_text": "<copy the source rule text verbatim>",
            "file": "CLAUDE.md",
            "line_start": 42,
            "line_end": 42,
            "judgment": {
                "why": "<what does this rule say that makes it a hook?>",
                "suggested_shape": "<PreToolUse matcher + decision; skill file path; subagent tool list>",
                "next_step": "<add to .claude/settings.json; scaffold .claude/skills/name/SKILL.md; etc.>",
                "tradeoff": None,  # or "<specific downside>"
            },
        },
        # Compound candidate — only for entries whose best_fit == "compound".
        {
            "rule_id": "R023",
            "primitive": "compound",
            "rule_text": "<copy the source rule text verbatim>",
            "file": "CLAUDE.md",
            "line_start": 23,
            "line_end": 23,
            "compound": {
                "split_hint": "<one phrase naming where the rule splits>",
                "part_a": {
                    "primitive": "hook",
                    "text": "<first half>",
                    "suggested_shape": "<...>",
                    "next_step": "<...>",
                    "tradeoff": None,
                },
                "part_b": {
                    "primitive": "subagent",
                    "text": "<second half>",
                    "suggested_shape": "<...>",
                    "next_step": "<...>",
                    "tradeoff": None,
                },
                "glue": None,  # or a small skill description when compound_needs_glue is true
            },
        },
    ],
}
with open(".rulesense-tmp/promotions_input.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)
```

## Post-write handling

After running the two Bash invocations specified in Step 5a, check the output JSON for `warnings`. If any move was missing judgment fields, `--write-promotions` emits a warnings array plus stderr messages identifying the rule IDs. Regenerate the payload with complete judgment strings and re-run before presenting results — users should NEVER see a header-only entry.

The write is atomic: either `.rulesense/PROMOTIONS.md` is written AND all moved rules are removed from their source files, or nothing changes. On hard failure (source-file drift, write error), the JSON output has `status: "failed"` with a `reason` field.
