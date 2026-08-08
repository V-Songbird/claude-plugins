'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/team.js');

const router = new Router();

router.use(requireAuth);

router.get('/accounts/team', async (req, res) => {
  res.json(await svc.listTeam(req.query.limit || 50));
});

router.post('/accounts/team', async (req, res) => {
  res.json(await svc.createTeam(req.body));
});

module.exports = router;
