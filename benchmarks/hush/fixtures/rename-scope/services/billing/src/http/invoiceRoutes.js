'use strict';

const service = require('../service/invoiceService.js');
const { serialize } = require('../../../../lib/serialize.js');

// HTTP handlers for invoice in the billing service. The account_id comes off the
// verified session, never off the request body.

async function handleGet(req, res) {
  const account_id = req.session.account_id;
  const row = await service.fetchInvoice({ account_id, id: req.params.id });
  if (!row) return res.status(404).json({ error: 'not_found' });
  return res.json(serialize('invoice', row));
}

async function handleList(req, res) {
  const account_id = req.session.account_id;
  const page = await service.pageInvoices({ account_id, page: Number(req.query.page || 0) });
  return res.json({
    data: page.rows.map((r) => serialize('invoice', r)),
    total: page.total,
  });
}

async function handleCreate(req, res) {
  const account_id = req.session.account_id;
  const created = await service.createInvoice({ account_id, values: req.body });
  return res.status(201).json(serialize('invoice', created));
}

async function handleDelete(req, res) {
  const account_id = req.session.account_id;
  await service.removeInvoice({ account_id, id: req.params.id });
  return res.status(204).end();
}

module.exports = { handleGet, handleList, handleCreate, handleDelete };
