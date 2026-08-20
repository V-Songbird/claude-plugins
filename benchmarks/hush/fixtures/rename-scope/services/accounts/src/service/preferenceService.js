'use strict';

const repo = require('../repo/preference.js');
const { audit } = require('../../../../lib/audit.js');

// Preference rules for the accounts service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchPreference({ account_id, id }) {
  if (!account_id) throw new Error('preferenceService: missing account_id');
  const row = await repo.getPreference(account_id, id);
  if (!row) return null;
  audit('accounts.preference.read', { account_id, id });
  return row;
}

async function pagePreferences({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listPreferences(account_id, size, page * size);
  const total = await repo.countPreferences(account_id);
  return { rows, total, page, size, account_id };
}

async function createPreference({ account_id, values }) {
  const created = await repo.insertPreference(account_id, values);
  audit('accounts.preference.create', { account_id });
  return created;
}

async function removePreference({ account_id, id }) {
  await repo.deletePreference(account_id, id);
  audit('accounts.preference.delete', { account_id, id });
}

module.exports = { fetchPreference, pagePreferences, createPreference, removePreference };
