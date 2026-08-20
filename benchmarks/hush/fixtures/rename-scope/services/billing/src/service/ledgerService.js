'use strict';

const repo = require('../repo/ledger.js');
const { audit } = require('../../../../lib/audit.js');

// Ledger rules for the billing service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchLedger({ account_id, id }) {
  if (!account_id) throw new Error('ledgerService: missing account_id');
  const row = await repo.getLedger(account_id, id);
  if (!row) return null;
  audit('billing.ledger.read', { account_id, id });
  return row;
}

async function pageLedgers({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listLedgers(account_id, size, page * size);
  const total = await repo.countLedgers(account_id);
  return { rows, total, page, size, account_id };
}

async function createLedger({ account_id, values }) {
  const created = await repo.insertLedger(account_id, values);
  audit('billing.ledger.create', { account_id });
  return created;
}

async function removeLedger({ account_id, id }) {
  await repo.deleteLedger(account_id, id);
  audit('billing.ledger.delete', { account_id, id });
}

module.exports = { fetchLedger, pageLedgers, createLedger, removeLedger };
