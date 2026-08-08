'use strict';

const { db } = require('../lib/db.js');

async function listInvoice(limit) {
  return db.execute({ sql: 'SELECT * FROM invoices ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createInvoice(body) {
  return db.execute({ sql: 'INSERT INTO invoices (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listInvoice, createInvoice };
