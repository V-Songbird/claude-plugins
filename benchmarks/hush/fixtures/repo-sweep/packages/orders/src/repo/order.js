'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Order reads and writes for the orders area.

async function getOrderById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM orders WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listOrders(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedOrder(id) {
  const hit = await cache.query('orders:' + id);
  if (hit) return hit;
  const row = await getOrderById(id);
  await cache.set('orders:' + id, row);
  return row;
}

async function updateOrder(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE orders SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getOrderById(id);
}

module.exports = { getOrderById, listOrders, updateOrder, cachedOrder };
