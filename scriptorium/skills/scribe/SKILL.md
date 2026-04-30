---
name: scribe
description: Use when authoring any Claude Code instruction artifact — SKILL.md, CLAUDE.md, plan files, subagent definitions, slash commands, hook scripts, or any markdown intended to steer Claude Code behavior in a later session. Ensures the artifact names Claude Code's interactive and UX-shaping tools (AskUserQuestion with header/multiSelect, TodoWrite/TaskCreate with paired content/activeForm, Bash with description, Agent with description/name, plan-mode gates, subagent limitations, hooks, permission modes) at the right points with complete parameter coverage, rather than prose placeholders or bare tool calls that Claude Code silently degrades.
---

# Authoring Claude Code Instruction Artifacts

## When this skill applies

Load this skill whenever authoring or editing any of:

- A `SKILL.md` (new or edit)
- A `CLAUDE.md` (managed, user, or project level)
- A plan file produced via plan mode
- A subagent definition (`~/.claude/agents/*.md`, `.claude/agents/*.md`, or `<plugin>/agents/*.md`)
- A slash command (`.claude/commands/*.md`) — note: merged into skills, see `references/slash-commands.md`
- A hook script or its documentation
- Any markdown whose purpose is to steer Claude Code behavior in a future session

This skill does NOT apply when *executing* inside Claude Code (writing code, running builds). It governs only the text of instruction artifacts that Claude Code will consume later.

## Preload manifest — load these references BEFORE writing

Per artifact type, `Read` the listed reference files BEFORE drafting. Loading them after the fact catches mistakes only on the proofreader pass — by then you have already encoded the wrong shape across multiple files. The cost of a four-file `Read` upfront is one round-trip; the cost of a re-audit loop is multiple proofreader dispatches plus rewrites.

| Authoring … | MUST preload | SHOULD preload when relevant |
|---|---|---|
| `SKILL.md` | `references/skill-authoring.md`, `references/tools.md` | `references/dynamic-context.md` (if injection used), `references/permissions.md` (if `allowed-tools` used) |
| Subagent definition (`agents/*.md`) | `references/subagents.md`, `references/tools.md` | `references/workflow-skill-shapes.md` § 3 (for `model` / `maxTurns` derivation) |
| `CLAUDE.md` | `references/claude-md.md`, `references/tools.md` | `references/hooks.md` (if hooks cited) |
| Plan file (via plan mode) | `references/plans.md`, `references/permissions.md` | `references/tools.md` (`ExitPlanMode` `allowedPrompts` schema) |
| Slash command (`.claude/commands/*.md`) | `references/slash-commands.md`, `references/skill-authoring.md` | `references/permissions.md` |
| Hook script / hook documentation | `references/hooks.md`, `references/permissions.md` | `references/settings.md` |
| Decomposing a monolithic workflow | `references/decomposition.md`, `references/workflow-skill-shapes.md`, `references/claude-md.md` | All of the above — decomposition emits multiple artifact types |

`anti-patterns.md` is consulted at the *end* of authoring (scan before returning), not preloaded. For the proofreader's audit pass, the entire scribe SKILL.md is preloaded via the `skills:` field.

## The problem this skill solves

Instruction artifacts routinely fail in two ways:

1. **Tool-level omission.** The artifact says "ask the user" instead of `invoke AskUserQuestion with …` → downstream session asks in prose, breaks the button-driven flow.
2. **Parameter-level omission.** The artifact says `AskUserQuestion with options A/B/C` but omits `header`, `multiSelect`, or per-option `description` → the tool fires with a bare schema, UI falls back to truncation, multi-answer is silently disabled.

This skill fixes both. Every rule below applies to the *text you write into the artifact*, not to the tools you use while authoring it.

## Pre-completion checklist

Before returning any instruction artifact, verify every item. If any fails, revise.

1. **Every clarification point names `AskUserQuestion` with full shape.** The top-level input is `{ questions: [{ … }] }` — the `questions` array wrapper is required (matches the tool's TypeScript schema, 1–4 entries per call). Each question object specifies `question`, `header` (≤12 chars), `multiSelect: true|false`, and 2–4 `options` each with `label` + `description`. `header` and `multiSelect` are tool-required in practice; omission silently degrades UI. Per-option `preview` is optional but must be paired with a note about `toolConfig.askUserQuestion.previewFormat` if used.

2. **Every multi-step workflow names `TodoWrite` (SDK / non-interactive) or `TaskCreate` + `TaskUpdate` (interactive; `TaskGet` / `TaskList` also available for inspection) with paired `content` + `activeForm` on every item.** `content` is imperative (`"Read the file"`), `activeForm` is progressive (`"Reading the file"`). They are not interchangeable — `activeForm` renders during `in_progress`, `content` renders when `pending` or `completed`. An item missing `activeForm` is a fail. **Task-lifecycle invariant:** the artifact MUST NOT instruct Claude to leave multiple tasks `in_progress` simultaneously, start a new task before marking the prior one `completed`, or skip the `completed` transition on exit / error / branch. Silence inherits the system default (single-active, close-before-next) and is NOT a fail; only explicit contradictions of the invariant fail this item. **Umbrella-task pattern (recommended):** when a single planned task expands at runtime into N internal sub-steps, prefer keeping one `in_progress` todo and mutating its `activeForm` per sub-step (`"Applying fix 1 of 3 — promoting placement candidates"` → `"Applying fix 2 of 3 — rewriting weak rules"` → …) over inserting new todos mid-flight. Inserting into the array after work has started causes list-corruption UX (rows mixing, disappearing, confusing the user about what is actually running). `TodoWrite` / `TaskUpdate` re-render the row in place when the array shape is preserved.

3. **Every long-running or non-obvious `Bash` call names `description`.** Bare `Bash` invocations with just `command` fail. Exception: trivial commands like `pwd`, `ls`, `whoami` where a description would be noise.

4. **Every `Agent` dispatch names `description` and `subagent_type` (both required per `references/tools.md`), adds `name` when user-facing, and specifies `model` / `run_in_background` / `max_turns` / `isolation` when their defaults would be wrong.** Paired sub-rule for subagent *definitions*: when the artifact being authored is itself a subagent (`agents/*.md`), tool restrictions MUST live in the `tools` frontmatter field, NEVER in body prose. A subagent body that says *"you have Read, Grep, Glob — no write access"* without a corresponding `tools: Read, Grep, Glob` frontmatter line silently inherits the dispatcher's full tool set. Synthesis-shaped subagents (master-plan, expert-revise, critic) MUST also set `model: opus` even if the source artifact omits the annotation — synthesis quality is model-bound, not effort-bound. Bound `maxTurns` per the derivation rule in `references/workflow-skill-shapes.md` § 3 rather than picking by feel.

5. **Any plan gate names `ExitPlanMode`.** `ExitPlanMode` accepts an optional `allowedPrompts: Array<{ tool: "Bash"; prompt: string }>` to pre-approve specific `Bash` commands for the post-plan execution phase. Caveat: pre-approvals persist session-wide, not just for the plan's scope ([anthropics/claude-code#27160](https://github.com/anthropics/claude-code/issues/27160)). For commands that must gate per-invocation, prefer `permissions.allow` rules in `settings.json` instead. An artifact that uses `allowedPrompts` without surfacing the session-scope caveat is a partial fail. See `references/plans.md`.

6. **Subagent prompts MUST resolve ambiguity up-front.** Foreground subagents technically *can* invoke `AskUserQuestion` (passes through to user); background subagents fail silently. Since a foreground subagent can be backgrounded at runtime (Ctrl+B), never rely on `AskUserQuestion` from a subagent — resolve all ambiguity in the dispatching session before the `Agent` call.

7. **Every tool name appears literally**, adjacent to its trigger, with strong directive verbs (`MUST invoke`, `ALWAYS create`, `NEVER skip`). Weasel verbs (`should consider`, `may want to`, `can use`) paired with tool names fail — Claude treats them as advisory.

8. **`SKILL.md` body stays within budget; embedded content extracts to `references/`; supporting files are indexed via `## Additional resources`.** Applies only to `SKILL.md` artifacts (N/A elsewhere). Partial fail if the body exceeds 500 lines OR if the body contains any single embedded code block / payload template / pattern table longer than ~20 lines that is pure content (not control flow). Full fail if the body exceeds roughly 5,000 tokens — content above that cap vanishes after auto-compaction. Frontmatter `description` over 1,536 chars is a hard fail. Any supporting file in the skill directory (e.g. `reference.md`, `examples.md`, `references/*.md`) that is not linked from the body — ideally under a `## Additional resources` section with one "For X, see [file](file)" bullet per file — is a partial fail: Claude will not know to load it. Fix is always extraction to a reference file with a pointer in the body, never re-phrasing for terseness. See the `Structural principle` section below for what belongs in body vs references.

9. **Every file reference in the artifact resolves.** Applies to every artifact type. Every markdown link `[text](path)`, every inline backtick path adjacent to a directive verb (`see references/foo.md`, `load examples/bar.md`, `read @path/to/file`), and every CLAUDE.md `@path` import must point to a file that actually exists. Resolution is relative to the artifact's own directory unless the path is absolute or uses `@~/` for home. Broken references fail silently at runtime — Claude attempts the load, gets nothing, and proceeds as if the referenced guidance did not exist. Partial fail per broken reference; the fix is either correct the path or remove the reference. Section anchors in links (`[text](file.md#section)`) are also validated when present — the linked heading must exist in the target file.

10. **User-facing output (every `AskUserQuestion` question, every option `description`, every status message and result report the artifact tells Claude to emit) reads to a non-author.** Plain language, no internal jargon (phase numbers, internal step labels, enum values, function names, tool names exposed in chat). One voice per skill — first-person skill paired with second-person user is the default; mixing first/third/passive across adjacent messages fails. Name the action and its consequence, not the implementation mechanism. Short sentences, active verbs. NEVER expose file paths, function names, or internal tool names in user-facing prose unless the user is meant to open or inspect them. See `## Phrasing rules for user-facing output` below for the 5 sub-rules and worked phrasings.

## Decomposing monolithic instruction artifacts

When the source artifact is a long workflow document — multiple subagent dispatches, multiple numbered phases, embedded templates that recur across phases — the right output is NOT a single SKILL.md. It is a small graph of skills, references, subagents, and (occasionally) hooks routed by what each piece actually is.

### Trigger

Run the 5 mechanical checks at [references/decomposition.md](references/decomposition.md) § 1. Decomposition fires when **≥ 2 signals hold**. Below the threshold, this section does NOT apply — produce a single artifact normally.

### Phase order when decomposition fires

1. **Detect.** Confirm which of the 5 signals fire. Cite the matched line ranges in your eventual output so the user can verify the routing.

2. **Route.** Walk every distinct piece of the source through the 7-destination routing table at [references/decomposition.md](references/decomposition.md) § 2. Each piece maps to one of: `CLAUDE.md` / reference skill / action skill / subagent / agent-team flag / hook flag / MCP flag. Auto-author skills + subagents + extracted reference files; flag-only for hooks, agent teams, and MCP.

3. **Surface judgment calls.** For each of the 6 questions at [references/decomposition.md](references/decomposition.md) § 9, MUST invoke `AskUserQuestion` with full shape — `questions: [{ question, header (≤12 chars), multiSelect: false, options: [{ label, description }, …] }]` — carrying the tradeoff text from the table. **Q1 (Deploy: project-local vs plugin-shipped) MUST fire FIRST** — every other artifact's destination depends on it. **Q2 (Name) fires only when Q1 = Plugin-shipped.** NEVER silently pick.

4. **Derive frontmatter mechanically.** For each generated skill, fill frontmatter per [references/decomposition.md](references/decomposition.md) § 4. NEVER set `context: fork` on workflow-orchestrator skills — it loses main-session conversation context AND blocks subagent dispatch (subagents cannot nest).

5. **Apply target shape.** Every generated action skill follows the 7-section body layout from [references/workflow-skill-shapes.md](references/workflow-skill-shapes.md) § 2. Body ≤ 100 lines; templates ≥ 15 lines extract to `references/`.

6. **Generate the CLAUDE.md hub.** Use the fixed-shape spec at [references/workflow-skill-shapes.md](references/workflow-skill-shapes.md) § 4. ≤ 200 lines; NO full `Agent(...)` prompt bodies, NO templates, NO stack-specifics — those live in skills and `references/`.

7. **Hoist read-only round-trips.** For each generated skill whose dispatch template opens *"first invoke `Bash` to get Y, then …"* where the command is read-only, hoist into a `## Current Codebase State` block per [references/dynamic-context.md](references/dynamic-context.md) § 8. Auto-add the narrowest scoped `Bash(<cmd> *)` to `allowed-tools`. Skip on synthesis-only skills (master-plan, expert-revise) where current state is redundant relative to the conversation context being synthesized.

8. **Flag SUGGEST candidates** (do not auto-author):
   - **Hook candidates** — every deterministic obligation in the source ("MUST cite file:line", "MUST escalate blockers"). Name the lifecycle event (`SubagentStop`, `PreToolUse`, etc.) and the validation logic. Trust-sensitive — author must review.
   - **Agent-team candidates** — every cross-subagent iteration loop ("Continue until X and Y reach coherence"). Note the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` requirement.
   - **MCP candidates** — every external service mentioned ("query the database", "post to Slack", "fetch from JIRA").

9. **Self-audit.** Dispatch `proofreader` per the next section, passing the produced tree's root (CLAUDE.md and the `.claude/` directory). Items 11–13 of the proofreader checklist specifically validate the decomposition output.

### What stays in main session

Source steps labeled *"Direct execution in main session"* or *"Action: Direct"* — orchestrator-only steps with no subagent dispatch — become rows in the CLAUDE.md step table, NOT skills. The action skills are dispatchers; main-session orchestration glues them together. This is the documented [Skill+Subagent combination pattern](https://code.claude.com/docs/en/features-overview#combine-features) — preserve it; do not flatten dispatchers into the workers they call.

For the canonical worked example (286-line monolith → 5 skills + 1 subagent + CLAUDE.md hub + workflow-reference.md, with line-range provenance and the four `AskUserQuestion` calls), see [examples/workflow-decomposition.md](examples/workflow-decomposition.md).

## Final step — self-audit with `proofreader` before returning the artifact

The checklist above is what a well-authored artifact looks like. This step is how you verify you produced one. After drafting or editing any instruction artifact covered by this skill, dispatch `proofreader` to audit it. Do NOT rely on the user or a later reviewer to catch checklist failures — scribe's contract is that artifacts it produces are already audited.

Invoke `Agent` with the full shape:

```
subagent_type: "proofreader"
name: "proofreader"
description: "Audit <artifact kind> against scribe checklist"
prompt: "<absolute path to the artifact, OR the full inline artifact content if it has not been written to disk yet>"
```

If the artifact is a `SKILL.md` at `~/.claude/plugins/foo/skills/bar/SKILL.md`, pass that path. If the artifact is a draft that has not been written (e.g. a new `CLAUDE.md` you are about to hand back), pass the inline content in the `prompt` field — `proofreader` audits either form.

Handle the returned report:

- **Verdict PASS (all 12 verdict-counted items PASS or N/A; item 12 SUGGEST is informational only)** — return the artifact as-is. If item 12 emitted SUGGEST flags, surface them to the user as opportunities to consider — do not silently apply.
- **Verdict PARTIAL** — for each `FAIL` item, apply the `Fix:` text in the report. Then dispatch `proofreader` AGAIN with the re-audit template below. **The re-audit dispatch is mandatory, not optional** — applying fixes without re-running the audit is the most common scribe failure mode (the fixes themselves can introduce new violations, or miss the actual root cause). Loop until PASS, up to 2 re-audits — if item 9 (file references) still fails after two passes, surface the remaining issues to the user with the proofreader's evidence rather than returning a silently-broken artifact.
- **Verdict FAIL** — same loop as PARTIAL; treat every `FAIL` item as mandatory to fix.

**Re-audit dispatch template** (use on pass 2 and 3 — saves proofreader from re-evaluating items that already passed):

```
subagent_type: "proofreader"
name: "proofreader"
description: "Re-audit pass <N> on <artifact>"
prompt: "Re-audit pass <N> of 3. Prior verdict: <PARTIAL|FAIL>. Items previously PASS: <list>. Items previously FAIL: <list with one-line summary of the fix applied>. Items previously N/A: <list>.

Focus the re-audit on the previously-FAILED items and any items the fixes may have touched. Mark previously-passing items PASS without re-evaluation UNLESS your scan reveals the fix introduced a regression there. Artifact path or content: <…>"
```

Do not dispatch `proofreader` with `run_in_background: true` — you need the report before deciding whether to return. Do not pass `isolation: "worktree"` — proofreader is read-only and does not modify files.

This step does NOT apply when the user explicitly says they want a draft without verification ("just give me a sketch", "don't run the audit yet"). In every other case, run it.

## Structural principle: the SKILL.md body is an orchestrator

A `SKILL.md` body is control flow and decision logic — the steps Claude must take, the branches it must choose between, the invariants it must preserve. It is **not** a container for embedded content.

**Action skills vs reference skills.** Per the [features overview](https://code.claude.com/docs/en/features-overview#skill-vs-subagent), skills are either *action skills* (imperative top-level steps with a clear start and end — `/expert-analysis`, `/deploy`) or *reference skills* (standing knowledge applied throughout the session — API style guides, role catalogs). The body shape MUST match: action skills have imperative verbs at the top of each step; reference skills have section headings naming knowledge categories. `context: fork` only fits action skills with self-contained tasks — a reference skill paired with `context: fork` gives the forked subagent guidelines but no task and returns nothing useful. See [references/workflow-skill-shapes.md](references/workflow-skill-shapes.md) § 1 for the routing.

Move to `references/` (read on demand) and keep out of the body:

- Payload templates, file-write templates, JSON/YAML schemas longer than ~10 lines
- Pattern catalogs and pattern tables (teaching-summary tables, shape catalogs, categorized examples)
- Pipeline mechanics that a single step already delegates to ("Phase N Steps A–D" sub-pipelines)
- Large worked examples beyond one canonical illustration

Keep in the body:

- Phase order, step order, branch conditions
- Tool invocations with full shape (per `Phrasing rules` below)
- Invariants that Claude must hold across steps (e.g. task-lifecycle, single-active-task)
- Pointers that name which `references/<file>.md` to load when a step needs detail

**Budgets to respect** (see `references/skill-authoring.md` for the full rationale):

| Limit | Value | Enforcement |
|---|---|---|
| Frontmatter `description` | 1,536 chars | Hard cap |
| `SKILL.md` body | < 500 lines | Soft cap |
| Per-skill compaction re-attach | ~5,000 tokens | Content above this cap vanishes after auto-compaction |

If the body is approaching 500 lines or 5k tokens, the first question is always "what can move to `references/`?" — not "how do I rephrase this more tersely?" Extraction preserves the logic; terseness usually erodes it.

**Reference supporting files from `SKILL.md` with the canonical `## Additional resources` section** so Claude knows what each file contains and when to load it (per [Anthropic's skill authoring guide](https://docs.claude.com/en/docs/claude-code/skills)):

```markdown
## Additional resources

- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

Rules:

- One bullet per reference file. Each bullet states **when to load** it ("For X, see …"), not what it contains.
- Use a relative markdown link. Flat layout (`[reference.md](reference.md)`) or subdirectory layout (`[references/tools.md](references/tools.md)`) are both valid — pick one and stay consistent within a skill.
- Supporting files are **not auto-loaded**. Claude reads them with `Read` only when the body instructs — either via this section or via an inline pointer at the step that needs the detail (e.g. "See `references/plans.md` for the full `ExitPlanMode` schema").
- Inline pointers at the point of use are complementary to the `## Additional resources` index, not a replacement for it — the index is what a Claude skimming the SKILL.md first sees.

## Additional resources

This `SKILL.md` is the index. Load the relevant file on demand when authoring the matching artifact type — Claude Code does not auto-load supporting files.

- For full tool schemas and UX-critical parameters, see [references/tools.md](references/tools.md)
- For `SKILL.md` frontmatter, compaction budgets, and content lifecycle, see [references/skill-authoring.md](references/skill-authoring.md)
- For subagent frontmatter and dispatch patterns, see [references/subagents.md](references/subagents.md)
- For the hook event catalog and handler types, see [references/hooks.md](references/hooks.md)
- For `CLAUDE.md` discovery and `@path` imports, see [references/claude-md.md](references/claude-md.md)
- For plan-mode lifecycle and the `ExitPlanMode` schema, see [references/plans.md](references/plans.md)
- For slash-command authoring and argument substitutions, see [references/slash-commands.md](references/slash-commands.md)
- For permission modes and rule syntax, see [references/permissions.md](references/permissions.md)
- For `settings.json` keys affecting instruction execution, see [references/settings.md](references/settings.md)
- For dynamic context injection (`` !`cmd` `` and ` ```! ` blocks), safety rules, and the round-trip-hoisting pattern, see [references/dynamic-context.md](references/dynamic-context.md)
- For decomposing monolithic workflow artifacts into a tree of skills + subagents + CLAUDE.md hub, see [references/decomposition.md](references/decomposition.md)
- For workflow-skill target shapes (7-section layout, when to set each frontmatter field, CLAUDE.md hub spec, Skill+Subagent combination pattern), see [references/workflow-skill-shapes.md](references/workflow-skill-shapes.md)
- For the canonical weak-to-strong illustration, see [examples/worked-example.md](examples/worked-example.md)
- For a well-authored `SKILL.md`, see [examples/strong-skill.md](examples/strong-skill.md)
- For a well-authored `CLAUDE.md`, see [examples/strong-claude-md.md](examples/strong-claude-md.md)
- For a well-authored subagent definition, see [examples/strong-subagent.md](examples/strong-subagent.md)
- For a well-authored plan file, see [examples/strong-plan.md](examples/strong-plan.md)
- For the canonical decomposition walkthrough (286-line monolith → 5 skills + 1 subagent + CLAUDE.md hub), see [examples/workflow-decomposition.md](examples/workflow-decomposition.md)
- For failure modes and correct-form fixes (scan before returning any artifact), see [anti-patterns.md](anti-patterns.md)

## Phrasing rules for reliable tool firing

1. **Name tools literally, adjacent to triggers.** Distance between trigger phrase and tool name is the single largest predictor of whether the tool fires. Put the tool name in the same sentence as the trigger, not three paragraphs later.

2. **Strong directive verbs.** `MUST invoke`, `ALWAYS create`, `NEVER skip` fire reliably. `should consider`, `may want to`, `can use` are treated as advisory and often skipped.

3. **Specify arguments inline.** Don't write "call AskUserQuestion." Write the full schema with every UX-relevant field filled.

4. **Positive framing for primary instructions.** "Invoke X when Y" fires more reliably than "Don't forget X when Y."

5. **Anchor triggers to observable conditions.** "When ≥2 valid implementation approaches exist" is enforceable. "When appropriate" is not.

6. **When prescribing a tool, prescribe its full shape.** Partial schemas produce partial calls. See `references/tools.md` for the full schema of each tool.

## Phrasing rules for user-facing output

The rules above govern how Claude invokes tools. These rules govern the prose the skill instructs Claude to **say to the user** — `AskUserQuestion` questions and option `description`s, summary blocks after a phase, menu labels, status previews, result reports. Skills ship to everyone from new users to experts; the output must read the same to both.

1. **Use plain language; never internal jargon.** If a term appears only in the skill's own authoring (phase numbers, internal step labels, pattern codes, enum values from the implementation), translate it before it reaches the user. "Applying fix 2 of 3 — rewriting weak rules" is fine. "Executing Phase 3c Step 5b rewrite-pipeline" is not.

2. **Pick one voice per skill and hold it.** First-person for the skill (`"I found 3 placement candidates"`, `"I'll move them into …"`) paired with second-person for the user (`"you'll pick …"`, `"nothing moves until you submit"`) reads cleanly. Don't mix first-person, third-person (`"The skill found …"`), and passive (`"3 candidates were found"`) across adjacent messages in the same flow. When in doubt, match the voice already used by the skill's `AskUserQuestion` questions — those are the most visible anchor.

3. **Name the action and its consequence, not the internal mechanism.** "If you pick 'Promote' next, I'll write move-suggestions to `placement-suggestions.md`" beats "Selecting promote will trigger the `_write_promotions.py` payload handler." The user cares what will happen, not how.

4. **Short sentences; active verbs.** Match the rhythm of the `description` fields the user is already reading on option buttons — not the rhythm of the authoring prose inside the SKILL.md.

5. **Never expose file paths, function names, or tool names inside user-facing prose unless the user is meant to open or inspect them.** A path like `placement-suggestions.md` is fine because the user will open it. `_write_promotions.py` or `TaskUpdate` is not — those are implementation details.

## Worked example — weak to strong

For the canonical weak-to-strong illustration (a single feature-addition workflow rendered first without scribe discipline, then with every tool invocation carrying the full shape), see [examples/worked-example.md](examples/worked-example.md). Full worked examples for other artifact types live alongside it in `examples/`.

## Scope reminder

This skill governs *the text you write into instruction artifacts*. It does not restrict which tools you use during the authoring session — use your full tool set normally. The checklist and patterns apply only to the downstream artifact.

## Source and re-audit

Schemas and claims sourced from:
- https://code.claude.com/docs/en/tools-reference
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/permissions
- https://code.claude.com/docs/en/plugins-reference
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/features-overview

Re-audit every reference file on each Claude Code release — tool schemas and frontmatter fields evolve, and omissions here become omissions in every artifact downstream. Last audit: 2026-04-26.
