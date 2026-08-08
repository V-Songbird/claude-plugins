'use strict';

const { db } = require('../../../../lib/db.js');

// CategoryAdmin reads and writes for the catalog area.

async function getCategoryAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM category_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listCategoryAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM category_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateCategoryAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE category_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getCategoryAdminById(id);
}

module.exports = { getCategoryAdminById, listCategoryAdmins, updateCategoryAdmin };
