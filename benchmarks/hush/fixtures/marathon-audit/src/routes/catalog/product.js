'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/product.js');

const router = new Router();

router.use(requireAuth);

router.get('/catalog/product', async (req, res) => {
  res.json(await svc.listProduct(req.query.limit || 50));
});

router.post('/catalog/product', async (req, res) => {
  res.json(await svc.createProduct(req.body));
});

module.exports = router;
