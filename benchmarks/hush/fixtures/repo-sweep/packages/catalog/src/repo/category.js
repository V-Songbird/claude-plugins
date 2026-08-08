'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Category reads and writes for the catalog area.

async function getCategoryById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM categorys WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listCategorys(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM categorys ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedCategory(id) {
  const hit = await cache.query('categorys:' + id);
  if (hit) return hit;
  const row = await getCategoryById(id);
  await cache.set('categorys:' + id, row);
  return row;
}

async function updateCategory(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE categorys SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getCategoryById(id);
}

module.exports = { getCategoryById, listCategorys, updateCategory, cachedCategory };
