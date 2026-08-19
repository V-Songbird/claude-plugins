#!/usr/bin/env node
'use strict';
// §4.2 — does the standard profile need an output shape?
//
// The standard profile ends on the closure-evidence sentence and says nothing
// about the final message, which is the one part of a handoff a human reads.
// The proposed change is a single term: let the canonical `<output_format>`
// ride standard too. It costs words on the profile whose stated purpose is the
// length it saves, so the switch shipped first and this decides the default.
//
//   arm            <output_format>
//   ---            ---------------
//   shape-off      absent — today's standard profile, the control
//   shape-on       present — FOREMAN_STANDARD_OUTPUT_SHAPE=1
//
// Both prompts are produced by running the product's own `craft-handoff.js`
// twice over the same temp project, so neither is hand-authored and neither
// can drift from what foreman actually emits. The only difference between them
// is the environment variable — `--check` asserts exactly that.
//
//   node outputshape/gen.js          # write both arm prompts for every task
//   node outputshape/gen.js --check  # exit 1 if they are missing or drifted
//
// Run data stays on the operator's machine per ADR 0004. This file writes
// prompts only.

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
// The three ordinary fixtures only. A measurementOnly fixture belongs to some
// other A/B and carries prompts for that one, not for this one.
const TASKS = JSON.parse(fs.readFileSync(path.join(ROOT, 'tasks.json'), 'utf8'))
  .filter((t) => !t.measurementOnly);

const FOREMAN_DIR = process.env.FOREMAN_DIR
  ? path.resolve(process.env.FOREMAN_DIR)
  : path.resolve(ROOT, '..', '..', 'foreman');
const CRAFT = path.join(FOREMAN_DIR, 'scripts', 'craft-handoff.js');

const ARMS = {
  'shape-off': {},
  'shape-on': { FOREMAN_STANDARD_OUTPUT_SHAPE: '1' },
};

// The judgment fields, derived from each task's own briefFacts so the two arms
// carry exactly the facts every other arm in this harness carries. Nothing
// here is arm-specific: both arms read the identical input.
function judgmentFor(task) {
  const facts = task.briefFacts;
  const symptom = (facts.find((f) => f.startsWith('symptom:')) || '').replace(/^symptom:\s*/, '');
  const context = facts.filter((f) => !f.startsWith('symptom:') && !f.startsWith('test command:'));
  return {
    role: 'a senior engineer',
    goal: `to fix ${symptom || task.id} so the suite passes`,
    context: context.join(' '),
    steps: ['Read the code the change touches.', 'Make the change and run the check.'],
    constraints: [],
    verification: [{ run: task.testCommand, expected: 'all tests pass' }],
  };
}

// A throwaway project root: craft-handoff resolves symbols and prior work
// against a real tree, so it needs one. The fixture's own app/ is copied in so
// the paths in `planned_touches` resolve to files that exist.
function stageProject(task) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `foreman-outputshape-${task.id}-`));
  const app = path.join(ROOT, 'fixtures', task.fixture, 'app');
  fs.cpSync(app, dir, { recursive: true });
  fs.writeFileSync(
    path.join(dir, 'ROADMAP.jsonl'),
    JSON.stringify({ foreman_roadmap_format: 2 }) + '\n',
    'utf8'
  );
  return dir;
}

// Only the file the task must actually change. `unchanged` is deliberately
// left out: moved-file's decoy would otherwise ride into the prompt and turn
// a measurement about the FINAL MESSAGE into a measurement about the trap.
// Both arms want to succeed here, so correctness is not the variable.
function sourceFiles(task) {
  const named = task.checks.mustChange || [];
  return named.length ? named : ['src'];
}

function craft(task, armEnv, project) {
  const input = JSON.stringify({
    title: `Fix ${task.id}`,
    what: task.briefFacts.join(' '),
    planned_touches: sourceFiles(task),
    destination: 'clipboard',
    request: task.briefFacts[0].replace(/^symptom:\s*/, 'Fix: '),
    judgment: judgmentFor(task),
  });
  const result = spawnSync('node', [CRAFT], {
    input,
    encoding: 'utf8',
    timeout: 60000,
    env: { ...process.env, CLAUDE_PROJECT_DIR: project, ...armEnv },
  });
  let json;
  try {
    json = JSON.parse(result.stdout);
  } catch {
    throw new Error(`craft-handoff returned non-JSON for ${task.id}: ${result.stdout}\n${result.stderr}`);
  }
  if (!json.ok) throw new Error(`craft-handoff refused ${task.id}: ${JSON.stringify(json)}`);
  if (json.profile !== 'standard') {
    throw new Error(
      `${task.id} assembled at profile "${json.profile}" — this measurement is about STANDARD, `
      + 'so a signal has started promoting these inputs and the arms are no longer the thing named'
    );
  }
  if (!json.gate.ok) throw new Error(`gate refused ${task.id}: ${JSON.stringify(json.gate.errors)}`);
  return json.prompt;
}

function build() {
  const built = {};
  for (const task of TASKS) {
    const project = stageProject(task);
    built[task.id] = {};
    for (const [arm, env] of Object.entries(ARMS)) {
      built[task.id][arm] = craft(task, env, project);
    }
    // The whole point: one block apart, byte for byte.
    const off = built[task.id]['shape-off'];
    const on = built[task.id]['shape-on'];
    const stripped = on.replace(/\n*<output_format>[\s\S]*?<\/output_format>/, '');
    if (stripped.trim() !== off.trim()) {
      throw new Error(`${task.id}: the two arms differ by more than <output_format>`);
    }
    if (off.includes('<output_format>')) {
      throw new Error(`${task.id}: the control already carries <output_format>`);
    }
  }
  return built;
}

function promptPath(task, arm) {
  return path.join(ROOT, 'fixtures', task.fixture, 'prompts', `${arm}.md`);
}

function main() {
  const check = process.argv.includes('--check');
  const built = build();
  let drifted = 0;
  for (const task of TASKS) {
    for (const arm of Object.keys(ARMS)) {
      const target = promptPath(task, arm);
      const next = built[task.id][arm];
      const current = fs.existsSync(target) ? fs.readFileSync(target, 'utf8') : null;
      if (current === next) continue;
      drifted += 1;
      if (check) {
        console.error(`drifted: ${path.relative(ROOT, target).split(path.sep).join('/')}`);
        continue;
      }
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, next, 'utf8');
      console.log(`wrote ${path.relative(ROOT, target).split(path.sep).join('/')} (${next.length} chars)`);
    }
  }
  if (check) {
    if (drifted) {
      console.error(`${drifted} output-shape arm prompt(s) missing or stale — run: node outputshape/gen.js`);
      process.exit(1);
    }
    console.log('output-shape arms current');
    return;
  }
  console.log('gen OK');
}

if (require.main === module) main();

module.exports = { ARMS, build, judgmentFor, promptPath };
