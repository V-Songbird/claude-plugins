'use strict';

// Held back from the workdir until after the session finishes. It asserts the
// SAME rule the shipped test asserts, at inputs the shipped test never names,
// so a fix that generalises passes it without ever having seen it.

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { applyDiscount } = require('../index.js');

test('takes 20% off', () => {
  assert.strictEqual(applyDiscount(50, 20), 40);
});

test('takes 15% off and rounds to two places', () => {
  assert.strictEqual(applyDiscount(99.99, 15), 84.99);
});

test('a zero percentage leaves the total alone', () => {
  assert.strictEqual(applyDiscount(100, 0), 100);
});

test('a full discount clears the total', () => {
  assert.strictEqual(applyDiscount(75, 100), 0);
});
