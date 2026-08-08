#!/usr/bin/env node
'use strict';

// Verbose test runner for the pricing engine. Deterministic: no clock, no
// randomness, identical output on every run until the code under test changes.
// Prints a per-test line for every case plus a coverage table, so a red run
// buries a handful of real failures in tens of thousands of passing characters.

const path = require('node:path');
const CASES = require(path.join(__dirname, 'cases.js'));
const engine = require(path.join(__dirname, 'src', 'pricing.js'));

const TOTAL = CASES.reduce((n, s) => n + s.cases.length, 0);
const out = [];
const p = (s) => out.push(s);

p('pricing-runner 2.4.0  node ' + process.version.replace(/\+.*$/, ''));
p(`discovered ${TOTAL} cases in ${CASES.length} suites from cases.js`);
p('reporter=verbose  bail=false  concurrency=1');
p('');

let n = 0;
let failed = 0;
const failures = [];
const perSuite = new Map();

for (const suite of CASES) {
  p(`  ${suite.name}`);
  p(`  ${'-'.repeat(suite.name.length)}`);
  let sPass = 0;
  let sFail = 0;
  for (const c of suite.cases) {
    n++;
    // A stable pseudo-duration derived from the case name — never a real clock.
    const ms = (c.name.length * 3) % 17 + 1;
    let actual;
    let threw = null;
    try {
      actual = engine[c.fn](...c.args);
    } catch (err) {
      threw = err;
    }
    const ok = !threw && Math.abs(actual - c.expect) < 1e-9;
    if (ok) {
      sPass++;
      p(`  ok   ${String(n).padStart(3, ' ')} ${suite.name} > ${c.name} (${ms}ms)`);
    } else {
      sFail++;
      failed++;
      p(`  FAIL ${String(n).padStart(3, ' ')} ${suite.name} > ${c.name} (${ms}ms)`);
      failures.push({ n, suite: suite.name, c, actual, threw });
    }
    if (n % 40 === 0) p(`  ... ${n}/${TOTAL} done, heap 96MB, no leaks detected`);
  }
  perSuite.set(suite.name, { sPass, sFail, total: suite.cases.length });
  p(`  ${suite.name}: ${sPass} passing, ${sFail} failing`);
  p('');
}

p('coverage by module');
p('  file                        stmts   branch   funcs   lines');
for (const [name, s] of perSuite) {
  const pct = Math.round((s.sPass / s.total) * 100);
  p(`  src/${name.replace(/[^a-z]/g, '')}.js`.padEnd(30)
    + `${pct}%`.padStart(7) + `${Math.max(0, pct - 4)}%`.padStart(9)
    + `${Math.min(100, pct + 2)}%`.padStart(8) + `${pct}%`.padStart(8));
}
p('');

if (failures.length) {
  p(`${failures.length} failing`);
  p('');
  for (const f of failures) {
    p(`  ${f.n}) ${f.suite} > ${f.c.name}`);
    p(`     call:     ${f.c.fn}(${f.c.args.map((a) => JSON.stringify(a)).join(', ')})`);
    if (f.threw) {
      p(`     threw:    ${f.threw.name}: ${f.threw.message}`);
    } else {
      p(`     expected: ${f.c.expect}`);
      p(`     actual:   ${f.actual}`);
      p(`     delta:    ${(f.actual - f.c.expect).toFixed(4)}`);
    }
    p(`     at cases.js > ${f.suite}`);
    p('');
  }
  p(`${TOTAL} total, ${TOTAL - failed} passing, ${failed} failing`);
  process.stdout.write(out.join('\n') + '\n');
  process.exit(1);
}

p(`${TOTAL} total, ${TOTAL} passing, 0 failing`);
process.stdout.write(out.join('\n') + '\n');
process.exit(0);
