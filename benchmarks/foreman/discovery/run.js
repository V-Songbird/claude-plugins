#!/usr/bin/env node
'use strict';
// §4.3 — where is the discovery bar actually set?
//
// The post-commit discovery block opened with two qualitative words,
// "CONFIRMED opportunities, bugs, or ideas — not vague hunches", and closed
// with "Say nothing if nothing is confirmed." The concrete criterion already
// existed two clauses later, but it governed how to WRITE an accepted
// candidate rather than what got in. Both gates have to swap together or it is
// a no-op, because the closing one binds hardest at the emit point.
//
//   arm            the bar
//   ---            -------
//   bar-confirmed  today's wording, the control
//   bar-concrete   FOREMAN_DISCOVERY_CONCRETE_BAR=1
//
// The block text is read out of the plugin at run time, never restated here,
// so a reworded product string breaks this harness rather than silently
// benchmarking prose the product no longer ships.
//
// This is a separate chassis from runner/run.js on purpose: that one gives a
// session a task and scores the tree it leaves behind, and there is no tree
// here. The whole outcome is a judgment about text already in the prompt.
//
// ONE DELIBERATE DEVIATION, identical in both arms: the shipped block ends by
// telling the session to ask the user what to do with each candidate, and to
// skip entirely when there is no user. A headless session has no user, so both
// arms would report nothing and the bar would be unmeasurable. That closing
// instruction is replaced with "write the candidates down as JSON". Every other
// clause — the bar, the density rule, the duplicate rule — is the shipped text
// verbatim, and the bar is the only thing that differs between the arms.
//
//   node discovery/run.js --dry-run
//   node discovery/run.js --tag d43 --reps 4 --model sonnet
//
// Run data stays on the operator's machine per ADR 0004.

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const FOREMAN_DIR = process.env.FOREMAN_DIR
  ? path.resolve(process.env.FOREMAN_DIR)
  : path.resolve(ROOT, '..', '..', 'foreman');
const HOOK = path.join(FOREMAN_DIR, 'hooks', 'post-commit.js');

const ARMS = {
  'bar-confirmed': {},
  'bar-concrete': { FOREMAN_DISCOVERY_CONCRETE_BAR: '1' },
};

// --- CLI --------------------------------------------------------------------
const argv = process.argv.slice(2);
const flag = (name, dflt) => {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 ? argv[i + 1] : dflt;
};
const tag = flag('tag', 'dev');
const model = flag('model', 'sonnet');
const reps = Number(flag('reps', 4));
const concurrency = Number(flag('concurrency', 3));
const dryRun = argv.includes('--dry-run');
const armNames = flag('arms', Object.keys(ARMS).join(',')).split(',');
for (const a of armNames) {
  if (!ARMS[a]) {
    console.error(`unknown arm "${a}" — valid: ${Object.keys(ARMS).join(', ')}`);
    process.exit(1);
  }
}

// --- the commit under review -------------------------------------------------
// One diff, held constant across every arm and rep. It carries things a scan
// can name concretely — an exact symbol, an exact path, an observed behaviour —
// alongside ordinary noise, so a bar that admits more has more to admit.
const COMMIT_SUBJECT = 'Add retry handling to the webhook dispatcher';
const COMMIT_DIFF = `diff --git a/src/dispatch.js b/src/dispatch.js
@@
-function send(event) {
-  return post(event.url, event.body);
+function send(event, attempt = 0) {
+  try {
+    return post(event.url, event.body);
+  } catch (err) {
+    // TODO: this swallows a 4xx the same as a 5xx
+    if (attempt < 3) return send(event, attempt + 1);
+    return null;
+  }
 }
+
+// Copied from src/mailer.js, which has the same three lines.
+function backoffMs(attempt) {
+  return Math.min(1000 * 2 ** attempt, 30000);
+}
diff --git a/src/queue.js b/src/queue.js
@@
   drain() {
-    for (const item of this.items) this.send(item);
+    for (const item of this.items) this.send(item);
+    this.items = [];
   }
diff --git a/tests/dispatch.test.js b/tests/dispatch.test.js
@@
+test('retries a failed send', () => {
+  assert.equal(attempts, 3);
+});
`;

const SESSION_NOTES = [
  'While making this change I noticed src/queue.js drain() clears this.items even when a send threw, so a failed item is dropped rather than retried.',
  'backoffMs is computed in src/dispatch.js but never called by send().',
  'The new test asserts the attempt count but never asserts the 4xx-versus-5xx behaviour the TODO names.',
].join(' ');

// --- prompt ------------------------------------------------------------------
function shippedBlock(env) {
  // Read the real product string in a child, so the module-level bar constant
  // resolves under this arm's environment.
  const result = spawnSync(
    'node',
    ['-e', `process.stdout.write(require(${JSON.stringify(HOOK)}).discoveryBlock())`],
    { encoding: 'utf8', env: { ...process.env, ...env } }
  );
  if (result.status !== 0) throw new Error(`could not read the discovery block: ${result.stderr}`);
  return result.stdout;
}

// The one replaced clause, identical in both arms.
const ASK_TAIL_MARKER = 'Ask first (AskUserQuestion:';
const WRITE_THEM_DOWN =
  'This session has no user to ask, so instead of asking, END YOUR TURN with a single '
  + 'fenced ```json block holding an array of the candidates you would have offered, each '
  + '{"title": "...", "why": "..."}. An empty array is a valid and expected answer. Write '
  + 'nothing after the block.';

function promptFor(arm) {
  const block = shippedBlock(ARMS[arm]);
  const cut = block.indexOf(ASK_TAIL_MARKER);
  if (cut < 0) throw new Error('the discovery block no longer carries its asking clause');
  const kept = block.slice(0, cut).trim();
  return [
    `You just committed "${COMMIT_SUBJECT}". This is the whole diff:`,
    '',
    COMMIT_DIFF,
    '',
    `What you observed while making it: ${SESSION_NOTES}`,
    '',
    kept,
    '',
    WRITE_THEM_DOWN,
  ].join('\n');
}

// --- scoring -----------------------------------------------------------------
function candidatesIn(finalText) {
  const fence = String(finalText || '').match(/```json\s*([\s\S]*?)```/);
  if (!fence) return { parsed: false, count: null, titles: [] };
  try {
    const rows = JSON.parse(fence[1]);
    if (!Array.isArray(rows)) return { parsed: false, count: null, titles: [] };
    return { parsed: true, count: rows.length, titles: rows.map((r) => String(r.title || '')) };
  } catch {
    return { parsed: false, count: null, titles: [] };
  }
}

// --- run ---------------------------------------------------------------------
function baseArgs() {
  return [
    '-p', '--output-format', 'stream-json', '--verbose',
    '--model', model,
    '--max-turns', '8',
    '--setting-sources', 'project',
    '--strict-mcp-config',
    '--permission-mode', 'acceptEdits',
    // Nothing to run and nothing to change: the whole task is a judgment about
    // text already in the prompt, so every tool is denied and a scan that tries
    // to explore anyway shows up as a refusal rather than as extra evidence.
    '--disallowedTools', 'Bash,PowerShell,Read,Edit,Write,Glob,Grep,Agent,Task',
  ];
}

function oneRun(arm, rep) {
  return new Promise((resolve) => {
    const key = `${arm}__r${rep}`;
    const workDir = fs.mkdtempSync(path.join(os.tmpdir(), `foreman-d43-${rep}-`));
    const child = spawn('claude', baseArgs(), {
      cwd: workDir,
      shell: true,
      env: { ...process.env },
    });
    let out = '';
    child.stdout.on('data', (d) => { out += d; });
    child.stderr.on('data', () => {});
    child.stdin.write(promptFor(arm));
    child.stdin.end();
    child.on('close', (code) => {
      let finalText = '';
      let costUsd = 0;
      let subtype = null;
      for (const line of out.split('\n')) {
        if (!line.trim()) continue;
        let o;
        try { o = JSON.parse(line); } catch { continue; }
        if (o.type === 'result') {
          finalText = o.result || '';
          costUsd = o.total_cost_usd || 0;
          subtype = o.subtype;
        }
      }
      const scored = candidatesIn(finalText);
      resolve({ key, arm, rep, model, exitCode: code, subtype, costUsd, finalText, ...scored });
    });
  });
}

async function main() {
  const queue = [];
  for (const arm of armNames) for (let r = 1; r <= reps; r += 1) queue.push([arm, r]);

  if (dryRun) {
    console.log(`DRY RUN — ${queue.length} planned runs (${armNames.length} arms x ${reps} reps), model=${model}`);
    for (const arm of armNames) console.log(`  ${arm}: ${promptFor(arm).length} chars`);
    const a = promptFor(armNames[0]);
    const b = promptFor(armNames[armNames.length - 1]);
    console.log(`  prompts differ? ${a !== b} (must be true for a measurement)`);
    return;
  }

  const outDir = path.join(ROOT, 'results', tag);
  fs.mkdirSync(path.join(outDir, 'runs'), { recursive: true });
  console.log(`${queue.length} runs (${armNames.length} arms x ${reps} reps), model=${model}, tag=${tag}`);

  const results = [];
  let idx = 0;
  async function worker() {
    while (idx < queue.length) {
      const [arm, rep] = queue[idx++];
      const row = await oneRun(arm, rep);
      fs.writeFileSync(path.join(outDir, 'runs', `${row.key}.json`), JSON.stringify(row, null, 2));
      console.log(
        `${row.parsed ? 'OK  ' : 'BAD '} ${row.key.padEnd(22)} candidates=${row.count}  cost=$${row.costUsd.toFixed(4)}`
      );
      results.push(row);
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, queue.length) }, worker));

  console.log('');
  for (const arm of armNames) {
    const all = results.filter((r) => r.arm === arm);
    const rows = all.filter((r) => r.parsed);
    const counts = rows.map((r) => r.count);
    const mean = counts.length ? counts.reduce((s, x) => s + x, 0) / counts.length : 0;
    console.log(
      `${arm.padEnd(16)} n=${rows.length}/${all.length}  candidates ${JSON.stringify(counts)}  mean=${mean.toFixed(2)}`
    );
  }
}

if (require.main === module) main();

module.exports = { ARMS, promptFor, candidatesIn, COMMIT_DIFF };
