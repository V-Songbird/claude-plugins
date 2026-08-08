'use strict';

// Release defaults every package starts from. A package only states what it
// needs to change; everything it leaves out comes from here.
const RELEASE_DEFAULTS = {
  minify: false,
  target: 'node18',
  output: {
    dir: 'dist',
    format: 'cjs',
    entry: 'index.js',
  },
  sourcemap: {
    mode: 'external',
    include: true,
  },
};

// Per-package overrides. These are partial by design — a package that names
// `output.format` is changing the format, not throwing away `output.dir`.
const PACKAGE_OVERRIDES = {
  '@acme/shared': {},
  '@acme/db': { target: 'node20' },
  '@acme/api': {
    output: { format: 'esm' },
    sourcemap: { mode: 'inline' },
  },
  '@acme/worker': { minify: false },
  '@acme/web': {
    output: { entry: 'browser.js', format: 'esm' },
  },
  '@acme/cli': { output: { entry: 'bin.js' } },
};

module.exports = { RELEASE_DEFAULTS, PACKAGE_OVERRIDES };
