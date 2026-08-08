'use strict';

const { db } = require('../lib/db.js');

async function listOrder(limit) {
  return db.execute({ sql: 'SELECT * FROM orders ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createOrder(body) {
  return db.execute({ sql: 'INSERT INTO orders (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listOrder, createOrder };
