'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/category.js');

const router = new Router();

router.use(requireAuth);

router.get('/catalog/category', async (req, res) => {
  res.json(await svc.listCategory(req.query.limit || 50));
});

router.post('/catalog/category', async (req, res) => {
  res.json(await svc.createCategory(req.body));
});

module.exports = router;
