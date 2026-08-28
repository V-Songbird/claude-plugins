'use strict';

// Splits a JWT and returns its payload. Assumes a real token: validating the
// signature happens upstream, in the gateway.
function decode(token) {
  const [, payload] = token.split('.');
  return JSON.parse(Buffer.from(payload, 'base64').toString('utf8'));
}

module.exports = { decode };
