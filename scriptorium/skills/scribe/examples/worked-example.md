# Worked example — weak to strong

This is the canonical weak-to-strong illustration for the scribe skill. It shows what a typical instruction artifact looks like without scribe's discipline, then what the same instructions look like after applying the checklist. Load this file when you need a full reference for how tool invocations, task lifecycle, and plan gating compose together inside a single artifact.

**Weak (typical output without this skill):**

> When the user asks to add a feature, understand the codebase, plan, ask clarifying questions, then implement.

**Strong (what this skill produces):**

> When the user asks to add a feature:
>
> 1. Invoke `TodoWrite` with these todos (use `TaskCreate` in interactive sessions):
>    - `{ content: "Explore codebase for relevant subsystems", activeForm: "Exploring codebase for relevant subsystems", status: "pending" }`
>    - `{ content: "Enumerate valid implementation approaches", activeForm: "Enumerating valid approaches", status: "pending" }`
>    - `{ content: "Resolve ambiguity with user", activeForm: "Resolving ambiguity with user", status: "pending" }`
>    - `{ content: "Draft and gate the plan", activeForm: "Drafting the plan", status: "pending" }`
>    - `{ content: "Implement approved changes", activeForm: "Implementing approved changes", status: "pending" }`
>    - `{ content: "Verify with lint, typecheck, tests", activeForm: "Verifying with lint typecheck tests", status: "pending" }`
>
> 2. Mark `explore` `in_progress` via `TodoWrite`. Invoke `Glob` and `Grep` with `output_mode: "files_with_matches"`. If the relevant subsystem exceeds 20 files, dispatch `Agent` with:
>    - `subagent_type: "general-purpose"`
>    - `description: "Scanning subsystem for touchpoints"`
>    - `prompt: "List every file that references [feature area] and summarize its role in ≤2 lines each"`
>    - `max_turns: 6`
>
> 3. Mark `enumerate` `in_progress`. List valid approaches.
>
> 4. If ≥2 valid approaches exist, mark `resolve-ambiguity` `in_progress` and invoke `AskUserQuestion` with:
>    ```
>    questions: [{
>      question: "Which implementation approach should I use?",
>      header: "Approach",
>      multiSelect: false,
>      options: [
>        { label: "<approach A>",  description: "<one-sentence trade-off>" },
>        { label: "<approach B>",  description: "<one-sentence trade-off>" },
>        { label: "You decide",    description: "Let Claude pick based on codebase fit" }
>      ]
>    }]
>    ```
>    The `questions: [...]` array wrapper is part of the canonical shape — see `../references/tools.md`. Each `label` ≤ 20 chars; append a "You decide" option as a fallback.
>
> 5. Mark `plan` `in_progress`. Invoke `EnterPlanMode`. Draft the plan. Invoke `ExitPlanMode` with plan sections: Problem · Approach · Files Touched · Risks · Test Strategy. For `Bash` commands the post-plan phase must run, either pass them via `allowedPrompts: [{ tool: "Bash", prompt: "npm test" }, ...]` (surface the session-wide scope caveat alongside) OR declare them in `permissions.allow` rules for narrower per-invocation scope.
>
> 6. On approval, mark `implement` `in_progress`. Apply changes via `Edit` (preferred) or `Write`. For multi-file renames, set session `permissionMode` to `"acceptEdits"` for the duration, then return to `"default"`.
>
> 7. Mark `verify` `in_progress`. Invoke `Bash` three times in sequence:
>    - `{ command: "npm run lint", description: "Linting the project", timeout: 60000 }`
>    - `{ command: "npm run typecheck", description: "Type-checking the project", timeout: 90000 }`
>    - `{ command: "npm test", description: "Running the test suite", timeout: 180000 }`
>
> 8. Mark every todo `completed` as it finishes — never batch. Return control to the user with a concise summary.

The strong version is longer because every tool invocation specifies the full schema with UX-shaping parameters named adjacent to the trigger. Full worked examples for other artifact types live alongside this file in `examples/` (`strong-skill.md`, `strong-claude-md.md`, `strong-subagent.md`, `strong-plan.md`).
