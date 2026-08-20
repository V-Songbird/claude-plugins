'use strict';

const repo = require('../repo/invite.js');
const { audit } = require('../../../../lib/audit.js');

// Invite rules for the accounts service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchInvite({ account_id, id }) {
  if (!account_id) throw new Error('inviteService: missing account_id');
  const row = await repo.getInvite(account_id, id);
  if (!row) return null;
  audit('accounts.invite.read', { account_id, id });
  return row;
}

async function pageInvites({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listInvites(account_id, size, page * size);
  const total = await repo.countInvites(account_id);
  return { rows, total, page, size, account_id };
}

async function createInvite({ account_id, values }) {
  const created = await repo.insertInvite(account_id, values);
  audit('accounts.invite.create', { account_id });
  return created;
}

async function removeInvite({ account_id, id }) {
  await repo.deleteInvite(account_id, id);
  audit('accounts.invite.delete', { account_id, id });
}

module.exports = { fetchInvite, pageInvites, createInvite, removeInvite };
