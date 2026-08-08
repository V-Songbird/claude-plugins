'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/fulfilment.js');

const router = new Router();

router.use(requireAuth);

router.get('/orders/fulfilment', async (req, res) => {
  res.json(await svc.listFulfilment(req.query.limit || 50));
});

router.post('/orders/fulfilment', async (req, res) => {
  res.json(await svc.createFulfilment(req.body));
});

module.exports = router;
