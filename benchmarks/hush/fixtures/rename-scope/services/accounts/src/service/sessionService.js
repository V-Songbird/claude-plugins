'use strict';

const repo = require('../repo/session.js');
const { audit } = require('../../../../lib/audit.js');

// Session rules for the accounts service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchSession({ account_id, id }) {
  if (!account_id) throw new Error('sessionService: missing account_id');
  const row = await repo.getSession(account_id, id);
  if (!row) return null;
  audit('accounts.session.read', { account_id, id });
  return row;
}

async function pageSessions({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listSessions(account_id, size, page * size);
  const total = await repo.countSessions(account_id);
  return { rows, total, page, size, account_id };
}

async function createSession({ account_id, values }) {
  const created = await repo.insertSession(account_id, values);
  audit('accounts.session.create', { account_id });
  return created;
}

async function removeSession({ account_id, id }) {
  await repo.deleteSession(account_id, id);
  audit('accounts.session.delete', { account_id, id });
}

module.exports = { fetchSession, pageSessions, createSession, removeSession };
