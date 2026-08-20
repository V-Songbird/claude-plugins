'use strict';

const service = require('../service/inviteService.js');
const { serialize } = require('../../../../lib/serialize.js');

// HTTP handlers for invite in the accounts service. The account_id comes off the
// verified session, never off the request body.

async function handleGet(req, res) {
  const account_id = req.session.account_id;
  const row = await service.fetchInvite({ account_id, id: req.params.id });
  if (!row) return res.status(404).json({ error: 'not_found' });
  return res.json(serialize('invite', row));
}

async function handleList(req, res) {
  const account_id = req.session.account_id;
  const page = await service.pageInvites({ account_id, page: Number(req.query.page || 0) });
  return res.json({
    data: page.rows.map((r) => serialize('invite', r)),
    total: page.total,
  });
}

async function handleCreate(req, res) {
  const account_id = req.session.account_id;
  const created = await service.createInvite({ account_id, values: req.body });
  return res.status(201).json(serialize('invite', created));
}

async function handleDelete(req, res) {
  const account_id = req.session.account_id;
  await service.removeInvite({ account_id, id: req.params.id });
  return res.status(204).end();
}

module.exports = { handleGet, handleList, handleCreate, handleDelete };
