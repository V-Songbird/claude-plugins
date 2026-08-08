'use strict';

const { db } = require('../../../../lib/db.js');

// RefundAdmin reads and writes for the billing area.

async function getRefundAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM refund_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listRefundAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM refund_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateRefundAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE refund_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getRefundAdminById(id);
}

module.exports = { getRefundAdminById, listRefundAdmins, updateRefundAdmin };
