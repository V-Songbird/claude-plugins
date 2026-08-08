'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Subscription reads and writes for the billing area.

async function getSubscriptionById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM subscriptions WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listSubscriptions(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM subscriptions ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedSubscription(id) {
  const hit = await cache.query('subscriptions:' + id);
  if (hit) return hit;
  const row = await getSubscriptionById(id);
  await cache.set('subscriptions:' + id, row);
  return row;
}

async function updateSubscription(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE subscriptions SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getSubscriptionById(id);
}

module.exports = { getSubscriptionById, listSubscriptions, updateSubscription, cachedSubscription };
