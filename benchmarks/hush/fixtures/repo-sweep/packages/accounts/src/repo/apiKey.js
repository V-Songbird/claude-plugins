'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// ApiKey reads and writes for the accounts area.

async function getApiKeyById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM api_keys WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listApiKeys(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM api_keys ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedApiKey(id) {
  const hit = await cache.query('api_keys:' + id);
  if (hit) return hit;
  const row = await getApiKeyById(id);
  await cache.set('api_keys:' + id, row);
  return row;
}

async function updateApiKey(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE api_keys SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getApiKeyById(id);
}

module.exports = { getApiKeyById, listApiKeys, updateApiKey, cachedApiKey };
