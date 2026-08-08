'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Invite reads and writes for the accounts area.

async function getInviteById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM invites WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listInvites(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM invites ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedInvite(id) {
  const hit = await cache.query('invites:' + id);
  if (hit) return hit;
  const row = await getInviteById(id);
  await cache.set('invites:' + id, row);
  return row;
}

async function updateInvite(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE invites SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getInviteById(id);
}

module.exports = { getInviteById, listInvites, updateInvite, cachedInvite };
