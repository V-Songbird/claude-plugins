'use strict';

const { db } = require('../../../../lib/db.js');

// ApiKeyAdmin reads and writes for the accounts area.

async function getApiKeyAdminById(id) {
  const rows = await db.query('SELECT * FROM api_key_admins WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listApiKeyAdmins(limit, offset) {
  return db.query('SELECT * FROM api_key_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function updateApiKeyAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE api_key_admins SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getApiKeyAdminById(id);
}

module.exports = { getApiKeyAdminById, listApiKeyAdmins, updateApiKeyAdmin };
