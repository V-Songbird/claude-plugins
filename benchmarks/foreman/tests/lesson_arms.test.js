'use strict';

// The P2 arms are only a measurement if they differ in exactly one thing. A
// second difference — a reworded rule, a dropped guardrail block, an extra
// hint — makes every number a confound, and nothing downstream would notice.
// So the invariants are pinned here rather than trusted.

const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const gen = require(path.join(ROOT, 'lessons', 'gen.js'));
const BASE = fs.readFileSync(
  path.join(ROOT, 'fixtures', 'moved-file', 'prompts', 'foreman.md'),
  'utf8'
);

const ARM_NAMES = Object.keys(gen.ARMS);

function built(arm) {
  return gen.build(arm);
}

describe('P2 lesson arms', () => {
  test('the four arms exist on disk and match what gen.js would write', () => {
    for (const arm of ARM_NAMES) {
      const target = gen.armPath(arm);
      assert.ok(fs.existsSync(target), `${arm}.md is missing — run: node lessons/gen.js`);
      assert.equal(
        fs.readFileSync(target, 'utf8'),
        built(arm),
        `${arm}.md is stale — run: node lessons/gen.js`
      );
    }
  });

  test('the control arm is the frozen prompt, unchanged', () => {
    assert.equal(built('lessons-control'), BASE);
  });

  test('every other arm is the control plus one block, and nothing else', () => {
    for (const arm of ARM_NAMES) {
      if (arm === 'lessons-control') continue;
      const text = built(arm);
      const added = text.replace(gen.ARMS[arm] + '\n', '');
      assert.equal(added, BASE, `${arm} differs from the control in more than its lesson block`);
    }
  });

  test('the graded arm labels its staleness and the unlabeled arm does not', () => {
    const graded = built('lessons-graded');
    const unlabeled = built('lessons-unlabeled');
    assert.ok(graded.includes(gen.STALE_LABEL));
    assert.ok(!unlabeled.includes(gen.STALE_LABEL));
    assert.ok(!unlabeled.includes('possibly stale'), 'the harm arm must carry no freshness signal');
  });

  test('both stale arms carry the identical claim — only the label moves', () => {
    assert.ok(built('lessons-graded').includes(gen.STALE_LESSON));
    assert.ok(built('lessons-unlabeled').includes(gen.STALE_LESSON));
  });

  test('the stale claim names the decoy file, which is what makes it a test', () => {
    assert.ok(gen.STALE_LESSON.includes('src/parser.js'));
    assert.ok(!gen.STALE_LESSON.includes('src/tokenizer.js'));
  });

  test('the block sits inside <background>, after the files and before the context', () => {
    const text = built('lessons-fresh');
    const files = text.indexOf('</relevant_files>');
    const lesson = text.indexOf('Lessons recorded by earlier closed tasks');
    const context = text.indexOf('<context>');
    assert.ok(files < lesson && lesson < context, 'the block must land where craft-handoff puts it');
  });

  test('the header and closer come from the plugin, not a second copy here', () => {
    const foremanDir = process.env.FOREMAN_DIR
      ? path.resolve(process.env.FOREMAN_DIR)
      : path.resolve(ROOT, '..', '..', 'foreman');
    const { NOTES_HEADER, NOTES_CLOSER } = require(path.join(foremanDir, 'scripts', 'craft-handoff.js'));
    const text = built('lessons-fresh');
    assert.ok(text.includes(NOTES_HEADER));
    assert.ok(text.includes(NOTES_CLOSER));
  });
});
