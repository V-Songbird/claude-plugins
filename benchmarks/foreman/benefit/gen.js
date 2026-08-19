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
//   node benefit/gen.js            # write both arm prompts
//   node benefit/gen.js --check    # exit 1 if they are missing or stale
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

const { NOTES_HEADER, NOTES_CLOSER } = require(path.join(FOREMAN_DIR, 'scripts', 'craft-handoff.js'));

// The lesson is TRUE of the repo now, and it is the only place the pin exists.
// Worded the way a real close would have worded it, and within the store's own
// 500-character cap on a lesson.
const PIN_LESSON =
  'the three percentile helpers in src/stats.js (p50/p90/p99) are copy-pasted on purpose — ticket PERF-1123 pins them until the sampling rework lands, so do not unify them';
const PIN_LABEL = '[entry 131, 2026-06-02, at 5f2a1c8 — unchanged since]';
const PIN_MATCH = '(matched: planned src/stats.js ↔ recorded src/stats.js)';

const ARMS = {
  'pin-off': null,
  'pin-on': `${NOTES_HEADER}\n- ${PIN_LESSON} ${PIN_LABEL} ${PIN_MATCH}\n${NOTES_CLOSER}`,
};

// The block lands where craft-handoff.js puts it: inside <background>, after
// <relevant_files>, before <context>.
const ANCHOR = '</relevant_files>\n';

function build(armName) {
  const base = fs.readFileSync(path.join(PROMPTS, 'foreman.md'), 'utf8');
  const lessons = ARMS[armName];
  if (!lessons) return base;
  const at = base.indexOf(ANCHOR);
  if (at === -1) {
    throw new Error(`foreman.md no longer contains ${JSON.stringify(ANCHOR)} — the arms cannot be spliced`);
  }
  const cut = at + ANCHOR.length;
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

module.exports = { ARMS, build, armPath, PIN_LESSON, PIN_LABEL };
