'use strict';

const { db } = require('../../../../lib/db.js');

// InviteAdmin reads and writes for the accounts area.

async function getInviteAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM invite_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listInviteAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM invite_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateInviteAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE invite_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getInviteAdminById(id);
}

module.exports = { getInviteAdminById, listInviteAdmins, updateInviteAdmin };
