"use strict";

// The retelling scorer only means anything if the reader really put the reply
// in its own words. `longestSharedRun` is the guard: a reader that lifts a run
// of the reply verbatim shows up as a long shared run, and a score built on
// copied text measures nothing. These pin its behaviour at the edges.

const { test } = require("node:test");
const assert = require("node:assert");
const { longestSharedRun } = require("../runner/retold.js");

test("an identical retelling shares every word", () => {
  const s = "the suite is green and the discount is taxed before the total is written";
  assert.strictEqual(longestSharedRun(s, s), s.split(" ").length);
});

test("nothing in common scores zero", () => {
  assert.strictEqual(
    longestSharedRun("the suite is green", "completamente distinto sin nada igual"),
    0
  );
});

test("a lifted run is found inside a genuine paraphrase", () => {
  const reply = "Fixed in src/pricing.js by taxing the discounted figure, so the total is right.";
  // "by taxing the discounted figure" carried over verbatim, the rest reworded.
  const retelling =
    "They changed a pricing file: it now works by taxing the discounted figure, which fixes the sum.";
  assert.strictEqual(longestSharedRun(reply, retelling), 5);
});

test("a clean paraphrase scores low even when it shares single words", () => {
  const reply = "The build passes now. Two real bugs came out of the dependency bump.";
  const retelling = "Everything compiles again, and the upgrade had introduced a pair of genuine faults.";
  assert.ok(longestSharedRun(reply, retelling) <= 1);
});

test("case and punctuation are ignored", () => {
  assert.strictEqual(longestSharedRun("Green: 625 passing!", "green 625 passing"), 3);
});

test("an empty retelling scores zero rather than throwing", () => {
  assert.strictEqual(longestSharedRun("the suite is green", ""), 0);
});
