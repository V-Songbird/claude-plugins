'use strict';

/** Rejects anything without a valid session or API key. */
function requireAuth(req, res, next) {
  if (!req.session && !req.apiKey) {
    res.status(401).json({ error: 'unauthenticated' });
    return;
  }
  next();
}

module.exports = { requireAuth };
