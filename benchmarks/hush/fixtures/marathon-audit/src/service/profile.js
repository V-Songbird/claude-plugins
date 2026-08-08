'use strict';

const { db } = require('../lib/db.js');

async function listProfile(limit) {
  return db.execute({ sql: 'SELECT * FROM profiles ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createProfile(body) {
  return db.execute({ sql: 'INSERT INTO profiles (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listProfile, createProfile };
