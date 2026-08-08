'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Variant reads and writes for the catalog area.

async function getVariantById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM variants WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listVariants(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM variants ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedVariant(id) {
  const hit = await cache.query('variants:' + id);
  if (hit) return hit;
  const row = await getVariantById(id);
  await cache.set('variants:' + id, row);
  return row;
}

async function updateVariant(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE variants SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getVariantById(id);
}

module.exports = { getVariantById, listVariants, updateVariant, cachedVariant };
