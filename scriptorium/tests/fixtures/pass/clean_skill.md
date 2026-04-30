---
name: format-files
description: Formats source files in the project. Asks which files to format, runs the formatter, and reports results. Invoke when the user wants to format code.
---

# Format Files

## Step 1 — Confirm scope

MUST invoke `AskUserQuestion` before touching any files:

```
AskUserQuestion({
  questions: [{
    question: "Which files should I format?",
    header: "Scope",
    multiSelect: false,
    options: [
      { label: "All files", description: "Format every source file in the project" },
      { label: "Changed files only", description: "Format only files modified since the last commit" }
    ]
  }]
})
```

## Step 2 — Track progress

ALWAYS create a task list with `TodoWrite` before starting work:

```
TodoWrite({
  todos: [
    { content: "Find files matching the selected pattern", activeForm: "Finding files", status: "pending" },
    { content: "Run formatter on each file", activeForm: "Formatting files", status: "pending" },
    { content: "Report results", activeForm: "Reporting results", status: "pending" }
  ]
})
```

## Step 3 — Run formatter

MUST invoke `Bash` with a description:

```
Bash({
  command: "npx prettier --write \"src/**/*.{ts,tsx}\"",
  description: "Run Prettier on all TypeScript source files"
})
```

## Step 4 — Report

Tell the user how many files were formatted and whether any errors occurred.
