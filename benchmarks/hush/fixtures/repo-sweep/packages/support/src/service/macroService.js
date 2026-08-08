'use strict';

const { db } = require('../../../../lib/db.js');

// MacroService reads and writes for the support area.

async function getMacroServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM macro_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listMacroServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM macro_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateMacroService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE macro_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getMacroServiceById(id);
}

module.exports = { getMacroServiceById, listMacroServices, updateMacroService };
