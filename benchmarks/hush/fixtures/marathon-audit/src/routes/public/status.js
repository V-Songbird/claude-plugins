'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/status.js');

const router = new Router();

router.get('/public/status', async (req, res) => {
  res.json(await svc.listStatus(req.query.limit || 50));
});

router.post('/public/status', async (req, res) => {
  res.json(await svc.createStatus(req.body));
});

module.exports = router;
