'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/login.js');

const router = new Router();

router.use(requireAuth);

router.get('/accounts/login', async (req, res) => {
  res.json(await svc.listLogin(req.query.limit || 50));
});

router.post('/accounts/login', async (req, res) => {
  res.json(await svc.createLogin(req.body));
});

module.exports = router;
