'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Product reads and writes for the catalog area.

async function getProductById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM products WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listProducts(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM products ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedProduct(id) {
  const hit = await cache.query('products:' + id);
  if (hit) return hit;
  const row = await getProductById(id);
  await cache.set('products:' + id, row);
  return row;
}

async function updateProduct(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE products SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getProductById(id);
}

module.exports = { getProductById, listProducts, updateProduct, cachedProduct };
