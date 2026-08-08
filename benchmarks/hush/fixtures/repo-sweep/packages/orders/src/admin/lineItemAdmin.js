'use strict';

const { db } = require('../../../../lib/db.js');

// LineItemAdmin reads and writes for the orders area.

async function getLineItemAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM line_item_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listLineItemAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM line_item_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateLineItemAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE line_item_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getLineItemAdminById(id);
}

module.exports = { getLineItemAdminById, listLineItemAdmins, updateLineItemAdmin };
