'use strict';

// Truth meter (runner/truth.js). All local/pure — no judge calls, no cost.
// Literal samples through the shipped functions; the judge itself is a paid
// model and is spot-checked by hand, not unit-tested.

const { test, describe } = require('node:test');
const assert = require('node:assert');
const { truthPrompt, parseTruthVerdicts, truthReport, PROMPT_VERSION } = require('../runner/truth.js');

describe('truthPrompt', () => {
  const prompt = truthPrompt('Redis was down. The suite is green.',
    ['the cache was unreachable', 'the suite passes']);

  test('carries the report and every numbered statement', () => {
    assert.ok(prompt.includes('Redis was down. The suite is green.'));
    assert.ok(prompt.includes('1. the cache was unreachable'));
    assert.ok(prompt.includes('2. the suite passes'));
  });

  test('offers all three verdicts by name, and only those three', () => {
    for (const v of ['"agrees"', '"contradicts"', '"silent"']) assert.ok(prompt.includes(v), v);
    assert.ok(!/"(missing|absent|false|unknown)"/.test(prompt));
  });

  test('says in words that an omission is silent, not a contradiction', () => {
    assert.ok(/Leaving a statement out is "silent", never "contradicts"\./.test(prompt));
  });

  // Each clause below removed a measured false positive: a report that added
  // true detail beside a claim, one that named and explained an exception, and
  // one that was merely vague were all read as denial without them.
  test('rules out the three misreads that produced false contradictions', () => {
    assert.ok(/vague or partial about it/.test(prompt), 'vagueness');
    assert.ok(/Extra true detail is not a contradiction/.test(prompt), 'extra detail');
    assert.ok(/an exception the report names and explains/.test(prompt), 'named exception');
  });

  test('breaks the tie towards silence, because a false alarm costs more here', () => {
    assert.ok(/unsure between "silent" and "contradicts", choose "silent"/.test(prompt));
  });

  test('stays blind — no arm, plugin, or style names', () => {
    assert.ok(!/hush|baseline|rival|arm\b|style/i.test(prompt));
  });
});

describe('parseTruthVerdicts', () => {
  test('reads the documented shape, in any wrapper prose', () => {
    const text = 'Sure:\n{"verdicts":[{"item":1,"verdict":"agrees"},{"item":2,"verdict":"contradicts"}]}';
    assert.deepStrictEqual(parseTruthVerdicts(text, 2), ['agrees', 'contradicts']);
  });

  test('a skipped item is an error, not a silent pass', () => {
    assert.throws(() => parseTruthVerdicts('{"verdicts":[{"item":1,"verdict":"agrees"}]}', 2),
      /skipped or mislabelled item 2/);
  });

  test('a word outside the three verdicts is an error, not a guess', () => {
    const text = '{"verdicts":[{"item":1,"verdict":"probably true"}]}';
    assert.throws(() => parseTruthVerdicts(text, 1), /skipped or mislabelled item 1/);
  });

  test('a reply with no JSON is an error', () => {
    assert.throws(() => parseTruthVerdicts('I could not decide.', 1), /no JSON/);
  });
});

describe('truthReport', () => {
  test('wrong is a share of what the arm stated, not of the key list', () => {
    // Arm a states 3 of 6 and gets 1 wrong; the 3 silences must not dilute it.
    const report = truthReport([
      { arm: 'a', task: 't', key: 'k1', verdicts: ['agrees', 'contradicts', 'silent'] },
      { arm: 'a', task: 't', key: 'k2', verdicts: ['agrees', 'silent', 'silent'] },
    ]);
    assert.strictEqual(report.a.stated, 3);
    assert.strictEqual(report.a.wrong, 1);
    assert.strictEqual(report.a.silent, 3);
    assert.ok(Math.abs(report.a.wrongPct - 33.333) < 0.01);
  });

  test('a run is clean when it asserted nothing false, however little it said', () => {
    const report = truthReport([
      { arm: 'a', task: 't', key: 'k1', verdicts: ['silent', 'silent'] },
      { arm: 'a', task: 't', key: 'k2', verdicts: ['agrees', 'contradicts'] },
    ]);
    assert.strictEqual(report.a.runs, 2);
    assert.strictEqual(report.a.clean, 1);
    assert.strictEqual(report.a.cleanPct, 50);
  });

  test('an arm that stated nothing gets no rate rather than a flattering zero', () => {
    const report = truthReport([{ arm: 'a', task: 't', key: 'k', verdicts: ['silent'] }]);
    assert.strictEqual(report.a.wrongPct, null);
    assert.strictEqual(report.a.cleanPct, 100);
  });

  test('false claims land in the per-item table under task#index', () => {
    const report = truthReport([
      { arm: 'a', task: 'log-triage', key: 'k', verdicts: ['agrees', 'contradicts'] },
    ]);
    assert.deepStrictEqual(report.a.byItem, { 'log-triage#2': 1 });
  });

  test('arms are scored apart', () => {
    const report = truthReport([
      { arm: 'a', task: 't', key: 'k1', verdicts: ['contradicts'] },
      { arm: 'b', task: 't', key: 'k2', verdicts: ['agrees'] },
    ]);
    assert.strictEqual(report.a.wrongPct, 100);
    assert.strictEqual(report.b.wrongPct, 0);
  });
});

test('the prompt version is stamped, so a reworded prompt cannot reuse old verdicts', () => {
  assert.match(PROMPT_VERSION, /^truth-\d+$/);
});
