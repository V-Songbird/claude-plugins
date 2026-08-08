'use strict';

const { db } = require('../../../../lib/db.js');

// SlaAdmin reads and writes for the support area.

async function getSlaAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM sla_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listSlaAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM sla_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateSlaAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE sla_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getSlaAdminById(id);
}

module.exports = { getSlaAdminById, listSlaAdmins, updateSlaAdmin };
