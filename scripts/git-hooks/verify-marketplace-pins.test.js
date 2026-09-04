"use strict";

// Tests for verify-marketplace-pins.js -- the CI backstop that checks
// marketplace.json's pinned source.sha against each submodule's actual
// checked-out commit (absolute truth, not a diff).

const { test, describe } = require("node:test");
const assert = require("node:assert/strict");

const { verify } = require("./verify-marketplace-pins");

describe("verify", () => {
  // verify() calls the module-level submoduleHead(), which does real fs/git
  // work -- so we test it through a small root/marketplace fixture instead
  // of mocking, using the same fake-repo approach as the other hook tests.
  const fs = require("fs");
  const os = require("os");
  const path = require("path");
  const { execSync } = require("child_process");

  function makeFakeRoot(pluginShas) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "foundry-pins-"));
    const plugins = Object.entries(pluginShas).map(([name, sha]) => {
      const dir = path.join(root, name);
      fs.mkdirSync(dir, { recursive: true });
      execSync("git init -q", { cwd: dir });
      fs.writeFileSync(path.join(dir, "f.txt"), "x", "utf-8");
      execSync("git add f.txt", { cwd: dir });
      execSync('git -c user.email=t@t -c user.name=t commit -q -m init', { cwd: dir });
      const actualSha = execSync("git rev-parse HEAD", { cwd: dir, encoding: "utf-8" }).trim();
      return { name, actualSha };
    });
    return { root, plugins };
  }

  test("passes when marketplace.json's sha matches the real checked-out commit", () => {
    const { root, plugins } = makeFakeRoot({ demo: null });
    const actualSha = plugins[0].actualSha;
    const marketplace = { plugins: [{ name: "demo", source: { source: "url", sha: actualSha } }] };
    const problems = verify(root, marketplace);
    assert.deepEqual(problems, []);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test("flags a mismatch between marketplace.json's sha and the real checked-out commit", () => {
    const { root } = makeFakeRoot({ demo: null });
    const marketplace = { plugins: [{ name: "demo", source: { source: "url", sha: "f".repeat(40) } }] };
    const problems = verify(root, marketplace);
    assert.equal(problems.length, 1);
    assert.match(problems[0], /demo/);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test("flags a plugin whose directory is not checked out at all", () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "foundry-pins-missing-"));
    const marketplace = { plugins: [{ name: "missing-plugin", source: { source: "url", sha: "b".repeat(40) } }] };
    const problems = verify(root, marketplace);
    assert.equal(problems.length, 1);
    assert.match(problems[0], /not checked out/);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test("ignores plugins with a non-url source (e.g. a relative path)", () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "foundry-pins-relpath-"));
    const marketplace = { plugins: [{ name: "local-plugin", source: "./local-plugin" }] };
    const problems = verify(root, marketplace);
    assert.deepEqual(problems, []);
    fs.rmSync(root, { recursive: true, force: true });
  });

  // The checkout and the recorded pointer are two different commits, and a
  // clone only ever gets the recorded one. Checking the checkout alone passed
  // a repo whose marketplace.json had been committed without its plugin
  // directory staged alongside it.
  //
  // A gitlink is written straight into the index rather than through a real
  // `git submodule add`: the plugin dirs above are already git repos, and
  // update-index records the pointer without any of the submodule machinery.
  function pinPointer(root, name, sha) {
    const git = (cmd) => execSync(cmd, { cwd: root, env: cleanEnv() });
    git("git init -q");
    git(`git update-index --add --cacheinfo 160000,${sha},${name}`);
    git('git -c user.email=t@t -c user.name=t commit -q -m pin');
  }

  // git exports GIT_DIR and friends when it runs a hook, and this suite runs
  // from one. Inherited, they beat cwd for repo discovery and the fixture's
  // commits would land in the real repo instead.
  function cleanEnv() {
    return Object.fromEntries(Object.entries(process.env).filter(([k]) => !k.startsWith("GIT_")));
  }

  test("flags a recorded pointer the marketplace sha has moved past", () => {
    const { root, plugins } = makeFakeRoot({ demo: null });
    const actualSha = plugins[0].actualSha;
    pinPointer(root, "demo", "a".repeat(40));
    const marketplace = { plugins: [{ name: "demo", source: { source: "url", sha: actualSha } }] };
    const problems = verify(root, marketplace);
    assert.equal(problems.length, 1);
    assert.match(problems[0], /records the submodule pointer at aaaaaaaaaaaa/);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test("passes when the checkout and the recorded pointer both match", () => {
    const { root, plugins } = makeFakeRoot({ demo: null });
    const actualSha = plugins[0].actualSha;
    pinPointer(root, "demo", actualSha);
    const marketplace = { plugins: [{ name: "demo", source: { source: "url", sha: actualSha } }] };
    assert.deepEqual(verify(root, marketplace), []);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test("a root with no history is not a stale pointer", () => {
    const { root, plugins } = makeFakeRoot({ demo: null });
    const marketplace = { plugins: [{ name: "demo", source: { source: "url", sha: plugins[0].actualSha } }] };
    assert.deepEqual(verify(root, marketplace), []);
    fs.rmSync(root, { recursive: true, force: true });
  });

  test("checks multiple plugins independently", () => {
    const { root, plugins } = makeFakeRoot({ good: null, bad: null });
    const goodSha = plugins.find((p) => p.name === "good").actualSha;
    const marketplace = {
      plugins: [
        { name: "good", source: { source: "url", sha: goodSha } },
        { name: "bad", source: { source: "url", sha: "c".repeat(40) } },
      ],
    };
    const problems = verify(root, marketplace);
    assert.equal(problems.length, 1);
    assert.match(problems[0], /bad/);
    fs.rmSync(root, { recursive: true, force: true });
  });
});
