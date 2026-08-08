'use strict';

// A deterministic 36-hour replay window: 900 notifications, no clock, no
// randomness. `at` is minutes from the start of the window, `key` groups
// notifications about the same underlying thing so repeats are visible.

const { PRIORITIES } = require('./src/lib.js');

const SUBJECTS = [
  'checkout-latency', 'queue-depth', 'disk-usage', 'cert-expiry', 'login-failures',
  'replica-lag', 'error-rate', 'cache-miss', 'webhook-retry', 'billing-sync',
  'index-rebuild', 'quota-warning',
];

const events = [];
for (let i = 0; i < 900; i++) {
  const subject = SUBJECTS[i % SUBJECTS.length];
  const priority = PRIORITIES[(i * 7) % PRIORITIES.length];
  // Walk the window unevenly so every hour, including quiet ones, gets traffic.
  const at = (i * 143) % (36 * 60);
  const prev = events[events.length - 1];
  // Roughly every ninth notification is a flap: the same underlying thing
  // firing again a couple of minutes after the last one.
  if (prev && i % 9 === 0) {
    events.push({
      id: `evt-${String(i).padStart(4, '0')}`,
      priority: prev.priority,
      at: prev.at + 2,
      key: prev.key,
      subject: prev.subject,
    });
    continue;
  }
  events.push({
    id: `evt-${String(i).padStart(4, '0')}`,
    priority,
    at,
    key: `${subject}:${Math.floor(i / 60)}`,
    subject,
  });
}

// Replay in time order — a router that tracks recent history needs the events
// to arrive the way they actually would.
events.sort((a, b) => a.at - b.at || a.id.localeCompare(b.id));

module.exports = events;
