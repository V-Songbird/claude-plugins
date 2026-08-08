'use strict';

// Delivery channels the router can pick from.
const CHANNELS = {
  EMAIL: 'email',
  SMS: 'sms',
  PUSH: 'push',
  PAGER: 'pager',
  QUEUE: 'queue',
};

// Priorities, low to high. `rank` is what comparisons should use — never
// compare the strings.
const PRIORITIES = ['low', 'normal', 'high', 'critical'];
const rank = (p) => PRIORITIES.indexOf(p);

/**
 * Local hour, 0-23, for an event timestamp. Timestamps are minutes since the
 * start of the window, which keeps every run reproducible.
 */
function hourOf(minutes) {
  return Math.floor(minutes / 60) % 24;
}

module.exports = { CHANNELS, PRIORITIES, rank, hourOf };
