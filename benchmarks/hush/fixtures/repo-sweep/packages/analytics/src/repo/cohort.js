'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Cohort reads and writes for the analytics area.

async function getCohortById(id) {
  const rows = await db.query('SELECT * FROM cohorts WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listCohorts(limit, offset) {
  return db.query('SELECT * FROM cohorts ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function cachedCohort(id) {
  const hit = await cache.query('cohorts:' + id);
  if (hit) return hit;
  const row = await getCohortById(id);
  await cache.set('cohorts:' + id, row);
  return row;
}

async function updateCohort(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE cohorts SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getCohortById(id);
}

module.exports = { getCohortById, listCohorts, updateCohort, cachedCohort };
