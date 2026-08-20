'use strict';

const { db } = require('../../../../lib/db.js');

// LineItem rows for the orders service. Everything here is scoped to one
// account: no query in this file may run without an account_id.

async function getLineItem(account_id, id) {
  const rows = await db.execute({
    sql: 'SELECT * FROM line_items WHERE account_id = ? AND id = ?',
    params: [account_id, id],
  });
  return rows[0] || null;
}

async function listLineItems(account_id, limit, offset) {
  return db.execute({
    sql: 'SELECT * FROM line_items WHERE account_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
    params: [account_id, limit, offset],
  });
}

async function countLineItems(account_id) {
  const rows = await db.execute({
    sql: 'SELECT COUNT(*) AS n FROM line_items WHERE account_id = ?',
    params: [account_id],
  });
  return rows[0] ? rows[0].n : 0;
}

async function insertLineItem(account_id, values) {
  if (!account_id) throw new Error('lineItem: account_id is required');
  return db.execute({
    sql: 'INSERT INTO line_items (account_id, payload) VALUES (?, ?)',
    params: [account_id, JSON.stringify({ ...values, account_id })],
  });
}

async function deleteLineItem(account_id, id) {
  return db.execute({
    sql: 'DELETE FROM line_items WHERE account_id = ? AND id = ?',
    params: [account_id, id],
  });
}

module.exports = {
  getLineItem, listLineItems, countLineItems, insertLineItem, deleteLineItem,
};
