'use strict';

// Ground truth for the repo-sweep task. Exit 0 = pass.
//
// Three ways to get this wrong, and all three fail here: leaving a straggler
// behind, rewriting the cache's unrelated `query`, and editing vendored code.

const fs = require('node:fs');
const path = require('node:path');

const problems = [];
const fail = (m) => problems.push(m);

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.js')) out.push(p);
  }
  return out;
}

const PKG = path.join(__dirname, 'packages');
const files = walk(PKG);
if (files.length !== 75) fail(`packages/ holds ${files.length} modules, expected 75`);

// --- every old call site is gone from the app code -------------------------
let cacheQueries = 0;
for (const f of files) {
  const src = fs.readFileSync(f, 'utf8');
  const rel = path.relative(__dirname, f).replace(/\\/g, '/');
  const stale = src.match(/db\s*\.\s*query\s*\(/g);
  if (stale) fail(`${rel} still calls db.query (${stale.length} site${stale.length > 1 ? 's' : ''})`);
  cacheQueries += (src.match(/cache\s*\.\s*query\s*\(/g) || []).length;
  // Every execute call has to carry both named fields.
  for (const call of src.match(/db\s*\.\s*execute\s*\(\s*\{[^}]*\}/g) || []) {
    if (!/\bsql\s*:/.test(call)) fail(`${rel} has a db.execute call with no sql: field`);
    if (!/\bparams\s*:/.test(call)) fail(`${rel} has a db.execute call with no params: field`);
  }
}
if (cacheQueries !== 25) fail(`cache.query appears ${cacheQueries} times, expected 25 — the cache is not the database`);

// --- vendored code is untouched --------------------------------------------
const VENDOR = path.join(__dirname, 'vendor', 'legacy-orm', 'adapter.js');
if (!fs.existsSync(VENDOR)) fail('vendor/legacy-orm/adapter.js is gone');
else {
  const v = fs.readFileSync(VENDOR, 'utf8');
  if ((v.match(/db\s*\.\s*query\s*\(/g) || []).length !== 2) {
    fail('vendor/legacy-orm/adapter.js was edited — vendored code is replaced on upgrade');
  }
}

// --- the modules still work -------------------------------------------------
if (!problems.length) {
  const { db, calls } = require(path.join(__dirname, 'lib', 'db.js'));
  db.query = async () => {
    throw new Error('db.query was called at runtime');
  };
  (async () => {
    for (const f of files) {
      const rel = path.relative(__dirname, f).replace(/\\/g, '/');
      let mod;
      try {
        mod = require(f);
      } catch (err) {
        fail(`${rel} no longer loads: ${err.message}`);
        continue;
      }
      for (const [name, fn] of Object.entries(mod)) {
        if (typeof fn !== 'function' || !/^(get|list)/.test(name)) continue;
        calls.length = 0;
        try {
          await fn(1, 10, 0);
        } catch (err) {
          fail(`${rel} > ${name}() threw: ${err.message}`);
          continue;
        }
        const made = calls.filter((c) => c.form === 'execute');
        if (!made.length) {
          fail(`${rel} > ${name}() made no db.execute call`);
          continue;
        }
        for (const c of made) {
          if (typeof c.sql !== 'string' || !c.sql.trim()) fail(`${rel} > ${name}() passed no sql`);
          if (!Array.isArray(c.params)) fail(`${rel} > ${name}() passed params as ${typeof c.params}, expected an array`);
        }
      }
    }

    if (problems.length) {
      for (const p of problems) console.error(`FAIL ${p}`);
      process.exit(1);
    }
    console.log('OK every db.query call site moved to db.execute, and nothing else moved');
  })();
} else {
  for (const p of problems) console.error(`FAIL ${p}`);
  process.exit(1);
}
