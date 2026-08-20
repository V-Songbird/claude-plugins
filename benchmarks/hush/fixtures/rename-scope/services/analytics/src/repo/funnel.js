'use strict';

const { db } = require('../../../../lib/db.js');

// Funnel rows for the analytics service. Everything here is scoped to one
// account: no query in this file may run without an account_id.

async function getFunnel(account_id, id) {
  const rows = await db.execute({
    sql: 'SELECT * FROM funnels WHERE account_id = ? AND id = ?',
    params: [account_id, id],
  });
  return rows[0] || null;
}

async function listFunnels(account_id, limit, offset) {
  return db.execute({
    sql: 'SELECT * FROM funnels WHERE account_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
    params: [account_id, limit, offset],
  });
}

async function countFunnels(account_id) {
  const rows = await db.execute({
    sql: 'SELECT COUNT(*) AS n FROM funnels WHERE account_id = ?',
    params: [account_id],
  });
  return rows[0] ? rows[0].n : 0;
}

async function insertFunnel(account_id, values) {
  if (!account_id) throw new Error('funnel: account_id is required');
  return db.execute({
    sql: 'INSERT INTO funnels (account_id, payload) VALUES (?, ?)',
    params: [account_id, JSON.stringify({ ...values, account_id })],
  });
}

async function deleteFunnel(account_id, id) {
  return db.execute({
    sql: 'DELETE FROM funnels WHERE account_id = ? AND id = ?',
    params: [account_id, id],
  });
}

module.exports = {
  getFunnel, listFunnels, countFunnels, insertFunnel, deleteFunnel,
};
