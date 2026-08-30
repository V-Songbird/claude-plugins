# Reproduce hush's benchmarks

Curious whether the numbers on hush's front page hold up? This is the actual harness — run it yourself.

It drives **real headless Claude Code sessions** (`claude -p`) on the same fixed tasks, once with no plugin and once with hush. Cost and token counts come straight out of the API's own usage blocks. No tokenizer estimates, no hand-waving, and no single-shot prompts — a canned reply can't tell you what a plugin costs across a real multi-turn session. Correctness is checked mechanically, so compression that mangles the answer scores as a *failure*, not a win.

## Before you start

- **Claude Code, signed in.** `claude` must be on your PATH and already authenticated (run any `claude` command once first). Every run bills your account — see the cost note below.
- **Node** on your PATH (any recent version). If you use [fnm](https://github.com/Schniz/fnm), activate it in this shell first — e.g. on PowerShell: `fnm env --use-on-cd | Out-String | Invoke-Expression`.
- Run the commands **from this directory** (`benchmarks/hush/` in the marketplace repo).

## The honest disclaimer, up front

> [!WARNING]
> This costs real money. The default run is roughly **$12–16 on the small model** and takes a few minutes. Extra arms or the bigger model cost more — the bill scales with tasks × arms × reps. `--tasks log-triage,dep-bump-warnings` is the cheap way to see the shape first.

> [!NOTE]
> The numbers move between runs — a handful of reps against a live model, not a powered experiment. Expect single-digit-percent swings on any given task, and more on the noisy ones. Judge a task by the *per-rep spread*, not just the mean.

**What you should see:** the same *shape* as our published charts — hush **cutting hard on the tasks whose commands print a lot** (`log-triage`, `release-digest`, `incident-forensics`), **costing a little on the ones that print little** (`feature-drift`, `failing-suite`, `dep-bump-warnings`, `repo-sweep`, `rename-scope`), **far less mid-turn narration** throughout, and every task still passing. You will **not** reproduce our exact figures, and that's expected. A run where hush is cheaper on every single task would be the surprising result, not the target.

## Run it

**0. Check your flags for free.** `--dry-run` resolves the arms, builds the randomized order and stops there — nothing spawned, nothing billed:

```bash
node runner/run.js --tag plan --dry-run
```

**1. Smoke test first** (one task, one rep — pennies, ~30s) to confirm the plumbing drives `claude` and scores an answer:

```bash
node runner/run.js --tag smoke --tasks failing-suite --reps 1
```

**2. The real thing** — the whole suite (9 tasks × baseline + hush × 2 reps) on the model our headline numbers use:

```bash
node runner/run.js --tag mine
node runner/report.js --tag mine
```

That writes `results/mine/report.md` and `results/mine/report.html` — tables, per-segment distributions, SVG bar charts, and the two arms' final answers side by side. Open the HTML to see it all at a glance.

**3. Cross-check on the larger model** (optional) — a result only counts when both models agree on the direction:

```bash
node runner/run.js --tag big --model opus
```

Flags: `--tasks a,b` (pick tasks) · `--reps N` · `--model sonnet|opus` · `--arms baseline,hush` · `--concurrency N` · `--tag NAME` · `--seed N` (the arm order is shuffled inside every task-and-rep block so no arm always meets a cold cache; pass the seed a run printed to replay its exact order) · `--ablations` (see below) · `--resume` (re-read completed runs from disk instead of paying for them again — a rate-limited or interrupted run records as an error and re-runs) · `--hush-debug` (attach hush's per-decision manifest to each hush-arm record, surfaced in `report.md` as a "hush decisions" line per task).

## Which half of hush is doing the work?

hush has two independent surfaces — Core (tool-output compression, exit codes, compaction) and Quiet (the turn nudge, the subagent brief). `--ablations` adds an arm for each, so a win lands on a surface instead of on "the plugin":

```bash
node runner/run.js --tag abl --ablations
```

That runs `hush-core-only` (Quiet switched off) and `hush-quiet-only` (Core switched off) alongside the usual two arms, same tasks, same everything else.

## Bring your own rival

Want to see how hush stacks up against some *other* plugin? Point `--rival-dir` at any plugin directory on your machine and it becomes a third arm — measured on exactly the same tasks, same way:

```bash
node runner/run.js --tag vs --rival-dir /path/to/other-plugin
node runner/report.js --tag vs
```

Options: `--rival-name <label>` (how it shows up in the report) · `--rival-settings <path>` (a `--settings` file if that plugin needs one) · `--rival-env KEY=VAL,KEY2=VAL2` (env vars it expects). Repeat the flags to race several rivals at once — the Nth `--rival-name`, `--rival-dir`, `--rival-settings` and `--rival-env` all describe the same arm. We don't ship or name any rival plugin — you bring whichever one you're curious about.

**Racing a built-in style.** Claude Code ships its own output styles, and one of them — `Concise` — sets out to do much of what hush's final message does. It needs no plugin loaded, so leave `--rival-dir` out and point at a settings file instead:

```bash
node runner/run.js --tag native --rival-name concise --rival-settings settings-concise.json
```

`settings-concise.json` is in this directory and holds one line. Any built-in style works the same way — swap the name inside it.

## Verify it yourself, for free

The claims also rest on hush's unit tests, which cost nothing to run — they exercise the compression and narration logic directly:

```bash
node --test hush/tests/*.test.js
```

(Run that from the repo root. On Windows Node 22, use the explicit `*.test.js` glob shown here — a bare `node --test tests/` with a trailing slash trips up on that version.)

## What's measured

Each run records, per session: cost, output tokens, **context traffic** (the sum of input + cache tokens across every API call — where tool-output compression shows up), mid-turn narration words vs. the final answer, characters of tool output that entered context, turns, wall time, and a pass/fail from the task's ground-truth check.

Reports group all of that **by segment**, because a plugin that saves you money on a log-triage session and costs you a little on a one-line question is two different results, not one average. Each segment gets its own median, mean, quartiles, confidence interval, win rate against baseline, and the single worst task regression, named. Correctness is a keyword rubric or a `node` exit code, hand-ground-truthed per task — a degenerate one-word answer fails. Where the grader is a script the prompt never mentions, it is held out of the workspace while the session runs and put back from the fixture for the check — a session that could read it would either implement its answer or stop to ask why it says more than the prompt did.

The tasks: **10** in all, across three segments — the shapes of real engineering work hush is built for. **Nine of them run by default**; `crash-origin` sits outside the default set and joins a run only when you name it with `--tasks`.

- **noisy build and test output** (4) — a production log to triage, 380 commits of release history hiding three changes anyone would notice, a dependency bump that buried a real error under 400 warnings, and a 625-case suite hiding three real failures.
- **search-heavy work** (4) — finishing a half-done API migration across 76 modules without touching the vendored copy, scoping a column rename that matches a thousand lines and must not touch three of them, finding the file and line a crash really comes from when the stack trace names a different one, and planning a new CLI flag without editing anything.
- **long sessions that drift** (2) — a feature whose requirements change under it across five prompts, and a four-prompt incident investigation over 300KB of logs. These are the shapes where history piles up.

The suite spans the size range on purpose. hush can only compress output that reaches the session, so its effect swings from a large saving on a task whose tool results run to tens of thousands of characters down to a small loss on a task with almost nothing to cut. Half the tasks sit at each end, and the per-task table shows where the line falls rather than hiding it in an average.

Every repo the tasks run in is a purpose-built fixture — a small seeded project with the bug, the noisy log, or the half-done migration already in place, not an open-source checkout. That keeps runs comparable and cheap; it also means the suite measures those shapes of work, not the shape of your repo. Short no-tools questions are deliberately absent: hush costs a little more there, the front page says so, and a suite of them would measure a workload hush is not for.

## How hard is the answer to read?

Cost is only half of what a plugin changes. `readability.js` scores the one final
message every arm shipped, on measures that predate all of them — Flesch Reading
Ease, Flesch-Kincaid grade level, words per sentence, the share of long words,
whether the reply opens with the answer, and whether it hands you something to run:

```bash
node runner/readability.js --records records/mine-1a2b3c4d --by-segment
```

Same code scores every arm, so no tool is marked against its own rulebook. It is a
regex pass over markdown, not a reader: syllables come from the usual vowel-group
heuristic, wrong on some words in every English text and wrong the same way for
every arm. The numbers compare two texts scored by the same version. They are not
a literacy verdict.

## Records you can audit

Every run leaves two copies. `results/<tag>/` is yours: raw transcripts and reports, full of your paths and your machine's name, and gitignored so it stays put. `records/<batch>/` is the auditable copy — the same numbers with absolute paths, usernames, machine names, env values and anything secret-shaped scrubbed out before the file is written. Records are written once and stamped with a content hash: a second write to the same name is refused, and an edited record is caught on read rather than quietly published. They land read-only, so on Windows a batch you no longer want needs its read-only attribute cleared before it will delete — `attrib -R records\<batch>\*.* /S` and then remove the folder.

Turn a batch of records into the tables and charts:

```bash
node runner/publish.js --records records/mine-1a2b3c4d
```

That writes `claims.md` and standalone SVG charts, per segment, from the records alone — every published number is generated, never hand-typed. Records carry the batch they came from, and publishing refuses a mix of batches: a warm prompt cache roughly halves cost, so numbers from two batches are not comparable and arms have to be raced together, inside one batch.

### A note on fairness

hush's output style is part of the product, so its prompt overhead is included in the measurement, not subtracted. Each arm runs in a fresh throwaway workspace outside any git repo, with only that one plugin loaded (`--setting-sources project`, no MCP servers, a scoped tool allowlist) — so a difference between arms is the plugin, nothing else.
