'use strict';

const { db } = require('../lib/db.js');

async function listFulfilment(limit) {
  return db.execute({ sql: 'SELECT * FROM fulfilments ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createFulfilment(body) {
  return db.execute({ sql: 'INSERT INTO fulfilments (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listFulfilment, createFulfilment };
