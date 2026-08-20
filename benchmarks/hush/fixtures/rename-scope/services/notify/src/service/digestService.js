'use strict';

const repo = require('../repo/digest.js');
const { audit } = require('../../../../lib/audit.js');

// Digest rules for the notify service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchDigest({ account_id, id }) {
  if (!account_id) throw new Error('digestService: missing account_id');
  const row = await repo.getDigest(account_id, id);
  if (!row) return null;
  audit('notify.digest.read', { account_id, id });
  return row;
}

async function pageDigests({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listDigests(account_id, size, page * size);
  const total = await repo.countDigests(account_id);
  return { rows, total, page, size, account_id };
}

async function createDigest({ account_id, values }) {
  const created = await repo.insertDigest(account_id, values);
  audit('notify.digest.create', { account_id });
  return created;
}

async function removeDigest({ account_id, id }) {
  await repo.deleteDigest(account_id, id);
  audit('notify.digest.delete', { account_id, id });
}

module.exports = { fetchDigest, pageDigests, createDigest, removeDigest };
