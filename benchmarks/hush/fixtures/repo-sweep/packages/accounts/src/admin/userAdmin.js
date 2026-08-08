'use strict';

const { db } = require('../../../../lib/db.js');

// UserAdmin reads and writes for the accounts area.

async function getUserAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM user_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listUserAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM user_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateUserAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE user_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getUserAdminById(id);
}

module.exports = { getUserAdminById, listUserAdmins, updateUserAdmin };
