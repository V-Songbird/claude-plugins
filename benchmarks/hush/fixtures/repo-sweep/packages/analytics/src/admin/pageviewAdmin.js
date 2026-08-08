'use strict';

const { db } = require('../../../../lib/db.js');

// PageviewAdmin reads and writes for the analytics area.

async function getPageviewAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM pageview_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listPageviewAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM pageview_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updatePageviewAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE pageview_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getPageviewAdminById(id);
}

module.exports = { getPageviewAdminById, listPageviewAdmins, updatePageviewAdmin };
