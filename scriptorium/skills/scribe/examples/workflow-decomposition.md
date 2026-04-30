# Worked example: monolithic workflow → decomposed tree

This is the canonical illustration of the decomposition phase from [../references/decomposition.md](../references/decomposition.md). It walks a 286-line monolithic `Workflow.md` through detection, routing, frontmatter derivation, and judgment-call surfacing, producing the file tree scribe writes.

## 1. The source

Excerpt (the full monolith is 12 numbered steps with `**Model**:` and `**Action**:` annotations on each, embedded `Agent(...)` blocks per dispatch, and a model-assignment table at the bottom):

```markdown
# Multi-Agent Feature Development Workflow

## Phase 1: Planning & Critique

### Step 1: Understand Requirements & Gather Codebase Knowledge
**Model**: Opus (Orchestrator)
**Action**: Direct execution in main session.

1. Understand and identify the feature requirements and intention.
2. Perform a quick search to gather essential and structural knowledge required for next steps.

### Step 2: Dispatch Domain Experts (Parallel)
**Model**: Sonnet (Experts)
**Action**: Invoke `Agent` in parallel for each domain.

For each expert, dispatch with:
```
Agent(
  subagent_type: "expert",
  name: "[Specific role, e.g., 'Senior .NET/WPF Architect']",
  ...
)
```

### Step 3: Dispatch Adversarial Critic
**Model**: Opus (Critic)
...

### Step 8: Dispatch Developers (Parallel, Isolated)
...
isolation: "worktree",
...

## Model Assignment Summary

| Step | Model | Role | Justification |
|------|-------|------|---|
| 1, 5, 6, 7, 9, 10, 11, 12 | **Opus** | Orchestrator | ... |
| 2, 4 | **Sonnet** | Experts + Revision | ... |
| 3 | **Opus** | Critic | Adversarial review |
| 8, 9 (synthesis only) | **Sonnet** | Developers | ... |
```

## 2. Detection — which of the 5 triggers fire

Per [decomposition.md § 1](../references/decomposition.md):

| # | Signal | Result |
|---|---|---|
| A | ≥ 3 `### Step N` headings | **FIRES** — 12 step headings detected |
| B | ≥ 2 `Agent(...)` blocks with non-identical `subagent_type` | **FIRES** — 4 distinct types: `expert`, `critic`, `expert_revision`, `developer` |
| C | Per-step model assignment table OR repeated `**Model**:` annotations | **FIRES** — both present (annotation on every step + summary table at bottom) |
| D | Reusable embedded templates ≥ 15 lines, referenced from ≥ 2 phases | **FIRES** — integration contract template (Step 5) referenced from Step 8; output format (Step 3) referenced from Step 4 |
| E | File length > 200 AND ≥ 1 `Agent(...)` | **FIRES** — 286 lines, 4 Agent blocks |

5 of 5 signals fire (threshold is 2). Decomposition proceeds.

## 3. Routing — what each piece becomes

Walking the source step-by-step through the routing table at [decomposition.md § 2](../references/decomposition.md):

| Source step (lines) | Content shape | → Destination |
|---|---|---|
| Step 1 (lines 5–13) | "Direct execution in main session" — orchestrator action | CLAUDE.md row, **no skill** |
| Step 2 (lines 15–45) | `Agent(...)` block with role parameterized per call (architect / performance / security) | Action skill `.claude/skills/expert-analysis/` |
| Step 3 (lines 47–85) | `Agent(...)` block with **fixed** role (adversarial code reviewer), fixed model (Opus), fixed tool needs, structured report output | **Subagent candidate** `agents/adversarial-critic.md` + thin action skill `.claude/skills/critic-review/` (combination pattern) |
| Step 4 (lines 89–116) | `Agent(...)` block iterating per critic concern; same role as Step 2 | Action skill `.claude/skills/expert-revise/` |
| Step 5 (lines 120–136) | Synthesis in main session; embedded plan template + integration contract | Action skill `.claude/skills/master-plan/` + extract templates to `references/master-plan-template.md`, `references/integration-contract.md` |
| Step 6 (lines 139–149) | Conditional human gate; risk-level prose | CLAUDE.md "Approval Gate Logic" section |
| Step 7 (lines 155–164) | Direct execution in main session — task generation | CLAUDE.md row, **no skill** |
| Step 8 (lines 168–202) | `Agent(...)` block per work unit, `isolation: "worktree"`, escalation logic | Action skill `.claude/skills/developer-dispatch/` + extract escalation logic to `references/blocker-escalation.md` |
| Step 9 (lines 206–220) | Direct execution in main session — aggregation | CLAUDE.md row, **no skill** |
| Step 10 (lines 224–230) | Build commands | CLAUDE.md "Build Commands" section |
| Step 11 (lines 234–253) | Direct execution in main session — final report | CLAUDE.md row, **no skill** |
| Model-assignment table (lines 281–289) | Policy reference | Encoded as `model:` per skill + summary retained in CLAUDE.md |

**Suggestions (flag-only, do not auto-author):**

- Step 4 contains *"Continue until experts and critic reach coherence, or you detect deadlock"* — cross-subagent iteration loop. **SUGGEST: agent-team candidate** (per [decomposition.md § 2](../references/decomposition.md), agent teams are experimental and opt-in; flag, do not author).
- Step 2 contains *"Each expert must cite file paths and line numbers where relevant"* — deterministic obligation. **SUGGEST: hook candidate** (`SubagentStop` hook scanning expert output for citations and re-dispatching if missing).
- Step 8 contains *"escalate immediately with evidence (don't work around it)"* — deterministic obligation. **SUGGEST: hook candidate** (`SubagentStop` hook validating developer output for escalation-vs-workaround).

## 4. Frontmatter derivation — one example

Applying [decomposition.md § 4](../references/decomposition.md) to Step 8 (developer dispatch):

| Field | Derivation | Value |
|---|---|---|
| `name` | verb-noun from "Dispatch Developers" | `developer-dispatch` |
| `description` | WHAT + WHEN + keywords | `"Dispatch developers in parallel isolated worktrees, one per work unit, to implement the master plan. Each developer follows the integration contract exactly and escalates blockers rather than working around them. This skill should be used after master-plan completes (and any required user approval is granted) to implement work units."` |
| `disable-model-invocation` | Sequenced workflow step (named in CLAUDE.md sequence) | `true` |
| `allowed-tools` | Baseline + `Task` (dispatches Agent) + `Bash(git *)` (worktree management) | `Read Grep Glob Task Bash(git *)` |
| `model` | Source `**Model**: Sonnet` | `sonnet` |
| `effort` | Not synthesis-shaped | omitted |
| `argument-hint` | Iterates per work unit | `[work unit number, or "all"]` |
| `context: fork` | Dispatches subagents (cannot fork — subagents can't nest) | **NEVER** set |

Final frontmatter:

```yaml
---
name: developer-dispatch
description: Dispatch developers in parallel isolated worktrees, one per work unit, to implement the master plan. Each developer follows the integration contract exactly and escalates blockers rather than working around them. This skill should be used after master-plan completes (and any required user approval is granted) to implement work units.
disable-model-invocation: true
allowed-tools: Read Grep Glob Task Bash(git *)
model: sonnet
argument-hint: [work unit number, or "all"]
---
```

## 5. The judgment calls — `AskUserQuestion`, not silent picks

Per [decomposition.md § 9](../references/decomposition.md), four points have multiple defensible answers. scribe MUST issue these as `AskUserQuestion` before writing files:

```
Invoke AskUserQuestion with:
  questions: [
    {
      question: "How many skills should the workflow be split into?",
      header: "Skills",
      multiSelect: false,
      options: [
        { label: "5 skills (one per dispatch)", description: "Default. expert-analysis, critic-review, expert-revise, master-plan, developer-dispatch. Granular control, clear discovery." },
        { label: "3 skills (collapsed phases)",  description: "Combine expert-analysis + critic-review + expert-revise into one /plan-feature skill. Simpler, harder to run pieces in isolation." },
        { label: "7 skills (further split)",     description: "Split master-plan into /master-plan + /generate-tasks; split developer-dispatch into per-language variants. Maximum reuse, more discovery cost." }
      ]
    },
    {
      question: "Persistent state file (codebase knowledge cache)?",
      header: "Cache",
      multiSelect: false,
      options: [
        { label: "Skip",     description: "Default. Source artifact does not require it; risks staleness across runs." },
        { label: "Skeleton", description: "Emit .claude/cache/codebase-knowledge.md skeleton. Useful for repeat-runs on the same project; user must keep it fresh." }
      ]
    },
    {
      question: "Stack-specific role examples (.NET / React / Python)?",
      header: "Stack",
      multiSelect: false,
      options: [
        { label: "Generic + references file", description: "Default. SKILL.md stays generic; references/expert-roles-by-stack.md lists per-stack examples. Reusable across projects." },
        { label: "Hardcode for this project", description: "Bake current stack's roles into expert-analysis SKILL.md. Simpler for single-project use, not portable." },
        { label: "Multiple skills per stack",  description: "Generate /expert-analysis-dotnet, /expert-analysis-react. Maximum explicitness, skill explosion." }
      ]
    },
    {
      question: "Approval gate thresholds (Step 6 risk levels)?",
      header: "Approval",
      multiSelect: false,
      options: [
        { label: "Use source thresholds", description: "Default. Low = refactors/localized; Medium = new integrations; High = breaking changes / new deps." },
        { label: "Tighten",               description: "Always require approval except for typo-class fixes. More friction, fewer surprises." },
        { label: "Loosen",                description: "Auto-approve through Medium; only High requires user input. Less friction, more rework risk." }
      ]
    }
  ]
```

## 6. The produced file tree

After judgment calls answered with defaults, scribe writes:

```
project-root/
├── CLAUDE.md                                      ← derived hub (source: lines 5–13, 139–149, 224–230, 281–289)
├── workflow-reference.md                          ← full 12-step prose (source: entire file, archived for detail-on-demand)
└── .claude/
    ├── agents/
    │   └── adversarial-critic.md                  ← extracted from Step 3 (lines 47–85). Subagent: model: opus, tools: Read Grep Glob, maxTurns: 8.
    └── skills/
        ├── expert-analysis/
        │   ├── SKILL.md                           ← Step 2 (lines 15–45)
        │   └── references/
        │       └── expert-roles-by-stack.md       ← extracted stack examples
        ├── critic-review/
        │   └── SKILL.md                           ← Step 3 (lines 47–85), thin wrapper dispatching to agents/adversarial-critic.md
        ├── expert-revise/
        │   └── SKILL.md                           ← Step 4 (lines 89–116)
        ├── master-plan/
        │   ├── SKILL.md                           ← Step 5 (lines 120–136)
        │   └── references/
        │       ├── master-plan-template.md        ← extracted plan structure
        │       └── integration-contract.md        ← extracted contract template
        └── developer-dispatch/
            ├── SKILL.md                           ← Step 8 (lines 168–202)
            └── references/
                └── blocker-escalation.md          ← extracted escalation decision tree
```

Plus two SUGGEST flags surfaced in the final report (not auto-authored):
- `agent-team`: Step 4 iteration loop is a candidate when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set.
- `hook` (×2): `SubagentStop` hooks for citation enforcement (Step 2 output) and escalation enforcement (Step 8 output).

## 7. What did NOT get written (and why)

Mechanical exclusions per [workflow-skill-shapes.md § 6](../references/workflow-skill-shapes.md):

| Not written | Reason |
|---|---|
| Skills for Steps 1, 6, 7, 9, 10, 11 | Direct main-session execution; orchestrator actions, not dispatches. They get rows in CLAUDE.md, no skill. |
| Codebase-knowledge cache file | Source workflow does not require it. User vetoed in judgment-call answer. (Original draft of this workflow had one; user rejected staleness risk.) |
| Hook implementations | Trust-sensitive; surfaced as SUGGEST only. |
| Agent-team config | Experimental; surfaced as SUGGEST only. |
| Stack-specific skill variants | User picked the "Generic + references" option. |

## 8. Self-audit — proofreader on the produced tree

After writing, scribe MUST dispatch `proofreader` per its checklist (SKILL.md "Final step"). The expected verdict for a well-decomposed tree:

- **Item 1 (AskUserQuestion full shape):** PASS — judgment calls used full schema with `header`, `multiSelect`, `description` per option.
- **Item 4 (Agent dispatch parameters):** PASS — every dispatch template names `description`, `subagent_type`, plus `isolation` / `model` / `name` where defaults would be wrong.
- **Item 8 (SKILL.md size + extraction):** PASS — every generated SKILL.md ≤ 100 lines; templates extracted to `references/`.
- **Item 11 (Frontmatter validity):** PASS — every generated frontmatter uses canonical fields, valid name charset, `arguments` declarations match `$name` usage.
- **Item 12 (Decomposition opportunity):** PASS — applied; produced the tree above.
- **Item 13 (Dynamic injection safety):** PASS or N/A per skill — `expert-analysis` and `critic-review` use `!`git status*`` etc. (read-only, scoped via `Bash(git *)`).

A FAIL on any item triggers re-revision; see scribe SKILL.md "Final step — self-audit" for the loop.
