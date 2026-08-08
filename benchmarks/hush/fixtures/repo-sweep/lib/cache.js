'use strict';

// The read-through cache. Its `query` takes a cache key, not SQL, and has
// nothing to do with the database handle — the shared name is a coincidence.

const store = new Map();

const cache = {
  async query(key) {
    return store.has(key) ? store.get(key) : null;
  },
  async set(key, value) {
    store.set(key, value);
  },
};

module.exports = { cache, store };
