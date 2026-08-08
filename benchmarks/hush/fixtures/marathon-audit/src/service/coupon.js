'use strict';

const { db } = require('../lib/db.js');

async function listCoupon(limit) {
  return db.execute({ sql: 'SELECT * FROM coupons ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createCoupon(body) {
  return db.execute({ sql: 'INSERT INTO coupons (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listCoupon, createCoupon };
