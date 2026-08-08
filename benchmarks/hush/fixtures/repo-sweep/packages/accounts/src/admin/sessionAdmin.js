'use strict';

const { db } = require('../../../../lib/db.js');

// SessionAdmin reads and writes for the accounts area.

async function getSessionAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM session_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listSessionAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM session_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateSessionAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE session_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getSessionAdminById(id);
}

module.exports = { getSessionAdminById, listSessionAdmins, updateSessionAdmin };
