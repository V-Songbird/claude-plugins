'use strict';

const { db } = require('../lib/db.js');

async function listHealth(limit) {
  return db.execute({ sql: 'SELECT * FROM healths ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createHealth(body) {
  return db.execute({ sql: 'INSERT INTO healths (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listHealth, createHealth };
