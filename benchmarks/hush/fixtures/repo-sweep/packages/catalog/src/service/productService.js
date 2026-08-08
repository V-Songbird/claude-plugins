'use strict';

const { db } = require('../../../../lib/db.js');

// ProductService reads and writes for the catalog area.

async function getProductServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM product_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listProductServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM product_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateProductService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE product_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getProductServiceById(id);
}

module.exports = { getProductServiceById, listProductServices, updateProductService };
