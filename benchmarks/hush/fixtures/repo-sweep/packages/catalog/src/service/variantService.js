'use strict';

const { db } = require('../../../../lib/db.js');

// VariantService reads and writes for the catalog area.

async function getVariantServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM variant_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listVariantServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM variant_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateVariantService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE variant_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getVariantServiceById(id);
}

module.exports = { getVariantServiceById, listVariantServices, updateVariantService };
