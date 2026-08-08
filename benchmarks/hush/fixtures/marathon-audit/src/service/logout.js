'use strict';

const { db } = require('../lib/db.js');

async function listLogout(limit) {
  return db.execute({ sql: 'SELECT * FROM logouts ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createLogout(body) {
  return db.execute({ sql: 'INSERT INTO logouts (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listLogout, createLogout };
