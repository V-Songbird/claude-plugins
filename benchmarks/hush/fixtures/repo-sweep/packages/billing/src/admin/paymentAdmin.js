'use strict';

const { db } = require('../../../../lib/db.js');

// PaymentAdmin reads and writes for the billing area.

async function getPaymentAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM payment_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listPaymentAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM payment_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updatePaymentAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE payment_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getPaymentAdminById(id);
}

module.exports = { getPaymentAdminById, listPaymentAdmins, updatePaymentAdmin };
