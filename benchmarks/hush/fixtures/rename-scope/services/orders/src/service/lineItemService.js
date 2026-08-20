'use strict';

const repo = require('../repo/lineItem.js');
const { audit } = require('../../../../lib/audit.js');

// LineItem rules for the orders service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchLineItem({ account_id, id }) {
  if (!account_id) throw new Error('lineItemService: missing account_id');
  const row = await repo.getLineItem(account_id, id);
  if (!row) return null;
  audit('orders.lineItem.read', { account_id, id });
  return row;
}

async function pageLineItems({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listLineItems(account_id, size, page * size);
  const total = await repo.countLineItems(account_id);
  return { rows, total, page, size, account_id };
}

async function createLineItem({ account_id, values }) {
  const created = await repo.insertLineItem(account_id, values);
  audit('orders.lineItem.create', { account_id });
  return created;
}

async function removeLineItem({ account_id, id }) {
  await repo.deleteLineItem(account_id, id);
  audit('orders.lineItem.delete', { account_id, id });
}

module.exports = { fetchLineItem, pageLineItems, createLineItem, removeLineItem };
