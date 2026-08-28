'use strict';
// The usefulness scorer: it counts what a message gives the eye, and it reads
// those counts against a band rather than treating more as better.
//
// Every sample below is a literal message, not a generated one, so a change to
// the regexes shows up here as a changed number rather than as two sides of the
// same bug agreeing with each other.

const { describe, test } = require('node:test');
const assert = require('node:assert');

const { analyzeMessage, structureReport, BANDS } = require('../runner/structure.js');

const PLAIN = 'Fixed the login crash. The token was null.';

const SHAPED = [
  '**Build passes now.** Two real bugs from the bump.',
  '',
  '| File | Bug | Fix |',
  '|---|---|---|',
  '| [options.js:6](src/core/options.js:6) | `retries` renamed | Read either key |',
  '| [retryPolicy.js:7](src/net/retryPolicy.js:7) | Unset flag threw | Treat as `false` |',
  '',
  'The 8 remaining warnings are deprecations.',
].join('\n');

describe('analyzeMessage: what the message gives the eye', () => {
  test('a plain message scores zero on every affordance', () => {
    const m = analyzeMessage(PLAIN);
    assert.strictEqual(m.bold, 0);
    assert.strictEqual(m.links, 0);
    assert.strictEqual(m.codeSpans, 0);
    assert.strictEqual(m.tableRows, 0);
    assert.strictEqual(m.hasTable, false);
    assert.strictEqual(m.bullets, 0);
    assert.strictEqual(m.headings, 0);
    assert.strictEqual(m.blocks, 1);
  });

  test('a shaped message counts each affordance once', () => {
    const m = analyzeMessage(SHAPED);
    assert.strictEqual(m.bold, 1);
    assert.strictEqual(m.links, 2);
    assert.strictEqual(m.codeSpans, 2);
    assert.strictEqual(m.tableRows, 4);
    assert.strictEqual(m.hasTable, true);
    assert.strictEqual(m.blocks, 3);
  });

  test('an empty or missing message does not throw', () => {
    for (const input of ['', null, undefined]) {
      const m = analyzeMessage(input);
      assert.strictEqual(m.bold, 0);
      assert.strictEqual(m.blocks, 0);
      assert.strictEqual(m.hasTable, false);
    }
  });
});

describe('fenced blocks are content, not signposts', () => {
  const fenced = ['**Green.**', '', '```js', '// **not bold**, `not a span`', 'const x = 1;', '```'].join('\n');

  test('marks inside a fence are excluded from the prose counts', () => {
    const m = analyzeMessage(fenced);
    assert.strictEqual(m.bold, 1, 'the bold inside the fence must not count');
    assert.strictEqual(m.codeSpans, 0, 'the span inside the fence must not count');
  });

  test('carrying a fence is reported as its own column', () => {
    assert.strictEqual(analyzeMessage(fenced).hasFence, true);
    assert.strictEqual(analyzeMessage(PLAIN).hasFence, false);
  });
});

describe('a link that carries the line is worth more than one that does not', () => {
  test('an anchored target counts as both linked and anchored', () => {
    const m = analyzeMessage('See [options.js:6](src/core/options.js:6).');
    assert.strictEqual(m.links, 1);
    assert.strictEqual(m.anchoredLinks, 1);
  });

  test('a bare path counts as a link but not as an anchor', () => {
    const m = analyzeMessage('See [the options file](src/core/options.js).');
    assert.strictEqual(m.links, 1);
    assert.strictEqual(m.anchoredLinks, 0);
  });

  test('an arm that never linked reports null, not zero', () => {
    const r = structureReport([{ arm: 'hush', finalText: PLAIN }]);
    assert.strictEqual(r.arms.hush.anchoredPct, null);
  });

  test('the share is over links, not over runs', () => {
    const r = structureReport([
      { arm: 'hush', finalText: 'See [a](src/a.js:1) and [b](src/b.js).' },
      { arm: 'hush', finalText: PLAIN },
    ]);
    assert.strictEqual(r.arms.hush.anchoredPct, 50);
  });
});

describe('bands, not maxima', () => {
  test('one bold mark is in band and eight is not', () => {
    assert.strictEqual(analyzeMessage('**one**').boldInBand, true);
    assert.strictEqual(analyzeMessage(Array(8).fill('**mark**').join(' ')).boldInBand, false);
  });

  test('zero bold marks is also out of band', () => {
    assert.strictEqual(analyzeMessage(PLAIN).boldInBand, false);
  });

  test('the band edges are inclusive on both sides', () => {
    const [lo, hi] = BANDS.bold;
    assert.strictEqual(analyzeMessage(Array(lo).fill('**m**').join(' ')).boldInBand, true);
    assert.strictEqual(analyzeMessage(Array(hi).fill('**m**').join(' ')).boldInBand, true);
    assert.strictEqual(analyzeMessage(Array(hi + 1).fill('**m**').join(' ')).boldInBand, false);
  });
});

describe('structureReport: per arm, and honest about what it skipped', () => {
  const records = [
    { arm: 'hush', task: 't1', segment: 'noisy-output', finalText: SHAPED },
    { arm: 'hush', task: 't2', segment: 'noisy-output', finalText: PLAIN },
    { arm: 'baseline', task: 't1', segment: 'noisy-output', finalText: PLAIN },
    { arm: 'baseline', task: 't2', segment: 'search-heavy', finalText: PLAIN },
  ];

  test('averages per arm, and rates carry their denominator', () => {
    const r = structureReport(records);
    assert.strictEqual(r.runs, 4);
    assert.strictEqual(r.arms.hush.runs, 2);
    assert.strictEqual(r.arms.hush.bold, 0.5);
    assert.strictEqual(r.arms.hush.tablePct, 50);
    assert.strictEqual(r.arms.hush.linkedPct, 50);
    assert.strictEqual(r.arms.baseline.bold, 0);
    assert.strictEqual(r.arms.baseline.tablePct, 0);
  });

  test('errored runs and runs with no final message are skipped, not zeroed', () => {
    const r = structureReport([
      ...records,
      { arm: 'hush', task: 't3', error: 'rate limited' },
      { arm: 'hush', task: 't4', finalText: '' },
    ]);
    assert.strictEqual(r.arms.hush.runs, 2, 'a skipped run must not drag the mean toward zero');
    assert.strictEqual(r.arms.hush.bold, 0.5);
  });

  test('--by-segment slices without changing the totals', () => {
    const r = structureReport(records, { bySegment: true });
    assert.strictEqual(r.arms.baseline.segments['noisy-output'].runs, 1);
    assert.strictEqual(r.arms.baseline.segments['search-heavy'].runs, 1);
    assert.strictEqual(r.arms.hush.segments['noisy-output'].runs, 2);
  });
});
