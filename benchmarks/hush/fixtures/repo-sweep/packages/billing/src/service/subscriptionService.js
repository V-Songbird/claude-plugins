'use strict';

const { db } = require('../../../../lib/db.js');

// SubscriptionService reads and writes for the billing area.

async function getSubscriptionServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM subscription_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listSubscriptionServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM subscription_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateSubscriptionService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE subscription_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getSubscriptionServiceById(id);
}

module.exports = { getSubscriptionServiceById, listSubscriptionServices, updateSubscriptionService };
