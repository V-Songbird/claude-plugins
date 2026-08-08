'use strict';

const { db } = require('../../../../lib/db.js');

// InviteService reads and writes for the accounts area.

async function getInviteServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM invite_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listInviteServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM invite_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateInviteService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE invite_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getInviteServiceById(id);
}

module.exports = { getInviteServiceById, listInviteServices, updateInviteService };
