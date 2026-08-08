'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// LineItem reads and writes for the orders area.

async function getLineItemById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM line_items WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listLineItems(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM line_items ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedLineItem(id) {
  const hit = await cache.query('line_items:' + id);
  if (hit) return hit;
  const row = await getLineItemById(id);
  await cache.set('line_items:' + id, row);
  return row;
}

async function updateLineItem(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE line_items SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getLineItemById(id);
}

module.exports = { getLineItemById, listLineItems, updateLineItem, cachedLineItem };
