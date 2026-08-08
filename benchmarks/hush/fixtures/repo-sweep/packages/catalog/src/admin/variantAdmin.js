'use strict';

const { db } = require('../../../../lib/db.js');

// VariantAdmin reads and writes for the catalog area.

async function getVariantAdminById(id) {
  const rows = await db.query('SELECT * FROM variant_admins WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listVariantAdmins(limit, offset) {
  return db.query('SELECT * FROM variant_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function updateVariantAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE variant_admins SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getVariantAdminById(id);
}

module.exports = { getVariantAdminById, listVariantAdmins, updateVariantAdmin };
