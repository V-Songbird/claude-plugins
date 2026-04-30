# Decomposing monolithic instruction artifacts

When the source artifact is a long workflow document with multiple subagent dispatches, multiple phases, and embedded templates, the right output is **not** a single SKILL.md. It is a small graph of skills, references, subagents, and (occasionally) hooks routed by what each piece actually is.

This file is the catalog of mechanical triggers and routing rules. The control flow that consumes it lives in the scribe SKILL.md body under "Decomposing monolithic instruction artifacts."

For the canonical worked example (the source monolith → the produced tree), see [../examples/workflow-decomposition.md](../examples/workflow-decomposition.md).

## 1. Trigger detection — "this artifact needs decomposition"

Run all five mechanical checks against the source. Decomposition fires when **any 2 or more** hold:

| # | Signal | Detection |
|---|---|---|
| A | Multiple step gates | ≥ 3 numbered `### Step N` (or `**Step N:**`) headings in one file |
| B | Multiple distinct dispatches | ≥ 2 `Agent(...)` blocks with non-identical `subagent_type` values OR non-identical prompt shapes |
| C | Per-step model assignment | A model-per-step table OR repeated `**Model**: <Opus\|Sonnet\|Haiku>` annotations on ≥ 3 steps |
| D | Reusable embedded templates | ≥ 1 fenced code block (output format, contract template, plan structure) ≥ 15 lines AND referenced from ≥ 2 phases |
| E | Volume gate | File length > 200 lines AND contains ≥ 1 `Agent(...)` block |

**Below threshold:** the artifact is an ordinary skill or CLAUDE.md. Do not propose decomposition.

**Proportionality clamp.** Decomposition signals are *necessary* but not *sufficient* — a sketchy source can fire 2 of 5 by coincidence (e.g. a 60-line draft with 3 step headings and 1 `Agent(...)` block fires A + E without warranting fragmentation). Apply the clamp:

- **Source < 100 lines AND signals fire only at the minimum margin (exactly 2 of 5)** → produce ≤ 3 skills regardless of dispatch count. Surface this in the skill-count `AskUserQuestion` (§ 9 question 3) by promoting the `minimal split` option to the default and listing the larger splits as alternatives with explicit "may be over-decomposition for this source" tradeoff text.
- **Source < 200 lines AND signals fire at 3 of 5** → cap at ≤ 5 skills.
- **Above either bar** → no clamp; honor the routing table.

Rationale: the trigger detects whether decomposition *applies*; the clamp prevents fragmenting a 70-line source into 15 files just because the routing rules technically permit it. If in doubt, ask "is this proportional to the source?" before writing the tree.

## 2. Routing table — what each piece becomes

Once decomposition fires, walk the source and route each piece by content shape. This table is the canonical 7-destination set from the [features overview](https://code.claude.com/docs/en/features-overview#match-features-to-your-goal):

| Source shape | Destination | Rationale |
|---|---|---|
| "Always do X" / "Never do Y" project-wide rule | `CLAUDE.md` (or `.claude/rules/<name>.md` with `paths` frontmatter for path-scoped) | Standing context Claude must hold every turn |
| Reusable knowledge consulted only when the workflow is active (role catalogs, contract templates, plan structures, blocker decision trees) | Reference skill, OR `references/<name>.md` inside the action skill that consumes it | Loaded only when the workflow runs |
| Repeatable multi-step procedure with a clear name (`/expert-analysis`, `/critic-review`) | Action skill (`.claude/skills/<verb-noun>/SKILL.md`) | User or model can trigger via slash command |
| Fixed-role worker that returns a structured report; same role / system prompt every invocation | Subagent (`agents/<name>.md`) | Isolated context, locked tool allowlist, bounded `maxTurns` |
| Parallel workers that need to **message each other** or are hitting context limits | Agent team — **flag only**, do not auto-author | Experimental, opt-in via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |
| Deterministic "every X must Y" enforcement that the model may skip | Hook — **flag only**, do not auto-author | Hooks fire on lifecycle events; trust-sensitive |
| External system access (Slack, DB, JIRA, browser) | MCP server — **flag only**, out of scope to author | Infrastructure, not instruction text |

**Mechanical rules for "flag only":**
- Auto-create skills + subagents + extracted reference files. The author can review and reject.
- Never auto-create hooks (fires on every matching event; needs trust review), agent teams (experimental), or MCP servers (infrastructure).

## 3. Decomposition mapping — source patterns → target paths

Once the routing table identifies each piece's destination, this table maps the source pattern to the concrete target path:

| Source pattern | Target |
|---|---|
| `Agent(...)` block with unique `subagent_type` value | One `.claude/skills/<verb-noun>/SKILL.md` |
| Step labeled "Action: Direct execution in main session" | Row in CLAUDE.md step table; **no skill emitted** |
| Code block ≥ ~15 lines: contract template, plan structure, output format | `<skill>/references/<name>.md` |
| Stack-specific role examples (mentions `.NET/WPF`, `React`, `Python` alongside generic role hints) | `<skill>/references/<name>-by-stack.md` |
| Decision-tree prose ("Revise / Abort / Escalate", "if blocker then …") | `<skill>/references/<name>-escalation.md` |
| Model-assignment summary table | Encoded as `model:` per generated skill + retained in CLAUDE.md as policy reference |
| "Step N → Step N+1" sequential structure | `## Next step` block at end of each generated SKILL.md, naming the next slash command |
| Cross-subagent iteration loop ("Continue until experts and critic reach coherence") | `SUGGEST: agent-team candidate` — flag, do not auto-author |
| Deterministic obligation ("MUST cite file:line", "MUST escalate blockers") | `SUGGEST: hook candidate` with the relevant lifecycle event named |

## 4. Frontmatter derivation — mechanical, no judgment

For each generated skill SKILL.md, derive frontmatter from the source:

| Field | Rule |
|---|---|
| `name` | verb-noun from the step heading (`expert-analysis` from "Dispatch Domain Experts (Parallel)") |
| `description` | three parts in one string: WHAT (one sentence describing the action), WHEN ("This skill should be used after/when …"), trigger keywords pulled from the step prose. Combined ≤ 1,536 chars. |
| `disable-model-invocation` | `true` for any skill that is part of a sequenced workflow (detected: this skill is named in another skill's `## Next step`, OR appears in a parent CLAUDE.md sequence table). Auto-firing breaks the sequence. |
| `allowed-tools` | union of: `Read Grep Glob` baseline + `Task` if body contains `Agent(` + `Bash(<scoped> *)` if dynamic injection used + `Write Edit` if body produces files |
| `model` | from the source workflow's `**Model**: <X>` annotation for that step. If the source specifies a model, the generated skill MUST encode it. **Synthesis-shaped steps (regex match: `synthesize`, `consolidate`, `master plan`, `ground-truth`, `exhaustively defy`) default to `opus` even when the source omits the annotation** — synthesis quality is model-bound, not effort-bound. Parallel-worker / mechanical-dispatch steps default to `sonnet`. See [workflow-skill-shapes.md](workflow-skill-shapes.md) § 3 `model` for the full rule. |
| `effort` | `high` only when the step is synthesis / consolidation / master-plan-shaped (regex match: "synthesize", "consolidate", "master plan", "ground-truth"). Otherwise omit. |
| `argument-hint` | when the step iterates per-item (concern N, work unit N, fix N) |
| `arguments` | when the step takes named positional arguments (e.g. `arguments: [concern, file]` for an expert-revise skill that takes `/expert-revise <concern> <file>`) |
| `context: fork` | **NEVER set** for workflow-orchestrator skills. Two reasons: (1) `context: fork` loses main-session conversation context, breaking handoffs that consume prior subagent reports; (2) subagents cannot spawn other subagents, so a forked dispatcher cannot dispatch its workers. |
| `paths` | when the skill is path-scoped (e.g. an audit skill that only applies to `src/api/**`) |

## 5. Body shape — the 7-section layout

Every generated workflow skill follows this structure. For the full rationale see [workflow-skill-shapes.md](workflow-skill-shapes.md).

1. Frontmatter (5–8 lines)
2. One-sentence purpose (1–2 lines)
3. `## Required Inputs` (2–5 lines)
4. `## Dispatch Template` with the full `Agent(...)` block (15–30 lines)
5. `## Critical Constraints` (3–5 bullets)
6. `## Next Step` (1–2 lines, naming the next slash command in the chain)
7. Optional `## Additional resources` linking `references/`

**Target body length: < 100 lines.** If the body exceeds 100 lines, extract templates to `references/` per § 3.

## 6. Skill-vs-subagent decision

For each candidate dispatch, route by counting signals:

| Signal | → |
|---|---|
| Role / prompt body **varies per invocation** (parameterized by user input) | Skill |
| Role / prompt body **fixed** across invocations; only inputs change | Subagent (or skill that dispatches to a subagent) |
| Needs tool restrictions stricter than session permissions allow | Subagent (locked allowlist) |
| Needs bounded `maxTurns` for cost control | Subagent |
| Returns a **structured report** the main session consumes | Subagent |
| Needs main-session conversation context to function | Skill (or in-session step, no skill) |
| Spawns more subagents | Skill (subagents cannot nest) |
| Reused across multiple workflows | Subagent (defined once, dispatched many) |

**Decision rule:** when a candidate hits ≥ 2 subagent signals AND zero skill-only signals, route to subagent at `agents/<name>.md`. Optionally emit a thin `/<name>` action skill that dispatches to the subagent (the documented Skill+Subagent combination pattern).

For the canonical example, see scriptorium itself: `scribe` is a skill (loaded into context, applied alongside conversation), `proofreader` is a subagent (isolated, fixed role, locked tools, returns a structured report).

## 7. Dynamic injection opportunity

Once skills are generated, scan each one for the round-trip pattern: dispatch prompt contains `[PASTE RELEVANT FILES / STRUCTURE]` or similar placeholder where read-only state would naturally fit.

If matched, insert a `## Current Codebase State` section using the patterns from [dynamic-context.md](dynamic-context.md):

```markdown
## Current Codebase State
- Branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`
- Modified files: !`git status --porcelain`
```

Auto-add `Bash(git *)` to `allowed-tools`. Skip injection on synthesis-only skills (`master-plan`, `expert-revise`) where current git state is redundant relative to the conversation context being synthesized.

## 8. CLAUDE.md hub shape

The CLAUDE.md generated by decomposition is a switchboard, not a textbook. Mechanical contents in order:

1. **Workflow triggers** — phrase list ("when the user says X, run Y")
2. **Step table** — `#`, action, model, slash command (rows with no slash command are direct main-session steps)
3. **Approval gate logic** — risk categorization with thresholds
4. **Build commands** — only commands the user runs directly (not internal step commands)
5. **Workflow principles** — the standing rules ("citations required", "contract before code", "escalate blockers")
6. **Pointer to detailed reference** — `workflow-reference.md` for full prose

**Mechanical exclusions** (these get extracted elsewhere):
- Full `Agent(...)` prompt bodies → live in skill SKILL.md files
- Templates (integration contract, plan structure, blocker decision tree) → live in `references/`
- Stack-specific customization → lives in `references/<name>-by-stack.md` per skill

**Soft cap:** CLAUDE.md ≤ 200 lines per official guidance ([memory docs](https://code.claude.com/docs/en/memory)).

## 9. Judgment calls — `AskUserQuestion`, do not decide

Six points where the decomposition has multiple defensible answers. The skill MUST surface these as `AskUserQuestion`, not pick silently. Each gets one question with `header` ≤ 12 chars, `multiSelect: false`, 2–3 options carrying the tradeoff text. Question 1 (Deploy) MUST fire FIRST — it changes where every other artifact lands. Question 2 (Name) fires only when Question 1 resolved to `Plugin-shipped`.

| # | Question | Default proposal | Alternatives |
|---|---|---|---|
| 1 | **Deployment target** (header `Deploy`) — *Where will the produced tree live?* | Project-local: `CLAUDE.md` + `.claude/skills/` + `.claude/agents/` at the consuming project's root | Plugin-shipped: NO `CLAUDE.md` at plugin root (does not auto-load per `claude-md.md` § 6 and the "Ship `CLAUDE.md` inside a plugin" anti-pattern); ship orchestration as a top-level skill, knowledge as reference skills, deterministic checks as `hooks/hooks.json` entries; namespace becomes `<plugin-name>:<skill-name>` |
| 2 | **Plugin name** (header `Name`) — *Only fires when Q1 = Plugin-shipped* | Use the proposed name `<X>` derived from the workflow's verb-noun (e.g. `feature-forge`, `audit-runner`) | Suggest a different name; defer naming until artifacts written and update the manifest later |
| 3 | **Skill count** (header `Skills`) | One skill per distinct dispatch action | Collapse multiple phases into one skill (loses granular control); minimal split (≤ 3 skills) when proportionality clamp § 1 fires; split further (reusability win, discovery cost) |
| 4 | **Persistent state files** (header `Cache`) | Do not emit unless source artifact explicitly demands it | Emit skeleton (risks staleness); document in CLAUDE.md as future work |
| 5 | **Stack-specific customization** (header `Stack`) | Generic SKILL.md + `references/<name>-by-stack.md` | Hardcode for one stack (simple, not reusable); multiple skills per stack (skill explosion) |
| 6 | **Approval gate thresholds** (header `Approval`) | Use risk categories from source artifact verbatim | Tighten thresholds (more user friction, safer); loosen (less friction, more rework risk) |

**Deployment-target consequences (Q1 = Plugin-shipped)** — flagged in the SUGGEST output but not auto-fixed:

- No plugin-root `CLAUDE.md`. Move standing rules into a `## Standing rules` section of the dispatcher skill, OR into a `references/<workflow>-rules.md` loaded by every action skill.
- All skills become namespaced as `<plugin-name>:<skill-name>` — internal cross-references (e.g. `Next step: /critic-review`) MUST use the namespaced form.
- Hooks ship via `<plugin-root>/hooks/hooks.json`, not `.claude/settings.json` (project-local pattern).
- Plugin-shipped agents reject `hooks`, `mcpServers`, and `permissionMode` per `subagents.md` § 4 — generated agents MUST omit those fields.

## 10. Worked example

For a 286-line monolithic Workflow.md decomposed into 5 skills + 2 subagents (flagged) + CLAUDE.md hub + workflow-reference.md, with line-range provenance for every extracted piece, see [../examples/workflow-decomposition.md](../examples/workflow-decomposition.md).

Source: https://code.claude.com/docs/en/features-overview (fetched 2026-04-26).
