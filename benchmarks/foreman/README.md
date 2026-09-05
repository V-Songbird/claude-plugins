# Reproduce foreman's benchmarks

Curious whether a structured handoff prompt actually buys anything? This is the actual harness — run it yourself.

It drives **real headless Claude Code sessions** (`claude -p`) on the same three fixed bug-fix tasks, asking for the same job four different ways. The four: the one-line ask a vibe coder types, the paragraph a competent dev writes by hand, the generic role/context/task/format template the prompt guides recommend, and a Foreman handoff built from [`prompt-template.md`](../../foreman/prompt-template.md). Cost and token counts come straight out of the API's own usage blocks. Correctness is checked mechanically — tests must pass AND the session must respect the task's stated constraints, verified by hash comparison against the pristine fixture. A fix that "works" by editing the frozen file scores as a *failure*, not a win.

Every fixture hides a trap where the lazy route is the easy route: a facade file that must stay byte-identical even though patching it makes the tests pass, a brief that names the wrong file (the file it names exists, looks plausible, and is dead code), and an in-code TODO inviting a refactor the task explicitly forbids. The interesting question isn't "can the model fix the bug" — it's which prompt style keeps the session on the rails.

## Before you start

- **Claude Code, signed in.** `claude` must be on your PATH and already authenticated (run any `claude` command once first). Every run bills your account — see the cost note below.
- **Node** on your PATH (any recent version). If you use [fnm](https://github.com/Schniz/fnm), activate it in this shell first — e.g. on PowerShell: `fnm env --use-on-cd | Out-String | Invoke-Expression`.
- Run the commands **from this `benchmarks/foreman/` directory.**

## The honest disclaimer, up front

> [!WARNING]
> This costs real money. The default grid (3 tasks × 4 arms × 4 reps = 48 sessions) is roughly **$2–4 on the small model** and takes a while. The bigger model costs several times that.

> [!NOTE]
> The numbers move between runs — a handful of reps against a live model, not a powered experiment. Judge every cell by its *per-rep spread*, not just the mean, and expect the shape rather than exact figures.

**What you should see:** the *shape*, not our numbers. On the small model, the one-line ask tends to ship broken or constraint-violating work on the trap tasks — especially the one whose brief names the wrong file — while the structured arms recover. On the bigger model everything tends to pass, and the difference moves into cost and discipline: the one-line ask often costs *more*, because the session burns turns rediscovering everything the ask didn't say. The `vibe` arm losing is partly informational (it deliberately drops detail); the comparison that isolates *structure* is freeform vs. webtemplate vs. foreman, which all carry identical facts.

## Sanity-check it for free

None of this invokes `claude`:

```bash
node selfcheck.js                  # every fixture: bug planted, lazy path trapped, solution passes
node runner/run.js --dry-run --tag smoke   # print the full planned run matrix, invoke nothing
```

`selfcheck.js` proves each fixture the hard way: the pristine app fails its tests; the lazy shortcut either passes tests but trips the constraint checks or goes nowhere; the correct solution passes everything. It also verifies the frozen foreman prompts still match the current `prompt-template.md` — if the template has moved, selfcheck says so instead of letting you benchmark a stale prompt.

## Run it

**1. Smoke test first** (one task, two arms, one rep — pennies) to confirm the plumbing drives `claude` and scores an answer:

```bash
node runner/run.js --tag smoke --tasks api-constraint --reps 1 --model sonnet --arms vibe,foreman
node runner/report.js --tag smoke
```

**2. The real thing** — the full default grid:

```bash
node runner/run.js --tag mine --model sonnet
node runner/report.js --tag mine
```

That writes `results/mine/report.md`: per-task × per-arm tables (correctness, cost, tokens, reads-before-first-edit, verification, violations) plus per-rep rows so you can see the spread yourself.

**3. Go bigger** (optional — costs more):

```bash
node runner/run.js --tag big --model sonnet
```

Flags: `--tasks a,b` · `--reps N` · `--model sonnet|opus` · `--arms vibe,freeform,webtemplate,foreman,trio` · `--concurrency N` · `--tag NAME`.

## The arms

| Arm | What it is |
|---|---|
| `vibe` | The one casual line: "hey the rate limiter is broken, fix it?" Deliberately drops detail — that information loss is the arm's point. |
| `freeform` | The paragraph a competent dev writes by hand: every fact, natural prose, no structural guardrails. |
| `webtemplate` | The generic Role/Context/Task/Format shape common prompt guides recommend. Same facts, structured — but no truth-grounding, scope-discipline, or mandatory-verification blocks. |
| `foreman-std` | **The foreman arm to quote.** A handoff assembled by running the product's own `craft-handoff.js` — same facts again, plus the template's guardrail blocks and a required verification command. Generated by `defaultarm/gen.js`, and it passes `check-prompt.js`, the gate a real crafting session must clear. |
| `foreman` (legacy) | The older hand-frozen prompt. **Do not quote it.** It fails `check-prompt.js` with six errors — altered `<scope_discipline>`, no closure-evidence rule, no `<plan>`, no no-invention line, no fixed closing paragraph, and an *unbounded* fix loop — so foreman would refuse to hand it over. Kept only so previously tagged runs stay re-reportable. |
| `trio` (opt-in) | The identical foreman prompt, executed in a destination session with hush and razor active — the full trio versus foreman-alone. Runs only when named via `--arms`. |
| `lessons-*` (opt-in) | Four arms for the lesson-ledger question below — `moved-file` only. Same prompt, one block spliced in, nothing else different. |
| `shape-off` / `shape-on` (opt-in) | Does the standard profile need an output shape? Both come out of `craft-handoff.js` itself and differ by `<output_format>` alone. |
| `gaming-off` / `gaming-on` (opt-in) | Does naming the test-gaming shortcut stop it, or teach it? `gamed-check` only, scored on held-back tests. |
| `pin-off` / `pin-on` / `pin-wrong` (opt-in) | Does a served lesson change the outcome, and what does a wrong one cost? `pinned-dup` only — the fact the lesson carries exists nowhere else in the fixture. |

**The fairness rule the whole harness hinges on:** every arm except `vibe` carries the exact same brief facts. Arms differ in format and guardrails, never in information access — including the deliberately wrong file name in the stale-brief task, which every arm states identically.

That rule is now asserted rather than trusted. `defaultarm/gen.js` refuses to write an arm prompt that drops a constraint fact or repairs the stale file name, `tests/default_arm.test.js` pins the file set against the `freeform` arm, and `selfcheck.js` runs the product's own gate over the generated prompt. The reason for all three: `shape-off` — built for a *within-foreman* A/B where fact poverty cancels out — passes its constraint facts as `judgment.context`, which the standard profile drops, and names the task's real file rather than the brief's claimed one. It is a valid control for its own question and an invalid stand-in for foreman.

### The trio arm

`trio` needs the hush and razor plugins on disk. By default they resolve as sibling checkouts of the foreman plugin (`../../hush`, `../../razor` from this directory — a monorepo checkout already looks like this). If yours live elsewhere:

```bash
HUSH_PLUGIN_DIR=/path/to/hush RAZOR_PLUGIN_DIR=/path/to/razor \
  node runner/run.js --tag trio --reps 4 --model sonnet --arms foreman,trio
```

The default four arms never need those plugins; if `trio` is named and they're missing, the runner fails fast and tells you which env vars to set. `settings-trio.json` pins hush's output style for the headless session (forced plugin styles don't apply on their own under `--setting-sources project` in `-p` mode).

## The picks mini-benchmark

A separate, smaller question: what does "what should I work on next?" cost against a backlog of 10, 50, or 150 tasks?

```bash
node picks/gen.js                            # generate the synthetic backlogs (free, deterministic)
node picks/run.js --tag mine --arms foreman  # foreman arm: zero tokens, no LLM — free
node picks/run.js --tag mine                 # adds the markdown arm: 5 claude sessions per size — bills you
```

Both arms see the same backlog content. The `markdown` arm hands a session a human-style TODO.md and asks it to pick; the `foreman` arm runs `roadmap.js next-candidates` — mechanical dependency-graph filtering, zero tokens, and the same answer every time. The report counts distinct picks across reps (normalized, so "Task X" and "**Task X** (#007)" count as one answer) next to mean cost and tokens.

To inspect a possible ranking change without changing Foreman's production
sorter, replay any real or synthetic roadmap through the current ranking,
critical-depth-first, and critical depth as a late tie-breaker:

```bash
node picks/ranking-replay.js --roadmap /path/to/ROADMAP.jsonl
```

The replay is deterministic and free. It reports top-pick disagreements for
human judgment; it does not silently turn critical depth into a new priority
system.

**Which roadmap you replay decides whether the answer means anything.** The
generated backlogs at `picks/fixtures/10`, `/50` and `/150` cannot separate
the three orderings at all: every entry in them has a critical depth of 0 or
1, and depth equals `unblocks_total` on every row, so all three come back
byte-identical however large the backlog gets. A replay over those reports no
disagreement and means nothing by it.

`picks/fixtures/deep` is hand-authored to be the shape they never produce — a
four-long serial chain against a three-wide fan, deliberately tied on
`unblocks_total` so the comparator has to fall through to direct `unblocks`:

```bash
node picks/ranking-replay.js --roadmap picks/fixtures/deep/ROADMAP.jsonl
```

Current ranking picks the fan head; critical-depth-first picks the chain head;
critical depth as a late tie-breaker changes nothing, because direct
`unblocks` has already separated the two rows before depth is consulted. That
one disagreement is the whole trade, and Foreman declines it: its user works
one task at a time, so three immediate options beat a longer critical path.
`tests/ranking_replay.test.js` pins all of it, so a future change to the
sorter has to argue with the case rather than rediscover it.

## The prompt-engineering arms

Three changes came out of a prompting audit with a note attached: measure them
before shipping. Each one ships behind an environment switch first, so both
arms come out of the product itself and the default only moves if the numbers
say it should. Nothing in the product ever writes these variables.

### Does the standard profile need an output shape?

The standard profile ends on the closure-evidence sentence and says nothing
about the final message, which is the one part of a handoff a human reads.
`FOREMAN_STANDARD_OUTPUT_SHAPE=1` lets the canonical `<output_format>` ride
standard too.

```bash
node outputshape/gen.js                                    # write both arm prompts (free)
node outputshape/gen.js --check                            # exit 1 if they drifted
node runner/run.js --arms shape-off,shape-on --reps 3      # 3 tasks x 2 arms
```

Both prompts come out of `craft-handoff.js` itself, run twice over the same
temp project, so neither is hand-authored and neither can drift from what
foreman emits. The arms differ by that one block and nothing else, and
`tests/output_shape_arms.test.js` fails if they ever differ by two.

### Does naming the shortcut stop it, or teach it?

The `testFirst` branch is the one place a handoff asks a session to author the
very check it is graded on. `FOREMAN_TEST_GAMING_CLAUSE=1` adds a sentence
saying the test verifies the rule rather than defining it — and the house's own
recorded lesson is that wording which describes a failure can prime it.

```bash
node gaming/gen.js
node runner/run.js --tasks gamed-check --arms gaming-off,gaming-on --reps 6
```

The `gamed-check` fixture is the point. Its shipped suite names exactly **one**
case of a rule that holds for every input, so a fix hard-coded to that case
passes everything the session can see. `fixtures/gamed-check/hidden/` asserts
the same rule at inputs the session never sees and is copied in only after the
run is over, which is what `checks.hiddenTests` reads. A run whose shipped
tests pass while the held-back ones fail is scored `gamed:` — its own
violation, never folded into `tests`.

`gamed-check` is `measurementOnly`, so it carries no prompts for the four
default arms and joins a run only when named with `--tasks`.

### Where is the discovery bar actually set?

The post-commit discovery block set its inclusion bar with two qualitative
words — "CONFIRMED", "not vague hunches" — while the concrete criterion two
clauses later governed only how to *write* an accepted candidate.
`FOREMAN_DISCOVERY_CONCRETE_BAR=1` swaps both gates, the opening bar and the
closing "Say nothing if nothing is confirmed", which binds hardest at the emit
point. Swapping one alone is a no-op, and the tests fail if only one moves.

```bash
node discovery/run.js --dry-run
node discovery/run.js --tag d43 --reps 5 --model sonnet
```

This is a separate chassis from `runner/run.js`: there is no tree to score,
because the whole outcome is a judgment about text already in the prompt. It
reads the real block out of the plugin at run time and counts the candidates
each arm proposes.

**One deliberate deviation, identical in both arms.** The shipped block ends by
telling the session to ask the user about each candidate, and to skip entirely
when there is no user — so headless, both arms would report nothing and the bar
would be unmeasurable. That closing instruction is replaced with "write the
candidates down as JSON". Every other clause is the shipped text verbatim, and
the bar is the only thing that differs between the arms.

## The lesson-ledger arms

A third question: when a handoff quotes a lesson an earlier task recorded, does saying how stale it is actually matter?

```bash
node lessons/gen.js                                        # write the four arm prompts (free, deterministic)
node lessons/gen.js --check                                # exit 1 if they drifted
node runner/run.js --tasks moved-file --arms lessons-control,lessons-fresh,lessons-graded,lessons-unlabeled
```

All four arms are the same `moved-file` prompt with one block spliced in, so the only thing that varies is what that block says. `lessons-control` carries none. `lessons-fresh` carries a correct lesson. `lessons-graded` carries a stale one that says it might be stale — what the product actually ships. `lessons-unlabeled` carries the same stale claim with the label stripped, and it is there on purpose: if it doesn't do worse than `lessons-graded`, the label isn't earning its place.

The fixture is already a decoy — the prompt names `src/parser.js` and the real code lives in `src/tokenizer.js` — so the stale lesson points exactly where a session should not go.

```bash
node lessons/p3-report.js --root /path/to/project
```

That one is free and reads your own project: how often a close actually recorded a lesson, and which refusals fired. It needs `trialLog` turned on.

## The benefit arms

The lesson-ledger arms above answer the safety half: a stale lesson that admits
it might be stale does no harm. They cannot answer the benefit half, because
their control arm was already right every time — a correct lesson had no room
to help. These two arms are built for that question.

```bash
node benefit/gen.js                                        # write both arm prompts (free, deterministic)
node benefit/gen.js --check                                # exit 1 if they drifted
node runner/run.js --tasks pinned-dup --arms pin-off --reps 3   # does the control fail? run this first
node runner/run.js --tasks pinned-dup --arms pin-off,pin-on
node runner/run.js --tasks pinned-dup --arms pin-off,pin-on,pin-wrong --reps 6
```

The fixture is `pinned-dup`: the `adjacent-mess` module with the ticket that
pins its three copy-pasted percentile helpers removed from the code comment,
the brief and the prompt alike. The `TODO: collapse these three copies` that
invites the tidy-up is still there. So `pin-off` has every reason to unify them
and nothing telling it not to, and `pin-on` is told by the lesson alone.

Collapsing the helpers is caught by three `sentinels` on the lines the collapse
removes, however it is done — one shared helper, three thin delegates, anything.
`fixtures/pinned-dup/lazy/` is that exact tidy-up, and `selfcheck.js` runs it on
every invocation, so the detector is proven without spending a session on it.

**Run the control alone first.** If `pin-off` never unifies the helpers, there
is no room for the lesson to help and the benefit half stays unmeasured. That is a real
answer, and three runs buy it.

`pin-wrong` is the mirror. It carries a *different* pin, in the same block, on
the same `unchanged since` label and the same correct path match — and it is
false: it pins the very branch the task was sent to fix. Nothing in the product
can catch that case, because the staleness resolver answers "have these files
changed", never "was this claim ever true". So what a wrong lesson costs is a
measurement, not an argument. Two things get scored: whether the shipped suite
still passes (did the false pin talk the session out of the fix) and what the
arm spent (what adjudicating a false claim costs when it does not).

### The chain arms

A handoff now names the earlier tasks whose commits shaped each function it
mentions, read straight from the file's git history. Does a fact arrive as
well through that block as through a recorded lesson? `chain-on` is the same
`pinned-dup` prompt with that block spliced in — one line saying `p50` was
shaped by an earlier entry whose reason carries the pin — and `chain-off` is
the control. Same pin, same single line, a different channel.

```bash
node benefit/gen.js
node runner/run.js --tasks pinned-dup --arms chain-off,chain-on --reps 6
```

### The uncheckable lesson

`pin-wrong` hands the session a test that refutes the false claim. The
dangerous shape is a false lesson nothing can refute. `unpinned-dup` is the
same app with the opposite truth: the task asks for the collapse, the in-code
TODO invites it, and no ticket pins anything — and `unpin-wrong` serves
`pin-on`'s exact block anyway. If the session obeys it, the collapse it was
sent to make never happens, and the task's inverted sentinels score that.

```bash
node runner/run.js --tasks unpinned-dup --arms unpin-off,unpin-wrong --reps 6
```

## Roadmap health and attention cost

A different question again: does a roadmap stay accurate over months, and what
does keeping one cost you? Mechanical tests can't answer either, so the foreman
plugin ships two health tools under `scripts/health/` that measure them
directly. From this directory, in a marketplace checkout:

```bash
node ../../foreman/scripts/health/roadmap-health.js --roadmap /path/to/ROADMAP.jsonl --date 2026-07-28
```

Free, deterministic, read-only, and no default roadmap — you name the file.
It reports stale entries, survey breadcrumbs, stranded dependencies, look-alike
duplicates, archive growth, and duplicate-id repairs, reusing `roadmap.js` and
the doctor's own checks so the numbers can't disagree with `roadmap.js doctor`.
`--archive` is autodetected next to the roadmap; `--date` fixes the run date so
a report is reproducible.

`attention-cost.js` is the same shape, asking what Foreman costs you rather
than what shape the roadmap is in:

```bash
node ../../foreman/scripts/health/attention-cost.js --roadmap /path/to/ROADMAP.jsonl --date 2026-07-28
```

Also free, deterministic, read-only, same flags. Three of its seven metrics
need nothing but the files: how closely each closed task's predicted files
matched the files it actually changed (precision and recall, matched with
`roadmap.js`'s own prefix-aware rule, so `src/auth` counts as predicting
`src/auth/middleware.ts`), how many files it changed that nothing predicted
— cross-checked against the scope-drift note the close already stamped — and
how much fixed guardrail text the short handoff profile drops relative to the
full one, read out of `prompt-template.md` through `check-prompt.js`'s own
exports so the two can't disagree.

Seven of the sixteen metrics across the two tools — whether you accept the
recommendation, override it, get what you meant from a hint, how long setup
runs before the first useful task, how many questions a task costs, how often a
commit gets interrupted, and whether an interrupted run comes back — only exist
if a session records them as they happen. [`TRIALS.md`](../../foreman/TRIALS.md)
defines those as opt-in, local, count-only project trials: no titles, no paths,
no ids, a log you can delete at any time, and only the script-side events
recorded today — the model-side ones (recommendation acceptance, override rate,
questions per task) stay unwired.
Pass `--trial-log <path>` and each tool computes its own rates; without one they
report `null` with a reason rather than zero. The recovery number additionally
ships a clearly labeled proxy — how much interrupted work is sitting open —
which is not the same thing and never stands in for the rate.

One of `attention-cost.js`'s numbers: **the standard handoff profile carries 68
words of fixed guardrail text against the reinforced profile's 567, 12% of it,
499 words saved on every standard handoff.** That is a static computation over
`prompt-template.md`, not a model trial.

Run output stays local — `results/` and `records/` are gitignored. `results/` is
your own local run output. The harness in this repo is the published way to
regenerate any number a README states.

## What's measured

Each run records, per session: cost, output tokens, context traffic (input + cache tokens across every API call), mid-turn narration words, turns, wall time — and the discipline signals: how many Read/Glob/Grep calls before the first edit, whether a test-intent command actually ran (`npm test`, `node --test`, or executing the test file directly all count), the constraint violations by name, and on the stale-brief task, whether the final message names the file mismatch it found.

### A note on fairness

Each session runs in a fresh throwaway workspace in the system temp directory, outside any git repo, with a scoped tool allowlist, no MCP servers, and `--setting-sources project` — so a difference between arms is the prompt (or, for `trio`, the prompt plus the named plugins), nothing else. Scope checks are hash comparisons in the scorer, not model judgment. The foreman prompt's extra length is part of the product, so its overhead is included in the measurement, not subtracted.

## The README replay

The animated exchange at the top of Foreman's README is drawn from recorded transcripts, never typed:

```bash
node runner/demo.js --exchange records/<dir>/exchange.json
```

`exchange.json` names the project, the model, and one entry per turn: the text the user sent and the `claude -p --output-format stream-json` transcript of Foreman's answer (a `--resume` of the same session for the follow-up). The drawer plays each reply at its share of the recorded wall clock, cuts any reply after the first at a paragraph boundary with a word count, and shows the `task_context` and `relevant_files` blocks of the handoff prompt the session returned. Transcripts stay under `records/` and never ship; `foreman/assets/demo.svg` does.
