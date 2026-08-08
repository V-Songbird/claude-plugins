'use strict';

const { Router } = require('../lib/router.js');
const { requireAuth } = require('../middleware/auth.js');
const svc = require('../service/ticket.js');

const router = new Router();

router.use(requireAuth);

router.get('/support/ticket', async (req, res) => {
  res.json(await svc.listTicket(req.query.limit || 50));
});

router.post('/support/ticket', async (req, res) => {
  res.json(await svc.createTicket(req.body));
});

module.exports = router;
