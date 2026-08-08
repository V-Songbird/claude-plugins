'use strict';

const { db } = require('../lib/db.js');

async function listMacro(limit) {
  return db.execute({ sql: 'SELECT * FROM macros ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createMacro(body) {
  return db.execute({ sql: 'INSERT INTO macros (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listMacro, createMacro };
