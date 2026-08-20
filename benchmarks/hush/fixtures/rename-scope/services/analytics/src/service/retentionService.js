'use strict';

const repo = require('../repo/retention.js');
const { audit } = require('../../../../lib/audit.js');

// Retention rules for the analytics service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchRetention({ account_id, id }) {
  if (!account_id) throw new Error('retentionService: missing account_id');
  const row = await repo.getRetention(account_id, id);
  if (!row) return null;
  audit('analytics.retention.read', { account_id, id });
  return row;
}

async function pageRetentions({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listRetentions(account_id, size, page * size);
  const total = await repo.countRetentions(account_id);
  return { rows, total, page, size, account_id };
}

async function createRetention({ account_id, values }) {
  const created = await repo.insertRetention(account_id, values);
  audit('analytics.retention.create', { account_id });
  return created;
}

async function removeRetention({ account_id, id }) {
  await repo.deleteRetention(account_id, id);
  audit('analytics.retention.delete', { account_id, id });
}

module.exports = { fetchRetention, pageRetentions, createRetention, removeRetention };
