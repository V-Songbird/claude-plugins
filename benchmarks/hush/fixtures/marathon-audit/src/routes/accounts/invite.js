'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/invite.js');

const router = new Router();

router.use(requireAuth);

router.get('/accounts/invite', async (req, res) => {
  res.json(await svc.listInvite(req.query.limit || 50));
});

router.post('/accounts/invite', async (req, res) => {
  res.json(await svc.createInvite(req.body));
});

module.exports = router;
