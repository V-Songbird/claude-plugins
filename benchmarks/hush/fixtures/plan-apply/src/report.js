'use strict';

const fs = require('node:fs');
const path = require('node:path');

const DATA = path.join(__dirname, '..', 'data', 'runs.json');

// The report's rows, before anything decides how to print them. Every field a
// run carries survives this step — the slowest suites first, so the worst
// offender is at the top of whatever comes next.
function buildRows() {
  const runs = JSON.parse(fs.readFileSync(DATA, 'utf8'));
  return runs
    .map((run) => ({
      id: run.id,
      suite: run.suite,
      status: run.status,
      ms: run.ms,
      owner: run.owner,
      slow: run.ms > 5000,
    }))
    .sort((a, b) => b.ms - a.ms);
}

module.exports = { buildRows };
