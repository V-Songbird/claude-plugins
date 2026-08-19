'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { applyDiscount } = require('../index.js');

test('takes 10% off a round total', () => {
  assert.strictEqual(applyDiscount(200, 10), 180);
});
