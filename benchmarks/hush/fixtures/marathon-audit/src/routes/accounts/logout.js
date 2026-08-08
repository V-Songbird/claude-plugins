'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/logout.js');

const router = new Router();

router.use(requireAuth);

router.get('/accounts/logout', async (req, res) => {
  res.json(await svc.listLogout(req.query.limit || 50));
});

router.post('/accounts/logout', async (req, res) => {
  res.json(await svc.createLogout(req.body));
});

module.exports = router;
