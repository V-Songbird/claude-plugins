'use strict';

const { db } = require('../../../../lib/db.js');

// OrderAdmin reads and writes for the orders area.

async function getOrderAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM order_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listOrderAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM order_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateOrderAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE order_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getOrderAdminById(id);
}

module.exports = { getOrderAdminById, listOrderAdmins, updateOrderAdmin };
