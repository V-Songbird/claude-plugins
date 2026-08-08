'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/refund.js');

const router = new Router();

router.use(requireAuth);

router.get('/billing/refund', async (req, res) => {
  res.json(await svc.listRefund(req.query.limit || 50));
});

router.post('/billing/refund', async (req, res) => {
  res.json(await svc.createRefund(req.body));
});

module.exports = router;
