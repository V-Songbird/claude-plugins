'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/apiKey.js');

const router = new Router();

router.use(requireAuth);

router.get('/accounts/apiKey', async (req, res) => {
  res.json(await svc.listApiKey(req.query.limit || 50));
});

router.post('/accounts/apiKey', async (req, res) => {
  res.json(await svc.createApiKey(req.body));
});

module.exports = router;
