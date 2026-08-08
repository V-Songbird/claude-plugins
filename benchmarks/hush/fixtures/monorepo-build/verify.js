'use strict';

// Ground truth for the monorepo-build task. Exit 0 = pass.
//
// A green build is not enough. Papering over the merge by spelling every key
// out in defaults.js leaves the next partial override broken, so this checks
// the layering rule itself with an override the fixture never shipped.

const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const problems = [];
const fail = (m) => problems.push(m);

const DEFAULTS_FILE = path.join(__dirname, 'packages', 'shared', 'defaults.js');
const CONFIG_FILE = path.join(__dirname, 'packages', 'shared', 'config.js');
for (const f of [DEFAULTS_FILE, CONFIG_FILE, path.join(__dirname, 'build.js')]) {
  if (!fs.existsSync(f)) fail(`${path.relative(__dirname, f)} is gone`);
}

// --- the overrides are still partial ---------------------------------------
if (!problems.length) {
  const { RELEASE_DEFAULTS, PACKAGE_OVERRIDES } = require(DEFAULTS_FILE);
  if (RELEASE_DEFAULTS.output?.dir !== 'dist') fail('the default output.dir is no longer "dist"');
  if (RELEASE_DEFAULTS.sourcemap?.mode !== 'external') fail('the default sourcemap.mode changed');
  const api = PACKAGE_OVERRIDES['@acme/api'];
  if (!api) fail('the @acme/api override is gone');
  else {
    if (api.output?.format !== 'esm') fail('@acme/api no longer overrides output.format');
    if ('dir' in (api.output || {})) {
      fail('@acme/api now spells out output.dir — the merge was worked around, not fixed');
    }
    if ('include' in (api.sourcemap || {})) {
      fail('@acme/api now spells out sourcemap.include — the merge was worked around, not fixed');
    }
  }
}

// --- the layering rule holds for an override the fixture never shipped -----
if (!problems.length) {
  const { resolveRelease } = require(CONFIG_FILE);

  const api = resolveRelease('@acme/api', { minify: true, target: 'node20' });
  if (api.output?.dir !== 'dist') fail(`@acme/api output.dir resolved to ${JSON.stringify(api.output?.dir)}`);
  if (api.output?.format !== 'esm') fail('@acme/api output.format lost its override');
  if (api.output?.entry !== 'index.js') fail('@acme/api output.entry lost the default');
  if (api.sourcemap?.mode !== 'inline') fail('@acme/api sourcemap.mode lost its override');
  if (api.sourcemap?.include !== true) fail('@acme/api sourcemap.include lost the default');
  if (api.minify !== true || api.target !== 'node20') fail('the cli flags stopped winning');

  // A partial nested flag from the command line has to layer the same way.
  const web = resolveRelease('@acme/web', { output: { dir: 'build' } });
  if (web.output?.dir !== 'build') fail('a cli output.dir did not win over the default');
  if (web.output?.entry !== 'browser.js') fail('a cli output.dir wiped the package output.entry');
  if (web.output?.format !== 'esm') fail('a cli output.dir wiped the package output.format');
  if (web.sourcemap?.mode !== 'external') fail('@acme/web lost the default sourcemap.mode');

  // Defaults must not be mutated by resolving.
  const { RELEASE_DEFAULTS } = require(DEFAULTS_FILE);
  if (RELEASE_DEFAULTS.output.dir !== 'dist' || RELEASE_DEFAULTS.output.format !== 'cjs') {
    fail('resolveRelease mutated RELEASE_DEFAULTS');
  }
}

// --- and the build the task was about actually goes green ------------------
if (!problems.length) {
  try {
    execFileSync(process.execPath, [path.join(__dirname, 'build.js')], { stdio: 'pipe' });
  } catch (err) {
    const tail = String(err.stdout || '').trim().split('\n').slice(-2).join(' | ');
    fail(`build.js still exits non-zero: ${tail}`);
  }
}

if (problems.length) {
  for (const p of problems) console.error(`FAIL ${p}`);
  process.exit(1);
}
console.log('OK the config merge layers properly and the build is green');
