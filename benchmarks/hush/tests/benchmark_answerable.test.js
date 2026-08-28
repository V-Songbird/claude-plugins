'use strict';
// The answerable scorer, everything except the paid call: the prompt it builds,
// the answers it parses back, and how it scores them against the task's own
// rubric.
//
// Samples are literal judge replies, not generated ones, so a change to the
// parser shows up here as a changed number rather than as two halves of the
// same bug agreeing.

const { describe, test } = require('node:test');
const assert = require('node:assert');

const {
  QUESTIONS, ABSENT, judgePrompt, parseAnswers, isAbsent, scoreAnswers, answerableReport,
} = require('../runner/answerable.js');

const FULL = [
  'A1: Redis at 10.0.0.12:6379 died and every reconnect was refused.',
  'A2: Open the Redis host, and check why it refused connections.',
  'A3: Restart Redis, then confirm the queue drains below 500.',
].join('\n');

const PARTIAL = [
  'A1: Something in the cache layer failed.',
  `A2: ${ABSENT}`,
  `A3: ${ABSENT}`,
].join('\n');

describe('the prompt handed to the judge', () => {
  const p = judgePrompt('Prod fell over last night.', '**Redis died.** Check `10.0.0.12`.');

  test('carries the request and the whole reply', () => {
    assert.ok(p.includes('Prod fell over last night.'));
    assert.ok(p.includes('**Redis died.** Check `10.0.0.12`.'));
  });

  test('asks all three questions and names the absent marker', () => {
    for (const q of QUESTIONS) assert.ok(p.includes(q), `missing question: ${q}`);
    assert.ok(p.includes(ABSENT));
  });

  test('tells the judge it may use nothing but the reply', () => {
    assert.ok(/ONLY the reply/.test(p));
    assert.ok(/Do not guess/.test(p));
  });
});

describe('parsing the judge back', () => {
  test('reads three answers in order', () => {
    assert.deepStrictEqual(parseAnswers(FULL), [
      'Redis at 10.0.0.12:6379 died and every reconnect was refused.',
      'Open the Redis host, and check why it refused connections.',
      'Restart Redis, then confirm the queue drains below 500.',
    ]);
  });

  test('a missing line reads as absent rather than empty', () => {
    const answers = parseAnswers('A1: The build passes now.');
    assert.strictEqual(answers.length, 3);
    assert.strictEqual(isAbsent(answers[1]), true);
    assert.strictEqual(isAbsent(answers[2]), true);
  });

  test('surrounding chatter does not break the lines out', () => {
    const answers = parseAnswers(['Here you go:', '', ...FULL.split('\n'), '', 'Hope that helps.'].join('\n'));
    assert.strictEqual(answers[0], 'Redis at 10.0.0.12:6379 died and every reconnect was refused.');
    assert.strictEqual(isAbsent(answers[2]), false);
  });

  test('empty and missing judge text score as three absent answers', () => {
    for (const input of ['', null, undefined]) {
      assert.deepStrictEqual(parseAnswers(input).map(isAbsent), [true, true, true]);
    }
  });
});

describe('scoring against the task rubric, never against itself', () => {
  const patterns = ['Redis', 'ECONNREFUSED|refused', 'queue|backlog'];

  test('a full answer set is answerable and recovers the rubric', () => {
    const s = scoreAnswers(parseAnswers(FULL), patterns);
    assert.strictEqual(s.answered, 3);
    assert.strictEqual(s.answerable, true);
    assert.strictEqual(s.recovered, 3);
    assert.strictEqual(s.recoveredPct, 100);
    assert.deepStrictEqual(s.missed, []);
  });

  test('each question keeps its own verdict, in order', () => {
    assert.deepStrictEqual(scoreAnswers(parseAnswers(FULL), patterns).perQuestion, [true, true, true]);
    assert.deepStrictEqual(scoreAnswers(parseAnswers(PARTIAL), patterns).perQuestion, [true, false, false]);
  });

  test('absent answers are not scored, and what they carried is named as missed', () => {
    const s = scoreAnswers(parseAnswers(PARTIAL), patterns);
    assert.strictEqual(s.answered, 1);
    assert.strictEqual(s.answerable, false);
    assert.strictEqual(s.recovered, 0);
    assert.deepStrictEqual(s.missed, patterns);
  });

  test('a fact only in an absent line cannot be recovered', () => {
    const s = scoreAnswers(['The cache broke.', ABSENT, ABSENT], ['Redis']);
    assert.strictEqual(s.recovered, 0, 'naming the thing plainly must not count as recovering it');
  });

  test('a task with no keyword rubric reports null rather than a fake 100%', () => {
    const s = scoreAnswers(parseAnswers(FULL), []);
    assert.strictEqual(s.recoveredPct, null);
    assert.strictEqual(s.answered, 3);
  });
});

describe('rolling up per arm', () => {
  const rows = [
    { arm: 'hush', answered: 3, answerable: true, perQuestion: [true, true, true], recoveredPct: 100, costUsd: 0.01 },
    { arm: 'hush', answered: 2, answerable: false, perQuestion: [true, true, false], recoveredPct: 50, costUsd: 0.01 },
    { arm: 'baseline', answered: 3, answerable: true, perQuestion: [true, true, true], recoveredPct: 100, costUsd: 0.02 },
  ];

  test('means and rates carry their denominator', () => {
    const r = answerableReport(rows);
    assert.strictEqual(r.arms.hush.judged, 2);
    assert.strictEqual(r.arms.hush.answered, 2.5);
    assert.strictEqual(r.arms.hush.answerablePct, 50);
    assert.strictEqual(r.arms.hush.recoveredPct, 75);
    assert.strictEqual(r.arms.baseline.answerablePct, 100);
  });

  test('the three questions roll up separately, so the two misses stay apart', () => {
    const r = answerableReport(rows);
    assert.deepStrictEqual(r.arms.hush.qPct, [100, 100, 50]);
    assert.deepStrictEqual(r.arms.baseline.qPct, [100, 100, 100]);
  });

  test('a failed judge call is counted and named, never averaged in', () => {
    const r = answerableReport([...rows, { arm: 'hush', error: 'rate limited' }]);
    assert.strictEqual(r.arms.hush.runs, 3);
    assert.strictEqual(r.arms.hush.judged, 2);
    assert.strictEqual(r.arms.hush.failed, 1);
    assert.strictEqual(r.arms.hush.answered, 2.5, 'the failure must not drag the mean');
  });
});
