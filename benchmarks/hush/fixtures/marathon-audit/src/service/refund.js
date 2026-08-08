'use strict';

const { db } = require('../lib/db.js');

async function listRefund(limit) {
  return db.execute({ sql: 'SELECT * FROM refunds ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createRefund(body) {
  return db.execute({ sql: 'INSERT INTO refunds (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listRefund, createRefund };
