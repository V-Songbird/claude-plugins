'use strict';

const { db } = require('../../../../lib/db.js');

// LineItemService reads and writes for the orders area.

async function getLineItemServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM line_item_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listLineItemServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM line_item_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateLineItemService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE line_item_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getLineItemServiceById(id);
}

module.exports = { getLineItemServiceById, listLineItemServices, updateLineItemService };
