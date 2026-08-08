'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/version.js');

const router = new Router();

router.get('/public/version', async (req, res) => {
  res.json(await svc.listVersion(req.query.limit || 50));
});

router.post('/public/version', async (req, res) => {
  res.json(await svc.createVersion(req.body));
});

module.exports = router;
