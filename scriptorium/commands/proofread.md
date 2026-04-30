---
description: Audit a Claude Code instruction artifact against the scribe 13-item checklist. Pass a file path as the argument to audit that file; omit it to provide artifact content directly. Returns a PASS / FAIL / PARTIAL verdict with per-item evidence and concrete fix text for each failure.
argument-hint: [path/to/artifact.md]
disable-model-invocation: true
---

# Proofread

Dispatch the `proofreader` subagent to audit the target artifact.

If `$ARGUMENTS` is a non-empty file path, MUST invoke `Agent` immediately:

```
Agent({
  subagent_type: "proofreader",
  name: "proofreader",
  description: "Audit artifact against scribe 13-item checklist",
  prompt: "$ARGUMENTS"
})
```

If `$ARGUMENTS` is empty (no argument was provided), MUST first invoke `AskUserQuestion` to collect the target, then dispatch `Agent` with the user's response as the `prompt`:

```
AskUserQuestion({
  questions: [{
    question: "What should I proofread?",
    header: "Target",
    multiSelect: false,
    options: [
      { label: "Paste content", description: "I'll send the artifact text in my next message" },
      { label: "Enter a path", description: "I'll type the file path to audit" }
    ]
  }]
})
```
