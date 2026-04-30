# Promotion Guide

Reference for Phase 3d (placement opportunities) of the audit skill. Loaded only when Phase 3d fires.

This file tells Claude how to turn a placement detection into the per-candidate judgment strings (`why`, `suggested_shape`, `next_step`, `tradeoff`) that get written into `.rulesense/PROMOTIONS.md`.

## The primitive-mapping principle

Each Claude Code primitive has a niche:

- **Hooks** for deterministic gates you want mechanically unavoidable. Run outside the model's context, cannot be rationalized around, short-circuit the agent loop.
- **Skills** for context-triggered procedural guidance the main agent follows. Reference skills (style guides, API vocabulary) or action skills (`/deploy`, `/release`). Load on demand, not every session.
- **Subagents** for delimited tasks needing isolated reasoning, bias independence, or high-volume file reading. Main conversation stays lean; only a summary returns.

**If you find yourself encoding a judgment call in a hook or a mechanical check in a skill, you've misallocated.**

## What each judgment string must carry

When producing the JSON payload for `--write-promotions`, every candidate needs a `judgment` object with four fields. Templates below tell you what each field must cover per primitive.

### Hook candidates

- **`why`** — name the deterministic pattern. What specific tool-invocation, file-write, or lifecycle-event does the rule describe that a hook can catch without interpretation? Example: *"Mechanically detectable git tool-invocation (git commit / git push in Bash). A PreToolUse hook that rejects matching tool calls removes the possibility of bypass."*
- **`suggested_shape`** — name the event, the matcher, and the decision.
  - Event: `PreToolUse` / `PostToolUse` / `UserPromptSubmit` / `Stop` / `SessionStart` / `PreCompact`
  - Matcher: the specific tool name (`Bash`, `Edit`, `Write`) or pattern the hook should filter on
  - Decision: `block` (short-circuit) / `allow` (audit only) / `exit 1 on failure`
  - Example: *"PreToolUse with matcher: 'Bash', rejecting when the command matches `^git (commit|push)\\b`."*
- **`next_step`** — the concrete move. Usually "add to `.claude/settings.json` under `hooks.<Event>`" plus any helper-script name.
- **`tradeoff`** — optional. Name it if the hook has a known cost (slow suite, false-positive rate, etc.). Leave as `null` if there's no real tradeoff.

### Skill candidates

Choose **reference** or **action** based on the detection `sub_type`.

**Reference skill:**
- **`why`** — name what the reference contains. *"The rule is a pointer to the v2 style guide at `dll-components-v2/docs/dll-styleguide-tokens.md`. The real content is the reference, not the rule text."*
- **`suggested_shape`** — skill file path + invocation. *"Reference skill at `.claude/skills/v2-style-guide/SKILL.md` that Claude loads when styling v2 components. The SKILL.md embeds or links to the tokens doc."*
- **`next_step`** — scaffold the skill, delete the pointer rule.
- **`tradeoff`** — typically `null`. Reference skills have low downside.

**Action skill:**
- **`why`** — name the workflow and its invocation trigger. *"A multi-step release procedure invoked by user intent ('when deploying'). Keeping it as an always-loaded rule spends context on a procedure that runs rarely."*
- **`suggested_shape`** — skill file path + slash-command name + ordered steps. *"`/deploy` action skill at `.claude/skills/deploy/SKILL.md` running: (1) `npm run build`, (2) `npm test`, (3) `npm run deploy:prod`, (4) post to slack."*
- **`next_step`** — scaffold the skill, remove the workflow rule.
- **`tradeoff`** — note any steps that need secrets or credentials.

### Subagent candidates

Sub-types: `read-heavy` / `review` / `investigation`.

- **`why`** — name the isolation benefit. Pick one: *context hygiene* (would burn main attention on irrelevant files), *bias independence* (fresh context unmotivated by caller's assumptions), or *delimited task* (clean summary shape). Example: *"The rule asks Claude to read a large external tree as background for a judgment. Running this in the main context burns attention on files irrelevant to 95% of turns; a subagent reads on demand and returns a summary."*
- **`suggested_shape`** — agent file path, tool list, expected output.
  - File: `.claude/agents/<descriptive-name>.md`
  - Tools: restrict to what the task needs (usually `Read`, `Grep`, `Glob` for read-heavy / review)
  - Output: the summary shape (contract, verdict, inventory, list of gaps)
  - Example: *".claude/agents/coverage-auditor.md — Read-only subagent with tools [Read, Grep, Glob]. Prompt: 'Given this diff and these test files, verdict whether each new behavior is exercised by an assertion. Return APPROVED or a list of specific gaps.'"*
- **`next_step`** — scaffold the subagent file, invoke via the Agent tool at the appropriate moment.
- **`tradeoff`** — note if the subagent runs on every invocation vs. on-demand.

### Compound candidates

A compound rule's `judgment` has a different shape — `compound` object with `split_hint`, `part_a`, `part_b`, and optional `glue`.

- **`split_hint`** — one phrase naming where the rule splits. *"the comma before 'and make sure'"*.
- **`part_a`** / **`part_b`** — each a mini-judgment with `primitive`, `text`, `suggested_shape`, `next_step`, optional `tradeoff`. Use the per-primitive templates above.
- **`glue`** — emit ONLY when the compound has `compound_needs_glue: true` in the detection. The glue is a small skill that orchestrates the two parts at the right moment. If the parts fire independently, leave `glue: null`.

**Compound split heuristic:** look at the rule's verb chain. Find the conjunction (`, and`, `—`, `;`). Classify each half independently — one should score as hook or subagent from its verb shape ("never X", "audit Y"). The `split_hint` should name the conjunction in plain English.

## Bad judgment strings (examples)

Avoid generic templates. Each string must be tied to the specific rule.

| Bad | Why | Fix |
|---|---|---|
| "This should be a hook because it's mechanical." | Says nothing about the rule's specific verb or matcher. | Name the tool, the matcher, the decision. |
| "This is a skill because it's a workflow." | Doesn't name the invocation trigger or the steps. | List the ordered steps and the slash-command name. |
| "Move to a subagent." (with no shape) | User has no idea what to do next. | Name the agent file path, the tools, the summary output. |
| "Trade-off: there is a trade-off." | Non-answer. | Either name a concrete trade-off or set `tradeoff: null`. |

## Good judgment strings (full examples)

### Hook: `Never run git commit or git push`

```json
{
  "why": "Mechanically detectable tool-invocation pattern (git commit / git push in Bash). A PreToolUse hook that rejects matching tool calls removes the possibility of bypass under time pressure or long-conversation attention drift.",
  "suggested_shape": "PreToolUse with matcher: 'Bash', returning block when the command matches ^git (commit|push)\\b.",
  "next_step": "Add to .claude/settings.json under hooks.PreToolUse with a command that exits 1 and prints a reason on match.",
  "tradeoff": null
}
```

### Skill (reference): `Follow the v2 style guide at docs/tokens.md`

```json
{
  "why": "The rule is a pointer to an external reference (the v2 style guide). The substantive content lives in the referenced doc; the rule text just announces its existence, which burns context in every session regardless of whether Claude is touching v2 components.",
  "suggested_shape": "Reference skill at .claude/skills/v2-style-guide/SKILL.md that loads when Claude styles v2 components. The SKILL.md embeds the tokens doc or links to it with a load-on-demand pattern.",
  "next_step": "Scaffold the skill file, point it at dll-components-v2/docs/dll-styleguide-tokens.md, remove the pointer rule from CLAUDE.md.",
  "tradeoff": null
}
```

### Subagent: `When investigating dll/components imports, read the source at D:\\...\\Dallas-Digital`

```json
{
  "why": "The rule asks Claude to read a large external tree (the sibling dll/components source) as background for a judgment call. Running this in the main context burns attention on files irrelevant to most turns; a dedicated subagent reads on demand, returns a contract summary, and leaves the main conversation lean.",
  "suggested_shape": ".claude/agents/dll-components-reader.md — Read-only subagent (tools: Read, Grep, Glob) with the sibling repo path pinned in its instructions. Returns a summary of the requested component's props, exports, and contract.",
  "next_step": "Scaffold the subagent file; invoke via the Agent tool when Claude needs a dll-components contract, instead of triggering a full source read in the main loop.",
  "tradeoff": null
}
```

### Compound: `Never commit without tests, and make sure the suite covers the change`

```json
{
  "split_hint": "the comma before 'and make sure'",
  "part_a": {
    "primitive": "hook",
    "text": "Never commit without running tests",
    "suggested_shape": "PreToolUse on Bash matching ^git commit, runs the test command, exits non-zero on failure.",
    "next_step": "Add to .claude/settings.json under hooks.PreToolUse.",
    "tradeoff": "Full test suite on every commit is painful for slow suites. Mitigate with affected-tests-only (pytest --lf) or gate on a 'tests-passed-since-last-edit' marker file."
  },
  "part_b": {
    "primitive": "subagent",
    "text": "make sure the test suite covers the change",
    "suggested_shape": ".claude/agents/coverage-auditor.md — Read-only subagent (tools: Read, Grep, Glob). Prompt: given the diff and test files, verdict whether each new behavior is exercised by an assertion. Returns APPROVED or a list of gaps.",
    "next_step": "Scaffold the subagent file; invoke via the Agent tool before the hook fires.",
    "tradeoff": null
  },
  "glue": {
    "primitive": "skill",
    "text": "coordination between the gate and the audit",
    "suggested_shape": "Optional commit-discipline skill triggered while Claude prepares a commit, instructing it to invoke the coverage-auditor before the hook fires (so the audit runs while Claude is still reasoning about the diff, not after the agent has stopped thinking about it).",
    "next_step": "Optional — skip if invoking the subagent manually before commit is acceptable."
  }
}
```
