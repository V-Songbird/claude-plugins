'use strict';

const { db } = require('../../../../lib/db.js');

// Retention rows for the analytics service. Everything here is scoped to one
// account: no query in this file may run without an account_id.

async function getRetention(account_id, id) {
  const rows = await db.execute({
    sql: 'SELECT * FROM retentions WHERE account_id = ? AND id = ?',
    params: [account_id, id],
  });
  return rows[0] || null;
}

async function listRetentions(account_id, limit, offset) {
  return db.execute({
    sql: 'SELECT * FROM retentions WHERE account_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
    params: [account_id, limit, offset],
  });
}

async function countRetentions(account_id) {
  const rows = await db.execute({
    sql: 'SELECT COUNT(*) AS n FROM retentions WHERE account_id = ?',
    params: [account_id],
  });
  return rows[0] ? rows[0].n : 0;
}

async function insertRetention(account_id, values) {
  if (!account_id) throw new Error('retention: account_id is required');
  return db.execute({
    sql: 'INSERT INTO retentions (account_id, payload) VALUES (?, ?)',
    params: [account_id, JSON.stringify({ ...values, account_id })],
  });
}

async function deleteRetention(account_id, id) {
  return db.execute({
    sql: 'DELETE FROM retentions WHERE account_id = ? AND id = ?',
    params: [account_id, id],
  });
}

module.exports = {
  getRetention, listRetentions, countRetentions, insertRetention, deleteRetention,
};
