'use strict';

const repo = require('../repo/order.js');
const { audit } = require('../../../../lib/audit.js');

// Order rules for the orders service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchOrder({ account_id, id }) {
  if (!account_id) throw new Error('orderService: missing account_id');
  const row = await repo.getOrder(account_id, id);
  if (!row) return null;
  audit('orders.order.read', { account_id, id });
  return row;
}

async function pageOrders({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listOrders(account_id, size, page * size);
  const total = await repo.countOrders(account_id);
  return { rows, total, page, size, account_id };
}

async function createOrder({ account_id, values }) {
  const created = await repo.insertOrder(account_id, values);
  audit('orders.order.create', { account_id });
  return created;
}

async function removeOrder({ account_id, id }) {
  await repo.deleteOrder(account_id, id);
  audit('orders.order.delete', { account_id, id });
}

module.exports = { fetchOrder, pageOrders, createOrder, removeOrder };
