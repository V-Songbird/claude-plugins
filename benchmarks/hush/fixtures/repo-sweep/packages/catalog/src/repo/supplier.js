'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Supplier reads and writes for the catalog area.

async function getSupplierById(id) {
  const rows = await db.query('SELECT * FROM suppliers WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listSuppliers(limit, offset) {
  return db.query('SELECT * FROM suppliers ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function cachedSupplier(id) {
  const hit = await cache.query('suppliers:' + id);
  if (hit) return hit;
  const row = await getSupplierById(id);
  await cache.set('suppliers:' + id, row);
  return row;
}

async function updateSupplier(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE suppliers SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getSupplierById(id);
}

module.exports = { getSupplierById, listSuppliers, updateSupplier, cachedSupplier };
