'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { parseDuration, readTimeout } = require('../src/duration.js');

test('parseDuration reads a single unit', () => {
  assert.strictEqual(parseDuration('250ms'), 250);
  assert.strictEqual(parseDuration('30s'), 30000);
  assert.strictEqual(parseDuration('5m'), 300000);
  assert.strictEqual(parseDuration('2h'), 7200000);
});

test('parseDuration reads days', () => {
  assert.strictEqual(parseDuration('3d'), 259200000);
});

test('parseDuration reads compound strings, largest unit first', () => {
  assert.strictEqual(parseDuration('1h30m'), 5400000);
  assert.strictEqual(parseDuration('2d4h'), 187200000);
  assert.strictEqual(parseDuration('1m30s500ms'), 90500);
});

test('parseDuration rejects nonsense', () => {
  assert.throws(() => parseDuration('soon'), TypeError);
  assert.throws(() => parseDuration('5x'), TypeError);
});

test('readTimeout retries until the config appears', () => {
  const reads = ['1h30m'];
  const value = readTimeout((n) => (n === 0 ? null : reads[0]), 3);
  assert.strictEqual(value, 5400000);
});
