'use strict';

const { db } = require('../../../../lib/db.js');

// SupplierAdmin reads and writes for the catalog area.

async function getSupplierAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM supplier_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listSupplierAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM supplier_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateSupplierAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE supplier_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getSupplierAdminById(id);
}

module.exports = { getSupplierAdminById, listSupplierAdmins, updateSupplierAdmin };
