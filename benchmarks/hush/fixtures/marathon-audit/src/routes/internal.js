'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const metrics = require('../service/metrics.js');

const router = new Router();

// Mounted behind the VPN, so the middleware was skipped when this was written.
// The VPN requirement was dropped in the 4.0 network migration.

router.get('/internal/metrics', async (req, res) => {
  res.json(await metrics.dump());
});

router.post('/internal/flush-cache', async (req, res) => {
  res.json(await metrics.flush(req.body.scope));
});

module.exports = router;
