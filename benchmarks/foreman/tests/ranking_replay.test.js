"use strict";

const { test, describe, before, beforeEach } = require("node:test");
const assert = require("node:assert/strict");
const {
  makeTmpProject,
  writeRoadmap,
} = require("../../../foreman/tests/helpers");
const {
  criticalDepths,
  candidateComparator,
  replay,
} = require("../picks/ranking-replay");

let project;

function entry(id, depends_on = [], overrides = {}) {
  return {
    id,
    title: `Task ${id}`,
    why: `Why ${id}`,
    what: `What ${id}`,
    status: "planned",
    source: "user",
    depends_on,
    touches: [`src/${id}.js`],
    commits: [],
    created_at: `2026-01-${id}`,
    updated_at: `2026-01-${id}`,
    notes: "",
    ...overrides,
  };
}

beforeEach(() => {
  project = makeTmpProject();
});

describe("critical-depth ranking replay", () => {
  test("computes longest remaining dependent chain without changing production ranking", () => {
    const entries = [
      entry("001"),
      entry("002", ["001"]),
      entry("003", ["002"]),
      entry("004"),
    ];
    const depths = criticalDepths(entries);

    assert.equal(depths.get("001"), 2);
    assert.equal(depths.get("002"), 1);
    assert.equal(depths.get("003"), 0);
    assert.equal(depths.get("004"), 0);
  });

  test("rejects cycles instead of inventing a depth", () => {
    assert.throws(
      () => criticalDepths([entry("001", ["002"]), entry("002", ["001"])]),
      /dependency cycle/
    );
    assert.throws(
      () =>
        criticalDepths([
          entry("001", ["002"], { status: "done" }),
          entry("002", ["001"], { status: "dropped" }),
        ]),
      /dependency cycle/
    );
  });

  test("records when critical depth would choose differently", () => {
    writeRoadmap(project, [
      entry("001"),
      entry("002", ["001"]),
      entry("003", ["001"]),
      entry("004", ["001"]),
      entry("010"),
      entry("011", ["010"]),
      entry("012", ["011"]),
      entry("013", ["012"]),
    ]);

    const result = replay(project);

    assert.equal(result.strategies.current[0], "001");
    assert.equal(result.strategies.depth_first[0], "010");
    assert.deepEqual(result.disagreements, [
      { strategy: "depth_first", current: "001", alternative: "010" },
    ]);
  });

  test("keeps collision avoidance ahead of depth in the late-tiebreaker strategy", () => {
    const candidates = [
      { id: "001", unblocks_total: 4, unblocks: 1, collision: true, critical_depth: 4 },
      { id: "002", unblocks_total: 4, unblocks: 1, collision: false, critical_depth: 1 },
    ];

    candidates.sort(candidateComparator("depth-tiebreaker"));

    assert.equal(candidates[0].id, "002");
  });

  test("is deterministic across repeated replays", () => {
    writeRoadmap(project, [entry("001"), entry("002"), entry("003")]);
    assert.deepEqual(replay(project), replay(project));
  });
});

// [Foreman: 147] The replay is only evidence if the roadmaps it runs over can
// actually separate the strategies. The seeded generator's backlogs cannot:
// every entry in fixtures/10, /50 and /150 has critical_depth 0 or 1, and
// depth equals unblocks_total on every row, so all three orderings come back
// byte-identical no matter how large the backlog gets. A replay over those
// alone would report "no disagreement" and mean nothing by it.
//
// fixtures/deep is hand-authored to be the one shape they never produce: a
// four-long serial chain against a three-wide fan, tied on unblocks_total so
// the current comparator has to fall through to direct `unblocks`.
describe("the shipped picks fixtures, replayed", () => {
  const fs = require("node:fs");
  const path = require("node:path");
  const { spawnSync } = require("node:child_process");
  const PICKS = path.join(__dirname, "..", "picks");
  const FIXTURES = path.join(PICKS, "fixtures");
  const NAMES = ["10", "50", "150", "deep"];

  // The repo ignores every ROADMAP.jsonl, fixtures included, so a fresh clone
  // arrives without them. gen.js is free and deterministic — run it once here
  // rather than making these tests depend on someone having run it by hand.
  before(() => {
    const missing = NAMES.some((n) => !fs.existsSync(path.join(FIXTURES, n, "ROADMAP.jsonl")));
    if (!missing) return;
    const result = spawnSync("node", [path.join(PICKS, "gen.js")], { encoding: "utf-8" });
    assert.equal(result.status, 0, `picks/gen.js failed: ${result.stderr}`);
  });

  function replayFixture(name) {
    return replay(path.join(FIXTURES, name));
  }

  for (const size of ["10", "50", "150"]) {
    test(`the generated backlog at ${size} cannot separate the strategies`, () => {
      const result = replayFixture(size);
      assert.ok(result.candidates.length > 0, `fixture ${size} produced no candidates`);
      // The reason it cannot: depth never exceeds 1 and never diverges from
      // unblocks_total, so the depth comparisons are dead code on this input.
      for (const c of result.candidates) {
        assert.ok(c.critical_depth <= 1, `fixture ${size} entry ${c.id} has depth ${c.critical_depth}`);
        assert.equal(
          c.critical_depth,
          c.unblocks_total,
          `fixture ${size} entry ${c.id}: depth and unblocks_total diverge, so this fixture CAN separate them`
        );
      }
      assert.deepEqual(result.strategies.depth_first, result.strategies.current);
      assert.deepEqual(result.strategies.depth_tiebreaker, result.strategies.current);
      assert.deepEqual(result.disagreements, []);
    });
  }

  test("the deep fixture exists and is the chain-versus-fan case", () => {
    const file = path.join(FIXTURES, "deep", "ROADMAP.jsonl");
    assert.ok(fs.existsSync(file), "fixtures/deep/ROADMAP.jsonl is gone");
    const result = replayFixture("deep");
    const byId = new Map(result.candidates.map((c) => [c.id, c]));

    const chain = byId.get("101");
    const fan = byId.get("110");
    assert.ok(chain && fan, "the chain head and fan head are no longer both candidates");
    assert.equal(chain.critical_depth, 3, "the chain is no longer four long");
    assert.equal(chain.unblocks, 1, "the chain head should block exactly one successor");
    assert.equal(fan.critical_depth, 1, "the fan is no longer one level");
    assert.equal(fan.unblocks, 3, "the fan head should block exactly three successors");
    assert.equal(
      chain.unblocks_total,
      fan.unblocks_total,
      "the two must tie on unblocks_total or the comparator never reaches the interesting branch"
    );
  });

  test("depth-first picks the chain, current picks the fan, and that is the whole disagreement", () => {
    const result = replayFixture("deep");
    assert.equal(result.strategies.current[0], "110");
    assert.equal(result.strategies.depth_first[0], "101");
    assert.deepEqual(result.disagreements, [
      { strategy: "depth_first", current: "110", alternative: "101" },
    ]);
  });

  // The judgment, pinned so it is not silently reversed: the late tiebreaker
  // changes nothing, because direct `unblocks` has already separated the two
  // rows before depth is ever consulted. Only depth_first — promoting depth
  // above breadth outright — moves the pick, and that trade is the one foreman
  // declined: its user works one task at a time, so the fan's three immediate
  // options beat the chain's longer critical path. Nothing in scripts/roadmap.js
  // changed as a result.
  test("the late tiebreaker never moves the pick, even on the deep fixture", () => {
    const result = replayFixture("deep");
    assert.deepEqual(
      result.strategies.depth_tiebreaker,
      result.strategies.current,
      "depth as a late tiebreaker now changes the order; the 147 judgment needs re-running"
    );
  });
});
