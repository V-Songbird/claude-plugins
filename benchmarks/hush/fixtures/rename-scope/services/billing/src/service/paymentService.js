'use strict';

const repo = require('../repo/payment.js');
const { audit } = require('../../../../lib/audit.js');

// Payment rules for the billing service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchPayment({ account_id, id }) {
  if (!account_id) throw new Error('paymentService: missing account_id');
  const row = await repo.getPayment(account_id, id);
  if (!row) return null;
  audit('billing.payment.read', { account_id, id });
  return row;
}

async function pagePayments({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listPayments(account_id, size, page * size);
  const total = await repo.countPayments(account_id);
  return { rows, total, page, size, account_id };
}

async function createPayment({ account_id, values }) {
  const created = await repo.insertPayment(account_id, values);
  audit('billing.payment.create', { account_id });
  return created;
}

async function removePayment({ account_id, id }) {
  await repo.deletePayment(account_id, id);
  audit('billing.payment.delete', { account_id, id });
}

module.exports = { fetchPayment, pagePayments, createPayment, removePayment };
