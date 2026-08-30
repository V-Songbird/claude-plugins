'use strict';

// The `foreman-std` arm is the harness's only fact-matched foreman prompt, and
// the whole cross-arm comparison rests on two properties nothing else pins:
// it carries the same facts as the hand-authored arms, and it passes the
// product's own gate. The hand-frozen `foreman` arm fails that gate with six
// errors, which is why it must never be the arm a headline quotes.

const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const gen = require(path.join(ROOT, 'defaultarm', 'gen.js'));
const TASKS = JSON.parse(fs.readFileSync(path.join(ROOT, 'tasks.json'), 'utf8'))
  .filter((t) => !t.measurementOnly);
const CONFIG = JSON.parse(fs.readFileSync(path.join(ROOT, 'config.json'), 'utf8'));

const FOREMAN_DIR = process.env.FOREMAN_DIR
  ? path.resolve(process.env.FOREMAN_DIR)
  : path.resolve(ROOT, '..', '..', 'foreman');
const CHECK_PROMPT = path.join(FOREMAN_DIR, 'scripts', 'check-prompt.js');

function gate(file) {
  const r = spawnSync('node', [CHECK_PROMPT, file, '--destination', 'clipboard'], {
    encoding: 'utf8',
    // A neutral cwd: run from the repo and this repo's own .foreman config
    // colours the result with usePersona/omitSections rules the fixture never
    // declared, which is not what is being asserted.
    cwd: require('node:os').tmpdir(),
    timeout: 30000,
  });
  return JSON.parse(r.stdout.trim().split('\n').pop());
}

describe('the fact-matched foreman arm', () => {
  test('the constraint facts reach the prompt — outputshape/gen.js drops them', () => {
    for (const task of TASKS) {
      const j = gen.judgmentFor(task);
      const expected = task.briefFacts.filter((f) => f.startsWith('constraint:'));
      assert.equal(
        j.constraints.length,
        expected.length,
        `${task.id}: ${expected.length} constraint fact(s) in the brief, ${j.constraints.length} in the judgment`
      );
    }
  });

  test("planned_touches carries the brief's CLAIMED file, so the stale-brief trap is sprung", () => {
    const moved = TASKS.find((t) => t.id === 'moved-file');
    assert.ok(moved, 'moved-file is the stale-brief task and must exist');
    assert.deepEqual(
      gen.claimedFile(moved),
      ['src/parser.js'],
      'the arm must name the wrong file the other arms name, not the real one'
    );
  });

  for (const task of TASKS) {
    test(`${task.id}: the arm prompt is current, fact-matched and gate-clean`, () => {
      const file = gen.promptPath(task);
      assert.ok(fs.existsSync(file), 'foreman-std.md is missing — run: node defaultarm/gen.js');
      const prompt = fs.readFileSync(file, 'utf8');

      // Parity is defined against the hand-authored paragraph arm, which is the
      // arm the comparison is actually against: every file `freeform` names,
      // this one names too. That is what outputshape's arm fails.
      const files = (text) => new Set(text.match(/[A-Za-z0-9_.-]*(?:src|lib|app)\/[A-Za-z0-9_.-]+\.[a-z]+|\bindex\.js\b/g) || []);
      const freeform = files(fs.readFileSync(
        path.join(ROOT, 'fixtures', task.fixture, 'prompts', 'freeform.md'), 'utf8'
      ));
      for (const name of freeform) {
        assert.ok(prompt.includes(name), `${task.id}: freeform states ${name} and this arm does not`);
      }

      const result = gate(file);
      assert.equal(result.ok, true, `gate rejected foreman-std: ${JSON.stringify(result.errors)}`);
    });
  }

  test('the hand-frozen `foreman` arm still fails the gate — the reason this arm exists', () => {
    const legacy = path.join(ROOT, 'fixtures', 'api-constraint', 'prompts', 'foreman.md');
    if (!fs.existsSync(legacy)) return; // kept only for re-reporting old tags
    const result = gate(legacy);
    assert.equal(result.ok, false, 'the frozen arm now passes — re-check whether it should replace foreman-std');
  });

  test('the arm is not in the default matrix, so an ordinary run never pays for it', () => {
    assert.ok(!CONFIG.arms.includes(gen.ARM), `${gen.ARM} joined config.json's default arms`);
  });
});
