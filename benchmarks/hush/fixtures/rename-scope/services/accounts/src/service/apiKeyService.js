'use strict';

const repo = require('../repo/apiKey.js');
const { audit } = require('../../../../lib/audit.js');

// ApiKey rules for the accounts service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchApiKey({ account_id, id }) {
  if (!account_id) throw new Error('apiKeyService: missing account_id');
  const row = await repo.getApiKey(account_id, id);
  if (!row) return null;
  audit('accounts.apiKey.read', { account_id, id });
  return row;
}

async function pageApiKeys({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listApiKeys(account_id, size, page * size);
  const total = await repo.countApiKeys(account_id);
  return { rows, total, page, size, account_id };
}

async function createApiKey({ account_id, values }) {
  const created = await repo.insertApiKey(account_id, values);
  audit('accounts.apiKey.create', { account_id });
  return created;
}

async function removeApiKey({ account_id, id }) {
  await repo.deleteApiKey(account_id, id);
  audit('accounts.apiKey.delete', { account_id, id });
}

module.exports = { fetchApiKey, pageApiKeys, createApiKey, removeApiKey };
