'use strict';

// Vendored copy of legacy-orm 2.1.4. Do not edit — it is replaced wholesale on
// every upgrade, and local changes are silently lost.

const { db } = require('../../lib/db.js');

async function findAll(tableName, where) {
  return db.query('SELECT * FROM ' + tableName + ' WHERE ' + where, []);
}

async function findOne(tableName, id) {
  const rows = await db.query('SELECT * FROM ' + tableName + ' WHERE id = ?', [id]);
  return rows[0] || null;
}

module.exports = { findAll, findOne };
