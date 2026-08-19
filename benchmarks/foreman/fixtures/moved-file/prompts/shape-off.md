<task_context>
You are a senior engineer.
Your goal is to fix punctuation rides along with word tokens ('Hello, world!' -> ['hello,', 'world!']) so the suite passes.
</task_context>

Treat every claim in this prompt as a hypothesis to verify against the codebase before acting on it; if reality contradicts it, trust reality, say so in one line, and never create a file or symbol just to make this prompt true.

<background>
<relevant_files>
src/tokenizer.js — tokenize (6)
Unresolved in the entry's own description (not found in any touched file): tokens, location — an invented API or an un-caught rename, resolve before trusting it.
</relevant_files>
</background>

<task_rules>
- Read the code the change touches.
- Make the change and run the check.

Verification (REQUIRED):
Run: node --test
Expected: all tests pass
Do NOT claim success without running this. If it fails, fix and re-run — but after two failed fix attempts, stop and report what is still failing instead of widening the change to make the check pass.
</task_rules>

Fix: punctuation rides along with word tokens ('Hello, world!' -> ['hello,', 'world!'])

Closure notes and findings describe only observed work and cite supporting files, commands, commits, or outcomes; never restate planned scope as evidence that it was executed.
