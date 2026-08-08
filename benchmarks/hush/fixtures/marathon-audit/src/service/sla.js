'use strict';

const { db } = require('../lib/db.js');

async function listSla(limit) {
  return db.execute({ sql: 'SELECT * FROM slas ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createSla(body) {
  return db.execute({ sql: 'INSERT INTO slas (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listSla, createSla };
