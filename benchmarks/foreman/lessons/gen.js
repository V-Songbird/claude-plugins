#!/usr/bin/env node
'use strict';
// P2 — the lesson-ledger measurement arms.
//
// The product thesis is a delta, not an absolute: a stale lesson that SAYS it
// might be stale should not hurt, and the same lesson with the label stripped
// should. So the four arms differ in exactly one thing — the lesson block
// inside `<background>` — and in nothing else. Everything above and below it
// is the frozen `foreman.md` prompt, byte for byte.
//
//   arm             lesson block
//   ---             ------------
//   control         none at all (the no-notes baseline)
//   fresh           a correct lesson, labelled unchanged
//   graded          a STALE lesson, labelled possibly-stale (what v1 ships)
//   unlabeled       the same stale lesson with the label stripped (the harm arm)
//
// The fixture is `moved-file`, whose whole shape is already a decoy: the
// prompt names `src/parser.js`, reality is `src/tokenizer.js`, and the decoy
// file contains a plausible split that makes the wrong claim feel confirmable.
// The stale lesson points at the decoy, which is precisely the failure the
// staleness label exists to defuse.
//
// Header and closer are read from the plugin, never restated here — a reworded
// product string must fail the arm test rather than silently benchmark prose
// the product no longer ships.
//
//   node lessons/gen.js            # write the four arm prompts
//   node lessons/gen.js --check    # exit 1 if they are missing or stale
//
// Run data (results, transcripts, reports) stays on the operator's machine per
// ADR 0004. This file writes prompts only.

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const FIXTURE = path.join(ROOT, 'fixtures', 'moved-file');
const PROMPTS = path.join(FIXTURE, 'prompts');

const FOREMAN_DIR = process.env.FOREMAN_DIR
  ? path.resolve(process.env.FOREMAN_DIR)
  : path.resolve(ROOT, '..', '..', 'foreman');

const { NOTES_HEADER, NOTES_CLOSER } = require(path.join(FOREMAN_DIR, 'scripts', 'craft-handoff.js'));

// The decoy claim, worded the way a real close would have worded it back when
// `src/parser.js` was still the live tokenizer. It is TRUE of the repo at the
// anchor commit and FALSE of the repo now — which is what makes it a fair
// test of the label rather than a test of whether a model can spot nonsense.
const STALE_LESSON =
  'tokenizing lives in src/parser.js — the word split is the only place punctuation is handled';
const FRESH_LESSON =
  'the failing suite is tests/tokenizer.test.js and it is the contract; do not edit it to make it pass';

const STALE_LABEL = '[entry 118, 2026-05-04, at 4c1e9a2 — possibly stale: 1 of its 1 files changed since]';
const FRESH_LABEL = '[entry 122, 2026-06-11, at 8d3b7f0 — unchanged since]';

const MATCH_STALE = '(matched: planned src/parser.js ↔ recorded src/parser.js)';
const MATCH_FRESH = '(matched: planned tests/tokenizer.test.js ↔ recorded tests/tokenizer.test.js)';

function block(lines) {
  return `${NOTES_HEADER}\n${lines.join('\n')}\n${NOTES_CLOSER}`;
}

const ARMS = {
  'lessons-control': null,
  'lessons-fresh': block([`- ${FRESH_LESSON} ${FRESH_LABEL} ${MATCH_FRESH}`]),
  'lessons-graded': block([`- ${STALE_LESSON} ${STALE_LABEL} ${MATCH_STALE}`]),
  // The harm arm: same claim, same position, no freshness signal anywhere.
  // If this arm does not lose to `lessons-graded`, the label is doing nothing
  // and the whole read side is unjustified.
  'lessons-unlabeled': block([`- ${STALE_LESSON} ${MATCH_STALE}`]),
};

// The block lands where craft-handoff.js puts it: inside <background>, after
// <relevant_files>, before <context>. Splicing on the literal tag keeps the
// arms honest if the frozen prompt is ever regenerated.
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
    console.error(`stale or missing arm prompts: ${stale.join(', ')}\nRun: node lessons/gen.js`);
    process.exit(1);
  }
  if (check) console.log('lesson arms current');
}

if (require.main === module) main();

module.exports = { ARMS, build, armPath, STALE_LESSON, FRESH_LESSON, STALE_LABEL, FRESH_LABEL };
