'use strict';

const { db } = require('../../../../lib/db.js');

// RoleAdmin reads and writes for the accounts area.

async function getRoleAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM role_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listRoleAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM role_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateRoleAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE role_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getRoleAdminById(id);
}

module.exports = { getRoleAdminById, listRoleAdmins, updateRoleAdmin };
