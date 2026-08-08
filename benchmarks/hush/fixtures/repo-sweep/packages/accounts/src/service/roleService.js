'use strict';

const { db } = require('../../../../lib/db.js');

// RoleService reads and writes for the accounts area.

async function getRoleServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM role_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listRoleServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM role_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateRoleService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE role_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getRoleServiceById(id);
}

module.exports = { getRoleServiceById, listRoleServices, updateRoleService };
