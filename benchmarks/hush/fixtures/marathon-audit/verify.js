'use strict';

// Ground truth for the marathon-audit task. Exit 0 = pass.
//
// Four problems are planted in the tree, one per question the session was
// asked. The write-up has to name all four and point at the right file. It
// also has to stay an audit: nothing in the service may be edited.

const fs = require('node:fs');
const path = require('node:path');

const problems = [];
const fail = (m) => problems.push(m);

const REPORT = path.join(__dirname, 'AUDIT.md');
if (!fs.existsSync(REPORT)) {
  console.error('FAIL AUDIT.md was never written');
  process.exit(1);
}
const doc = fs.readFileSync(REPORT, 'utf8');
const has = (re) => re.test(doc);

if (doc.trim().length < 200) fail(`AUDIT.md is only ${doc.trim().length} characters long`);

// --- finding 1: the internal routes lost their auth ------------------------
if (!has(/routes[\\/]internal\.js|internal\.js/)) fail('no finding points at src/routes/internal.js');
else if (!has(/auth|unauthenticat|requireAuth|authenticat/i)) fail('the internal.js finding never mentions auth');

// --- finding 2: a password in a committed config ---------------------------
if (!has(/staging\.js|config[\\/]staging/)) fail('no finding points at config/staging.js');
else if (!has(/password|secret|credential/i)) fail('the staging.js finding never mentions the credential');

// --- finding 3: SQL built by concatenation ---------------------------------
if (!has(/repo[\\/]report\.js|report\.js|runSavedReport/)) fail('no finding points at src/repo/report.js');
else if (!has(/concat|interpolat|injection|string.built|parameteris|parameteriz/i)) {
  fail('the report.js finding never says the SQL is concatenated');
}

// --- finding 4: a yanked dependency ----------------------------------------
if (!has(/fast-parse/)) fail('no finding names the fast-parse dependency');
else if (!has(/1\.4\.2|yank|1\.4\.3/)) fail('the fast-parse finding names no version');

// --- it was an audit, not a rewrite ----------------------------------------
const untouched = [
  ['src/routes/internal.js', /router\.use\(requireAuth\)/, false],
  ['config/staging.js', /St4ging-Pg-2024!weakish/, true],
  ['src/repo/report.js', /sql \+ " WHERE "/, true],
];
for (const [rel, re, shouldMatch] of untouched) {
  const f = path.join(__dirname, rel);
  if (!fs.existsSync(f)) { fail(`${rel} was deleted`); continue; }
  const src = fs.readFileSync(f, 'utf8');
  if (re.test(src) !== shouldMatch) fail(`${rel} was edited — this task was a read-only audit`);
}
const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));
if (pkg.dependencies['fast-parse'] !== '1.4.2') fail('package.json was edited — this task was a read-only audit');

if (problems.length) {
  for (const p of problems) console.error(`FAIL ${p}`);
  process.exit(1);
}
console.log('OK AUDIT.md names all four findings and the service was left alone');
