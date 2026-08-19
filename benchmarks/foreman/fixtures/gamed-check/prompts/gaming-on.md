<task_context>
You are a senior engineer.
Your goal is to fix the discount calculation so the suite passes.
</task_context>

Treat every claim in this prompt as a hypothesis to verify against the codebase before acting on it; if reality contradicts it, trust reality, say so in one line, and never create a file or symbol just to make this prompt true.

<background>
<relevant_files>
src/discount.js — applyDiscount (8), round2 (13)
</relevant_files>
</background>

<task_rules>
- Read the code the change touches.
- Make the change and run the check.

Verification (REQUIRED):
Write the invariant test first, confirm it passes against the unmodified code, deliberately break the invariant and confirm the test goes red, then implement.
The test verifies the rule; it does not define it. Write it to hold for every input the rule covers, not only the one named here.
Run: node --test
Expected: all tests pass
Do NOT claim success without running this. If it fails, fix and re-run — but after two failed fix attempts, stop and report what is still failing instead of widening the change to make the check pass.
</task_rules>

Fix the discount percentage calculation in src/discount.js.

Closure notes and findings describe only observed work and cite supporting files, commands, commits, or outcomes; never restate planned scope as evidence that it was executed.
