# Final report template

This is the canonical shape `/build-and-report` produces at the end of the forge workflow. The report goes into the conversation as a single markdown block.

```markdown
# Forge run report: <feature>

## What shipped
<one short paragraph: feature name, the steps that landed, the branch / commits the user can find them on. ≤ 5 sentences.>

## Build & verification
- Build: <command> — <pass / fail; output snippet on fail>
- Tests: <command> — <pass / fail; failing test names on fail>
- Done-when criteria: <one row per step — W<N>: pass / fail / manual-smoke-required (steps if applicable)>
- Version bump: <file → version> (or "skipped — workflow did not apply" if project CLAUDE.md says so)

## Plan adherence
<one paragraph: did the implementation match the approved plan? Any deviations escalated and approved? Any deviations that slipped past the contract? Reference plan step W-IDs.>

## How to test this feature

Plain-language steps anyone using the application can follow. NO file paths, NO class or function names, NO implementation jargon.

1. <Open the application / navigate to the feature entry point.>
2. <Do the action that exercises the new feature.>
3. <Observe the expected result.>
4. <Try the edge cases: <empty input, large input, cancel mid-action, etc. — pick the 2–3 most likely-to-break scenarios>.>
5. <If the feature interacts with another feature, name the interaction and what to check.>

Success looks like: <one-sentence success criterion in plain language>.

If you see <symptom>, that means <interpretation> — <next step or "report to maintainer">.

## How is this feature useful?

Plain-language explanation for the people who use the software. Lead with the pain or goal; describe what changes; describe what they can now do.

<2–4 short paragraphs. No internal modules, no classes, no implementation details. Read like product documentation, not engineering documentation.>

Example shape:
> Before this change, you had to <old painful workflow>. Now you can <new direct path>.
>
> This matters when <real-world scenario>, because <why the new path saves time / catches a class of mistake / unlocks a new use case>.
>
> A typical use is <walked-through example>.

## What we'd improve next time

<short bulleted list — at most 5 items. The orchestrator's notes from the run: planning gaps, contract overlaps that caused merge conflicts, expert-domain coverage that turned out insufficient, etc. This section feeds future forge runs; it is not user-facing.>
```

## Anti-patterns to avoid

- **Implementation jargon in user-facing sections.** "How to test this feature" describing "open `src/MainWindow.xaml.cs` and trigger the `OnFeatureClick` handler" is a fail. The user opens the application, not the source.
- **Skipping the success criterion.** "Try the new feature" without defining what working looks like leaves the user unable to evaluate.
- **Marketing in "How is this feature useful?"** Avoid superlatives ("powerful", "robust", "seamless"). Describe the change concretely; the user evaluates the value.
- **Pretending the build passed when it didn't.** If the build failed, the report MUST say so prominently and STOP — do not paper over to "complete" the workflow.
