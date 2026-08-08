'use strict';

// Ground truth for the feature-drift task. Exit 0 = pass.
//
// Only the LAST version of each rule counts. The quiet-hours rule was asked
// for once and then replaced, so a router still doing the first version fails
// here even though it did once match a request.

const path = require('node:path');
const { route, createState } = require(path.join(__dirname, 'src', 'router.js'));

const problems = [];
const fail = (m) => problems.push(m);
const same = (got, want) => Array.isArray(got)
  && got.length === want.length
  && [...got].sort().join(',') === [...want].sort().join(',');

// Probes in time order, so a router that tracks recent history sees them the
// way a real replay would.
const PROBES = [
  // --- quiet hours: everything queues, critical still pages ---------------
  { at: 60, priority: 'critical', key: 'a', want: ['pager'], why: 'critical pages during quiet hours' },
  { at: 70, priority: 'high', key: 'b', want: ['queue'], why: 'high queues during quiet hours' },
  { at: 80, priority: 'normal', key: 'c', want: ['queue'], why: 'normal queues during quiet hours' },
  { at: 90, priority: 'low', key: 'd', want: ['queue'], why: 'low queues during quiet hours' },
  { at: 400, priority: 'high', key: 'e', want: ['queue'], why: '06:40 is still inside quiet hours' },

  // --- ordinary hours ------------------------------------------------------
  { at: 425, priority: 'high', key: 'f', want: ['sms', 'email'], why: '07:05 is outside quiet hours' },
  { at: 480, priority: 'critical', key: 'g', want: ['pager'], why: 'critical pages' },
  { at: 490, priority: 'high', key: 'h', want: ['sms', 'email'], why: 'high goes to both sms and email' },
  { at: 500, priority: 'normal', key: 'i', want: ['push'], why: 'normal goes to push' },
  { at: 510, priority: 'low', key: 'j', want: ['email'], why: 'low goes to email' },
  { at: 1310, priority: 'normal', key: 'k', want: ['push'], why: '21:50 is outside quiet hours' },
  { at: 1330, priority: 'normal', key: 'l', want: ['queue'], why: '22:10 is inside quiet hours' },

  // --- repeats within five minutes ----------------------------------------
  { at: 600, priority: 'normal', key: 'dup', want: ['push'], why: 'first of a key delivers' },
  { at: 602, priority: 'normal', key: 'dup', want: [], why: 'a repeat two minutes later drops' },
  { at: 604, priority: 'normal', key: 'other', want: ['push'], why: 'a different key is not a repeat' },
  { at: 615, priority: 'normal', key: 'dup', want: ['push'], why: 'the same key delivers again after the window' },
  { at: 700, priority: 'critical', key: 'crit', want: ['pager'], why: 'first critical of a key delivers' },
  { at: 701, priority: 'critical', key: 'crit', want: [], why: 'repeats are dropped at every priority' },
];

let state;
try {
  state = createState();
} catch (err) {
  console.error(`FAIL createState() threw ${err.message}`);
  process.exit(1);
}

for (const [i, probe] of PROBES.entries()) {
  const event = { id: `probe-${i}`, priority: probe.priority, at: probe.at, key: probe.key, subject: probe.key };
  let got;
  try {
    got = route(event, state);
  } catch (err) {
    fail(`route() threw on ${probe.priority} at minute ${probe.at}: ${err.message}`);
    continue;
  }
  if (!same(got, probe.want)) {
    fail(`${probe.why} — ${probe.priority} at minute ${probe.at} gave [${got}], expected [${probe.want}]`);
  }
}

// A fresh replay must not inherit the previous one's history.
if (!problems.length) {
  const fresh = createState();
  const first = route({ id: 'x', priority: 'normal', at: 600, key: 'dup', subject: 'dup' }, fresh);
  if (!same(first, ['push'])) fail('createState() does not hand back clean state between replays');
}

if (problems.length) {
  for (const p of problems) console.error(`FAIL ${p}`);
  process.exit(1);
}
console.log('OK the router matches the rules as they finally stood');
