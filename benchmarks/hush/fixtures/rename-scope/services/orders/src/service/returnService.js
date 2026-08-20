'use strict';

const repo = require('../repo/return.js');
const { audit } = require('../../../../lib/audit.js');

// Return rules for the orders service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchReturn({ account_id, id }) {
  if (!account_id) throw new Error('returnService: missing account_id');
  const row = await repo.getReturn(account_id, id);
  if (!row) return null;
  audit('orders.return.read', { account_id, id });
  return row;
}

async function pageReturns({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listReturns(account_id, size, page * size);
  const total = await repo.countReturns(account_id);
  return { rows, total, page, size, account_id };
}

async function createReturn({ account_id, values }) {
  const created = await repo.insertReturn(account_id, values);
  audit('orders.return.create', { account_id });
  return created;
}

async function removeReturn({ account_id, id }) {
  await repo.deleteReturn(account_id, id);
  audit('orders.return.delete', { account_id, id });
}

module.exports = { fetchReturn, pageReturns, createReturn, removeReturn };
