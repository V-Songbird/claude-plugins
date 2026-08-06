'use strict';

// Cap conformance meter (benchmarks/runner/caps.js). All local/pure — no
// `claude` CLI invocation, no cost.
//
// The vocabulary here is pinned with LITERAL samples pushed through the shipped
// functions, never by asking the production regex whether it agrees with
// itself: an oracle built from the code under test proves nothing.

const { test, describe } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const { readCaps, loadCaps, analyzeMessage, capReport, unitsOf, countWords } =
  require('../benchmarks/runner/caps.js');

const CAPS = { lineCap: 12, wordCap: 15 };

describe('readCaps: the numbers come from the style, not from this file', () => {
  test('reads both caps out of the real style file', () => {
    const caps = loadCaps();
    assert.strictEqual(caps.lineCap, 12);
    assert.strictEqual(caps.wordCap, 15);
  });

  test('the caps the meter scores against are the caps the style states', () => {
    const style = fs.readFileSync(
      path.resolve(__dirname, '../../../hush/output-styles/hush.md'), 'utf8');
    const caps = loadCaps();
    assert.ok(style.includes(`**${caps.lineCap} lines**`), 'line cap must appear verbatim in the style');
    assert.ok(style.includes(`**${caps.wordCap} words**`), 'word cap must appear verbatim in the style');
  });

  test('a reworded style throws instead of scoring against a stale number', () => {
    assert.throws(() => readCaps('- 12 lines for the whole message.\n- 15 words per sentence.'),
      /could not read the line and word caps/);
    assert.throws(() => readCaps('- **12 lines** for the whole message.'),
      /could not read the line and word caps/);
  });
});

describe('countWords: an identifier is one word', () => {
  test('a backticked path does not spend the sentence budget', () => {
    assert.strictEqual(countWords('Fixed `src/net/retryPolicy.js` today.'), 3);
  });

  test('a bare path still counts as the words it is written with', () => {
    assert.strictEqual(countWords('Fixed src/net/retryPolicy.js today.'), 3);
  });

  test('plain prose counts every word', () => {
    assert.strictEqual(countWords('one two three four five'), 5);
  });
});

describe('unitsOf: what a cap applies to', () => {
  test('a bullet holding two sentences is two units', () => {
    const units = unitsOf('- The build failed. I fixed the import.');
    assert.deepStrictEqual(units, ['The build failed.', 'I fixed the import.']);
  });

  test('list markers and blockquote markers are not words', () => {
    assert.deepStrictEqual(unitsOf('> 1. Run the migration.'), ['Run the migration.']);
    assert.deepStrictEqual(unitsOf('* Run the migration.'), ['Run the migration.']);
  });

  test('table rows and separators are not sentences', () => {
    const md = '| Package | Version |\n|---|---|\n| `left-pad` | 1.3.0 |\nAll three bumped.';
    assert.deepStrictEqual(unitsOf(md), ['All three bumped.']);
  });

  test('a sentence closing inside bold is its own unit', () => {
    assert.deepStrictEqual(
      unitsOf('**Fixed the coupon bug.** The rate was missing.'),
      ['**Fixed the coupon bug.**', 'The rate was missing.']);
  });

  test('a quoted sentence closing inside quotes is its own unit', () => {
    assert.deepStrictEqual(
      unitsOf('It said "the build failed." Then it stopped.'),
      ['It said "the build failed."', 'Then it stopped.']);
  });

  test('headings are not sentences', () => {
    assert.deepStrictEqual(unitsOf('## What changed\nThe order was wrong.'), ['The order was wrong.']);
  });
});

describe('analyzeMessage: the caps', () => {
  test('a compliant message breaches nothing', () => {
    const msg = 'Fixed the coupon bug.\n\nThe rate was missing, so the code used 1.\n\nAll 214 tests pass.';
    const r = analyzeMessage(msg, CAPS);
    assert.strictEqual(r.overWordCap, 0);
    assert.strictEqual(r.overLineCap, false);
    assert.strictEqual(r.semicolons, 0);
    assert.strictEqual(r.parenUnits, 0);
    assert.strictEqual(r.units, 3);
  });

  test('a 16-word sentence breaches a 15-word cap and a 15-word one does not', () => {
    const fifteen = 'one two three four five six seven eight nine ten more words to fill it.';
    const sixteen = 'one two three four five six seven eight nine ten more words to fill it now.';
    assert.strictEqual(countWords(fifteen), 15);
    assert.strictEqual(countWords(sixteen), 16);
    assert.strictEqual(analyzeMessage(fifteen, CAPS).overWordCap, 0);
    assert.strictEqual(analyzeMessage(sixteen, CAPS).overWordCap, 1);
  });

  test('the longest sentence is reported with its length', () => {
    const r = analyzeMessage('Short one.\n\nA far longer sentence that runs well past the fifteen word limit set by the style.', CAPS);
    assert.strictEqual(r.longestWords, 16);
    assert.match(r.longestText, /^A far longer sentence/);
  });

  test('thirteen non-empty lines breach a twelve-line cap', () => {
    const under = Array.from({ length: 12 }, (_, i) => `Line ${i}.`).join('\n');
    assert.strictEqual(analyzeMessage(under, CAPS).overLineCap, false);
    assert.strictEqual(analyzeMessage(under + '\nLine 12.', CAPS).overLineCap, true);
  });

  test('blank lines do not count toward the line cap', () => {
    const spaced = Array.from({ length: 12 }, (_, i) => `Line ${i}.`).join('\n\n');
    assert.strictEqual(analyzeMessage(spaced, CAPS).lines, 12);
  });
});

describe('analyzeMessage: banned marks', () => {
  test('a semicolon in prose is counted', () => {
    assert.strictEqual(analyzeMessage('It failed; I fixed it.', CAPS).semicolons, 1);
  });

  test('a semicolon inside inline code is not prose', () => {
    assert.strictEqual(analyzeMessage('Run `a=1; b=2` and retry.', CAPS).semicolons, 0);
  });

  test('an aside inside a sentence is counted once per unit', () => {
    assert.strictEqual(analyzeMessage('The build is green (three warnings remain).', CAPS).parenUnits, 1);
    assert.strictEqual(analyzeMessage('One (first) and two (second) in one sentence.', CAPS).parenUnits, 1);
  });

  test('a call in inline code is not an aside', () => {
    assert.strictEqual(analyzeMessage('Call `withConnection(pool)` instead.', CAPS).parenUnits, 0);
  });

  test('a one-character group is not an aside', () => {
    assert.strictEqual(analyzeMessage('The flag (x) is set.', CAPS).parenUnits, 0);
  });
});

describe('analyzeMessage: fenced blocks are Never compress content', () => {
  const msg = [
    'Tests failed.',
    '',
    '```',
    'AssertionError: expected 540 to equal 560; at payroll.test.js:14',
    'a very long quoted failure line that runs far past any fifteen word cap the style could state',
    '```',
    '',
    'Fixed the order.',
  ].join('\n');

  test('a fenced block contributes no sentences and no line count', () => {
    const r = analyzeMessage(msg, CAPS);
    assert.strictEqual(r.units, 2);
    assert.strictEqual(r.overWordCap, 0);
    assert.strictEqual(r.lines, 2);
    assert.strictEqual(r.fencedBlocks, 1);
  });

  test('a semicolon inside quoted output is not a style breach', () => {
    assert.strictEqual(analyzeMessage(msg, CAPS).semicolons, 0);
  });

  test('an unterminated fence still swallows the rest, never half a block', () => {
    const r = analyzeMessage('Here:\n\n```\nraw; output (here)\n', CAPS);
    assert.strictEqual(r.semicolons, 0);
    assert.strictEqual(r.units, 1);
  });
});

describe('analyzeMessage: over-cap bands', () => {
  test('a breach is banded by how far past the cap it went', () => {
    const w = (n) => Array.from({ length: n }, (_, i) => `w${i}`).join(' ') + '.';
    const r = analyzeMessage([w(17), w(24), w(38), w(60)].join('\n'), CAPS);
    assert.deepStrictEqual(r.overBands, { '16-20': 1, '21-30': 1, '31-45': 1, '46+': 1 });
  });
});

describe('capReport: aggregation', () => {
  // Built word by word so the count is the fixture, not an arithmetic guess.
  const long = (n) => Array.from({ length: n }, (_, i) => `w${i}`).join(' ') + '.';

  const records = [
    { arm: 'baseline', task: 'log-triage', finalText: long(20) },
    { arm: 'baseline', task: 'log-triage', finalText: 'Short.' },
    { arm: 'hush', task: 'log-triage', finalText: 'Short and clean.' },
    { arm: 'hush', task: 'noisy-build', finalText: `Also short. ${long(20)}` },
    { arm: 'hush', task: 'noisy-build', error: 'rate limited', finalText: 'ignored' },
    { arm: 'hush', task: 'noisy-build' },
  ];

  test('errored and textless records never reach the numbers', () => {
    const r = capReport(records, CAPS);
    assert.strictEqual(r.runs, 4);
    assert.strictEqual(r.arms.hush.runs, 2);
  });

  test('per-arm counts and rate', () => {
    const r = capReport(records, CAPS);
    assert.strictEqual(r.arms.baseline.overWordCap, 1);
    assert.strictEqual(r.arms.hush.overWordCap, 1);
    assert.strictEqual(r.arms.hush.units, 3);
    assert.ok(Math.abs(r.arms.hush.overWordCapPct - (100 / 3)) < 0.01);
  });

  test('the worst sentence is named with its task', () => {
    const r = capReport(records, CAPS);
    assert.strictEqual(r.arms.hush.worst.task, 'noisy-build');
    assert.strictEqual(r.arms.hush.worst.words, 20);
  });

  test('breaches are attributed to the task that carried them', () => {
    const r = capReport(records, CAPS);
    assert.deepStrictEqual(r.arms.hush.overWordCapByTask, { 'noisy-build': 1 });
  });

  test('the caps used are reported alongside the numbers', () => {
    assert.deepStrictEqual(capReport(records, CAPS).caps, CAPS);
  });
});
