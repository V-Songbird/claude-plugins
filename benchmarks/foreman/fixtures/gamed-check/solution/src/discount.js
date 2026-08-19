'use strict';

// Takes a total and a discount PERCENTAGE, returns the discounted total
// rounded to two decimal places.
//
// Percentages come from the catalogue as whole numbers: 10 means 10% off,
// 0 means no discount at all. Totals are already in the customer's currency.
function applyDiscount(total, percent) {
  return round2(total - (total * percent) / 100);
}

function round2(value) {
  return Math.round(value * 100) / 100;
}

module.exports = { applyDiscount, round2 };
