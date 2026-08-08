'use strict';

const { db } = require('../../../../lib/db.js');

// ProductAdmin reads and writes for the catalog area.

async function getProductAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM product_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listProductAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM product_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateProductAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE product_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getProductAdminById(id);
}

module.exports = { getProductAdminById, listProductAdmins, updateProductAdmin };
