#!/usr/bin/env node
'use strict';

// Monorepo builder. Deterministic ~1,700-line log across six packages with
// five warnings, then a bundle stage that fails on a real, fixable bug in
// packages/shared/config.js. No randomness, no timestamps — byte-identical
// output on every run until the code changes.

const path = require('node:path');

const PACKAGES = [
  { name: '@acme/shared', dir: 'packages/shared', modules: 34 },
  { name: '@acme/db', dir: 'packages/db', modules: 46 },
  { name: '@acme/api', dir: 'packages/api', modules: 61 },
  { name: '@acme/worker', dir: 'packages/worker', modules: 38 },
  { name: '@acme/web', dir: 'packages/web', modules: 72 },
  { name: '@acme/cli', dir: 'packages/cli', modules: 29 },
];

const out = [];
const p = (s) => out.push(s);

p('acme-build 5.2.0  workspace protocol v2');
p('resolving workspace graph ... 6 packages, 0 cycles');
p('topological order: shared -> db -> api -> worker -> web -> cli');
p('');

let unit = 0;
for (const pkg of PACKAGES) {
  p(`▸ ${pkg.name}  (${pkg.dir})`);
  p(`  typecheck: tsconfig.build.json, ${pkg.modules} files`);
  for (let i = 0; i < pkg.modules; i++) {
    unit++;
    const file = `${pkg.dir}/src/${['core', 'util', 'model', 'route', 'view'][i % 5]}/${String(i).padStart(3, '0')}.ts`;
    p(`  [${String(unit).padStart(4, ' ')}] tsc ${file} ... ok (${(unit * 13) % 120 + 8}ms, ${(unit * 7) % 40 + 12} decls)`);
    if (unit % 11 === 0) p(`      emit ${file.replace(/\.ts$/, '.js')} + .d.ts + .js.map`);
    if (unit % 29 === 0) p(`      cache: ${Math.round((unit / 280) * 100)}% of the incremental buffer reused`);
  }
  p(`  bundle: ${pkg.modules} modules -> ${pkg.dir}/dist/index.js`);
  for (let i = 0; i < 42; i++) {
    p(`    chunk ${String(i).padStart(2, '0')}: ${((i * 37) % 900) + 100} symbols, ${((i * 17) % 60) + 4}KB, sourcemap ok`);
  }
  p(`  ${pkg.name}: typecheck ok, bundle ok`);
  p('');
}

p('lint pass: 280 files, 5 findings');
p('  WARN L1201 no-floating-promises  packages/worker/src/core/queue.ts:88');
p('  WARN L1204 prefer-const          packages/api/src/route/admin.ts:31');
p('  WARN L2210 no-explicit-any       packages/db/src/model/row.ts:14');
p('  WARN L2210 no-explicit-any       packages/db/src/model/row.ts:52');
p('  WARN L3318 deprecated-import     packages/web/src/view/legacy.ts:7 — `renderSync` moves in v6');
p('');

p('deduplication pass');
for (let i = 0; i < 260; i++) {
  p(`  fold: shared symbol ${String(i % 23).padStart(2, '0')} across ${(i % 5) + 2} packages (pass ${Math.floor(i / 23) + 1})`);
}
p('');

// Real bundle step: resolve the release config for every package and check
// each one came out complete. A bug in packages/shared/config.js drops nested
// keys, which aborts the build with a non-zero exit.
p('bundle stage: resolving release config per package');
try {
  const { resolveRelease } = require(path.join(__dirname, 'packages', 'shared', 'config.js'));
  for (const pkg of PACKAGES) {
    const cfg = resolveRelease(pkg.name, { minify: true, target: 'node20' });
    if (!cfg.output || typeof cfg.output.dir !== 'string') {
      throw new Error(`resolved config for ${pkg.name} has no output.dir`);
    }
    if (!cfg.sourcemap || typeof cfg.sourcemap.mode !== 'string') {
      throw new Error(`resolved config for ${pkg.name} has no sourcemap.mode`);
    }
    p(`  ${pkg.name}: out=${cfg.output.dir} sourcemap=${cfg.sourcemap.mode} minify=${cfg.minify} target=${cfg.target}`);
  }
  p('');
  p('emit: dist/acme-5.2.0.tgz  8.10 MB');
  p('build finished in 74.3s with 5 warnings, 0 errors');
  process.stdout.write(out.join('\n') + '\n');
  process.exit(0);
} catch (err) {
  p('');
  p(`ERROR EBUNDLE07 config-incomplete: packages/shared/config.js — ${err.name}: ${err.message}`);
  p('build aborted with 5 warnings, 1 error');
  process.stdout.write(out.join('\n') + '\n');
  process.exit(1);
}
