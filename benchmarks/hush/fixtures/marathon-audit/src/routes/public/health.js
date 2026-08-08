'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/health.js');

const router = new Router();

router.get('/public/health', async (req, res) => {
  res.json(await svc.listHealth(req.query.limit || 50));
});

router.post('/public/health', async (req, res) => {
  res.json(await svc.createHealth(req.body));
});

module.exports = router;
