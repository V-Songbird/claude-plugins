'use strict';

const { db } = require('../../../../lib/db.js');

// ReturnAdmin reads and writes for the orders area.

async function getReturnAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM return_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listReturnAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM return_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateReturnAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE return_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getReturnAdminById(id);
}

module.exports = { getReturnAdminById, listReturnAdmins, updateReturnAdmin };
