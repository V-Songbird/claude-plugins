'use strict';

const { db } = require('../lib/db.js');

async function listSubscription(limit) {
  return db.execute({ sql: 'SELECT * FROM subscriptions ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createSubscription(body) {
  return db.execute({ sql: 'INSERT INTO subscriptions (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listSubscription, createSubscription };
