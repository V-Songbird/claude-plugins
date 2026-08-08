'use strict';

const { db } = require('../lib/db.js');

async function listSearch(limit) {
  return db.execute({ sql: 'SELECT * FROM searchs ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createSearch(body) {
  return db.execute({ sql: 'INSERT INTO searchs (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listSearch, createSearch };
