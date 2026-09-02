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
  d: 24 * 60 * 60 * 1000,
};

function parseDuration(text) {
  const s = String(text).trim();
  const re = /(\d+(?:\.\d+)?)(ms|s|m|h|d)/g;
  let total = 0;
  let seen = 0;
  let at = 0;
  let m;
  while ((m = re.exec(s)) !== null) {
    if (m.index !== at) break;
    at = re.lastIndex;
    total += Number(m[1]) * UNITS[m[2]];
    seen += 1;
  }
  if (!seen || at !== s.length) throw new TypeError(`not a duration: ${text}`);
  return total;
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
