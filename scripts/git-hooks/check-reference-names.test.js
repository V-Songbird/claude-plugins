"use strict";

// Tests for check-reference-names.js -- the pre-commit/commit-msg gate that
// keeps private reference-project names out of public records.
//
// Every name below is synthetic. The real blocklist is private and gitignored;
// this file is committed, so a real name here would defeat the very check it
// tests.

const { test, describe } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const { main, scanText, loadBlocklist, isExemptPath, addedLinesFromDiff } = require("./check-reference-names");

const NAMES = ["zorblat", "qux.tool"];
const BLOCKLIST = "# a comment line\nzorblat\n\n  qux.tool  \n";

// Runs `fn` with cwd pointed at an empty throwaway directory, nested one level
// deep so loadBlocklist's `../docs/research` candidate can't resolve to
// anything real either. GIT_* is stripped for the duration: git sets those when
// it invokes a hook, and inherited they win over cwd for repo discovery -- the
// fixture's git commands would land in this repo's real .git (same footgun
// plugin-pre-commit-template.js's cleanEnv() documents).
function withSandbox(options, fn) {
  const root = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), "refnames-"));
  const work = path.join(root, "work");
  fs.mkdirSync(work);
  const cwd = process.cwd();
  const env = { ...process.env };
  for (const key of Object.keys(process.env)) {
    if (key.startsWith("GIT_")) delete process.env[key];
  }
  delete process.env.HOUSE_REFERENCE_BLOCKLIST;
  if (options.blocklist) {
    const file = path.join(root, "blocklist.txt");
    fs.writeFileSync(file, options.blocklist);
    process.env.HOUSE_REFERENCE_BLOCKLIST = file;
  }
  process.chdir(work);
  try {
    return fn(work);
  } finally {
    process.chdir(cwd);
    for (const key of Object.keys(process.env)) {
      if (!(key in env)) delete process.env[key];
    }
    Object.assign(process.env, env);
    fs.rmSync(root, { recursive: true, force: true });
  }
}

// main() reads its mode off process.argv and reports hits on stderr; both are
// noise for a test runner, so feed one and swallow the other.
function runMain(...argv) {
  const savedArgv = process.argv;
  const savedError = console.error;
  process.argv = [savedArgv[0], savedArgv[1], ...argv];
  console.error = () => {};
  try {
    return main();
  } finally {
    process.argv = savedArgv;
    console.error = savedError;
  }
}

function initRepo(dir) {
  const git = (...args) => execFileSync("git", args, { cwd: dir, encoding: "utf8" });
  git("init", "-q");
  git("config", "user.email", "test@example.com");
  git("config", "user.name", "Test");
  git("config", "commit.gpgsign", "false");
  return git;
}

describe("scanText", () => {
  test("does not match a blocklisted name inside a longer word", () => {
    assert.deepEqual(scanText("zorblatting and xzorblat and zorblats", NAMES, "x"), []);
  });

  test("matches at real word boundaries", () => {
    assert.equal(scanText("zorblat leads", NAMES, "x").length, 1);
    assert.equal(scanText("compared to zorblat", NAMES, "x").length, 1);
    assert.equal(scanText("beats (zorblat) here", NAMES, "x").length, 1);
  });

  test("matches case-insensitively in both directions", () => {
    assert.equal(scanText("we beat ZORBLAT", NAMES, "x").length, 1);
    assert.equal(scanText("we beat zorblat", ["ZORBLAT"], "x").length, 1);
  });

  test("treats regex metacharacters in a name as literals", () => {
    assert.deepEqual(scanText("quxXtool", NAMES, "x"), []);
    assert.equal(scanText("qux.tool", NAMES, "x").length, 1);
  });

  test("reports the label and the 1-based line number", () => {
    const hits = scanText("clean\nmentions zorblat", NAMES, "commit message");
    assert.deepEqual(hits, ['commit message:2: contains "zorblat"']);
  });

  test("returns no hits for clean text", () => {
    assert.deepEqual(scanText("nothing to see\nhere at all", NAMES, "x"), []);
  });
});

describe("isExemptPath — READMEs are the one allowed surface", () => {
  test("matches README.md at the repo root and in any subdirectory", () => {
    assert.equal(isExemptPath("README.md"), true);
    assert.equal(isExemptPath("hush/README.md"), true);
    assert.equal(isExemptPath("docs/guide/README.md"), true);
  });

  test("is case-insensitive on the basename", () => {
    assert.equal(isExemptPath("Readme.md"), true);
    assert.equal(isExemptPath("readme.md"), true);
  });

  test("does not exempt other docs or a README-ish name", () => {
    assert.equal(isExemptPath("CHANGELOG.md"), false);
    assert.equal(isExemptPath("README.txt"), false);
    assert.equal(isExemptPath("READMEfoo.md"), false);
    assert.equal(isExemptPath("src/readme.js"), false);
  });
});

describe("isExemptPath — retained benchmark records are the evidential surface", () => {
  test("matches a record under a plugin's records directory", () => {
    assert.equal(isExemptPath("benchmarks/hush/records/h2h-sonnet-abc123/batch.json"), true);
    assert.equal(isExemptPath("benchmarks/hush/records/h2h-sonnet-abc123/log-triage__zorblat__r1.json"), true);
    assert.equal(isExemptPath("benchmarks/foreman/records/x/published/claims.md"), true);
  });

  test("does not exempt the rest of the harness", () => {
    assert.equal(isExemptPath("benchmarks/hush/runner/run.js"), false);
    assert.equal(isExemptPath("benchmarks/hush/tasks.json"), false);
    assert.equal(isExemptPath("benchmarks/hush/results/mine/runs/a.json"), false);
  });

  test("does not exempt a records directory outside benchmarks/<plugin>/", () => {
    assert.equal(isExemptPath("records/a.json"), false);
    assert.equal(isExemptPath("benchmarks/records/a.json"), false);
    assert.equal(isExemptPath("src/records/a.json"), false);
  });
});

describe("addedLinesFromDiff — drops added lines in README files only", () => {
  const diff = (file, body) =>
    `diff --git a/${file} b/${file}\nindex 000..111 100644\n--- a/${file}\n+++ b/${file}\n@@ -0,0 +1 @@\n+${body}\n`;

  test("keeps an added line in a code file", () => {
    assert.equal(addedLinesFromDiff(diff("src/foo.js", "beat zorblat")), "+beat zorblat");
  });

  test("drops an added line in a README", () => {
    assert.equal(addedLinesFromDiff(diff("README.md", "beat zorblat")), "");
  });

  test("drops the README line but keeps the CHANGELOG line in a mixed diff", () => {
    const mixed = diff("README.md", "beat zorblat") + diff("CHANGELOG.md", "beat zorblat");
    assert.equal(addedLinesFromDiff(mixed), "+beat zorblat");
  });

  test("drops an added line in a retained benchmark record", () => {
    const rec = "benchmarks/hush/records/batch-1/log-triage__zorblat__r1.json";
    assert.equal(addedLinesFromDiff(diff(rec, '"arm": "zorblat",')), "");
  });

  test("keeps a runner line naming the same project", () => {
    assert.equal(
      addedLinesFromDiff(diff("benchmarks/hush/runner/run.js", "// beat zorblat")),
      "+// beat zorblat");
  });

  test("ignores removed lines and the +++ header", () => {
    const d = `diff --git a/notes.md b/notes.md\n--- a/notes.md\n+++ b/notes.md\n@@ -1 +1 @@\n-old zorblat\n+kept\n`;
    assert.equal(addedLinesFromDiff(d), "+kept");
  });
});

describe("loadBlocklist", () => {
  test("reads HOUSE_REFERENCE_BLOCKLIST, trimming blanks and comments", () => {
    withSandbox({ blocklist: BLOCKLIST }, () => {
      assert.deepEqual(loadBlocklist(), NAMES);
    });
  });

  test("returns null when no list is reachable", () => {
    withSandbox({}, () => {
      assert.equal(loadBlocklist(), null);
    });
  });

  test("returns null when every reachable list is empty of names", () => {
    withSandbox({ blocklist: "# only a comment\n\n" }, () => {
      assert.equal(loadBlocklist(), null);
    });
  });
});

describe("main — fail open", () => {
  test("passes a message that would otherwise fail, when no blocklist exists", () => {
    withSandbox({}, (work) => {
      const msg = path.join(work, "COMMIT_EDITMSG");
      fs.writeFileSync(msg, "beat zorblat by 40%");
      assert.equal(runMain("message", msg), 0);
    });
  });

  test("passes staged mode outside a git repo", () => {
    withSandbox({ blocklist: BLOCKLIST }, () => {
      assert.equal(runMain("staged"), 0);
    });
  });
});

describe("main — message mode", () => {
  test("fails on a commit message containing a blocklisted name", () => {
    withSandbox({ blocklist: BLOCKLIST }, (work) => {
      const msg = path.join(work, "COMMIT_EDITMSG");
      fs.writeFileSync(msg, "Compare against zorblat\n");
      assert.equal(runMain("message", msg), 1);
    });
  });

  test("passes a clean commit message", () => {
    withSandbox({ blocklist: BLOCKLIST }, (work) => {
      const msg = path.join(work, "COMMIT_EDITMSG");
      fs.writeFileSync(msg, "Compare against a rival tool\n");
      assert.equal(runMain("message", msg), 0);
    });
  });

  test("passes when the message path is unreadable", () => {
    withSandbox({ blocklist: BLOCKLIST }, (work) => {
      assert.equal(runMain("message", path.join(work, "nope.txt")), 0);
    });
  });
});

describe("main — staged mode", () => {
  test("fails on a staged added line containing a blocklisted name", () => {
    withSandbox({ blocklist: BLOCKLIST }, (work) => {
      const git = initRepo(work);
      fs.writeFileSync(path.join(work, "notes.md"), "we benchmarked zorblat\n");
      git("add", "notes.md");
      assert.equal(runMain("staged"), 1);
    });
  });

  test("passes when the name only appears on a removed line", () => {
    withSandbox({ blocklist: BLOCKLIST }, (work) => {
      const git = initRepo(work);
      const file = path.join(work, "notes.md");
      fs.writeFileSync(file, "we benchmarked zorblat\nkeep this line\n");
      git("add", "notes.md");
      git("commit", "-q", "--no-verify", "-m", "seed");
      fs.writeFileSync(file, "keep this line\n");
      git("add", "notes.md");
      assert.equal(runMain("staged"), 0);
    });
  });

  test("ignores the diff's own +++ header, so a filename can't trip the scan", () => {
    withSandbox({ blocklist: BLOCKLIST }, (work) => {
      const git = initRepo(work);
      fs.writeFileSync(path.join(work, "zorblat.md"), "nothing incriminating\n");
      git("add", "zorblat.md");
      assert.equal(runMain("staged"), 0);
    });
  });

  test("passes a blocklisted name staged in a README (the allowed surface)", () => {
    withSandbox({ blocklist: BLOCKLIST }, (work) => {
      const git = initRepo(work);
      fs.writeFileSync(path.join(work, "README.md"), "We beat zorblat on every job.\n");
      git("add", "README.md");
      assert.equal(runMain("staged"), 0);
    });
  });

  test("still fails a blocklisted name staged in a CHANGELOG", () => {
    withSandbox({ blocklist: BLOCKLIST }, (work) => {
      const git = initRepo(work);
      fs.writeFileSync(path.join(work, "CHANGELOG.md"), "Now faster than zorblat\n");
      git("add", "CHANGELOG.md");
      assert.equal(runMain("staged"), 1);
    });
  });
});

// This script is mirrored byte-for-byte into every plugin repo's own
// scripts/git-hooks/, where it runs from that repo's pre-commit and commit-msg.
// Nothing else compares the copies, so they can drift silently -- this does.
//
// razor: in-tree copies only. Repos that aren't checked out under this one are
// out of reach here; if one ever needs covering, the upgrade path is a CI step
// that clones it before diffing.
describe("mirrored copies", () => {
  const canonical = fs.readFileSync(path.join(__dirname, "check-reference-names.js"), "utf8");

  for (const repo of ["foreman", "hush", "razor"]) {
    test(`${repo}'s copy is identical to this one`, (t) => {
      const copy = path.join(__dirname, "..", "..", repo, "scripts", "git-hooks", "check-reference-names.js");
      if (!fs.existsSync(copy)) return t.skip(`${repo} is not checked out`);
      assert.equal(
        fs.readFileSync(copy, "utf8"),
        canonical,
        `${repo}/scripts/git-hooks/check-reference-names.js has drifted from scripts/git-hooks/check-reference-names.js — copy the canonical file over it`
      );
    });
  }
});
