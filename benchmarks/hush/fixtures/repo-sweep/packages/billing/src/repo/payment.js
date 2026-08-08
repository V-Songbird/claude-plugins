'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Payment reads and writes for the billing area.

async function getPaymentById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM payments WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listPayments(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM payments ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedPayment(id) {
  const hit = await cache.query('payments:' + id);
  if (hit) return hit;
  const row = await getPaymentById(id);
  await cache.set('payments:' + id, row);
  return row;
}

async function updatePayment(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE payments SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getPaymentById(id);
}

module.exports = { getPaymentById, listPayments, updatePayment, cachedPayment };
