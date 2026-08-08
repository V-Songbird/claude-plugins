'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/sla.js');

const router = new Router();

router.use(requireAuth);

router.get('/support/sla', async (req, res) => {
  res.json(await svc.listSla(req.query.limit || 50));
});

router.post('/support/sla', async (req, res) => {
  res.json(await svc.createSla(req.body));
});

module.exports = router;
