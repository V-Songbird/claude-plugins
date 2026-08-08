'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Macro reads and writes for the support area.

async function getMacroById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM macros WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listMacros(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM macros ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedMacro(id) {
  const hit = await cache.query('macros:' + id);
  if (hit) return hit;
  const row = await getMacroById(id);
  await cache.set('macros:' + id, row);
  return row;
}

async function updateMacro(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE macros SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getMacroById(id);
}

module.exports = { getMacroById, listMacros, updateMacro, cachedMacro };
