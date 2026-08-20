'use strict';

// Every audit line carries the account_id it happened under.

const lines = [];

function audit(event, fields) {
  lines.push({ event, account_id: fields.account_id, at: '2026-06-01T00:00:00.000Z', ...fields });
}

module.exports = { audit, lines };
