'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Funnel reads and writes for the analytics area.

async function getFunnelById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM funnels WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listFunnels(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM funnels ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedFunnel(id) {
  const hit = await cache.query('funnels:' + id);
  if (hit) return hit;
  const row = await getFunnelById(id);
  await cache.set('funnels:' + id, row);
  return row;
}

async function updateFunnel(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE funnels SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getFunnelById(id);
}

module.exports = { getFunnelById, listFunnels, updateFunnel, cachedFunnel };
