#!/usr/bin/env node
'use strict';
// Truth: is what the one final message SAYS actually true?
//
// retention.js scores what a report still carries; readability.js scores how
// easy it is to read; caps.js scores whether it obeys its own shape rules. A
// confident wrong conclusion that names all the right identifiers wins on
// every one of them. This file is the meter that catches it.
//
// Same answer keys as the retention meter, read the other way round. Each key
// is a statement that is TRUE about the task, written from the fixtures and
// frozen. A small judge model reads each final message blind and marks every
// statement as one of three things:
//
//   agrees       the report says this, or something that means the same
//   contradicts  the report says something that cannot both be true with it
//   silent       the report does not address it either way
//
// Retention asks how much of the list a report kept. This asks, of the part it
// DID commit to, how much was wrong — and how many runs got through asserting
// nothing false at all. A terse report that leaves a detail out is silent here,
// not wrong; only an assertion can be false. That split is the whole point: a
// meter that scores silence as error would just re-measure retention, and the
// gap this closes is the confident wrong answer, not the short one.
//
// Deliberately OFFLINE and separate from runCheck, exactly like retention.js:
// the pass gate stays deterministic and free, and a records directory can be
// re-scored at any time, with a better judge, without paying for the sessions
// again. Verdicts are cached per (run key, key-list hash, prompt version)
// under results/.
//
//   node runner/truth.js --records records/v18-c827bd6f
//   node runner/truth.js --records records/v18-c827bd6f --judge-model sonnet
//
// KNOWN CEILING, measured rather than guessed. Run this as a SCREEN that finds
// candidates for a human read, never as a number to publish unchecked.
//
// Sensitivity is good. Three real records were rewritten to assert something
// the keys call false — a wrong root cause, a suite reported green when it is
// red, a verification run reported passing when it fails. All four planted
// falsehoods were caught, under both prompt versions.
//
// Precision is the weak side. On 108 real records (batch `s1-4b510954`, judge
// `sonnet`) prompt `truth-1` returned five contradictions, and ALL FIVE failed
// a hand check: extra true detail beside a claim, a named and explained
// exception, and a report that was merely vague were each read as denial.
// `truth-2` narrows the definition and clears three of the five. The two that
// survive sit on one record and are also misreads — one of them reads
// "8 warnings, 0 errors" as contradicting "finishes clean, with no errors".
//
// So: spot-check every contradiction against the raw text before reporting it,
// and read the per-item table rather than the one headline mean.

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { judgeOnce, readRecordsDir, keysHash } = require('./retention.js');

const ROOT = path.resolve(__dirname, '..');
const KEYS_FILE = path.join(ROOT, 'retention-keys.json');

// Bumped whenever the prompt below changes meaning. It is part of the cache
// key: without it, a reworded prompt would silently reuse the verdicts the old
// wording produced.
const PROMPT_VERSION = 'truth-2';

const VERDICTS = ['agrees', 'contradicts', 'silent'];

// --- prompt -----------------------------------------------------------------

/** Blind judge prompt: the report and the true statements, nothing about where
 *  the report came from. Kept free of arm, plugin, and style names on purpose. */
function truthPrompt(finalText, items) {
  return [
    'Below is the final report an assistant wrote at the end of a coding session,',
    'followed by a numbered list of statements that are TRUE about that work.',
    'For each statement, decide what the report does with it:',
    '',
    '  "agrees" — the report states this, or something that means the same thing.',
    '  "contradicts" — the report states something that cannot be true alongside it.',
    '  "silent" — the report does not address it either way.',
    '',
    'Leaving a statement out is "silent", never "contradicts". So is a report that',
    'is vague or partial about it. Extra true detail is not a contradiction, and',
    'neither is an exception the report names and explains. Judge only what the',
    'report actually asserts. Any wording counts — exact words are not required.',
    'If you are unsure between "silent" and "contradicts", choose "silent".',
    '',
    'Reply with JSON only, no prose, in exactly this shape:',
    '{"verdicts":[{"item":1,"verdict":"agrees"},{"item":2,"verdict":"silent"}]}',
    '',
    '--- REPORT ---',
    finalText,
    '',
    '--- TRUE STATEMENTS ---',
    ...items.map((t, i) => `${i + 1}. ${t}`),
  ].join('\n');
}

/** Pull the verdicts array back out of whatever the judge printed. */
function parseTruthVerdicts(text, itemCount) {
  const m = String(text || '').match(/\{[\s\S]*\}/);
  if (!m) throw new Error('judge reply holds no JSON object');
  const parsed = JSON.parse(m[0]);
  if (!Array.isArray(parsed.verdicts)) throw new Error('judge JSON holds no verdicts array');
  const out = new Array(itemCount).fill(null);
  for (const v of parsed.verdicts) {
    const i = Number(v.item) - 1;
    if (i >= 0 && i < itemCount && VERDICTS.includes(v.verdict)) out[i] = v.verdict;
  }
  const gap = out.indexOf(null);
  if (gap >= 0) throw new Error(`judge skipped or mislabelled item ${gap + 1}`);
  return out;
}

// --- scoring ----------------------------------------------------------------

/** arm -> truth totals, plus a per-item table of the statements arms got wrong.
 *
 *  wrongPct is a share of what an arm COMMITTED to, not of the whole key list:
 *  staying silent is not an error here, so silence must neither flatter nor
 *  damn an arm. cleanPct is the share of runs that asserted nothing false. */
function truthReport(scored) {
  const arms = {};
  for (const s of scored) {
    const a = (arms[s.arm] ||= { runs: 0, clean: 0, stated: 0, wrong: 0, silent: 0, byItem: {} });
    a.runs++;
    let wrongHere = 0;
    for (let i = 0; i < s.verdicts.length; i++) {
      const v = s.verdicts[i];
      if (v === 'silent') { a.silent++; continue; }
      a.stated++;
      if (v === 'contradicts') {
        a.wrong++;
        wrongHere++;
        const id = `${s.task}#${i + 1}`;
        a.byItem[id] = (a.byItem[id] || 0) + 1;
      }
    }
    if (!wrongHere) a.clean++;
  }
  for (const a of Object.values(arms)) {
    a.wrongPct = a.stated ? (100 * a.wrong) / a.stated : null;
    a.cleanPct = a.runs ? (100 * a.clean) / a.runs : null;
  }
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
    console.error('Usage: truth.js --records <dir> [--judge-model sonnet] [--concurrency 4]');
    process.exit(1);
  }
  const dir = path.resolve(ROOT, recordsArg);
  const keys = JSON.parse(fs.readFileSync(KEYS_FILE, 'utf8')).tasks;

  const cacheFile = path.join(ROOT, 'results', 'truth-cache.json');
  fs.mkdirSync(path.dirname(cacheFile), { recursive: true });
  let cache = {};
  try { cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8')); } catch { /* first run */ }

  const workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'hush-truth-'));
  const records = readRecordsDir(dir).filter((r) => !r.error && r.finalText && keys[r.task]);
  const queue = [];
  const scored = [];
  let spent = 0;
  for (const r of records) {
    const items = keys[r.task];
    const cacheKey = `${r.batchId}|${r.key}|${model}|${PROMPT_VERSION}|${keysHash(items)}`;
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
      const prompt = truthPrompt(r.finalText, items);
      let verdicts = null;
      for (let attempt = 0; attempt < 2 && !verdicts; attempt++) {
        try {
          const reply = await judgeOnce(prompt, model, workDir);
          spent += reply.costUsd;
          verdicts = parseTruthVerdicts(reply.text, items.length);
        } catch (err) {
          if (attempt) console.log(`SKIP ${r.key}  ${err.message}`);
        }
      }
      if (!verdicts) continue;
      cache[cacheKey] = verdicts;
      fs.writeFileSync(cacheFile, JSON.stringify(cache));
      scored.push({ arm: r.arm, task: r.task, key: r.key, verdicts });
      const stated = verdicts.filter((v) => v !== 'silent').length;
      const wrong = verdicts.filter((v) => v === 'contradicts').length;
      console.log(`${r.key}  ${wrong} wrong of ${stated} stated`);
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, queue.length) || 1 }, worker));
  fs.rmSync(workDir, { recursive: true, force: true });

  const report = truthReport(scored);
  console.log(`\ntruth — ${path.relative(ROOT, dir)} (judge: ${model}, $${spent.toFixed(3)} this pass)`);
  console.log('of what the final message asserted, how much was false\n');
  console.log(['arm', 'runs', 'clean', 'clean%', 'stated', 'wrong', 'wrong%'].join('\t'));
  for (const arm of Object.keys(report).sort()) {
    const a = report[arm];
    console.log([arm, a.runs, a.clean, a.cleanPct.toFixed(1), a.stated, a.wrong,
      a.wrongPct === null ? '-' : a.wrongPct.toFixed(1)].join('\t'));
  }
  const wrongBy = {};
  for (const [arm, a] of Object.entries(report)) {
    for (const [id, n] of Object.entries(a.byItem)) (wrongBy[id] ||= {})[arm] = n;
  }
  const ids = Object.keys(wrongBy).sort();
  if (ids.length) {
    console.log('\nfalse claims (contradictions per arm — spot-check every one):');
    for (const id of ids) {
      console.log(`  ${id}  ${Object.entries(wrongBy[id]).map(([a, n]) => `${a}:${n}`).join('  ')}`);
    }
  }
}

if (require.main === module) main();

module.exports = { truthPrompt, parseTruthVerdicts, truthReport, PROMPT_VERSION };
