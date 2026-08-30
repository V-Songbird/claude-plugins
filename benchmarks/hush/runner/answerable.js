#!/usr/bin/env node
'use strict';
// Answerable: could a reader act on this message without asking a follow-up?
//
// CHANGED 2026-08-29, and numbers from before that date are not comparable:
// the judge used to mark "there is nothing to do next" as no answer at all.
// Only a reply willing to say a job is finished ever trips that, so it scored
// honesty as a miss and rewarded inventing a next step. The prompt now names
// it as an answer. Both arms are judged by the same prompt, as always.
//
// CHANGED AGAIN the same day, same rule about comparability: the second
// question reads "Which file, command or thing", and the judge was reading it
// as "which file". On a read-only diagnosis the thing to look at is a host or a
// service, not a path, so a correct reply scored as a miss. The prompt now says
// what its own word "thing" covers. It grants no new leniency: a reply that
// points at nothing is still a miss.
//
// Every other meter here scores the text. This one scores what a reader can get
// OUT of the text. A fresh session — no plugins, no output style, no sight of
// the work — is handed the original request and the one reply, and asked three
// fixed questions: what happened, what to open, what to do next. It answers in
// its own words or says the reply does not contain it.
//
// Two numbers come back per run:
//
//   answered   how many of the three questions the reply could answer at all
//   recovered  how many of the task's own rubric facts survive INTO those
//              answers, which is a stricter thing than the fact being somewhere
//              in the message
//
// WHY THAT SECOND NUMBER IS NOT CIRCULAR, and where it is still soft. The
// oracle is the task's rubric in tasks.json — the same independent ground truth
// runCheck already uses — never this file's own judgment and never the style's
// own rules. But runCheck greps the whole message, and this greps only the three
// answers, so a fact the reply merely name-drops can pass one and fail the
// other. That gap is the measurement. The soft part: a judge that quotes the
// reply wholesale will score like a grep, so `recovered` is a floor on
// reachability, not a comprehension score, and `answered` is the judge's
// opinion, one sample, on one model.
//
// COSTS MONEY. One extra session per record. Prints the plan and stops unless
// --go is passed.
//
//   node runner/answerable.js --records records/rm280-7e554675            # plan only
//   node runner/answerable.js --records records/rm280-7e554675 --go
//   node runner/answerable.js --tag shp1 --arms shape,shapeplus --go

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
// Keeps every cell's temp cwd out of the real ~/.claude registry and
// transcript store; must load before anything copies process.env.
require('../../bench-config-dir.js');

const ROOT = path.resolve(__dirname, '..');
const TASKS = JSON.parse(fs.readFileSync(path.join(ROOT, 'tasks.json'), 'utf8'));

// The three questions, fixed and identical for every task and every arm. They
// are the three things the style itself promises to deliver — what happened,
// whether it worked, what comes next — asked from the reader's side.
const QUESTIONS = [
  'What happened, or what is wrong?',
  'Which file, command or thing should I open or run?',
  'What should I do next?',
];

const ABSENT = 'NOT IN THE REPLY';

function judgePrompt(taskPrompt, finalText) {
  return [
    'Someone asked an assistant for help. Below is the request they made, and the',
    'entire reply they got back. You cannot see the work that was done, and there',
    'is nothing else to look at.',
    '',
    'Answer the three questions using ONLY the reply. Do not guess, do not use',
    'anything you know about the tools or files involved, and do not explain your',
    `reasoning. If the reply does not contain an answer, write exactly ${ABSENT}.`,
    '',
    '"There is nothing to do" IS an answer to the third question. A reply that',
    'says the work is finished and needs no follow-up has answered it — write',
    `that, not ${ABSENT}. Only a reply that leaves the question open is a miss.`,
    '',
    'The second question says "file, command or thing", and it means all three.',
    'A host, service, endpoint, URL, log or command to run answers it just as a',
    `file path does. Write ${ABSENT} only when the reply points at nothing.`,
    '',
    'Write exactly three lines and nothing else:',
    ...QUESTIONS.map((q, i) => `A${i + 1}: <answer to: ${q}>`),
    '',
    '--- THE REQUEST ---',
    taskPrompt,
    '',
    '--- THE ENTIRE REPLY ---',
    finalText,
  ].join('\n');
}

/** Pull A1/A2/A3 out of the judge's reply. A missing line reads as absent. */
function parseAnswers(text) {
  const out = [];
  for (let i = 1; i <= QUESTIONS.length; i++) {
    const m = String(text || '').match(new RegExp(`^\\s*A${i}\\s*:\\s*(.+?)\\s*$`, 'm'));
    out.push(m ? m[1] : ABSENT);
  }
  return out;
}

const isAbsent = (a) => !a || a.trim().toUpperCase().startsWith(ABSENT);

/**
 * Score one judged reply against the task's own rubric.
 * `patterns` comes from tasks.json — this file never invents an oracle.
 */
function scoreAnswers(answers, patterns = []) {
  const present = answers.filter((a) => !isAbsent(a));
  const corpus = present.join('\n');
  const hits = patterns.filter((p) => new RegExp(p, 'i').test(corpus));
  return {
    answered: present.length,
    answerable: present.length === QUESTIONS.length,
    // Which of the three was answered — the misses are two different things
    // (nothing to open vs nothing to do) and tuning needs them apart.
    perQuestion: answers.map((a) => !isAbsent(a)),
    recovered: hits.length,
    recoveredPct: patterns.length ? (100 * hits.length) / patterns.length : null,
    missed: patterns.filter((p) => !hits.includes(p)),
  };
}

// --- one judge call ----------------------------------------------------------

// The same two success-shaped failures the run harness refuses: a rate-limited
// call hands back the limit message AS the answer at cost 0, and any call that
// billed nothing did not happen the way we think it did.
const RATE_LIMITED = /you\s*['’]?ve hit your (session|usage|weekly) limit/i;

function judgeArgs(model) {
  return [
    '-p',
    '--output-format', 'json',
    '--model', model,
    '--max-turns', '1',
    // Same isolation the arms get: no user settings, no MCP, and here no tools
    // at all — the judge reads the reply it was handed and nothing else.
    '--setting-sources', 'project',
    '--strict-mcp-config',
    '--disallowedTools',
    'Read,Edit,Write,Glob,Grep,Bash,PowerShell,WebFetch,WebSearch,Agent,Task,TodoWrite',
  ];
}

function runJudge(prompt, model, cwd) {
  return new Promise((resolve) => {
    const child = spawn('claude', judgeArgs(model), { cwd, env: process.env, shell: true });
    let stdout = '', stderr = '';
    child.stdout.on('data', (d) => { stdout += d; });
    child.stderr.on('data', (d) => { stderr += d; });
    child.stdin.write(prompt);
    child.stdin.end();
    const killer = setTimeout(() => child.kill('SIGKILL'), 120000);
    child.on('close', () => {
      clearTimeout(killer);
      let text = '', costUsd = null;
      try {
        const ev = JSON.parse(stdout);
        text = typeof ev.result === 'string' ? ev.result : '';
        costUsd = ev.total_cost_usd ?? null;
      } catch { /* fall through to the guard below */ }
      if (!text) return resolve({ error: `judge produced no reply: ${stderr.slice(0, 200)}` });
      if (RATE_LIMITED.test(text)) return resolve({ error: `rate limited: ${text.trim().slice(0, 120)}` });
      if (!(costUsd > 0)) return resolve({ error: `zero-cost judge call (cost=${costUsd})` });
      resolve({ text, costUsd });
    });
  });
}

// --- many records ------------------------------------------------------------

function readRecordsDir(dir) {
  return fs.readdirSync(dir)
    .filter((f) => f.endsWith('.json') && f !== 'batch.json')
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')))
    .filter((r) => r && !r.error && r.finalText);
}

const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);

/** arm -> answerability totals. Judged rows only; a failed judge call is named, not averaged. */
function answerableReport(rows) {
  const arms = {};
  for (const arm of [...new Set(rows.map((r) => r.arm))]) {
    const mine = rows.filter((r) => r.arm === arm);
    const ok = mine.filter((r) => !r.error);
    arms[arm] = {
      runs: mine.length,
      judged: ok.length,
      failed: mine.length - ok.length,
      answered: mean(ok.map((r) => r.answered)),
      qPct: QUESTIONS.map((_, i) =>
        ok.length ? (100 * ok.filter((r) => r.perQuestion?.[i]).length) / ok.length : null),
      answerablePct: ok.length ? (100 * ok.filter((r) => r.answerable).length) / ok.length : null,
      recoveredPct: mean(ok.map((r) => r.recoveredPct).filter((n) => n != null)),
      costUsd: ok.reduce((n, r) => n + (r.costUsd || 0), 0),
    };
  }
  return { rows: rows.length, arms };
}

// --- CLI ---------------------------------------------------------------------

const n1 = (x) => (x == null ? '-' : x.toFixed(1));

async function main() {
  const argv = process.argv.slice(2);
  const at = (flag) => (argv.includes(flag) ? argv[argv.indexOf(flag) + 1] : null);
  const tag = at('--tag');
  const recordsArg = at('--records');
  const model = at('--model') || 'sonnet';
  const only = (at('--arms') || '').split(',').filter(Boolean);
  const save = at('--save');
  const go = argv.includes('--go');
  const dir = recordsArg
    ? path.resolve(ROOT, recordsArg)
    : tag ? path.join(ROOT, 'results', tag, 'runs') : null;
  if (!dir) {
    console.error('Usage: answerable.js --records <dir> | --tag <tag> [--arms a,b] [--model sonnet] --go');
    process.exit(1);
  }

  const records = readRecordsDir(dir).filter((r) => !only.length || only.includes(r.arm));
  console.log(`answerable — ${path.relative(ROOT, dir)}`);
  console.log(`${records.length} judge calls on ${model}, one per record, three fixed questions each.`);
  if (!go) {
    console.log('\nplan only — nothing was spawned and nothing was billed. Re-run with --go to spend.');
    return;
  }

  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'hush-answerable-'));
  const rows = [];
  for (const [i, r] of records.entries()) {
    const task = TASKS.find((t) => t.id === r.task);
    const taskPrompt = task?.prompt || (task?.prompts || []).join('\n') || '(prompt unavailable)';
    const patterns = task?.check?.type === 'keywords' ? task.check.patterns : [];
    const res = await runJudge(judgePrompt(taskPrompt, r.finalText), model, cwd);
    if (res.error) {
      rows.push({ arm: r.arm, task: r.task, error: res.error });
      console.log(`ERR  ${r.task}__${r.arm}  ${res.error}`);
      continue;
    }
    const answers = parseAnswers(res.text);
    const scored = scoreAnswers(answers, patterns);
    // The judge's literal answers ride along so a --save file shows WHAT a
    // reader got out, not just how much.
    rows.push({ arm: r.arm, task: r.task, costUsd: res.costUsd, answers, ...scored });
    console.log(`${scored.answerable ? 'OK  ' : 'GAP '} ${r.task}__${r.arm}  `
      + `q=${scored.perQuestion.map((b) => (b ? 'Y' : 'n')).join('')}  `
      + `answered=${scored.answered}/${QUESTIONS.length}  recovered=${n1(scored.recoveredPct)}%  `
      + `(${i + 1}/${records.length})`);
  }

  const report = answerableReport(rows);
  const arms = Object.keys(report.arms).sort(
    (a, b) => (a === 'baseline' ? -1 : b === 'baseline' ? 1 : a.localeCompare(b)));
  console.log('\narm\truns\tjudged\tanswered/3\tq1%\tq2%\tq3%\tfully answerable%\trubric recovered%\t$');
  for (const a of arms) {
    const x = report.arms[a];
    console.log([a, x.runs, x.judged, n1(x.answered), ...x.qPct.map(n1), n1(x.answerablePct),
      n1(x.recoveredPct), x.costUsd.toFixed(3)].join('\t'));
  }
  if (save) {
    fs.writeFileSync(save, rows.map((r) => JSON.stringify(r)).join('\n') + '\n');
    console.log(`\nsaved ${rows.length} judged rows to ${save}`);
  }

  // The README quotes these percentages, so they need a home on disk beside the
  // batch they came from. publish.js owns claims.md and never sees a judge run,
  // so this writes its own file next to it rather than editing that one.
  if (dir) {
    const out = path.join(dir, 'published', 'answerable.md');
    fs.mkdirSync(path.dirname(out), { recursive: true });
    const body = Object.keys(report.arms).map((a) => {
      const x = report.arms[a];
      return `| ${a} | ${x.judged} | ${n1(x.qPct[0])}% | ${n1(x.qPct[1])}% | `
        + `${n1(x.qPct[2])}% | ${n1(x.answerablePct)}% | ${n1(x.recoveredPct)}% |`;
    });
    fs.writeFileSync(out, [
      `# answerable — batch ${path.basename(dir)}`,
      '',
      `${rows.length} judged replies, three fixed questions each, judged on ${model}.`,
      '',
      '| Arm | runs | q1 what happened | q2 what to open | q3 what next | all three | task facts recovered |',
      '|---|---|---|---|---|---|---|',
      ...body,
      '',
    ].join('\n'));
    console.log(`wrote ${out}`);
  }
  const failed = rows.filter((r) => r.error).length;
  if (failed) console.log(`\n${failed} judge call(s) failed and were left out of the means.`);
}

if (require.main === module) main();

module.exports = {
  QUESTIONS, ABSENT, judgePrompt, parseAnswers, isAbsent, scoreAnswers, answerableReport,
  // retold.js runs the same second-stage judge over a retelling instead of the
  // reply, so it needs the same spawn and the same success guards.
  runJudge,
};
