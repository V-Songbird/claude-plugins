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
  test('every arm exists on disk and matches what gen.js would write', () => {
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

  test('every treatment is the control plus one block, and nothing else', () => {
    for (const arm of Object.keys(gen.ARMS)) {
      if (arm === 'pin-off') continue;
      assert.equal(
        gen.build(arm).replace(gen.ARMS[arm] + '\n', ''),
        BASE,
        `${arm} differs from the control in more than its lesson block`
      );
    }
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
    const ledger = require(path.join(
      process.env.FOREMAN_DIR ? path.resolve(process.env.FOREMAN_DIR) : path.resolve(ROOT, '..', '..', 'foreman'),
      'scripts',
      'ledger.js'
    ));
    assert.ok(gen.PIN_LESSON.length <= ledger.LESSON_MAX);
  });

  test('the fixture is measurement-only, so it stays out of the default matrix', () => {
    assert.equal(TASK.measurementOnly, true);
  });
});

// The mirror arm. `pin-on` proved a correct lesson moves the outcome, so the
// same channel has to be assumed to carry a wrong one just as hard — and
// nothing in the product can detect that case, because the staleness resolver
// answers "have the files changed", never "was the claim ever true".
describe('the wrong-lesson arm', () => {
  test('is the same block shape as the true one — only the claim differs', () => {
    const right = gen.ARMS['pin-on'];
    const wrong = gen.ARMS['pin-wrong'];
    const strip = (text, lesson, labelText) => text.replace(`- ${lesson} ${labelText} `, '- ');
    assert.equal(
      strip(wrong, gen.WRONG_LESSON, gen.WRONG_LABEL),
      strip(right, gen.PIN_LESSON, gen.PIN_LABEL),
      'the arms differ by more than the lesson line'
    );
  });

  test('claims the same freshness the true lesson does', () => {
    assert.ok(gen.WRONG_LABEL.includes('unchanged since'));
    assert.doesNotMatch(gen.build('pin-wrong'), /possibly stale/);
  });

  test('names a different entry and ticket, so nothing but the claim tells them apart', () => {
    assert.notEqual(gen.WRONG_LABEL, gen.PIN_LABEL);
    assert.doesNotMatch(gen.WRONG_LESSON, /PERF-1123/);
  });

  test('does not carry the true pin, which would confound the helpers half', () => {
    assert.doesNotMatch(gen.build('pin-wrong'), /do not unify them/);
    assert.doesNotMatch(gen.WRONG_LESSON, /p50|p90|p99/);
  });

  test('pins the exact thing the task was sent to change, so the two conflict', () => {
    assert.match(gen.WRONG_LESSON, /median\(\)/);
    assert.match(gen.WRONG_LESSON, /do not change it/);
    assert.match(BASE, /Fix the even-length branch of median\(\)/);
  });

  test('is falsifiable by the fixture itself — the shipped suite covers the branch', () => {
    const suite = fs.readFileSync(
      path.join(FIXTURE, 'app', 'tests', 'stats.test.js'),
      'utf8'
    );
    assert.match(suite, /median of even-length input averages the middle pair/);
  });

  test('the runner knows every arm, or the batch cannot be launched', () => {
    const run = fs.readFileSync(path.join(ROOT, 'runner', 'run.js'), 'utf8');
    for (const arm of Object.keys(gen.ARMS)) {
      assert.ok(run.includes(`'${arm}': { prompt: '${arm}'`), `run.js has no ${arm} arm`);
    }
  });
});

const FOREMAN_DIR = process.env.FOREMAN_DIR
  ? path.resolve(process.env.FOREMAN_DIR)
  : path.resolve(ROOT, '..', '..', 'foreman');

// The chain arms: the block craft-handoff.js builds from git history instead
// of a recorded lesson. When the 2026-09-05 batch ran, the line carried each
// entry's why and so the same pin as pin-on; entry 290 cut the why, so the arm
// now carries the entry's id and title only and the pin does not reach the
// session through it. The arm tracks the product's real shape, not the
// measured one — re-running it asks a different question.
describe('the chain arms', () => {
  const { CHAIN_HEADER } = require(path.join(FOREMAN_DIR, 'scripts', 'craft-handoff.js'));

  test('the control is the frozen prompt and the treatment is it plus the chain block only', () => {
    assert.equal(gen.build('chain-off'), BASE);
    assert.equal(gen.build('chain-on').replace(gen.ARMS['chain-on'] + '\n', ''), BASE);
  });

  test("the block is the product's own header plus one line in its own shape", () => {
    assert.ok(gen.ARMS['chain-on'].startsWith(`${CHAIN_HEADER}\n`));
    assert.equal(gen.ARMS['chain-on'].split('\n').length, 2, 'one symbol, one line');
    assert.match(gen.CHAIN_LINE, /^- p50 \(src\/stats\.js\): shaped by \d{3} [^—]+$/);
    assert.ok(!gen.CHAIN_LINE.includes(' — '), 'the product carries no why on a chain line since entry 290');
    assert.ok(!gen.CHAIN_LINE.includes('…'), 'the title sits under the product cut, so nothing is elided');
    assert.ok(gen.CHAIN_ENTRY_TITLE.length <= 40);
  });

  test('the pin no longer reaches the session through the chain, and no lesson block rides along', () => {
    assert.ok(!gen.build('chain-off').includes(PIN));
    assert.ok(!gen.build('chain-on').includes(PIN), 'a title-only chain line cannot carry the ticket');
    assert.ok(!gen.build('chain-on').includes('Lessons recorded'), 'no lesson block rides along');
  });

  test('the block sits where craft-handoff puts it: after the files, before the context', () => {
    const text = gen.build('chain-on');
    const files = text.indexOf('</relevant_files>');
    const chain = text.indexOf(CHAIN_HEADER);
    const context = text.indexOf('<context>');
    assert.ok(files < chain && chain < context);
  });
});

// The uncheckable-lesson arms. The wrong-lesson arm handed the session a test
// that refuted the false claim; these hand it nothing. Same app, opposite
// truth, pin-on's exact block.
describe('the uncheckable-lesson arms', () => {
  const UTASK = TASKS.find((t) => t.id === 'unpinned-dup');
  const read = (p) => fs.readFileSync(p, 'utf8');

  test('the task runs on the pinned-dup fixture itself — same app, same prompt, opposite truth', () => {
    assert.equal(UTASK.fixture, 'pinned-dup');
    assert.equal(UTASK.solutionDir, 'lazy', "pinned-dup's lazy overlay is this task's solution");
    assert.equal(UTASK.selfcheckLazy.dir, 'solution', "and pinned-dup's solution is this task's lazy path");
  });

  test("the served block is pin-on's block, verbatim, and the control carries none", () => {
    assert.equal(gen.ARMS['unpin-wrong'], gen.ARMS['pin-on']);
    assert.equal(gen.ARMS['unpin-off'], null);
    assert.equal(gen.build('unpin-off'), BASE);
  });

  test('the task asks for the very collapse the lesson forbids', () => {
    assert.match(BASE, /collapse any obvious copy-paste duplication/);
    assert.match(gen.PIN_LESSON, /do not unify them/);
  });

  test('nothing in the fixture can refute the claim — no ticket, no test on the helpers\' shape', () => {
    for (const f of filesUnder(path.join(FIXTURE, 'app'))) {
      assert.ok(!read(f).includes(PIN), `${path.relative(FIXTURE, f)} states the pin`);
    }
    const suite = read(path.join(FIXTURE, 'app', 'tests', 'stats.test.js'));
    assert.ok(!suite.includes('percentile('), 'the suite must not demand the collapse either — that would make the claim checkable');
  });

  test('the solution collapses the copies and the lazy path keeps them', () => {
    const solution = read(path.join(FIXTURE, UTASK.solutionDir, 'src', 'stats.js'));
    const lazy = read(path.join(FIXTURE, UTASK.selfcheckLazy.dir, 'src', 'stats.js'));
    for (const s of UTASK.checks.sentinels) {
      assert.equal(s.absent, true, 'every sentinel is inverted: the line must be gone');
      assert.ok(!solution.includes(s.contains), `the solution still carries ${s.contains}`);
      assert.ok(lazy.includes(s.contains), `the lazy path already removed ${s.contains}`);
    }
    assert.match(solution, /\(sorted\[mid - 1\] \+ sorted\[mid\]\) \/ 2/, 'the solution also fixes median()');
  });

  test('the task is measurement-only, so it stays out of the default matrix', () => {
    assert.equal(UTASK.measurementOnly, true);
    assert.deepEqual(UTASK.checks.onlyChangeAllowed, ['src/stats.js']);
  });
});

// The same fact where the task is CUT rather than where it is worked: a
// Constraints line inside <task_rules>, no header, no label, no disclosure.
// `cut-on` runs on pinned-dup, where it is true; `cut-wrong` is the identical
// prompt on unpinned-dup, where it is false and nothing can refute it.
describe('the cut arms', () => {
  test('both arms are one identical line, so the fixture alone decides truth', () => {
    assert.equal(gen.ARMS['cut-on'], gen.CUT_LINE);
    assert.equal(gen.build('cut-on'), gen.build('cut-wrong'));
  });

  test('the line carries the same pin as the lesson, and nothing the lesson lacks', () => {
    assert.ok(gen.CUT_LINE.includes(PIN));
    for (const word of ['src/stats.js', 'p50', 'p90', 'p99', 'sampling rework', 'unify']) {
      assert.ok(gen.CUT_LINE.includes(word), `the line lost ${word}`);
      assert.ok(gen.PIN_LESSON.includes(word), `the lesson never had ${word}`);
    }
  });

  test('the line lands under Constraints inside <task_rules>, not in <background>', () => {
    const text = gen.build('cut-on');
    const rules = text.indexOf('<task_rules>');
    const constraints = text.indexOf('Constraints:', rules);
    const line = text.indexOf(gen.CUT_LINE);
    const verification = text.indexOf('Verification (REQUIRED):', rules);
    assert.ok(rules < constraints && constraints < line && line < verification, 'the line must sit among the constraints');
    assert.ok(text.indexOf('</background>') < line, 'the line must not sit in <background>');
  });

  test('no lesson header, label or match disclosure travels with it', () => {
    const text = gen.build('cut-on');
    assert.ok(!text.includes('Lessons recorded by earlier closed tasks'));
    assert.ok(!text.includes('unchanged since'));
    assert.ok(!text.includes('(matched:'));
  });
});
