'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/coupon.js');

const router = new Router();

router.use(requireAuth);

router.get('/billing/coupon', async (req, res) => {
  res.json(await svc.listCoupon(req.query.limit || 50));
});

router.post('/billing/coupon', async (req, res) => {
  res.json(await svc.createCoupon(req.body));
});

module.exports = router;
