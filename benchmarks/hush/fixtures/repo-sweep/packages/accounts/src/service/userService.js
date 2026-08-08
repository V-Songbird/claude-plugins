'use strict';

const { db } = require('../../../../lib/db.js');

// UserService reads and writes for the accounts area.

async function getUserServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM user_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listUserServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM user_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateUserService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE user_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getUserServiceById(id);
}

module.exports = { getUserServiceById, listUserServices, updateUserService };
