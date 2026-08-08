'use strict';

const { db } = require('../lib/db.js');

async function listLogin(limit) {
  return db.execute({ sql: 'SELECT * FROM logins ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createLogin(body) {
  return db.execute({ sql: 'INSERT INTO logins (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listLogin, createLogin };
