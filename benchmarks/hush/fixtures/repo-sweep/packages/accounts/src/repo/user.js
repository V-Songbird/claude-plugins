'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// User reads and writes for the accounts area.

async function getUserById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM users WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listUsers(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedUser(id) {
  const hit = await cache.query('users:' + id);
  if (hit) return hit;
  const row = await getUserById(id);
  await cache.set('users:' + id, row);
  return row;
}

async function updateUser(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE users SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getUserById(id);
}

module.exports = { getUserById, listUsers, updateUser, cachedUser };
