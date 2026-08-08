'use strict';

const { db } = require('../lib/db.js');

async function listProduct(limit) {
  return db.execute({ sql: 'SELECT * FROM products ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createProduct(body) {
  return db.execute({ sql: 'INSERT INTO products (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listProduct, createProduct };
