#!/usr/bin/env node
'use strict';
// Retention: did the one final message keep the details that change what the
// reader does next?
//
// readability.js scores how EASY a reply is to read; this file scores what it
// still CARRIES. Each task in retention-keys.json lists the facts a report
// must convey, written from the fixtures before scoring and frozen. A small
// judge model reads each final message blind — no arm names, no tool names,
// just the report and the numbered claims — and marks each claim present or
// missing. Paraphrase counts; a regex would score "the pool ran dry" as a
// miss of POOL_EXHAUSTED, and the judge is the whole point.
//
// Deliberately OFFLINE and separate from runCheck: the pass gate stays
// deterministic and free, and a records directory can be re-scored at any
// time, with a better judge, without paying for the sessions again. Verdicts
// are cached per (run key, key-list hash) under results/, so a re-run only
// pays for records it has not judged yet.
//
//   node runner/retention.js --records records/v18-c827bd6f
//   node runner/retention.js --records records/v18-c827bd6f --judge-model sonnet
//
// KNOWN CEILING: the judge is a model, so single-item verdicts carry noise;
// spot-check a few against the raw text before trusting a close arm-to-arm
// gap, and read the per-item miss table rather than the one headline mean.

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const KEYS_FILE = path.join(ROOT, 'retention-keys.json');

// --- prompt -----------------------------------------------------------------

/** Blind judge prompt: the report and the claims, nothing about where the
 *  report came from. Kept free of arm, plugin, and style names on purpose. */
function judgePrompt(finalText, items) {
  return [
    'Below is the final report an assistant wrote at the end of a coding session,',
    'followed by a numbered list of claims. For each claim, decide whether the',
    'report conveys it. Any wording counts — exact words are not required. A claim',
    'the report leaves out or contradicts is false.',
    '',
    'Reply with JSON only, no prose, in exactly this shape:',
    '{"verdicts":[{"item":1,"present":true},{"item":2,"present":false}]}',
    '',
    '--- REPORT ---',
    finalText,
    '',
    '--- CLAIMS ---',
    ...items.map((t, i) => `${i + 1}. ${t}`),
  ].join('\n');
}

/** Pull the verdicts array back out of whatever the judge printed. */
function parseVerdicts(text, itemCount) {
  const m = String(text || '').match(/\{[\s\S]*\}/);
  if (!m) throw new Error('judge reply holds no JSON object');
  const parsed = JSON.parse(m[0]);
  if (!Array.isArray(parsed.verdicts)) throw new Error('judge JSON holds no verdicts array');
  const out = new Array(itemCount).fill(null);
  for (const v of parsed.verdicts) {
    const i = Number(v.item) - 1;
    if (i >= 0 && i < itemCount) out[i] = v.present === true;
  }
  if (out.some((v) => v === null)) throw new Error('judge skipped an item');
  return out;
}

// --- judge call -------------------------------------------------------------

// The judge runs bare: empty temp cwd so no project settings load, env
// stripped of nested-session and hush vars, no plugins, one turn. Same
// hygiene run.js applies to the sessions it measures.
function cleanEnv() {
  const env = {};
  for (const [k, v] of Object.entries(process.env)) {
    if (/^(CLAUDECODE|CLAUDE_CODE_|HUSH_)/.test(k)) continue;
    env[k] = v;
  }
  return env;
}

function judgeOnce(prompt, model, workDir) {
  return new Promise((resolve, reject) => {
    const child = spawn('claude',
      ['-p', '--output-format', 'json', '--model', model, '--max-turns', '1',
        '--strict-mcp-config', '--setting-sources', 'project', '--disallowedTools', 'Bash,PowerShell,Read,Edit,Write,Glob,Grep,Agent,Task'],
      { cwd: workDir, env: cleanEnv(), shell: true });
    let stdout = '', stderr = '';
    child.stdout.on('data', (d) => { stdout += d; });
    child.stderr.on('data', (d) => { stderr += d; });
    child.stdin.write(prompt);
    child.stdin.end();
    const killer = setTimeout(() => child.kill('SIGKILL'), 120000);
    child.on('close', () => {
      clearTimeout(killer);
      try {
        const body = JSON.parse(stdout);
        resolve({ text: body.result, costUsd: body.total_cost_usd || 0 });
      } catch {
        reject(new Error(`judge call failed: ${stderr.slice(0, 200) || stdout.slice(0, 200)}`));
      }
    });
  });
}

// --- scoring ----------------------------------------------------------------

const keysHash = (items) => crypto.createHash('sha256').update(JSON.stringify(items)).digest('hex').slice(0, 12);

function readRecordsDir(dir) {
  return fs.readdirSync(dir)
    .filter((f) => f.endsWith('.json') && f !== 'batch.json')
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));
}

/** arm -> retention totals, plus a per-item miss table for the arms present. */
function retentionReport(scored) {
  const arms = {};
  for (const s of scored) {
    const a = (arms[s.arm] ||= { runs: 0, hits: 0, total: 0, byItem: {} });
    a.runs++;
    for (let i = 0; i < s.verdicts.length; i++) {
      a.total++;
      if (s.verdicts[i]) a.hits++;
      else {
        const id = `${s.task}#${i + 1}`;
        a.byItem[id] = (a.byItem[id] || 0) + 1;
      }
    }
  }
  for (const a of Object.values(arms)) a.pct = a.total ? (100 * a.hits) / a.total : null;
  return arms;
}

// --- CLI --------------------------------------------------------------------

async function main() {
  const argv = process.argv.slice(2);
  const at = (flag, dflt) => (argv.includes(flag) ? argv[argv.indexOf(flag) + 1] : dflt);
  const recordsArg = at('--records', null);
  const model = at('--judge-model', 'sonnet');
  const concurrency = Number(at('--concurrency', 4));
  if (!recordsArg) {
    console.error('Usage: retention.js --records <dir> [--judge-model sonnet] [--concurrency 4]');
    process.exit(1);
  }
  const dir = path.resolve(ROOT, recordsArg);
  const keys = JSON.parse(fs.readFileSync(KEYS_FILE, 'utf8')).tasks;

  const cacheFile = path.join(ROOT, 'results', 'retention-cache.json');
  fs.mkdirSync(path.dirname(cacheFile), { recursive: true });
  let cache = {};
  try { cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8')); } catch { /* first run */ }

  const workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'hush-retention-'));
  const records = readRecordsDir(dir).filter((r) => !r.error && r.finalText && keys[r.task]);
  const queue = [];
  const scored = [];
  let spent = 0;
  for (const r of records) {
    const items = keys[r.task];
    const cacheKey = `${r.batchId}|${r.key}|${model}|${keysHash(items)}`;
    if (cache[cacheKey]) {
      scored.push({ arm: r.arm, task: r.task, key: r.key, verdicts: cache[cacheKey] });
    } else {
      queue.push({ r, items, cacheKey });
    }
  }
  console.log(`${records.length} records, ${scored.length} cached, ${queue.length} to judge (model ${model})`);

  let idx = 0;
  async function worker() {
    while (idx < queue.length) {
      const { r, items, cacheKey } = queue[idx++];
      const prompt = judgePrompt(r.finalText, items);
      let verdicts = null;
      for (let attempt = 0; attempt < 2 && !verdicts; attempt++) {
        try {
          const reply = await judgeOnce(prompt, model, workDir);
          spent += reply.costUsd;
          verdicts = parseVerdicts(reply.text, items.length);
        } catch (err) {
          if (attempt) console.log(`SKIP ${r.key}  ${err.message}`);
        }
      }
      if (!verdicts) continue;
      cache[cacheKey] = verdicts;
      fs.writeFileSync(cacheFile, JSON.stringify(cache));
      scored.push({ arm: r.arm, task: r.task, key: r.key, verdicts });
      console.log(`${r.key}  ${verdicts.filter(Boolean).length}/${verdicts.length}`);
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, queue.length) || 1 }, worker));
  fs.rmSync(workDir, { recursive: true, force: true });

  const report = retentionReport(scored);
  console.log(`\nretention — ${path.relative(ROOT, dir)} (judge: ${model}, $${spent.toFixed(3)} this pass)`);
  console.log('share of needed details the final message kept\n');
  console.log(['arm', 'runs', 'kept', 'of', 'kept%'].join('\t'));
  for (const arm of Object.keys(report).sort()) {
    const a = report[arm];
    console.log([arm, a.runs, a.hits, a.total, a.pct.toFixed(1)].join('\t'));
  }
  const missed = {};
  for (const [arm, a] of Object.entries(report)) {
    for (const [id, n] of Object.entries(a.byItem)) (missed[id] ||= {})[arm] = n;
  }
  const ids = Object.keys(missed).sort();
  if (ids.length) {
    console.log('\ndropped details (misses per arm):');
    for (const id of ids) {
      console.log(`  ${id}  ${Object.entries(missed[id]).map(([a, n]) => `${a}:${n}`).join('  ')}`);
    }
  }
}

if (require.main === module) main();

module.exports = { judgePrompt, parseVerdicts, retentionReport, keysHash };
