'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Return reads and writes for the orders area.

async function getReturnById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM returns WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listReturns(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM returns ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedReturn(id) {
  const hit = await cache.query('returns:' + id);
  if (hit) return hit;
  const row = await getReturnById(id);
  await cache.set('returns:' + id, row);
  return row;
}

async function updateReturn(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE returns SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getReturnById(id);
}

module.exports = { getReturnById, listReturns, updateReturn, cachedReturn };
