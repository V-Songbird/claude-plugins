'use strict';
const { refreshToken } = require('./auth/refresh');
const { decode } = require('./auth/tokens');

// Runs on every request that arrives with an expired access token.
async function resumeSession(req) {
  const token = await refreshToken(req.cookies.rt);
  const claims = decode(token);
  return { userId: claims.sub, scopes: claims.scopes };
}

module.exports = { resumeSession };
