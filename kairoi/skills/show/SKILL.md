---
name: show
description: Pretty-print what kairoi is currently tracking about the codebase — modules, guards, edges, recent activity, pending overrides, buffer status. For the human auditing what Claude believes. Triggers on show kairoi, kairoi status, kairoi model, kairoi state, what is kairoi tracking.
argument-hint: [module-name]
shell: bash
---

# kairoi show

Render the current `.kairoi/` state in a human-readable form. Not for
Claude to consume — for the user, so they can see what kairoi is tracking
in a stack they may not be able to read themselves. Visibility is part of
the protection.

MUST invoke `Bash` with:
- `command: '${CLAUDE_PLUGIN_ROOT}/scripts/show.sh $ARGUMENTS'`
- `description: 'Rendering kairoi state'`

On first surfacing, present the script's stdout to the user without
paraphrasing, summarizing, or reformatting — echo each line as it was
emitted. The output is designed to be read by a human auditing what
kairoi believes, and paraphrasing defeats the visibility purpose. (If
the user then asks a follow-up like "summarize that" or "which module
looks riskiest?", answer in prose — the verbatim mandate applies only
to the initial surfacing.)

With no argument, output includes:
- Every module: confidence tier, staleness counter, purpose, entry points,
  guards (with confirmed/disputed counts), known patterns, dependencies.
- All edges (semantic first, then co-modified by weight).
- Last 5 receipts.
- Any pending overrides (pinned fields, corrections, protected guards).
- Current buffer status.

With a module name as the argument, output shrinks to just that module's
detail.
