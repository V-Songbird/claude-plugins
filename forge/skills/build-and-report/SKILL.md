---
name: build-and-report
description: Steps 9 + 10 of the forge workflow. Aggregates implementer reports (or in-session edits if `/forge:dispatch-implementation` did not run), merges work-unit worktrees if any exist, bumps the version per the consuming project's convention, runs the project's build / verification commands, and produces a user-facing final report including the two mandatory sections "How to test this feature" and "How is this feature useful?". Stack-agnostic — actual build commands and version-bump file (`plugin.xml`, `package.json`, `Cargo.toml`, etc.) live in the consuming project's own CLAUDE.md.
user-invocable: false
model: sonnet
effort: medium
color: purple
---

# Build and Report

Post-implementation close for a forge run. Merges work-unit worktrees (if any), bumps the version per the consuming project's convention, runs the project's build, and emits the final report. Stack-agnostic: concrete commands live in the consuming project's own CLAUDE.md.

This skill handles two paths:

- **Parallel-implementation path** — `/forge:dispatch-implementation` ran; one or more work-unit worktrees need merging into the active branch before build.
- **In-session path** — the orchestrator implemented the plan directly in the main session; no worktrees to merge. Skip merge, go straight to version bump + build.

## Required Inputs

- The approved master plan in conversation context (the report references its steps + risks).
- One of:
  - All implementer reports from the most recent `/forge:dispatch-implementation` run (parallel path), OR
  - The orchestrator's in-session edit summary (in-session path).
- The consuming project's CLAUDE.md, which provides stack-specific build commands and the version-bump rule. (Note: this is the user's project CLAUDE.md, NOT the forge plugin's own files.)

## Procedure

### 1. Aggregate implementation status

**Parallel path:** for each implementer report:

- Confirm "done-when criterion: yes" (not "no" / "partial-because"). Any "no" or "partial" is a blocker — surface to the user before proceeding.
- Confirm the Blockers section is empty. If a hard blocker exists, route to the user; do NOT silently proceed to merge.

Tabulate:

```markdown
| Unit | Status | Files changed | Tests | Notes |
|------|--------|---------------|-------|-------|
| W1 | Done | … | passed | … |
| W2 | Blocked | … | n/a | <blocker summary, link to implementer report> |
```

If any unit is blocked, STOP. Surface the blocker to the user; do not merge worktrees with incomplete work.

**In-session path:** restate the orchestrator's edit summary with `file:line` for each change, mapped to the plan's steps. Confirm each step's done-when criterion was met before proceeding.

### 2. Merge work-unit worktrees (parallel path only)

Skip this step on the in-session path — there are no worktrees to merge.

Each implementer ran in `isolation: "worktree"` and committed once. Aggregate by merging each unit branch back to the working branch in dependency order (the plan's contract clause numbering is a reasonable proxy when there is no explicit dependency graph).

MUST invoke `Bash` for each merge with a clear `description`:

```
Bash(
  command: "git merge --no-ff <unit-branch>",
  description: "Merge work unit W<N> back into the active branch"
)
```

Resolve any merge conflict by reading both sides + the plan's contract clauses; never blindly accept either side. Conflicts usually signal that two units' "Files touched" sets overlapped — that's a planning gap to note in the final report's "what we'd improve" section.

### 3. Re-verify each step's done-when criterion against the merged tree

The step's `Done when` criterion is the canonical verification step (preferred form: a verification command). Run it against the merged tree, regardless of which path you took.

For each step:

- If the criterion is a **command**, invoke `Bash`. Record pass/fail + output snippet on fail.
- If the criterion is a **manual smoke test**, surface it in the final report as "manual-smoke-required: <steps>" so the user knows what to verify by hand.

If a command-based criterion fails, STOP. The merge is complete but the feature does not satisfy the plan. Surface to the user before bumping versions or producing the final report.

### 4. Bump the version, then run the project's build / verification commands

Forge is stack-agnostic; the actual commands depend on the consuming project. Read the consuming project's CLAUDE.md "Build Commands" section (or the closest equivalent it carries) for:

- The version-bump file(s) and the conventional bump rule (semver patch / minor / major). Examples: `plugin.xml` + `build.gradle.kts` for IntelliJ plugins; `package.json` for Node; `Cargo.toml` for Rust; `pyproject.toml` for Python; `.claude-plugin/plugin.json` for Claude Code plugins.
- The build command (e.g. `./gradlew buildPlugin`, `npm run build`, `cargo build`, etc.).
- The verification command (test suite, type-check, lint, smoke build) appropriate to the change set.

Bump the version BEFORE running the build, so the build artifact carries the new version number.

If the consuming project's CLAUDE.md does not specify these, MUST invoke `AskUserQuestion` with the full schema below — populate the first 2–3 option labels with concrete commands you discovered from the project (Makefile target, `package.json` script, build tool config, etc.) and keep "Skip build" as the last option. Do NOT invent commands you did not see in the project.

```
AskUserQuestion(questions: [{
  question: "The project's CLAUDE.md does not specify build commands. Which should I run?",
  header: "Build",
  multiSelect: false,
  options: [
    { label: "<discovered command 1>", description: "<what this command does, with the file/script it came from>" },
    { label: "<discovered command 2>", description: "<what this command does, with the file/script it came from>" },
    { label: "Skip build", description: "Complete the workflow without building. The final report will note that build verification was skipped." }
  ]
}])
```

For each command, MUST invoke `Bash` with a `description`:

```
Bash(
  command: "<project's build command from CLAUDE.md>",
  description: "Run project build to verify the merged change set compiles"
)
```

If the build fails: STOP. Surface the failure to the user with the failing output; do not paper over with `--no-verify` or skip flags.

### 5. Produce the final report

Append a single markdown report to the conversation, following the structure in [references/final-report.md](references/final-report.md). The report MUST include these two sections, named exactly:

- **How to test this feature** — step-by-step in plain language a non-developer can follow. Name the entry point (menu item / URL / command), the inputs to try, what counts as success, and which edge cases to poke. Avoid file paths and function names — the user does not need them at this layer.
- **How is this feature useful?** — explain the user-visible benefit in plain language. Lead with the user's pain or goal; describe what changes; describe what they can now do that they couldn't before. Do NOT name internal modules, classes, or implementation details — this section is for the people who use the software, not the people who build it.

For the full report template, see [references/final-report.md](references/final-report.md).

## Critical Constraints

- **NEVER skip the merge-conflict resolution step (parallel path).** Auto-accepting one side discards the other implementer's work.
- **NEVER skip a failing done-when criterion.** Step 3 verifies the merged change matches the plan's behaviour, not just that it compiles.
- **NEVER skip a failing build.** `--no-verify` or equivalent flags hide regressions; the build is the workflow's last safety net.
- **NEVER invent build commands.** If the project's CLAUDE.md does not name them, ask the user. Inventing a command risks silent breakage.
- **NEVER write the final report without both mandatory sections.** "How to test this feature" and "How is this feature useful?" are workflow contract; report renderers downstream rely on those exact headings.
- **NEVER write the report in implementer jargon.** Both mandatory sections are user-facing. Strip file paths, class names, and internal step labels before delivering.

## Next Step

Final step. The workflow is complete when this skill returns the report to the user.

## Additional resources

- For the full final-report template (with the two mandatory sections in their canonical form), see [references/final-report.md](references/final-report.md)
