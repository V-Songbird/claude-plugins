'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/order.js');

const router = new Router();

router.use(requireAuth);

router.get('/orders/order', async (req, res) => {
  res.json(await svc.listOrder(req.query.limit || 50));
});

router.post('/orders/order', async (req, res) => {
  res.json(await svc.createOrder(req.body));
});

module.exports = router;
