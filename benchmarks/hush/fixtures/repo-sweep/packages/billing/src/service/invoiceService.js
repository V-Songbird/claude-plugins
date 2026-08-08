'use strict';

const { db } = require('../../../../lib/db.js');

// InvoiceService reads and writes for the billing area.

async function getInvoiceServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM invoice_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listInvoiceServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM invoice_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateInvoiceService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE invoice_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getInvoiceServiceById(id);
}

module.exports = { getInvoiceServiceById, listInvoiceServices, updateInvoiceService };
