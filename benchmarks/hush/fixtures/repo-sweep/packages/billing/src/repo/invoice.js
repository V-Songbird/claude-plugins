'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Invoice reads and writes for the billing area.

async function getInvoiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM invoices WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listInvoices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM invoices ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedInvoice(id) {
  const hit = await cache.query('invoices:' + id);
  if (hit) return hit;
  const row = await getInvoiceById(id);
  await cache.set('invoices:' + id, row);
  return row;
}

async function updateInvoice(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE invoices SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getInvoiceById(id);
}

module.exports = { getInvoiceById, listInvoices, updateInvoice, cachedInvoice };
