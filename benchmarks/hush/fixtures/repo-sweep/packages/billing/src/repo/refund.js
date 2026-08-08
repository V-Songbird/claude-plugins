'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Refund reads and writes for the billing area.

async function getRefundById(id) {
  const rows = await db.query('SELECT * FROM refunds WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listRefunds(limit, offset) {
  return db.query('SELECT * FROM refunds ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function cachedRefund(id) {
  const hit = await cache.query('refunds:' + id);
  if (hit) return hit;
  const row = await getRefundById(id);
  await cache.set('refunds:' + id, row);
  return row;
}

async function updateRefund(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE refunds SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getRefundById(id);
}

module.exports = { getRefundById, listRefunds, updateRefund, cachedRefund };
