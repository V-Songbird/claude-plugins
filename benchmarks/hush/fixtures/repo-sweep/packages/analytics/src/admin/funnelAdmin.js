'use strict';

const { db } = require('../../../../lib/db.js');

// FunnelAdmin reads and writes for the analytics area.

async function getFunnelAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM funnel_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listFunnelAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM funnel_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateFunnelAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE funnel_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getFunnelAdminById(id);
}

module.exports = { getFunnelAdminById, listFunnelAdmins, updateFunnelAdmin };
