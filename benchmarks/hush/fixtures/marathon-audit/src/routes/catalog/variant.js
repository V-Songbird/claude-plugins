'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/variant.js');

const router = new Router();

router.use(requireAuth);

router.get('/catalog/variant', async (req, res) => {
  res.json(await svc.listVariant(req.query.limit || 50));
});

router.post('/catalog/variant', async (req, res) => {
  res.json(await svc.createVariant(req.body));
});

module.exports = router;
