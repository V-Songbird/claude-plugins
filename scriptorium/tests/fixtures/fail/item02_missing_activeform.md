---
name: run-tests
description: Runs the test suite and reports results.
---

# Run Tests

ALWAYS create a task list before starting:

```
TodoWrite({
  todos: [
    { content: "Run test suite", status: "pending" },
    { content: "Parse test results", status: "pending" },
    { content: "Report failures to user", status: "pending" }
  ]
})
```

MUST invoke `Bash` to execute the tests:

```
Bash({
  command: "npm test -- --reporter=json",
  description: "Execute the full test suite with JSON output"
})
```
