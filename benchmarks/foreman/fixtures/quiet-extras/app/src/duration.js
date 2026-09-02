'use strict';

// Duration strings -> milliseconds. Used by the scheduler and the HTTP client
// to read timeouts out of config.

const { warn } = require('./log.js');
const { withRetry } = require('./retry.js');

const UNITS = {
  ms: 1,
  s: 1000,
  m: 60 * 1000,
  h: 60 * 60 * 1000,
};

function parseDuration(text) {
  const m = /^(\d+(?:\.\d+)?)(ms|s|m|h)$/.exec(String(text).trim());
  if (!m) throw new TypeError(`not a duration: ${text}`);
  return Number(m[1]) * UNITS[m[2]];
}

// The scheduler reads a timeout, retrying while config is still being written.
function readTimeout(read, attempts) {
  return withRetry((n) => {
    const raw = read(n);
    if (raw == null) throw new Error(warn('no timeout configured yet'));
    return parseDuration(raw);
  }, attempts);
}

module.exports = { parseDuration, readTimeout, UNITS };
