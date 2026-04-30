---
name: master-plan
description: Consolidates the expert reports from `/forge:expert-analysis` into a single master implementation plan that the user can audit at a glance. Walks every expert report; reconciles overlapping claims; resolves cross-domain conflicts by reading the code; produces a single-layer plan (Feature, Steps, Risks, Open questions) capped at ≤ 80 lines for typical features. Optional Integration-contract appendix only when the plan has ≥ 2 steps marked `Parallel-friendly: yes`. Use as Step 4 of the forge workflow, immediately after `/forge:expert-analysis` returns. Produces the plan in conversation context only — no file is written.
user-invocable: false
model: opus
effort: high
color: blue
---

# Master Plan Synthesis

Synthesize the expert reports into a single, code-grounded plan the user can audit in one sitting. Runs in the main session (no subagent dispatch); the orchestrator does the consolidation directly because the expert reports already live in conversation context.

## Required Inputs

- Every expert report from the most recent `/forge:expert-analysis` run, present in the conversation transcript.
- The original feature requirements as the user expressed them.
- Optional: any user clarifications since the experts were dispatched.

## What to produce

A single markdown plan inside the conversation, capped at **≤ 80 lines for typical features** (1–3 steps; ≤ 120 lines for 4–5 steps). The plan has four sections, in this order: **Feature**, **Steps**, **Risks**, **Open questions**. An optional **Integration contract** appendix is appended ONLY when the plan has ≥ 2 steps marked `Parallel-friendly: yes`.

For the full template with field-by-field guidance, see [references/plan-structure.md](references/plan-structure.md).

## Synthesis procedure

1. **Cluster the steps.** Each step is a bounded edit a reader can hold in their head. 1 step is fine for focused changes; 5 is the practical ceiling. Cluster by what belongs together, NOT by parallelism — disjointness is the `Parallel-friendly` annotation's job, not the step boundary's.
2. **Write step descriptions as prose.** 2–4 sentences naming what gets built, against which existing patterns (cite `file:line`), and the order if it matters. NO numbered substeps, NO inline pseudocode, NO code snippets.
3. **Reconcile citations.** Every `file:line` cited by any expert appears in exactly one step's "Files touched" list. If two experts cite the same line with conflicting interpretations, MUST invoke `Read` on the file and resolve by reading the code yourself.
4. **Triage risks ruthlessly.** A risk has the shape: "if this mitigation goes wrong, the user observes <symptom>." Cap at 3. One-line code fixes (clamps, sort tie-breaks, exclusion sets) are NOT risks — fold them into the relevant step's description as a sentence and drop the row.
5. **Triage open questions ruthlessly.** Only items the user must decide. If you have a recommendation, write it as a stated decision in the relevant step's description and drop the row. Empty `Open questions` section is fine and common.
6. **Annotate `Parallel-friendly: yes` only when honest.** A step gets the annotation ONLY if its "Files touched" set is genuinely disjoint from every other step's AND its description has no ordering dependency. Default: omit the line entirely.
7. **Emit the Integration-contract appendix only when ≥ 2 steps are `Parallel-friendly: yes`.** Otherwise omit the appendix entirely; contract details fold inline into the relevant step's description (e.g. "subscribe to the dispatcher at `Foo.cs:120`, signature `void Handle(Bar)`"). For in-session implementation, the inline form is sufficient.

## Critical Constraints

- **Hard size cap: ≤ 80 lines for typical 1–3 step features; ≤ 120 lines for 4–5 step features.** If you exceed this, you've leaked implementation work into the plan. Cut prose, drop one-line-mitigation risks, fold Open questions with recommendations into stated decisions.
- **NEVER write the plan to disk.** Per workflow design, the plan lives in conversation context until `/forge:plan-revise` finishes.
- **NEVER preserve a Risk row whose mitigation is a one-line code edit.** Those are implementation details. The Risks section is for failure modes the implementer or critic could realistically miss.
- **NEVER preserve an Open question with a recommendation attached.** If you have an answer, write the answer into the relevant step's description and drop the question.
- **NEVER write step descriptions as pseudocode.** If your description has numbered substeps, code snippets, or branching logic, you're writing the implementation in the plan. Cut to prose.
- **NEVER emit the Integration-contract appendix for a single-step or sequential plan.** It is not load-bearing in those cases and just bloats the audit surface.
- **Cite `file:line` on every claim.** Plans without citations fail the critic and the implementer cannot verify against the code.

## Next Step

After the plan is in the conversation, invoke `/forge:critic-review` to dispatch the adversarial critic against it.

## Additional resources

- For the full plan template with field-by-field guidance, see [references/plan-structure.md](references/plan-structure.md)
