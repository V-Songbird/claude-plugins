"use strict";

// Tests for check-shared-copies.js -- the pre-commit gate that keeps a helper
// duplicated across plugins from drifting in one copy only.
//
// The fixtures are synthetic plugin trees, not the real submodules: the real
// ones are asserted separately, at the bottom, because a check that only ever
// sees its own fixtures proves nothing about the repo it guards.

const { test, describe } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");

const { functionBody, checkShared, SHARED } = require("./check-shared-copies");

const HELPER = { file: "lib/thing.js", fn: "doThing", plugins: ["alpha", "beta"] };

const BODY = [
  "function doThing(x) {",
  "  return x + 1;",
  "}",
].join("\n");

/** A throwaway root holding one file per plugin named in `sources`. */
function fixture(sources) {
  const root = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), "sharedcopies-"));
  for (const [plugin, source] of Object.entries(sources)) {
    const full = path.join(root, plugin, HELPER.file);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, source);
  }
  return root;
}

const scratch = [];
const withFixture = (sources) => {
  const root = fixture(sources);
  scratch.push(root);
  return root;
};

test.after(() => {
  for (const dir of scratch) fs.rmSync(dir, { recursive: true, force: true });
});

describe("functionBody", () => {
  test("returns the function from its signature to its closing brace", () => {
    assert.equal(functionBody(`"use strict";\n\n${BODY}\n\nmodule.exports = {};\n`, "doThing"), BODY);
  });

  test("returns null when the file has no such top-level function", () => {
    assert.equal(functionBody(`${BODY}\n`, "somethingElse"), null);
  });

  test("ignores a nested function that only looks like the one asked for", () => {
    const nested = `function outer() {\n  function doThing() { return 1; }\n}\n`;
    assert.equal(functionBody(nested, "doThing"), null);
  });
});

describe("checkShared", () => {
  test("identical copies are no problem", () => {
    const root = withFixture({
      alpha: `// alpha's own header\n\n${BODY}\n`,
      beta: `// beta says something else entirely\n\n${BODY}\n`,
    });
    assert.deepEqual(checkShared(root, [HELPER]), []);
  });

  test("a copy that drifted in one plugin is reported", () => {
    const root = withFixture({
      alpha: `${BODY}\n`,
      beta: `${BODY.replace("x + 1", "x + 2")}\n`,
    });
    const problems = checkShared(root, [HELPER]);
    assert.equal(problems.length, 1);
    assert.match(problems[0], /doThing\(\) differs between alpha and beta/);
  });

  test("a plugin that is not checked out is skipped, not failed", () => {
    const root = withFixture({ alpha: `${BODY}\n` });
    assert.deepEqual(checkShared(root, [HELPER]), []);
  });

  test("a copy that lost the function altogether is reported", () => {
    const root = withFixture({
      alpha: `${BODY}\n`,
      beta: "// someone deleted it\n",
    });
    const problems = checkShared(root, [HELPER]);
    assert.equal(problems.length, 1);
    assert.match(problems[0], /beta\/lib\/thing\.js has no top-level function doThing/);
  });
});

describe("this repo, today", () => {
  test("every shared copy the check names actually agrees", () => {
    assert.deepEqual(checkShared(), []);
  });

  test("safe-write is one of the helpers being watched", () => {
    assert.ok(SHARED.some((s) => s.file.endsWith("safe-write.js") && s.fn === "safeWriteFileSync"));
  });
});
