'use strict';

const { db } = require('../../../../lib/db.js');

// CategoryService reads and writes for the catalog area.

async function getCategoryServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM category_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listCategoryServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM category_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateCategoryService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE category_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getCategoryServiceById(id);
}

module.exports = { getCategoryServiceById, listCategoryServices, updateCategoryService };
