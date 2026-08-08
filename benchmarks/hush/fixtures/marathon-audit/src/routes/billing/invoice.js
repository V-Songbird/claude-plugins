'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/invoice.js');

const router = new Router();

router.use(requireAuth);

router.get('/billing/invoice', async (req, res) => {
  res.json(await svc.listInvoice(req.query.limit || 50));
});

router.post('/billing/invoice', async (req, res) => {
  res.json(await svc.createInvoice(req.body));
});

module.exports = router;
