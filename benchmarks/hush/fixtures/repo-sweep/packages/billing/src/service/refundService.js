'use strict';

const { db } = require('../../../../lib/db.js');

// RefundService reads and writes for the billing area.

async function getRefundServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM refund_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listRefundServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM refund_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateRefundService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE refund_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getRefundServiceById(id);
}

module.exports = { getRefundServiceById, listRefundServices, updateRefundService };
