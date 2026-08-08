'use strict';

const { db } = require('../lib/db.js');

const COLUMNS = ['id', 'account_id', 'total_cents', 'status', 'created_at'];

/**
 * Ad-hoc reporting query. The column list and the filter both come from the
 * saved-report definition the user picked in the UI.
 */
async function runSavedReport(def) {
  const cols = def.columns.filter((c) => COLUMNS.includes(c)).join(', ');
  let sql = 'SELECT ' + cols + ' FROM orders';
  if (def.filter) {
    sql = sql + " WHERE " + def.filter.field + " = '" + def.filter.value + "'";
  }
  if (def.orderBy) {
    sql = sql + ' ORDER BY ' + def.orderBy + ' ' + (def.direction || 'ASC');
  }
  sql = sql + ' LIMIT ' + (def.limit || 500);
  return db.execute({ sql, params: [] });
}

async function summaryFor(accountId) {
  return db.execute({
    sql: 'SELECT status, COUNT(*) AS n FROM orders WHERE account_id = ? GROUP BY status',
    params: [accountId],
  });
}

module.exports = { runSavedReport, summaryFor, COLUMNS };
