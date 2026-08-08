'use strict';

const { db } = require('../lib/db.js');

async function listStatus(limit) {
  return db.execute({ sql: 'SELECT * FROM statuss ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createStatus(body) {
  return db.execute({ sql: 'INSERT INTO statuss (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listStatus, createStatus };
