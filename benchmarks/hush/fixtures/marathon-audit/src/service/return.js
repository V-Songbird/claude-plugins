'use strict';

const { db } = require('../lib/db.js');

async function listReturn(limit) {
  return db.execute({ sql: 'SELECT * FROM returns ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createReturn(body) {
  return db.execute({ sql: 'INSERT INTO returns (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listReturn, createReturn };
