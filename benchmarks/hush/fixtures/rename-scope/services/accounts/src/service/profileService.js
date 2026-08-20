'use strict';

const repo = require('../repo/profile.js');
const { audit } = require('../../../../lib/audit.js');

// Profile rules for the accounts service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchProfile({ account_id, id }) {
  if (!account_id) throw new Error('profileService: missing account_id');
  const row = await repo.getProfile(account_id, id);
  if (!row) return null;
  audit('accounts.profile.read', { account_id, id });
  return row;
}

async function pageProfiles({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listProfiles(account_id, size, page * size);
  const total = await repo.countProfiles(account_id);
  return { rows, total, page, size, account_id };
}

async function createProfile({ account_id, values }) {
  const created = await repo.insertProfile(account_id, values);
  audit('accounts.profile.create', { account_id });
  return created;
}

async function removeProfile({ account_id, id }) {
  await repo.deleteProfile(account_id, id);
  audit('accounts.profile.delete', { account_id, id });
}

module.exports = { fetchProfile, pageProfiles, createProfile, removeProfile };
