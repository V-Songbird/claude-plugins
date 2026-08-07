'use strict';

// Reading-effort meter (runner/readability.js). All local/pure — no
// `claude` CLI invocation, no cost.
//
// Every expectation here is a LITERAL sample pushed through the shipped
// functions, with the arithmetic worked out by hand where a formula is
// involved. Asking the production regex whether it agrees with itself would
// prove nothing about either.

const { test, describe } = require('node:test');
const assert = require('node:assert');

const { syllables, proseWords, analyzeMessage, readabilityReport, PREAMBLE } =
  require('../runner/readability.js');

describe('syllables: the vowel-group heuristic, pinned by hand', () => {
  test('short words are one syllable', () => {
    for (const w of ['a', 'the', 'cat', 'run']) assert.strictEqual(syllables(w), 1, w);
  });

  test('counts vowel groups in longer words', () => {
    assert.strictEqual(syllables('reader'), 2);
    assert.strictEqual(syllables('message'), 2);
    assert.strictEqual(syllables('important'), 3);
  });

  test('a silent trailing e does not buy a syllable', () => {
    assert.strictEqual(syllables('house'), 1);
    assert.strictEqual(syllables('little'), 2);
  });

  test('never returns zero for a word with letters', () => {
    assert.ok(syllables('rhythm') >= 1);
    assert.ok(syllables('strengths') >= 1);
  });

  test('punctuation and digits do not count as words', () => {
    assert.strictEqual(syllables('---'), 0);
    assert.strictEqual(syllables('42'), 0);
  });
});

describe('proseWords: an identifier is one opaque token', () => {
  test('a backticked path collapses instead of splitting into prose', () => {
    assert.deepStrictEqual(proseWords('Fixed `src/net/retryPolicy.js` today'),
      ['Fixed', 'code', 'today']);
  });

  test('digits are not prose words', () => {
    assert.deepStrictEqual(proseWords('All 214 tests pass'), ['All', 'tests', 'pass']);
  });
});

describe('the formulas are Flesch and Flesch-Kincaid, unmodified', () => {
  // "The cat sat on the mat." — 6 words, 1 sentence, 6 syllables.
  //   ease  = 206.835 - 1.015*6 - 84.6*1        = 116.145
  //   grade = 0.39*6 + 11.8*1 - 15.59           = -1.45
  test('a hand-computed sample lands on the textbook numbers', () => {
    const m = analyzeMessage('The cat sat on the mat.');
    assert.strictEqual(m.sentences, 1);
    assert.strictEqual(m.proseWords, 6);
    assert.ok(Math.abs(m.ease - 116.145) < 0.01, `ease was ${m.ease}`);
    assert.ok(Math.abs(m.grade - -1.45) < 0.01, `grade was ${m.grade}`);
  });

  test('longer words and longer sentences score harder', () => {
    const easy = analyzeMessage('We fixed the bug. The tests pass now.');
    const hard = analyzeMessage(
      'Subsequent instrumentation demonstrated that the intermittent authentication '
      + 'failure originated from a misconfigured connection pooling parameter.');
    assert.ok(hard.ease < easy.ease, `${hard.ease} should be below ${easy.ease}`);
    assert.ok(hard.grade > easy.grade, `${hard.grade} should be above ${easy.grade}`);
    assert.ok(hard.hardWordPct > easy.hardWordPct);
  });

  test('an empty message reports null rather than an impossible score', () => {
    const m = analyzeMessage('');
    assert.strictEqual(m.ease, null);
    assert.strictEqual(m.grade, null);
    assert.strictEqual(m.sentences, 0);
  });
});

describe('fenced code is out of the prose measures but still reported', () => {
  const withCode = analyzeMessage('Run it.\n\n```bash\nnpm test -- auth.spec.ts\n```\n');

  test('the block does not enter the sentence or word counts', () => {
    assert.strictEqual(withCode.sentences, 1);
    assert.deepStrictEqual(proseWords('Run it.'), ['Run', 'it']);
    assert.strictEqual(withCode.proseWords, 2);
  });

  test('carrying something runnable is its own column', () => {
    assert.strictEqual(withCode.hasRunnable, true);
    assert.strictEqual(analyzeMessage('The bug was in the parser.').hasRunnable, false);
  });

  test('a bare identifier is not a command; an inline command is', () => {
    assert.strictEqual(analyzeMessage('Look at `paginate.js`.').hasRunnable, false);
    assert.strictEqual(analyzeMessage('Run `npm test` next.').hasRunnable, true);
  });
});

describe('answerFirst: the openers both sides ban, on the first line only', () => {
  const opens = (s) => analyzeMessage(s).answerFirst;

  test('a preamble opener fails', () => {
    for (const s of ['Great question! The bug is in `paginate.js`.',
      "Let me look at the code.",
      "I'll check the config first.",
      'Sure! Here is the fix.',
      'Looking at your auth flow, the token expires early.']) {
      assert.strictEqual(opens(s), false, s);
    }
  });

  test('an answer opener passes', () => {
    for (const s of ['Fixed the coupon bug.',
      'Run `npm install`, then edit `src/auth.ts:42`.',
      'The token expired one second early.',
      'All 214 tests pass.']) {
      assert.strictEqual(opens(s), true, s);
    }
  });

  test('a closing pleasantry is a different rule and is not scored here', () => {
    assert.strictEqual(opens('Fixed it.\n\nLet me know if you want more.'), true);
  });

  test('the regex is anchored to the start, so a mid-line hit does not count', () => {
    assert.strictEqual(PREAMBLE.test('The fix will let me know sooner.'), false);
  });

  test('a message with no prose line scores false rather than throwing', () => {
    assert.strictEqual(analyzeMessage('```\nnpm test\n```').answerFirst, false);
  });
});

describe('readabilityReport: rolls up per arm, and optionally per segment', () => {
  const records = [
    { arm: 'baseline', task: 't1', segment: 'coding', finalText: 'Great question! The authentication subsystem intermittently rejects credentials.' },
    { arm: 'baseline', task: 't2', segment: 'debugging', finalText: 'Let me explain. The parser mishandles the boundary condition.' },
    { arm: 'hush', task: 't1', segment: 'coding', finalText: 'Fixed the bug. Run `npm test`.' },
    { arm: 'hush', task: 't2', segment: 'debugging', finalText: 'The token expired early. All tests pass.' },
  ];

  test('an arm that opens with the answer every time reads 100%', () => {
    const r = readabilityReport(records);
    assert.strictEqual(r.arms.hush.answerFirstPct, 100);
    assert.strictEqual(r.arms.baseline.answerFirstPct, 0);
  });

  test('the easier arm scores the higher ease and the lower grade', () => {
    const r = readabilityReport(records);
    assert.ok(r.arms.hush.ease > r.arms.baseline.ease);
    assert.ok(r.arms.hush.grade < r.arms.baseline.grade);
  });

  test('errored and textless records are skipped, not scored as empty', () => {
    const r = readabilityReport([...records,
      { arm: 'hush', task: 't3', segment: 'coding', error: 'rate limited' },
      { arm: 'hush', task: 't4', segment: 'coding', finalText: '' }]);
    assert.strictEqual(r.arms.hush.runs, 2);
    assert.strictEqual(r.runs, 4);
  });

  test('--by-segment slices each arm without changing the totals', () => {
    const r = readabilityReport(records, { bySegment: true });
    assert.strictEqual(r.arms.hush.segments.coding.runs, 1);
    assert.strictEqual(r.arms.hush.segments.debugging.runs, 1);
    assert.strictEqual(r.arms.hush.runs, 2);
  });

  test('a record with no segment lands in one named bucket, not undefined', () => {
    const r = readabilityReport([{ arm: 'hush', task: 't', finalText: 'Fixed it.' }], { bySegment: true });
    assert.ok(r.arms.hush.segments.unsegmented);
  });
});
