'use strict';

const repo = require('../repo/push.js');
const { audit } = require('../../../../lib/audit.js');

// Push rules for the notify service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchPush({ account_id, id }) {
  if (!account_id) throw new Error('pushService: missing account_id');
  const row = await repo.getPush(account_id, id);
  if (!row) return null;
  audit('notify.push.read', { account_id, id });
  return row;
}

async function pagePushs({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listPushs(account_id, size, page * size);
  const total = await repo.countPushs(account_id);
  return { rows, total, page, size, account_id };
}

async function createPush({ account_id, values }) {
  const created = await repo.insertPush(account_id, values);
  audit('notify.push.create', { account_id });
  return created;
}

async function removePush({ account_id, id }) {
  await repo.deletePush(account_id, id);
  audit('notify.push.delete', { account_id, id });
}

module.exports = { fetchPush, pagePushs, createPush, removePush };
