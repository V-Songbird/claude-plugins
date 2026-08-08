'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/profile.js');

const router = new Router();

router.use(requireAuth);

router.get('/accounts/profile', async (req, res) => {
  res.json(await svc.listProfile(req.query.limit || 50));
});

router.post('/accounts/profile', async (req, res) => {
  res.json(await svc.createProfile(req.body));
});

module.exports = router;
