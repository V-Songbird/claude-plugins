'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Role reads and writes for the accounts area.

async function getRoleById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM roles WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listRoles(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM roles ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedRole(id) {
  const hit = await cache.query('roles:' + id);
  if (hit) return hit;
  const row = await getRoleById(id);
  await cache.set('roles:' + id, row);
  return row;
}

async function updateRole(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE roles SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getRoleById(id);
}

module.exports = { getRoleById, listRoles, updateRole, cachedRole };
