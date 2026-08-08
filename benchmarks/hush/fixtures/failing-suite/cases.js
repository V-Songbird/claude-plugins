'use strict';

// The spec, as data. Every `expect` is computed here from the rule the pricing
// engine is supposed to implement, independently of src/pricing.js — so a case
// fails when the engine disagrees with the rule, not when it disagrees with
// itself. All arithmetic is in integer cents unless a suite says otherwise.

const round = (x) => Math.round(x);

// --- suite builders ---------------------------------------------------------

function lineTotals() {
  const cases = [];
  for (let i = 0; i < 70; i++) {
    const unit = 199 + i * 37;
    const qty = 1 + (i % 12);
    cases.push({
      name: `${qty} x ${unit}c line total`,
      fn: 'lineTotal',
      args: [unit, qty],
      expect: unit * qty,
    });
  }
  return { name: 'line totals', cases };
}

function discounts() {
  const cases = [];
  for (let i = 0; i < 120; i++) {
    const cents = 1000 + i * 511;
    const pct = (i % 8) * 5;
    cases.push({
      name: `${pct}% off ${cents}c`,
      fn: 'applyDiscount',
      args: [cents, pct],
      expect: round(cents * (1 - pct / 100)),
    });
  }
  return { name: 'discounts', cases };
}

function taxes() {
  const cases = [];
  for (let i = 0; i < 120; i++) {
    const cents = 750 + i * 613;
    const rate = [0, 0.05, 0.075, 0.0825, 0.2][i % 5];
    cases.push({
      name: `tax at ${rate} on ${cents}c`,
      fn: 'applyTax',
      args: [cents, rate],
      expect: round(cents * (1 + rate)),
    });
  }
  return { name: 'taxes', cases };
}

function tiers() {
  const cases = [];
  const tier = (qty) => (qty >= 500 ? 0.2 : qty >= 100 ? 0.1 : qty >= 25 ? 0.05 : 0);
  for (let i = 0; i < 56; i++) {
    const cents = 2000 + i * 907;
    const qty = [1, 12, 24, 25, 60, 99, 100, 220, 499, 500, 900, 1500][i % 12];
    cases.push({
      name: `tier for qty ${qty} on ${cents}c`,
      fn: 'tieredDiscount',
      args: [cents, qty],
      expect: round(cents * (1 - tier(qty))),
    });
  }
  return { name: 'volume tiers', cases };
}

// The order-total suite. Most rows have a zero discount or a zero tax, which
// hides an ordering mistake — only a row with both non-zero can expose it.
function orderTotals() {
  const cases = [];
  const rows = [];
  for (let i = 0; i < 54; i++) rows.push([4000 + i * 733, 0, [0, 0.05, 0.0825][i % 3]]);
  for (let i = 0; i < 12; i++) rows.push([5200 + i * 811, [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60][i], 0]);
  rows.push([12000, 15, 0.0825]);
  rows.push([8650, 20, 0.05]);
  rows.push([33400, 10, 0.2]);
  for (const [cents, pct, rate] of rows) {
    cases.push({
      name: `total ${cents}c, ${pct}% off, tax ${rate}`,
      fn: 'orderTotal',
      args: [cents, pct, rate],
      // Discount first, then tax on the discounted amount.
      expect: round(round(cents * (1 - pct / 100)) * (1 + rate)),
    });
  }
  return { name: 'order totals', cases };
}

function refunds() {
  const cases = [];
  for (let i = 0; i < 52; i++) {
    const cents = 6000 + i * 449;
    const total = [30, 31, 365, 90][i % 4];
    const used = (i * 7) % total;
    cases.push({
      name: `refund ${used}/${total} days of ${cents}c`,
      fn: 'proratedRefund',
      args: [cents, used, total],
      expect: round(cents * ((total - used) / total)),
    });
  }
  return { name: 'prorated refunds', cases };
}

function shipping() {
  const cases = [];
  for (let i = 0; i < 48; i++) {
    const cents = 1500 + i * 1201;
    const kg = 0.5 + (i % 9);
    const base = cents >= 25000 ? 0 : 499;
    cases.push({
      name: `shipping ${kg}kg on ${cents}c`,
      fn: 'shippingFor',
      args: [cents, kg],
      expect: base === 0 ? 0 : base + round(kg * 60),
    });
  }
  return { name: 'shipping', cases };
}

function loyalty() {
  const cases = [];
  for (let i = 0; i < 46; i++) {
    const cents = 300 + i * 1777;
    cases.push({
      name: `points for ${cents}c`,
      fn: 'loyaltyPoints',
      args: [cents],
      expect: Math.floor(cents / 100),
    });
  }
  return { name: 'loyalty points', cases };
}

function rounding() {
  const cases = [];
  for (let i = 0; i < 44; i++) {
    const x = i * 13.5 + 0.5;
    cases.push({
      name: `round ${x}`,
      fn: 'roundCents',
      args: [x],
      expect: round(x),
    });
  }
  return { name: 'rounding', cases };
}

module.exports = [
  lineTotals(),
  discounts(),
  taxes(),
  tiers(),
  orderTotals(),
  refunds(),
  shipping(),
  loyalty(),
  rounding(),
];
