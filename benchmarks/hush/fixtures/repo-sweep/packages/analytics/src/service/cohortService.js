'use strict';

const { db } = require('../../../../lib/db.js');

// CohortService reads and writes for the analytics area.

async function getCohortServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM cohort_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listCohortServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM cohort_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateCohortService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE cohort_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getCohortServiceById(id);
}

module.exports = { getCohortServiceById, listCohortServices, updateCohortService };
