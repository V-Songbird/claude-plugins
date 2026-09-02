'use strict';

// Retry helper for the HTTP client. Nothing covers this file yet.

function withRetry(fn, max) {
  let attempt = 0;
  let last;
  while (attempt < max) {
    try {
      return fn(attempt);
    } catch (err) {
      last = err;
      attempt += 1;
    }
  }
  throw last;
}

module.exports = { withRetry };
