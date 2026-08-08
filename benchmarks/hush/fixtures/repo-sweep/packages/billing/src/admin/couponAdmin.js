'use strict';

const { db } = require('../../../../lib/db.js');

// CouponAdmin reads and writes for the billing area.

async function getCouponAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM coupon_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listCouponAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM coupon_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateCouponAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE coupon_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getCouponAdminById(id);
}

module.exports = { getCouponAdminById, listCouponAdmins, updateCouponAdmin };
