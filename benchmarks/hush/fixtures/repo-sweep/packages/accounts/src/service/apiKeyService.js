'use strict';

const { db } = require('../../../../lib/db.js');

// ApiKeyService reads and writes for the accounts area.

async function getApiKeyServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM api_key_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listApiKeyServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM api_key_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateApiKeyService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE api_key_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getApiKeyServiceById(id);
}

module.exports = { getApiKeyServiceById, listApiKeyServices, updateApiKeyService };
