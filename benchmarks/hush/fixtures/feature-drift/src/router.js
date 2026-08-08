'use strict';

const { CHANNELS } = require('./lib.js');

/**
 * Decide where one notification goes.
 *
 * @param {{id:string, priority:string, at:number, key:string}} event
 *   `at` is minutes since the start of the window; `key` groups notifications
 *   that are about the same underlying thing.
 * @param {object} state  Scratch object shared across a whole replay. The
 *   router owns its shape — `simulate.js` and the tests only create it.
 * @returns {string[]} the channels to deliver on, in any order. An empty array
 *   means the notification is dropped.
 */
function route(event, state) {
  return [CHANNELS.EMAIL];
}

/** Fresh scratch state for a replay. */
function createState() {
  return {};
}

module.exports = { route, createState };
