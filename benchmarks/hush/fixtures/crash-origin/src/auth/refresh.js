'use strict';
const { post } = require('../net/http');

// Error codes this service knows how to recover from. `invalid_grant` is
// deliberately not in here: a revoked refresh token is not retryable, and the
// user has to sign in again.
const RECOVERABLE = new Set(['token_expired', 'clock_skew']);

async function refreshToken(rt) {
  try {
    const res = await post('/oauth/refresh', { refresh_token: rt });
    return res.access_token;
  } catch (err) {
    if (!RECOVERABLE.has(err.code)) {
      return undefined;
    }
    const retried = await post('/oauth/refresh', { refresh_token: rt, retry: true });
    return retried.access_token;
  }
}

module.exports = { refreshToken };
