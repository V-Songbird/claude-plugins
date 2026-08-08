'use strict';

const { db } = require('../../../../lib/db.js');

// OrderService reads and writes for the orders area.

async function getOrderServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM order_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listOrderServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM order_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateOrderService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE order_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getOrderServiceById(id);
}

module.exports = { getOrderServiceById, listOrderServices, updateOrderService };
