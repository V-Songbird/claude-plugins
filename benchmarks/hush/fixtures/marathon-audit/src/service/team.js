'use strict';

const { db } = require('../lib/db.js');

async function listTeam(limit) {
  return db.execute({ sql: 'SELECT * FROM teams ORDER BY created_at DESC LIMIT ?', params: [limit] });
}

async function createTeam(body) {
  return db.execute({ sql: 'INSERT INTO teams (payload) VALUES (?)', params: [JSON.stringify(body)] });
}

module.exports = { listTeam, createTeam };
