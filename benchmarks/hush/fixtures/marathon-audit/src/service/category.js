'use strict';

const { db } = require('../lib/db.js');

async function listCategory(limit) {
  return db.execute({ sql: 'SELECT * FROM categorys ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createCategory(body) {
  return db.execute({ sql: 'INSERT INTO categorys (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listCategory, createCategory };
