'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/macro.js');

const router = new Router();

router.use(requireAuth);

router.get('/support/macro', async (req, res) => {
  res.json(await svc.listMacro(req.query.limit || 50));
});

router.post('/support/macro', async (req, res) => {
  res.json(await svc.createMacro(req.body));
});

module.exports = router;
