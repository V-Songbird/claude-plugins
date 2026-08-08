'use strict';

const { db } = require('../lib/db.js');

async function dump() {
  return db.execute({ sql: 'SELECT * FROM metrics_rollup', params: [] });
}

async function flush(scope) {
  return db.execute({ sql: 'DELETE FROM metrics_rollup WHERE scope = ?', params: [scope] });
}

module.exports = { dump, flush };
