#!/usr/bin/env node
'use strict';
// P3 — the dogfood counter. Reads a project's own `.foreman/trial-log.jsonl`
// and reports the three rates the lesson ledger's write side is judged on:
//
//   lesson_present rate   how often a close that COULD record a lesson did
//   rejection reasons     which refusal actually fires in practice
//   zero-path rate        closes refused for `no_observed_paths` — the one
//                         refusal that means the derivation is wrong rather
//                         than the author having nothing to say
//
// It reads counts only. The trial log records no title, no path, no id and
// nothing anybody typed (see foreman/TRIALS.md), so neither does this.
//
//   node lessons/p3-report.js [--root <project>]
//
// Run data stays on the operator's machine per ADR 0004: this prints, it never
// writes a report file.

const fs = require('node:fs');
const path = require('node:path');

function flag(name, fallback) {
  const at = process.argv.indexOf(`--${name}`);
  return at !== -1 && process.argv[at + 1] ? process.argv[at + 1] : fallback;
}

const root = path.resolve(flag('root', process.cwd()));
const logPath = path.join(root, '.foreman', 'trial-log.jsonl');

if (!fs.existsSync(logPath)) {
  console.error(
    `no trial log at ${logPath}\n` +
    'P3 needs the project to have opted in: set {"trialLog": true} in .foreman/config.json, ' +
    'then run ~20 closes with the ledger enabled.'
  );
  process.exit(1);
}

const events = fs
  .readFileSync(logPath, 'utf8')
  .split('\n')
  .map((line) => line.trim())
  .filter(Boolean)
  .map((line) => {
    try {
      return JSON.parse(line);
    } catch {
      return null;
    }
  })
  .filter((row) => row && row.event === 'lesson_present');

if (!events.length) {
  console.log('0 lesson_present events — no close has been offered the ask yet.');
  process.exit(0);
}

const stored = events.filter((row) => row.stored === true).length;
const outcomes = new Map();
for (const row of events) {
  const key = row.outcome || 'unknown';
  outcomes.set(key, (outcomes.get(key) || 0) + 1);
}
const zeroPath = outcomes.get('no_observed_paths') || 0;

const pct = (n) => `${((n / events.length) * 100).toFixed(1)}%`;

console.log(`closes offered the lesson ask: ${events.length}`);
console.log(`lesson_present rate:           ${stored}/${events.length}  ${pct(stored)}`);
console.log(`zero-path refusals:            ${zeroPath}/${events.length}  ${pct(zeroPath)}`);
console.log('outcomes:');
for (const [key, count] of [...outcomes].sort((a, b) => b[1] - a[1])) {
  console.log(`  ${key.padEnd(20)} ${count}`);
}
console.log(
  '\nBars: the ask is worth keeping if the rate is materially above zero, and the ' +
  'derivation is wrong (not the author) if zero-path refusals dominate.'
);
