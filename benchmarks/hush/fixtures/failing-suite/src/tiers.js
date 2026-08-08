'use strict';

// Volume tier table. Ordered high to low so the first match wins.
const TIERS = [
  { minQty: 500, off: 0.2 },
  { minQty: 100, off: 0.1 },
  { minQty: 25, off: 0.05 },
];

/** Fraction off for a given quantity. Returns 0 below the smallest tier. */
function tierFor(qty) {
  for (const t of TIERS) if (qty >= t.minQty) return t.off;
  return 0;
}

module.exports = { TIERS, tierFor };
