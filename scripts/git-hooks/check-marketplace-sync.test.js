"use strict";

// Tests for check-marketplace-sync.js -- the root-repo pre-commit gate that
// requires a staged submodule pointer bump to land in the same commit as a
// matching version/source.sha update in .claude-plugin/marketplace.json.

const { test, describe } = require("node:test");
const assert = require("node:assert/strict");

const { parseStagedSubmoduleChanges, findPluginEntry, evaluate } = require("./check-marketplace-sync");

describe("parseStagedSubmoduleChanges", () => {
  test("extracts new sha and path from a gitlink diff line", () => {
    const raw = ":160000 160000 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb M\tforeman";
    const changes = parseStagedSubmoduleChanges(raw);
    assert.equal(changes.length, 1);
    assert.equal(changes[0].path, "foreman");
    assert.equal(changes[0].newSha, "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb");
  });

  test("ignores regular file changes", () => {
    const raw = ":100644 100644 aaaaaaa bbbbbbb M\tREADME.md";
    assert.deepEqual(parseStagedSubmoduleChanges(raw), []);
  });

  test("handles multiple lines, mixed submodule and file changes", () => {
    const raw = [
      ":100644 100644 aaaaaaa bbbbbbb M\tREADME.md",
      ":160000 160000 1111111111111111111111111111111111111111 2222222222222222222222222222222222222222 M\thush",
      ":160000 160000 3333333333333333333333333333333333333333 4444444444444444444444444444444444444444 M\trazor",
    ].join("\n");
    const changes = parseStagedSubmoduleChanges(raw);
    assert.equal(changes.length, 2);
    assert.deepEqual(
      changes.map((c) => c.path),
      ["hush", "razor"]
    );
  });

  test("returns empty array for empty input", () => {
    assert.deepEqual(parseStagedSubmoduleChanges(""), []);
  });
});

describe("findPluginEntry", () => {
  test("finds a plugin by name", () => {
    const marketplace = { plugins: [{ name: "foreman" }, { name: "hush" }] };
    assert.equal(findPluginEntry(marketplace, "hush").name, "hush");
  });

  test("returns undefined when not found", () => {
    const marketplace = { plugins: [{ name: "foreman" }] };
    assert.equal(findPluginEntry(marketplace, "missing"), undefined);
  });

  test("tolerates a missing plugins array", () => {
    assert.equal(findPluginEntry({}, "foreman"), undefined);
  });
});

describe("evaluate", () => {
  test("passes when no submodule changes are staged", () => {
    const problems = evaluate({ submoduleChanges: [], marketplaceStaged: false, marketplace: null });
    assert.deepEqual(problems, []);
  });

  test("flags a submodule bump when marketplace.json was not staged at all", () => {
    const problems = evaluate({
      submoduleChanges: [{ path: "foreman", newSha: "a".repeat(40) }],
      marketplaceStaged: false,
      marketplace: null,
    });
    assert.equal(problems.length, 1);
    assert.match(problems[0], /foreman/);
    assert.match(problems[0], /not staged/);
  });

  test("flags a mismatch between the staged sha and marketplace.json's source.sha", () => {
    const problems = evaluate({
      submoduleChanges: [{ path: "hush", newSha: "b".repeat(40) }],
      marketplaceStaged: true,
      marketplace: { plugins: [{ name: "hush", source: { source: "url", sha: "c".repeat(40) } }] },
    });
    assert.equal(problems.length, 1);
    assert.match(problems[0], /hush/);
    assert.match(problems[0], /source\.sha/);
  });

  test("passes when the staged sha matches marketplace.json's source.sha", () => {
    const sha = "d".repeat(40);
    const problems = evaluate({
      submoduleChanges: [{ path: "razor", newSha: sha }],
      marketplaceStaged: true,
      marketplace: { plugins: [{ name: "razor", source: { source: "url", sha } }] },
    });
    assert.deepEqual(problems, []);
  });

  test("flags a submodule with no matching marketplace entry", () => {
    const problems = evaluate({
      submoduleChanges: [{ path: "new-plugin", newSha: "e".repeat(40) }],
      marketplaceStaged: true,
      marketplace: { plugins: [{ name: "foreman", source: { source: "url", sha: "f".repeat(40) } }] },
    });
    assert.equal(problems.length, 1);
    assert.match(problems[0], /no matching entry/);
  });

  test("evaluates multiple staged submodule changes independently", () => {
    const okSha = "1".repeat(40);
    const problems = evaluate({
      submoduleChanges: [
        { path: "foreman", newSha: okSha },
        { path: "hush", newSha: "2".repeat(40) },
      ],
      marketplaceStaged: true,
      marketplace: {
        plugins: [
          { name: "foreman", source: { source: "url", sha: okSha } },
          { name: "hush", source: { source: "url", sha: "9".repeat(40) } },
        ],
      },
    });
    assert.equal(problems.length, 1);
    assert.match(problems[0], /hush/);
  });
});

describe("evaluate with pluginNames", () => {
  test("ignores a submodule that is not a marketplace plugin", () => {
    const problems = evaluate({
      submoduleChanges: [{ path: "flint", newSha: "a".repeat(40) }],
      marketplaceStaged: false,
      marketplace: null,
      pluginNames: ["foreman", "hush", "razor"],
    });
    assert.deepEqual(problems, []);
  });

  test("still flags a plugin submodule when pluginNames is supplied", () => {
    const problems = evaluate({
      submoduleChanges: [{ path: "hush", newSha: "a".repeat(40) }],
      marketplaceStaged: false,
      marketplace: null,
      pluginNames: ["foreman", "hush", "razor"],
    });
    assert.equal(problems.length, 1);
    assert.match(problems[0], /hush/);
  });
});
