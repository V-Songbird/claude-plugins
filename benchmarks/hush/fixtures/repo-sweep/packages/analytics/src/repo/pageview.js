'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Pageview reads and writes for the analytics area.

async function getPageviewById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM pageviews WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listPageviews(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM pageviews ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedPageview(id) {
  const hit = await cache.query('pageviews:' + id);
  if (hit) return hit;
  const row = await getPageviewById(id);
  await cache.set('pageviews:' + id, row);
  return row;
}

async function updatePageview(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE pageviews SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getPageviewById(id);
}

module.exports = { getPageviewById, listPageviews, updatePageview, cachedPageview };
