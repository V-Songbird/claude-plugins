'use strict';

const { db } = require('../lib/db.js');

async function listVariant(limit) {
  return db.execute({ sql: 'SELECT * FROM variants ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createVariant(body) {
  return db.execute({ sql: 'INSERT INTO variants (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listVariant, createVariant };
