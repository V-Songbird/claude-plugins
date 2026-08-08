'use strict';

const { db } = require('../../../../lib/db.js');

// MacroAdmin reads and writes for the support area.

async function getMacroAdminById(id) {
  const rows = await db.query('SELECT * FROM macro_admins WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listMacroAdmins(limit, offset) {
  return db.query('SELECT * FROM macro_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function updateMacroAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE macro_admins SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getMacroAdminById(id);
}

module.exports = { getMacroAdminById, listMacroAdmins, updateMacroAdmin };
