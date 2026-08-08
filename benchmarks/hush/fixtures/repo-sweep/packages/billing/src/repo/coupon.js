'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Coupon reads and writes for the billing area.

async function getCouponById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM coupons WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listCoupons(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM coupons ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedCoupon(id) {
  const hit = await cache.query('coupons:' + id);
  if (hit) return hit;
  const row = await getCouponById(id);
  await cache.set('coupons:' + id, row);
  return row;
}

async function updateCoupon(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE coupons SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getCouponById(id);
}

module.exports = { getCouponById, listCoupons, updateCoupon, cachedCoupon };
