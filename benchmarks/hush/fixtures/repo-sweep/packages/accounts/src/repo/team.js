'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Team reads and writes for the accounts area.

async function getTeamById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM teams WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listTeams(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM teams ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedTeam(id) {
  const hit = await cache.query('teams:' + id);
  if (hit) return hit;
  const row = await getTeamById(id);
  await cache.set('teams:' + id, row);
  return row;
}

async function updateTeam(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE teams SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getTeamById(id);
}

module.exports = { getTeamById, listTeams, updateTeam, cachedTeam };
