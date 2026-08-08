'use strict';

const { db } = require('../../../../lib/db.js');

// InvoiceAdmin reads and writes for the billing area.

async function getInvoiceAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM invoice_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listInvoiceAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM invoice_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateInvoiceAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE invoice_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getInvoiceAdminById(id);
}

module.exports = { getInvoiceAdminById, listInvoiceAdmins, updateInvoiceAdmin };
