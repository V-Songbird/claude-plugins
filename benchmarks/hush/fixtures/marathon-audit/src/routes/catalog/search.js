'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/search.js');

const router = new Router();

router.use(requireAuth);

router.get('/catalog/search', async (req, res) => {
  res.json(await svc.listSearch(req.query.limit || 50));
});

router.post('/catalog/search', async (req, res) => {
  res.json(await svc.createSearch(req.body));
});

module.exports = router;
