'use strict';

const { db } = require('../lib/db.js');

async function listInvite(limit) {
  return db.execute({ sql: 'SELECT * FROM invites ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createInvite(body) {
  return db.execute({ sql: 'INSERT INTO invites (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listInvite, createInvite };
