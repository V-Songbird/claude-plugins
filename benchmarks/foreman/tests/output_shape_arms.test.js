'use strict';

// [§4.2] The two output-shape arms are only a measurement if they differ in
// exactly one thing. Both are produced by running the product's own
// craft-handoff.js, so neither can drift from what foreman emits — but nothing
// stops a future change from making the difference two things instead of one,
// and nothing downstream would notice.

const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const gen = require(path.join(ROOT, 'outputshape', 'gen.js'));
const TASKS = JSON.parse(fs.readFileSync(path.join(ROOT, 'tasks.json'), 'utf8'))
  .filter((t) => !t.measurementOnly);
const ARMS = JSON.parse(fs.readFileSync(path.join(ROOT, 'config.json'), 'utf8'));

describe('the output-shape arms', () => {
  const built = gen.build();

  test('there are exactly two, and only one of them sets the switch', () => {
    assert.deepEqual(Object.keys(gen.ARMS), ['shape-off', 'shape-on']);
    assert.deepEqual(gen.ARMS['shape-off'], {}, 'the control must set nothing');
    assert.deepEqual(gen.ARMS['shape-on'], { FOREMAN_STANDARD_OUTPUT_SHAPE: '1' });
  });

  for (const task of TASKS) {
    test(`${task.id}: the arms differ by <output_format> and nothing else`, () => {
      const off = built[task.id]['shape-off'];
      const on = built[task.id]['shape-on'];
      assert.ok(!off.includes('<output_format>'), 'the control already carries the block');
      assert.ok(on.includes('<output_format>'), 'the treatment is missing the block');
      const stripped = on.replace(/\n*<output_format>[\s\S]*?<\/output_format>/, '');
      assert.equal(stripped.trim(), off.trim());
    });

    test(`${task.id}: both arms carry the same verification command`, () => {
      for (const arm of ['shape-off', 'shape-on']) {
        assert.ok(
          built[task.id][arm].includes(task.testCommand),
          `${arm} does not cite ${task.testCommand}`
        );
      }
    });

    test(`${task.id}: neither arm leaks a file the task is graded on leaving alone`, () => {
      for (const untouched of task.checks.unchanged || []) {
        for (const arm of ['shape-off', 'shape-on']) {
          assert.ok(
            !built[task.id][arm].includes(untouched),
            `${arm} names ${untouched}, so the trap rides into a measurement about the final message`
          );
        }
      }
    });

    test(`${task.id}: the frozen prompts on disk match what the product emits now`, () => {
      for (const arm of ['shape-off', 'shape-on']) {
        const file = gen.promptPath(task, arm);
        assert.ok(fs.existsSync(file), `${arm}.md is missing — run: node outputshape/gen.js`);
        assert.equal(
          fs.readFileSync(file, 'utf8'),
          built[task.id][arm],
          `${arm}.md drifted — run: node outputshape/gen.js`
        );
      }
    });
  }

  test('the arms are not in the default matrix, so an ordinary run never pays for them', () => {
    for (const arm of ['shape-off', 'shape-on']) {
      assert.ok(!ARMS.arms.includes(arm), `${arm} joined config.json's default arms`);
    }
  });
});
