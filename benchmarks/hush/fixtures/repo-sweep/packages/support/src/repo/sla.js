'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Sla reads and writes for the support area.

async function getSlaById(id) {
  const rows = await db.query('SELECT * FROM slas WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listSlas(limit, offset) {
  return db.query('SELECT * FROM slas ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function cachedSla(id) {
  const hit = await cache.query('slas:' + id);
  if (hit) return hit;
  const row = await getSlaById(id);
  await cache.set('slas:' + id, row);
  return row;
}

async function updateSla(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE slas SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getSlaById(id);
}

module.exports = { getSlaById, listSlas, updateSla, cachedSla };
