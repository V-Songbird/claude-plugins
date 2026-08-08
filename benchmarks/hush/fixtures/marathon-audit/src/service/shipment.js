'use strict';

const { db } = require('../lib/db.js');

async function listShipment(limit) {
  return db.execute({ sql: 'SELECT * FROM shipments ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createShipment(body) {
  return db.execute({ sql: 'INSERT INTO shipments (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listShipment, createShipment };
