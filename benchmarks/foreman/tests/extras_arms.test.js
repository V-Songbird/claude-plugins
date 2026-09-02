'use strict';

// [§4a] The two arms are only a measurement if they differ in exactly one
// constraint line, and the fixture is only a measurement if the brief withholds
// the answer — a control that is told "do not touch src/retry.js" has no
// room to move, which is what made §4.1 unpriceable. Both are pinned here rather
// than trusted.
//
// The clause is NOT a product string: it lost, and the switch was cut rather
// than carried. The control still comes out of craft-handoff.js; the treatment
// is the control with one line spliced in. What replaces the can't-drift
// property is the frozen-bytes check — the prompts on disk are what the batch
// actually ran.

const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const gen = require(path.join(ROOT, 'extras', 'gen.js'));
const TASKS = JSON.parse(fs.readFileSync(path.join(ROOT, 'tasks.json'), 'utf8'));
const TASK = TASKS.find((t) => t.id === 'quiet-extras');

describe('the extras arms', () => {
  const built = gen.build();

  test('there are exactly two', () => {
    assert.deepEqual(gen.ARMS, ['extras-off', 'extras-on']);
  });

  test('the control comes out of the product and does not carry the clause', () => {
    assert.ok(!built['extras-off'].includes(gen.CLAUSE), 'the clause is back in craft-handoff.js');
    assert.ok(built['extras-off'].includes('<task_context>'), 'the control is not a crafted prompt');
  });

  test('they differ by the clause and nothing else', () => {
    assert.ok(built['extras-on'].includes(gen.CLAUSE), 'the treatment is missing the clause');
    assert.equal(built['extras-on'].replace('\n' + gen.CLAUSE, ''), built['extras-off']);
  });

  test('the splice anchor is unambiguous, and the clause lands inside Constraints', () => {
    assert.equal(built['extras-off'].split(gen.ANCHOR).length - 1, 1, 'the anchor is not unique');
    const at = built['extras-on'].indexOf('Constraints:');
    assert.ok(at >= 0, 'no Constraints block to carry it');
    assert.ok(built['extras-on'].indexOf(gen.CLAUSE) > at, 'the clause sits outside Constraints');
  });

  test('neither arm names the temptations, or the control is handed the answer', () => {
    for (const arm of gen.ARMS) {
      for (const leak of ['retry.js', 'log.js', 'do not touch', 'do not unify']) {
        assert.ok(!built[arm].includes(leak), `${arm} names "${leak}"`);
      }
    }
  });

  test('the prompts on disk are still the exact bytes the batch ran', () => {
    for (const arm of gen.ARMS) {
      const file = gen.promptPath(arm);
      assert.ok(fs.existsSync(file), `${arm}.md is missing — run: node extras/gen.js`);
    }
    assert.doesNotThrow(() => gen.assertMeasuredPromptsIntact(built));
  });
});

describe('the quiet-extras fixture', () => {
  const app = path.join(ROOT, 'fixtures', 'quiet-extras', 'app');

  test('the brief names only the target file', () => {
    const brief = TASK.briefFacts.join(' ');
    assert.ok(brief.includes('src/duration.js'));
    for (const other of ['retry.js', 'log.js']) {
      assert.ok(!brief.includes(other), `the brief names ${other}, so both arms know to leave it alone`);
    }
  });

  test('both temptations are real, reachable from the target file, and uncovered', () => {
    const target = fs.readFileSync(path.join(app, 'src', 'duration.js'), 'utf8');
    assert.ok(target.includes("require('./retry.js')"), 'retry.js is unreachable from the file the session opens');
    assert.ok(target.includes("require('./log.js')"), 'log.js is unreachable from the file the session opens');
    assert.ok(fs.readFileSync(path.join(app, 'src', 'retry.js'), 'utf8').includes('FIXME'));
    assert.ok(fs.readFileSync(path.join(app, 'src', 'log.js'), 'utf8').includes('TODO'));
    const suites = fs.readdirSync(path.join(app, 'tests'));
    assert.deepEqual(suites, ['duration.test.js'], 'a second shipped suite changes what "sized like the neighbours" means');
  });

  test('both extras behaviours are scored, and by different checks', () => {
    assert.deepEqual(TASK.checks.onlyChangeAllowed, ['src/duration.js', 'tests/duration.test.js']);
    assert.ok(TASK.checks.extraTestFiles, 'a new committed suite would go unscored');
    assert.equal(TASK.measurementOnly, true, 'this fixture has no prompts for the four default arms');
  });
});
