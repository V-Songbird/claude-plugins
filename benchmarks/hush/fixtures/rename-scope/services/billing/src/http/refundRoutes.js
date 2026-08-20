'use strict';

const service = require('../service/refundService.js');
const { serialize } = require('../../../../lib/serialize.js');

// HTTP handlers for refund in the billing service. The account_id comes off the
// verified session, never off the request body.

async function handleGet(req, res) {
  const account_id = req.session.account_id;
  const row = await service.fetchRefund({ account_id, id: req.params.id });
  if (!row) return res.status(404).json({ error: 'not_found' });
  return res.json(serialize('refund', row));
}

async function handleList(req, res) {
  const account_id = req.session.account_id;
  const page = await service.pageRefunds({ account_id, page: Number(req.query.page || 0) });
  return res.json({
    data: page.rows.map((r) => serialize('refund', r)),
    total: page.total,
  });
}

async function handleCreate(req, res) {
  const account_id = req.session.account_id;
  const created = await service.createRefund({ account_id, values: req.body });
  return res.status(201).json(serialize('refund', created));
}

async function handleDelete(req, res) {
  const account_id = req.session.account_id;
  await service.removeRefund({ account_id, id: req.params.id });
  return res.status(204).end();
}

module.exports = { handleGet, handleList, handleCreate, handleDelete };
