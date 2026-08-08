'use strict';

const { db } = require('../lib/db.js');

async function listVersion(limit) {
  return db.execute({ sql: 'SELECT * FROM versions ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createVersion(body) {
  return db.execute({ sql: 'INSERT INTO versions (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listVersion, createVersion };
