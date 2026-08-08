'use strict';

const { db } = require('../../../../lib/db.js');

// PageviewService reads and writes for the analytics area.

async function getPageviewServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM pageview_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listPageviewServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM pageview_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updatePageviewService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE pageview_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getPageviewServiceById(id);
}

module.exports = { getPageviewServiceById, listPageviewServices, updatePageviewService };
