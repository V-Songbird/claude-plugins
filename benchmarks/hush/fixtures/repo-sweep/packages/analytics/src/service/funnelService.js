'use strict';

const { db } = require('../../../../lib/db.js');

// FunnelService reads and writes for the analytics area.

async function getFunnelServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM funnel_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listFunnelServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM funnel_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateFunnelService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE funnel_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getFunnelServiceById(id);
}

module.exports = { getFunnelServiceById, listFunnelServices, updateFunnelService };
