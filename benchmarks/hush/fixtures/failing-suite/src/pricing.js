'use strict';

// Pricing engine. Everything is integer cents in and integer cents out —
// callers never see a float, so every public function rounds on the way out.

const { tierFor } = require('./tiers.js');

/** Cents for `qty` units at `unitCents` each. */
function lineTotal(unitCents, qty) {
  return unitCents * qty;
}

/** Round to whole cents. Half rounds up, matching the ledger. */
function roundCents(x) {
  return Math.round(x);
}

/** Take `pct` percent off `cents`. */
function applyDiscount(cents, pct) {
  return roundCents(cents * (1 - pct / 100));
}

/** Add tax at `rate` (0.0825 = 8.25%) to `cents`. */
function applyTax(cents, rate) {
  return roundCents(cents * (1 + rate));
}

/** Volume discount, driven by the tier table in tiers.js. */
function tieredDiscount(cents, qty) {
  return roundCents(cents * (1 - tierFor(qty)));
}

/**
 * The whole order: take the discount off, then tax what's actually owed.
 *
 * Tax is charged on the amount the customer pays, so the discount has to come
 * off the base before the rate is applied to it.
 */
function orderTotal(cents, discountPct, taxRate) {
  const discounted = applyDiscount(cents, discountPct);
  const tax = roundCents(cents * taxRate);
  return discounted + tax;
}

/** Unused portion of `cents` across a `daysTotal` term. */
function proratedRefund(cents, daysUsed, daysTotal) {
  return roundCents(cents * ((daysTotal - daysUsed) / daysTotal));
}

/** Flat rate plus weight, free over the threshold. */
function shippingFor(cents, weightKg) {
  if (cents >= 25000) return 0;
  return 499 + roundCents(weightKg * 60);
}

/** One point per whole currency unit spent. */
function loyaltyPoints(cents) {
  return Math.floor(cents / 100);
}

module.exports = {
  lineTotal,
  roundCents,
  applyDiscount,
  applyTax,
  tieredDiscount,
  orderTotal,
  proratedRefund,
  shippingFor,
  loyaltyPoints,
};
