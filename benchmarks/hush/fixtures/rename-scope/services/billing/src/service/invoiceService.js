'use strict';

const repo = require('../repo/invoice.js');
const { audit } = require('../../../../lib/audit.js');

// Invoice rules for the billing service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchInvoice({ account_id, id }) {
  if (!account_id) throw new Error('invoiceService: missing account_id');
  const row = await repo.getInvoice(account_id, id);
  if (!row) return null;
  audit('billing.invoice.read', { account_id, id });
  return row;
}

async function pageInvoices({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listInvoices(account_id, size, page * size);
  const total = await repo.countInvoices(account_id);
  return { rows, total, page, size, account_id };
}

async function createInvoice({ account_id, values }) {
  const created = await repo.insertInvoice(account_id, values);
  audit('billing.invoice.create', { account_id });
  return created;
}

async function removeInvoice({ account_id, id }) {
  await repo.deleteInvoice(account_id, id);
  audit('billing.invoice.delete', { account_id, id });
}

module.exports = { fetchInvoice, pageInvoices, createInvoice, removeInvoice };
