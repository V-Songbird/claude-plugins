#!/usr/bin/env node
'use strict';
// Retold: can a person carry the reply's meaning away, not just find it in the text?
//
// answerable.js hands a judge the reply and asks three questions of it. A judge
// that can pattern-match a string out of the text scores well whether or not
// the text was understandable. This adds a stage in front of it:
//
//   1. A READER sees the request and the reply, and writes down what it means
//      in its own words. Copying a run of more than four words is forbidden.
//   2. The SAME judge answerable.js uses reads only that retelling — never the
//      reply — and answers the same three fixed questions. The task's own
//      rubric is matched against those answers, exactly as before.
//
// So `retold` and `answerable` are the same instrument over two inputs, and the
// gap between them is meaning that did not survive being repeated by someone
// else. A reply that only reads well under a search scores well on one and
// badly on the other.
//
// The reader can cheat by copying, so every retelling is measured for the
// longest word run it shares with the reply and that is reported, not hidden.
//
// COSTS MONEY. Two calls per record. Prints the plan and stops unless --go.
//
//   node runner/retold.js --records records/rm300-93b2a811
//   node runner/retold.js --records records/rm300-93b2a811 --go

const fs = require('node:fs');
const path = require('node:path');
require('../../bench-config-dir.js');

const {
  QUESTIONS, ABSENT, judgePrompt, parseAnswers, scoreAnswers, answerableReport, runJudge,
} = require('./answerable.js');

const ROOT = path.resolve(__dirname, '..');
const TASKS = JSON.parse(fs.readFileSync(path.join(ROOT, 'tasks.json'), 'utf8'));
const COPY_LIMIT = 4;

function readerPrompt(taskPrompt, finalText) {
  return [
    'Someone asked an assistant for help and got the reply below. Read it, then',
    'write down what it means for the person who asked. Write it the way you',
    'would say it to a colleague who was not here.',
    '',
    'Rules:',
    `- Use your own words. Never copy a run of more than ${COPY_LIMIT} words from the reply.`,
    '- File names, commands, numbers and error text are exempt: copy those exactly.',
    '- Do not add anything the reply does not support.',
    '- If the reply leaves something out, leave it out.',
    '- Write prose, no headings and no lists, and nothing else.',
    '',
    '--- THE REQUEST ---',
    taskPrompt,
    '',
    '--- THE ENTIRE REPLY ---',
    finalText,
  ].join('\n');
}

/** Longest run of words the retelling shares with the reply, ignoring case. */
function longestSharedRun(reply, retelling) {
  const norm = (s) => (String(s).toLowerCase().match(/[a-z0-9]+/g) || []);
  const a = norm(reply), b = norm(retelling);
  const seen = new Map();
  for (let n = 1; n <= a.length; n++) {
    // Index every n-gram of the reply once, then walk the retelling. Stops as
    // soon as a length has no match, so a clean retelling costs almost nothing.
    seen.clear();
    for (let i = 0; i + n <= a.length; i++) seen.set(a.slice(i, i + n).join(' '), true);
    let hit = false;
    for (let i = 0; i + n <= b.length; i++) if (seen.has(b.slice(i, i + n).join(' '))) { hit = true; break; }
    if (!hit) return n - 1;
  }
  return a.length;
}

function readRecordsDir(dir) {
  return fs.readdirSync(dir)
    .filter((f) => f.endsWith('.json') && f !== 'batch.json')
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')))
    .filter((r) => r && !r.error && r.finalText);
}

const flag = (name, fallback = null) => {
  const i = process.argv.indexOf(`--${name}`);
  return i === -1 ? fallback : process.argv[i + 1];
};

async function main() {
  const dir = flag('records');
  if (!dir) { console.error('usage: node runner/retold.js --records <dir> [--go]'); process.exit(2); }
  const go = process.argv.includes('--go');
  const model = flag('model', 'sonnet');
  const records = readRecordsDir(dir);

  console.log(`retold — ${dir}`);
  console.log(`${records.length * 2} calls on ${model}: one retelling and one judging per record.\n`);
  if (!go) { console.log('plan only — nothing was spawned and nothing was billed.'); return; }

  const rows = [];
  for (const [i, r] of records.entries()) {
    const task = TASKS.find((t) => t.id === r.task) || {};
    const ask = (task.prompts || [task.prompt] || []).join('\n');
    const read = await runJudge(readerPrompt(ask, r.finalText), model, ROOT);
    if (read.error) { rows.push({ ...r, error: read.error }); console.log(`ERR  ${r.task}__${r.arm}  ${read.error}`); continue; }

    const judged = await runJudge(judgePrompt(ask, read.text), model, ROOT);
    if (judged.error) { rows.push({ ...r, error: judged.error }); console.log(`ERR  ${r.task}__${r.arm}  ${judged.error}`); continue; }

    const answers = parseAnswers(judged.text);
    const score = scoreAnswers(answers, task.check?.patterns || []);
    const copied = longestSharedRun(r.finalText, read.text);
    rows.push({
      ...r, ...score, copied,
      costUsd: (read.costUsd || 0) + (judged.costUsd || 0),
      retelling: read.text,
    });
    const q = score.perQuestion.map((ok) => (ok ? 'Y' : 'n')).join('');
    console.log(`${score.answerable ? 'OK  ' : 'GAP '} ${r.task}__${r.arm}  q=${q}  copied=${copied}w  (${i + 1}/${records.length})`);
  }

  const report = answerableReport(rows);
  const n1 = (x) => (x == null ? '—' : x.toFixed(1));
  console.log('\narm\truns\tjudged\tanswered/3\tq1%\tq2%\tq3%\tsurvives retelling%\trubric recovered%\tlongest copied run\t$');
  for (const a of Object.keys(report.arms)) {
    const x = report.arms[a];
    const mine = rows.filter((r) => r.arm === a && !r.error);
    const copy = mine.length ? mine.reduce((n, r) => n + r.copied, 0) / mine.length : null;
    console.log([a, x.runs, x.judged, n1(x.answered), ...x.qPct.map(n1), n1(x.answerablePct),
      n1(x.recoveredPct), n1(copy), x.costUsd.toFixed(3)].join('\t'));
  }
  const save = flag('save');
  if (save) fs.writeFileSync(save, rows.map((r) => JSON.stringify(r)).join('\n') + '\n');
}

if (require.main === module) main();
module.exports = { readerPrompt, longestSharedRun };
