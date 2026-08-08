'use strict';

const { db } = require('../../../../lib/db.js');

// CouponService reads and writes for the billing area.

async function getCouponServiceById(id) {
  const rows = await db.query('SELECT * FROM coupon_services WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listCouponServices(limit, offset) {
  return db.query('SELECT * FROM coupon_services ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function updateCouponService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE coupon_services SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getCouponServiceById(id);
}

module.exports = { getCouponServiceById, listCouponServices, updateCouponService };
