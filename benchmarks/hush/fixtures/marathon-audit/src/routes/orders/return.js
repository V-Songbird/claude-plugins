'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/return.js');

const router = new Router();

router.use(requireAuth);

router.get('/orders/return', async (req, res) => {
  res.json(await svc.listReturn(req.query.limit || 50));
});

router.post('/orders/return', async (req, res) => {
  res.json(await svc.createReturn(req.body));
});

module.exports = router;
