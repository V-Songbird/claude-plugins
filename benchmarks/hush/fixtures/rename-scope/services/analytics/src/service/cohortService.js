'use strict';

const repo = require('../repo/cohort.js');
const { audit } = require('../../../../lib/audit.js');

// Cohort rules for the analytics service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchCohort({ account_id, id }) {
  if (!account_id) throw new Error('cohortService: missing account_id');
  const row = await repo.getCohort(account_id, id);
  if (!row) return null;
  audit('analytics.cohort.read', { account_id, id });
  return row;
}

async function pageCohorts({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listCohorts(account_id, size, page * size);
  const total = await repo.countCohorts(account_id);
  return { rows, total, page, size, account_id };
}

async function createCohort({ account_id, values }) {
  const created = await repo.insertCohort(account_id, values);
  audit('analytics.cohort.create', { account_id });
  return created;
}

async function removeCohort({ account_id, id }) {
  await repo.deleteCohort(account_id, id);
  audit('analytics.cohort.delete', { account_id, id });
}

module.exports = { fetchCohort, pageCohorts, createCohort, removeCohort };
