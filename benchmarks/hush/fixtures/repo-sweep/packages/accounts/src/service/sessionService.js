'use strict';

const { db } = require('../../../../lib/db.js');

// SessionService reads and writes for the accounts area.

async function getSessionServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM session_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listSessionServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM session_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateSessionService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE session_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getSessionServiceById(id);
}

module.exports = { getSessionServiceById, listSessionServices, updateSessionService };
