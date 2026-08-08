'use strict';

const { db } = require('../../../../lib/db.js');

// SupplierService reads and writes for the catalog area.

async function getSupplierServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM supplier_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listSupplierServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM supplier_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateSupplierService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE supplier_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getSupplierServiceById(id);
}

module.exports = { getSupplierServiceById, listSupplierServices, updateSupplierService };
