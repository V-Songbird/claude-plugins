'use strict';

const { db } = require('../lib/db.js');

async function listApiKey(limit) {
  return db.execute({ sql: 'SELECT * FROM apiKeys ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createApiKey(body) {
  return db.execute({ sql: 'INSERT INTO apiKeys (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listApiKey, createApiKey };
