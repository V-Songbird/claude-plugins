'use strict';

const { RELEASE_DEFAULTS, PACKAGE_OVERRIDES } = require('./defaults.js');

/**
 * Resolve the release config for one package.
 *
 * Layering runs defaults -> package overrides -> whatever the caller passes on
 * the command line, with later layers winning. Overrides are partial: a layer
 * that names one key inside `output` changes that key and leaves the rest of
 * `output` alone.
 */
function resolveRelease(pkgName, cliFlags = {}) {
  const overrides = PACKAGE_OVERRIDES[pkgName] || {};
  return Object.assign({}, RELEASE_DEFAULTS, overrides, cliFlags);
}

module.exports = { resolveRelease };
