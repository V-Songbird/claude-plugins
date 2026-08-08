'use strict';

const { db } = require('../../../../lib/db.js');

// SlaService reads and writes for the support area.

async function getSlaServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM sla_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listSlaServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM sla_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateSlaService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE sla_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getSlaServiceById(id);
}

module.exports = { getSlaServiceById, listSlaServices, updateSlaService };
