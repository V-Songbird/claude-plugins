'use strict';

const { db } = require('../lib/db.js');

async function listTicket(limit) {
  return db.execute({ sql: 'SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createTicket(body) {
  return db.execute({ sql: 'INSERT INTO tickets (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listTicket, createTicket };
