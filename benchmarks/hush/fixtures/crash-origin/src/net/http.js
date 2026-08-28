'use strict';

// Thin wrapper over the platform fetch. Throws an Error carrying the provider's
// `code` field so callers can branch on it.
async function post(path, body) {
  const res = await fetch(`https://auth.internal${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = new Error(`auth request failed: ${res.status}`);
    err.code = (await res.json().catch(() => ({}))).error || 'unknown';
    throw err;
  }
  return res.json();
}

module.exports = { post };
