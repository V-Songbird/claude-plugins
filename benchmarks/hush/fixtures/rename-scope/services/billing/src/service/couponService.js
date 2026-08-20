'use strict';

const repo = require('../repo/coupon.js');
const { audit } = require('../../../../lib/audit.js');

// Coupon rules for the billing service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchCoupon({ account_id, id }) {
  if (!account_id) throw new Error('couponService: missing account_id');
  const row = await repo.getCoupon(account_id, id);
  if (!row) return null;
  audit('billing.coupon.read', { account_id, id });
  return row;
}

async function pageCoupons({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listCoupons(account_id, size, page * size);
  const total = await repo.countCoupons(account_id);
  return { rows, total, page, size, account_id };
}

async function createCoupon({ account_id, values }) {
  const created = await repo.insertCoupon(account_id, values);
  audit('billing.coupon.create', { account_id });
  return created;
}

async function removeCoupon({ account_id, id }) {
  await repo.deleteCoupon(account_id, id);
  audit('billing.coupon.delete', { account_id, id });
}

module.exports = { fetchCoupon, pageCoupons, createCoupon, removeCoupon };
