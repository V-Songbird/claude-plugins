'use strict';

const { db } = require('../../../../lib/db.js');

// SubscriptionAdmin reads and writes for the billing area.

async function getSubscriptionAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM subscription_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listSubscriptionAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM subscription_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateSubscriptionAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE subscription_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getSubscriptionAdminById(id);
}

module.exports = { getSubscriptionAdminById, listSubscriptionAdmins, updateSubscriptionAdmin };
