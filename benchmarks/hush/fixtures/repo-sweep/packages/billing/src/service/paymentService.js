'use strict';

const { db } = require('../../../../lib/db.js');

// PaymentService reads and writes for the billing area.

async function getPaymentServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM payment_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listPaymentServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM payment_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updatePaymentService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE payment_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getPaymentServiceById(id);
}

module.exports = { getPaymentServiceById, listPaymentServices, updatePaymentService };
