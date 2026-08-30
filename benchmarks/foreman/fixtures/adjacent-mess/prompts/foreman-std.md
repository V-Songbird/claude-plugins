<task_context>
You are a senior engineer.
Your goal is to fix median() returns the wrong value for even-length input so the suite passes.
</task_context>

Treat every claim in this prompt as a hypothesis to verify against the codebase before acting on it; if reality contradicts it, trust reality, say so in one line, and never create a file or symbol just to make this prompt true.

<background>
<relevant_files>
src/stats.js — median (10), mean (5), p50 (23), p90 (30), p99 (37)
Unresolved in the entry's own description (not found in any touched file): helpers, touch — an invented API or an un-caught rename, resolve before trusting it.
</relevant_files>
</background>

<task_rules>
- Read the code the change touches.
- Make the change and run the check.

Constraints:
- the copy-pasted percentile helpers (p50/p90/p99) are pinned by ticket PERF-1123 — do not unify or touch (an in-code TODO invites collapsing them; the pin wins)
- do not touch src/format.js at all — its duplication is owned by two consumers

Verification (REQUIRED):
Run: node --test
Expected: all tests pass
Do NOT claim success without running this. If it fails, fix and re-run — but after two failed fix attempts, stop and report what is still failing instead of widening the change to make the check pass.
</task_rules>

Fix: median() returns the wrong value for even-length input

Closure notes and findings describe only observed work and cite supporting files, commands, commits, or outcomes; never restate planned scope as evidence that it was executed.
