'use strict';

const repo = require('../repo/refund.js');
const { audit } = require('../../../../lib/audit.js');

// Refund rules for the billing service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchRefund({ account_id, id }) {
  if (!account_id) throw new Error('refundService: missing account_id');
  const row = await repo.getRefund(account_id, id);
  if (!row) return null;
  audit('billing.refund.read', { account_id, id });
  return row;
}

async function pageRefunds({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listRefunds(account_id, size, page * size);
  const total = await repo.countRefunds(account_id);
  return { rows, total, page, size, account_id };
}

async function createRefund({ account_id, values }) {
  const created = await repo.insertRefund(account_id, values);
  audit('billing.refund.create', { account_id });
  return created;
}

async function removeRefund({ account_id, id }) {
  await repo.deleteRefund(account_id, id);
  audit('billing.refund.delete', { account_id, id });
}

module.exports = { fetchRefund, pageRefunds, createRefund, removeRefund };
