'use strict';

// Retention meter (runner/retention.js). All local/pure — no judge calls,
// no cost. Literal samples through the shipped functions; the judge itself
// is a paid model and is spot-checked by hand, not unit-tested.

const { test, describe } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { judgePrompt, parseVerdicts, retentionReport, keysHash, PROMPT_VERSION } = require('../runner/retention.js');

describe('retention keys file', () => {
  const keys = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'retention-keys.json'), 'utf8')).tasks;
  const tasks = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'tasks.json'), 'utf8'));

  test('every suite task has a key list with at least two items', () => {
    for (const t of tasks) {
      assert.ok(Array.isArray(keys[t.id]), `${t.id} has no key list`);
      assert.ok(keys[t.id].length >= 2, `${t.id} has under two items`);
    }
  });

  test('no key list names an arm or a plugin', () => {
    // Arm names would unblind the judge. Rival arm names are checked by the
    // same rule — spelled generically here so no rival is named in this repo.
    const banned = /hush|baseline|plugin|rival|arm\b|style/i;
    for (const [task, items] of Object.entries(keys)) {
      for (const item of items) assert.ok(!banned.test(item), `${task}: "${item}"`);
    }
  });
});

describe('judgePrompt', () => {
  const prompt = judgePrompt('The build is green now.', ['the build passes', 'the cause is named']);

  test('carries the report and every numbered claim', () => {
    assert.ok(prompt.includes('The build is green now.'));
    assert.ok(prompt.includes('1. the build passes'));
    assert.ok(prompt.includes('2. the cause is named'));
  });

  test('stays blind — no arm, plugin, or style names', () => {
    assert.ok(!/hush|baseline|rival|arm\b|style/i.test(prompt));
  });
});

describe('parseVerdicts', () => {
  test('reads the documented shape, in any wrapper prose', () => {
    const text = 'Here you go:\n{"verdicts":[{"item":1,"present":true},{"item":2,"present":false}]}';
    assert.deepStrictEqual(parseVerdicts(text, 2), [true, false]);
  });

  test('a skipped item is an error, not a silent false', () => {
    assert.throws(() => parseVerdicts('{"verdicts":[{"item":1,"present":true}]}', 2),
      /skipped an item/);
  });

  test('a reply with no JSON is an error', () => {
    assert.throws(() => parseVerdicts('I could not decide.', 1), /no JSON/);
  });

  test('present must be literally true — "yes" or 1 count as false', () => {
    const text = '{"verdicts":[{"item":1,"present":"yes"},{"item":2,"present":1}]}';
    assert.deepStrictEqual(parseVerdicts(text, 2), [false, false]);
  });
});

describe('retentionReport', () => {
  test('hits over total per arm, worked by hand', () => {
    const report = retentionReport([
      { arm: 'a', task: 't', key: 'k1', verdicts: [true, true, false] },
      { arm: 'a', task: 't', key: 'k2', verdicts: [true, false, false] },
      { arm: 'b', task: 't', key: 'k3', verdicts: [true, true, true] },
    ]);
    assert.strictEqual(report.a.hits, 3);
    assert.strictEqual(report.a.total, 6);
    assert.strictEqual(report.a.pct, 50);
    assert.strictEqual(report.b.pct, 100);
  });

  test('misses land in the per-item table under task#index', () => {
    const report = retentionReport([
      { arm: 'a', task: 'log-triage', key: 'k', verdicts: [false, true] },
    ]);
    assert.deepStrictEqual(report.a.byItem, { 'log-triage#1': 1 });
  });
});

test('keysHash changes when an item changes', () => {
  assert.notStrictEqual(keysHash(['a', 'b']), keysHash(['a', 'c']));
});

// The cache key carries a prompt version so a reworded prompt re-judges
// instead of reusing the old wording's verdicts. It is empty on purpose:
// every verdict cached under the original prompt stays valid.
test('the prompt version is empty, so the cached verdicts stay valid', () => {
  assert.strictEqual(PROMPT_VERSION, '');
});
