---
name: pick-strategy
description: Asks the user to pick an implementation strategy before proceeding.
---

# Pick Strategy

MUST invoke `AskUserQuestion` to choose the approach:

```
AskUserQuestion({
  questions: [{
    question: "Which implementation strategy should I use?",
    options: [
      "Option A: incremental refactor",
      "Option B: full rewrite"
    ]
  }]
})
```

Proceed based on the user's selection.
