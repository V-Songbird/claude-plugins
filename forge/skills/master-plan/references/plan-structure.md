# Master plan structure

This is the canonical shape `/forge:master-plan` produces. The plan lives in conversation context as a single markdown block; copy and adapt this template.

## Single-layer principle

The plan has four sections — **Feature**, **Steps**, **Risks**, **Open questions** — in that order. An **Integration contract** appendix is appended ONLY when the plan has ≥ 2 steps marked `Parallel-friendly: yes`.

There is no two-layer split. The user reads top-to-bottom; the critic ground-truths the same surface; the implementer (or parallel implementers) work from the same surface. One audit surface, not two.

## Size discipline

| Plan size | Target |
|-----------|--------|
| 1–3 step feature | **≤ 80 lines total** |
| 4–5 step feature | ≤ 120 lines total |
| Past 150 lines | You have leaked implementation work into the plan — cut |

W-prefixed step IDs (W1, W2, …) are used for cross-skill reference (`/forge:critic-review`, `/forge:dispatch-implementation`, `/forge:build-and-report` all reference steps by W-ID). When `/forge:dispatch-implementation` routes a step to a parallel implementer in an isolated worktree, the implementation-harness skills refer to that step as a **work unit** — same plan artifact, different role.

## Template

```markdown
# Master plan: <feature>

## Feature

<2–3 sentences: what's being built, against which existing patterns, the user-visible outcome.>

## Steps

### W1 — <step title>
- **Files touched:** `path/a.ext`, `path/b.ext:42`
- **Description:** 2–4 sentences of prose. What gets built, against which pattern (cite `file:line`), the order if it matters. Stated decisions from synthesis go here as one-line sentences ("Threshold 4.0f matches `Foo.cs:42`"). NO numbered substeps, NO pseudocode, NO code snippets — the implementer reads the cited files for the procedure.
- **Done when:** <observable success criterion. Verification command preferred (`pytest tests/test_x.py::test_y`); manual smoke test only when no command applies.>
- **Parallel-friendly: yes** — *(omit line entirely if not applicable)*. Set ONLY when this step's `Files touched` set is genuinely disjoint from every other step's AND no ordering dependency exists.

### W2 — <step title>
… (same shape)

## Risks

- **R1.** <one-sentence failure mode that names what the user observes if the mitigation is wrong> — Mitigation: <how the plan handles it, or "accepted" with one-line rationale>.
- **R2.** …

(Cap at 3. Only real failure modes the implementer or critic could realistically miss. One-line code fixes are NOT risks; fold them into the relevant step's description.)

## Open questions

- **Q1.** <question only the user can answer> — Why it matters: <impact if guessed wrong>.

(Omit the section entirely if there are no open questions.)
```

## Integration contract appendix (conditional)

Append ONLY when ≥ 2 steps are marked `Parallel-friendly: yes`. The appendix names the seams parallel implementers must honor for clauses they don't own (since each implementer only sees its own work unit + the contract).

```markdown
---

## Integration contract (appendix)

| Clause | Seam (`file:line`) | Owner step | Constraint |
|--------|---------------------|------------|------------|
| C1 | `path/file.ext:120` | W2 | New handler registers here, signature `void Handle(Foo)`. |
| C2 | `path/dispatcher.ext:45` | W3 | Subscribers MUST not double-fire when both new + existing are present. |

Step descriptions cite the contract clauses they fulfill (e.g. "fulfills C1, C3"). Implementers MUST not violate clauses they don't own.
```

A clause is a place where new code structurally attaches to existing code: a method signature you're hooking, an event you're subscribing to, a state container you're writing into. UI copy, theme colors, csproj/manifest registrations, build commands, and "follow this existing pattern" hints are NOT contract clauses — they belong inline in the relevant step's description.

For in-session or sequential implementation, omit the appendix entirely. Contract details fold inline.

## Anti-patterns to avoid

- **Plan over 80 lines for a 1–3 step feature.** Signals leaked implementation. Cut step prose first, then the Risks (drop one-line-mitigation rows).
- **Risk rows whose mitigation is a one-line code edit.** Clamps, tie-break sorts, proximity guards — these are implementation details. The Risks section is for failure modes the implementer or critic could miss; cluttering it teaches readers to skim.
- **Open questions with recommendations attached.** If you wrote "Recommendation: YES", you have a decision. Fold it into the step description and drop the row.
- **Integration-contract appendix on a single-step or sequential plan.** Heavy ceremony with no payoff. Inline contract details into the step description instead.
- **Step descriptions as pseudocode.** Numbered substeps or inline code → you're writing the implementation in the plan. Cut to 2–4 sentences of prose.
- **Vague steps.** "Implement the new feature" is not a step. Each step has files, a description with cited patterns, and a done criterion.
- **Paraphrased expert claims.** The plan's claims trace back to expert claims trace back to code. Paraphrasing breaks the chain — the critic can't verify.
- **`Parallel-friendly: yes` on a step that touches files another step also touches.** The annotation is only honest when files-sets are genuinely disjoint. Overlap means sequential.
