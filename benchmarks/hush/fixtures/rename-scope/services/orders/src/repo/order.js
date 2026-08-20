'use strict';

const { db } = require('../../../../lib/db.js');

// Order rows for the orders service. Everything here is scoped to one
// account: no query in this file may run without an account_id.

async function getOrder(account_id, id) {
  const rows = await db.execute({
    sql: 'SELECT * FROM orders WHERE account_id = ? AND id = ?',
    params: [account_id, id],
  });
  return rows[0] || null;
}

async function listOrders(account_id, limit, offset) {
  return db.execute({
    sql: 'SELECT * FROM orders WHERE account_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
    params: [account_id, limit, offset],
  });
}

async function countOrders(account_id) {
  const rows = await db.execute({
    sql: 'SELECT COUNT(*) AS n FROM orders WHERE account_id = ?',
    params: [account_id],
  });
  return rows[0] ? rows[0].n : 0;
}

async function insertOrder(account_id, values) {
  if (!account_id) throw new Error('order: account_id is required');
  return db.execute({
    sql: 'INSERT INTO orders (account_id, payload) VALUES (?, ?)',
    params: [account_id, JSON.stringify({ ...values, account_id })],
  });
}

async function deleteOrder(account_id, id) {
  return db.execute({
    sql: 'DELETE FROM orders WHERE account_id = ? AND id = ?',
    params: [account_id, id],
  });
}

module.exports = {
  getOrder, listOrders, countOrders, insertOrder, deleteOrder,
};
