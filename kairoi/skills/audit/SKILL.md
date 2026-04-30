---
name: audit
description: Reconciles kairoi model files against source code. Verifies guards, validates edges, resets confidence. Run when confidence is low, after external changes, or periodically. Triggers on audit kairoi, validate models, check models, reconcile models.
argument-hint: [module-name or "all"]
effort: high
shell: bash
---

# Audit kairoi models

Dispatch the `kairoi-audit` subagent to reconcile models against
source code.

Target: $ARGUMENTS (defaults to "all")

## When to run

- Session boot shows modules with `low` confidence
- After merges, manual edits, or external contributions
- Periodically (~every 20-30 tasks)
- When guards seem wrong during work

## Invoke

MUST invoke `Agent` with:

```
subagent_type: "kairoi-audit"
name: "kairoi-audit"
description: "Audit kairoi models"
prompt: "Reconcile kairoi model files against source code. Target: $ARGUMENTS (defaults to 'all' if empty). Follow the kairoi-audit agent's Steps 1–7."
max_turns: 25
run_in_background: false
```

The `kairoi-audit` subagent is resolved by `subagent_type` name; its
definition lives under the plugin's `agents/` directory and declares
`maxTurns: 25`. The explicit `max_turns: 25` above matches that value
so the runtime does not default to a smaller budget.
`run_in_background: false` because the user expects to see the audit
report inline in the same turn that invoked `/kairoi:audit`.
