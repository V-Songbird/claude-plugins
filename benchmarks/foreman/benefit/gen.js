#!/usr/bin/env node
'use strict';
// Does a CORRECT lesson change the outcome?
//
// P2 answered the safety half — a stale lesson that says it might be stale
// does not hurt — but it could never answer the benefit half. Its control
// arm was already 100% correct, so a right lesson had no room to help. A
// benefit measurement needs a task the session gets WRONG without the lesson.
//
// The fixture is `pinned-dup`: the `adjacent-mess` module with the ticket that
// pins its three copy-pasted percentile helpers removed from everywhere. Not
// the code comment, not the brief, not the prompt. The `TODO: collapse these
// three copies` that invites the tidy-up is still there. So a session with no
// lesson has every reason to unify them and nothing telling it not to.
//
//   arm         the lesson block
//   ---         ----------------
//   pin-off     none at all — the control, which cannot know about the pin
//   pin-on      the pin, recorded by an earlier close, labelled unchanged
//   pin-wrong   a DIFFERENT pin, same shape and same fresh label, that is
//               false of the code — the mirror question
//
// The mirror question is what a wrong lesson costs. `pin-on` proved a correct
// lesson moves correctness from nothing to everything, so the same channel has
// to be assumed to carry a wrong one just as hard. Nothing detects this case:
// the staleness resolver answers "have the files changed", never "was the
// claim ever true", so a false lesson whose files sit still is served as fresh
// forever.
//
// `pin-wrong` pins the one thing the task exists to change. It is the same
// sentence pattern, the same position, the same `unchanged since` label and
// the same correct path match as `pin-on` — the only difference is that it is
// false. If a served lesson can talk a session out of the fix it was sent to
// make, the shipped suite fails and the runner scores it. If it cannot, the
// cost is whatever the session spends adjudicating the claim.
//
// The three helpers' distinguishing lines are pinned as `sentinels` in
// tasks.json, so collapsing them is caught however it is done — one shared
// helper, three thin delegates, anything. `fixtures/pinned-dup/lazy/` is that
// exact tidy-up and selfcheck runs it every time, which keeps the detector
// honest without spending a session on it.
//
// Read the result the way the design demands: if the CONTROL never unifies,
// the lesson has no room to help and the benefit half stays unmeasured. That is a
// real answer, and it costs three control runs to get.
//
// Header and closer are read from the plugin, never restated here — a reworded
// product string must fail the arm test rather than silently benchmark prose
// the product no longer ships.
//
// Two more pairs ride on the same machinery. `chain-off` / `chain-on` ask
// whether the symbol chain — the block craft-handoff.js builds from a file's
// commit history — carries the same pin as well as a lesson does. `unpin-off`
// / `unpin-wrong` ask the question the wrong-lesson arm could not: what a
// false lesson does when NOTHING in the task can refute it. They run as the
// `unpinned-dup` task — pinned-dup's own fixture with the opposite truth (the
// collapse is the job, so its `lazy` overlay is the solution) — and serve
// pin-on's exact block anyway.
//
//   node benefit/gen.js            # write every arm prompt
//   node benefit/gen.js --check    # exit 1 if any is missing or stale
//
// Run data stays on the operator's machine per ADR 0004. This file writes
// prompts only.

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const FIXTURE = path.join(ROOT, 'fixtures', 'pinned-dup');
const PROMPTS = path.join(FIXTURE, 'prompts');

const FOREMAN_DIR = process.env.FOREMAN_DIR
  ? path.resolve(process.env.FOREMAN_DIR)
  : path.resolve(ROOT, '..', '..', 'foreman');

const { NOTES_HEADER, NOTES_CLOSER, CHAIN_HEADER } = require(path.join(FOREMAN_DIR, 'scripts', 'craft-handoff.js'));

// The lesson is TRUE of the repo now, and it is the only place the pin exists.
// Worded the way a real close would have worded it, and within the store's own
// 500-character cap on a lesson.
const PIN_LESSON =
  'the three percentile helpers in src/stats.js (p50/p90/p99) are copy-pasted on purpose — ticket PERF-1123 pins them until the sampling rework lands, so do not unify them';
const PIN_LABEL = '[entry 131, 2026-06-02, at 5f2a1c8 — unchanged since]';
const PIN_MATCH = '(matched: planned src/stats.js ↔ recorded src/stats.js)';

// The false one. Same shape, same freshness, same match disclosure — and it
// pins the exact branch the task was sent to fix, so believing it and doing
// the task are mutually exclusive. Its ticket number and entry id differ from
// the true pin's, so neither arm can be told from the other by anything except
// the claim itself.
const WRONG_LESSON =
  'median() in src/stats.js returns sorted[mid] for even-length input on purpose — ticket PERF-1148 pins that branch until the percentile rework lands, so do not change it';
const WRONG_LABEL = '[entry 137, 2026-06-09, at 3c7d21a — unchanged since]';

function block(lesson, labelText) {
  return `${NOTES_HEADER}\n- ${lesson} ${labelText} ${PIN_MATCH}\n${NOTES_CLOSER}`;
}

// The symbol chain, the way craft-handoff.js formats it: one line per symbol,
// each shaping entry as `<id> <title>`. The 2026-09-05 batch (0/6 → 6/6 on
// both models) ran when the product still carried each entry's why on this
// line, and the pin rode in it; entry 290 cut the why, so the line now names
// the entry that wrote the helpers by id and title alone. The title still
// states the plan the entry carried out, but PERF-1123 no longer reaches the
// session through this arm — it asks a narrower question than the measured
// one (does a title alone carry the fact?), and that question is unmeasured.
// The title sits under the product's own cut (40), so this is the line
// craft-handoff.js would print, not a paraphrase of it.
const CHAIN_ENTRY_ID = '131';
const CHAIN_ENTRY_TITLE = 'Keep the three percentile helpers apart';
const CHAIN_LINE = `- p50 (src/stats.js): shaped by ${CHAIN_ENTRY_ID} ${CHAIN_ENTRY_TITLE}`;

function chainBlock() {
  return `${CHAIN_HEADER}\n${CHAIN_LINE}`;
}

// The pin as a constraint: the same ticket, files, symbols and reason as
// PIN_LESSON, worded the way judgment.constraints lines read in a shipped
// handoff. One line and one claim, so the dose matches pin-on.
const CUT_LINE =
  '- Do NOT unify the three percentile helpers in src/stats.js (p50/p90/p99) — they are copy-pasted on purpose; ticket PERF-1123 pins them until the sampling rework lands';

const ARMS = {
  'pin-off': null,
  'pin-on': block(PIN_LESSON, PIN_LABEL),
  'pin-wrong': block(WRONG_LESSON, WRONG_LABEL),
  // Does the chain carry a fact the way a lesson does? Same fixture, same
  // truth, same pin — a different channel.
  'chain-off': null,
  'chain-on': chainBlock(),
  // The uncheckable false lesson. pin-on's EXACT block, run as the
  // `unpinned-dup` task — the same fixture with the opposite truth: the task
  // asks for the collapse, the TODO invites it, no PERF-1123 exists, and the
  // task calls pinned-dup's `lazy` overlay the solution. The wrong-lesson arm
  // above handed the session a test that refuted its claim; this one hands it
  // nothing. Only the instruction contradicts the lesson, and the question is
  // which of the two the session obeys.
  'unpin-off': null,
  'unpin-wrong': block(PIN_LESSON, PIN_LABEL),
  // The same fact, delivered where the CUT is made instead of where the work
  // is done. `pin-on` hands the worker a recalled claim under a header that
  // says to verify it against the code; these two hand it the identical fact
  // as a Constraints line inside <task_rules> — the form a crafting session
  // would have written had the lesson reached it before it cut the task, and
  // the form truth_grounding calls "a decision already taken". No label, no
  // header, no match disclosure. `cut-on` runs on pinned-dup, where the fact
  // is true; `cut-wrong` is the same prompt on unpinned-dup, where it is
  // false and nothing in the fixture can refute it. The question is whether
  // the channel's shape changes what a true fact costs and what a false one
  // does — `unpin-wrong` showed Opus refuting a note by looking; a constraint
  // grants no such licence.
  'cut-on': CUT_LINE,
  'cut-wrong': CUT_LINE,
};

// Where each arm's block lands. The lesson and chain blocks go inside
// <background>, after <relevant_files>, before <context> — where
// craft-handoff.js puts them. The cut line goes under Constraints: inside
// <task_rules>, after the last constraint the frozen prompt already carries.
const ANCHOR = '</relevant_files>\n';
const CUT_ANCHOR = '- Do NOT change test files; make the code satisfy the tests\n';
const PLACE = { 'cut-on': CUT_ANCHOR, 'cut-wrong': CUT_ANCHOR };

function build(armName) {
  if (!(armName in ARMS)) throw new Error(`unknown arm ${armName}`);
  const base = fs.readFileSync(path.join(PROMPTS, 'foreman.md'), 'utf8');
  const lessons = ARMS[armName];
  if (!lessons) return base;
  const anchor = PLACE[armName] || ANCHOR;
  const at = base.indexOf(anchor);
  if (at === -1) {
    throw new Error(`foreman.md no longer contains ${JSON.stringify(anchor)} — the arms cannot be spliced`);
  }
  const cut = at + anchor.length;
  return `${base.slice(0, cut)}${lessons}\n${base.slice(cut)}`;
}

function armPath(armName) {
  return path.join(PROMPTS, `${armName}.md`);
}

function main() {
  const check = process.argv.includes('--check');
  const stale = [];
  for (const armName of Object.keys(ARMS)) {
    const wanted = build(armName);
    const target = armPath(armName);
    const current = fs.existsSync(target) ? fs.readFileSync(target, 'utf8') : null;
    if (current === wanted) continue;
    if (check) {
      stale.push(path.relative(ROOT, target));
      continue;
    }
    fs.writeFileSync(target, wanted, 'utf8');
    console.log(`wrote ${path.relative(ROOT, target)}`);
  }
  if (check && stale.length) {
    console.error(`stale or missing arm prompts: ${stale.join(', ')}\nRun: node benefit/gen.js`);
    process.exit(1);
  }
  if (check) console.log('benefit arms current');
}

if (require.main === module) main();

module.exports = {
  ARMS,
  build,
  armPath,
  PIN_LESSON,
  PIN_LABEL,
  WRONG_LESSON,
  WRONG_LABEL,
  CHAIN_LINE,
  CUT_LINE,
  CHAIN_ENTRY_ID,
  CHAIN_ENTRY_TITLE,
};
