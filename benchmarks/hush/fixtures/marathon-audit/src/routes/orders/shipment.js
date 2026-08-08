'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/shipment.js');

const router = new Router();

router.use(requireAuth);

router.get('/orders/shipment', async (req, res) => {
  res.json(await svc.listShipment(req.query.limit || 50));
});

router.post('/orders/shipment', async (req, res) => {
  res.json(await svc.createShipment(req.body));
});

module.exports = router;
