'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Session reads and writes for the accounts area.

async function getSessionById(id) {
  const rows = await db.query('SELECT * FROM sessions WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listSessions(limit, offset) {
  return db.query('SELECT * FROM sessions ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function cachedSession(id) {
  const hit = await cache.query('sessions:' + id);
  if (hit) return hit;
  const row = await getSessionById(id);
  await cache.set('sessions:' + id, row);
  return row;
}

async function updateSession(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE sessions SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getSessionById(id);
}

module.exports = { getSessionById, listSessions, updateSession, cachedSession };
