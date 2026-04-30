---
name: doctor
description: Validates structural integrity of .kairoi/ state files. Checks JSON validity, module consistency, guard fields, edge references, JSONL format, test command, and .gitignore coverage. Use when scripts error, state seems corrupted, or after manual edits. Triggers on doctor kairoi, check kairoi health, validate kairoi state, kairoi broken.
argument-hint: (no arguments)
shell: bash
---

# kairoi doctor

Validate structural integrity of `.kairoi/` state files.

MUST invoke `Bash` with:
- `command: '${CLAUDE_PLUGIN_ROOT}/scripts/doctor.sh'`
- `description: 'Validating kairoi state integrity'`
- `timeout: 30000`

On first surfacing, present the script's stdout to the user without
paraphrasing, summarizing, or reformatting — echo each line as it was
emitted. Each failing check's line includes the recovery action; those
action lines must not be suppressed or rewritten. (If the user then
asks a follow-up like "which of those should I fix first?", answer in
prose — the verbatim mandate applies only to the initial surfacing.)

This performs structural checks only — no semantic analysis. For
verifying that models accurately reflect source code, use
`/kairoi:audit` instead.

**Checks performed**:
- JSON/JSONL file validity
- Module files match _index.json registry
- Guard fields (trigger_files, source_task, check)
- Edge references point to existing modules
- _meta fields have valid values
- build-adapter.json test command is executable
- Transient files are covered by .gitignore
