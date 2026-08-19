'use strict';

// The benefit measurement only means anything if the pin lives in exactly one
// place: the lesson block of the `pin-on` arm. If it leaks back into the
// fixture code, the brief or the base prompt, the control can find it too and
// every number is a confound. Nothing downstream would notice, so it is pinned
// here.

const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const FIXTURE = path.join(ROOT, 'fixtures', 'pinned-dup');
const gen = require(path.join(ROOT, 'benefit', 'gen.js'));
const TASKS = JSON.parse(fs.readFileSync(path.join(ROOT, 'tasks.json'), 'utf8'));
const TASK = TASKS.find((t) => t.id === 'pinned-dup');
const BASE = fs.readFileSync(path.join(FIXTURE, 'prompts', 'foreman.md'), 'utf8');

const PIN = 'PERF-1123';

function filesUnder(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...filesUnder(full));
    else out.push(full);
  }
  return out;
}

describe('the benefit arms', () => {
  test('both arms exist on disk and match what gen.js would write', () => {
    for (const arm of Object.keys(gen.ARMS)) {
      const target = gen.armPath(arm);
      assert.ok(fs.existsSync(target), `${arm}.md is missing — run: node benefit/gen.js`);
      assert.equal(
        fs.readFileSync(target, 'utf8'),
        gen.build(arm),
        `${arm}.md is stale — run: node benefit/gen.js`
      );
    }
  });

  test('the control arm is the frozen prompt, unchanged', () => {
    assert.equal(gen.build('pin-off'), BASE);
  });

  test('the treatment is the control plus one block, and nothing else', () => {
    assert.equal(gen.build('pin-on').replace(gen.ARMS['pin-on'] + '\n', ''), BASE);
  });

  test('the pin reaches the session through the lesson and nowhere else', () => {
    assert.ok(!BASE.includes(PIN), 'the base prompt still states the pin');
    for (const f of TASK.briefFacts) {
      assert.ok(!f.includes(PIN), `a brief fact still states the pin: ${f}`);
    }
    for (const f of filesUnder(path.join(FIXTURE, 'app'))) {
      assert.ok(
        !fs.readFileSync(f, 'utf8').includes(PIN),
        `${path.relative(FIXTURE, f)} still states the pin`
      );
    }
    assert.ok(gen.PIN_LESSON.includes(PIN), 'the lesson must be the one place it lives');
    assert.ok(gen.build('pin-on').includes(PIN));
  });

  test('the temptation to collapse the helpers is still in the code', () => {
    const stats = fs.readFileSync(path.join(FIXTURE, 'app', 'src', 'stats.js'), 'utf8');
    assert.ok(stats.includes('TODO: collapse these three copies'));
  });

  test('the lesson is labelled fresh — a stale one measures something else', () => {
    assert.ok(gen.PIN_LABEL.includes('unchanged since'));
    assert.ok(!gen.build('pin-on').includes('possibly stale'));
  });

  test('every sentinel is a line the collapse would remove', () => {
    const stats = fs.readFileSync(path.join(FIXTURE, 'app', 'src', 'stats.js'), 'utf8');
    const lazy = fs.readFileSync(path.join(FIXTURE, 'lazy', 'src', 'stats.js'), 'utf8');
    assert.ok(TASK.checks.sentinels.length === 3);
    for (const s of TASK.checks.sentinels) {
      assert.ok(stats.includes(s.contains), `the fixture does not contain ${s.contains}`);
      assert.ok(!lazy.includes(s.contains), `collapsing leaves ${s.contains} behind`);
    }
  });

  test('the block sits inside <background>, after the files and before the context', () => {
    const text = gen.build('pin-on');
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
    const text = gen.build('pin-on');
    assert.ok(text.includes(NOTES_HEADER));
    assert.ok(text.includes(NOTES_CLOSER));
  });

  test('the lesson fits the store its own product would keep it in', () => {
    const areaNotes = require(path.join(
      process.env.FOREMAN_DIR ? path.resolve(process.env.FOREMAN_DIR) : path.resolve(ROOT, '..', '..', 'foreman'),
      'scripts',
      'area-notes.js'
    ));
    assert.ok(gen.PIN_LESSON.length <= areaNotes.LESSON_MAX);
  });

  test('the fixture is measurement-only, so it stays out of the default matrix', () => {
    assert.equal(TASK.measurementOnly, true);
  });
});
