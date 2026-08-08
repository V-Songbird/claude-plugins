'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/subscription.js');

const router = new Router();

router.use(requireAuth);

router.get('/billing/subscription', async (req, res) => {
  res.json(await svc.listSubscription(req.query.limit || 50));
});

router.post('/billing/subscription', async (req, res) => {
  res.json(await svc.createSubscription(req.body));
});

module.exports = router;
