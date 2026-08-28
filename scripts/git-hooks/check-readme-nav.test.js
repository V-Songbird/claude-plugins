"use strict";

const { test, describe } = require("node:test");
const assert = require("node:assert");

const { slug, headingSlugs, anchorsIn, navRegion, checkMarkdown, main } = require("./check-readme-nav");

const NAV = [
  '<p align="center">',
  '  <a href="#install-it">Install it</a>',
  '  <a href="#the-numbers">The numbers</a>',
  '  <a href="#license">License</a>',
  "</p>",
  "",
  "## Install it",
  "## The numbers",
  "## License",
].join("\n");

describe("slug", () => {
  test("matches GitHub's rule", () => {
    assert.equal(slug("The fix"), "the-fix");
    assert.equal(slug('Why "flint"'), "why-flint");
    assert.equal(slug("Does it work?"), "does-it-work");
    assert.equal(slug("1. Make it write like a person"), "1-make-it-write-like-a-person");
  });
});

describe("headingSlugs", () => {
  test("collects every heading level", () => {
    const s = headingSlugs("# One\n### Two words\n");
    assert.deepEqual([...s].sort(), ["one", "two-words"]);
  });

  test("ignores headings inside a fenced block", () => {
    const s = headingSlugs("# Real\n\n```\n## Quoted\n```\n");
    assert.deepEqual([...s], ["real"]);
  });
});

describe("anchorsIn", () => {
  test("finds html and markdown in-page links", () => {
    assert.deepEqual(anchorsIn('<a href="#a">x</a> and [y](#b)'), ["a", "b"]);
  });

  test("ignores links that leave the page", () => {
    assert.deepEqual(anchorsIn('<a href="https://x/#frag">x</a> [y](other.md)'), []);
  });
});

describe("navRegion", () => {
  test("stops at the first section", () => {
    const region = navRegion('[a](#a)\n\n## First\n\n[b](#b)\n');
    assert.match(region, /#a/);
    assert.doesNotMatch(region, /#b/);
  });

  test("is the whole file when there are no sections", () => {
    assert.match(navRegion("[a](#a)\n"), /#a/);
  });
});

describe("checkMarkdown", () => {
  test("passes a page with a nav whose links all resolve", () => {
    assert.deepEqual(checkMarkdown(NAV, "README.md"), []);
  });

  test("flags a page with no nav", () => {
    const problems = checkMarkdown("## Install it\n", "README.md");
    assert.equal(problems.length, 1);
    assert.match(problems[0], /no nav line/);
  });

  test("flags a nav that is too short to be one", () => {
    const problems = checkMarkdown('[a](#one)\n[b](#two)\n\n## One\n## Two\n', "README.md");
    assert.equal(problems.length, 1);
    assert.match(problems[0], /no nav line/);
  });

  test("flags an anchor pointing at a renamed heading", () => {
    const renamed = NAV.replace("## The numbers", "## Does it work?");
    const problems = checkMarkdown(renamed, "README.md");
    assert.equal(problems.length, 1);
    assert.match(problems[0], /#the-numbers/);
  });

  test("flags a dead anchor below the nav too", () => {
    const problems = checkMarkdown(NAV + "\n\nSee [that](#gone).\n", "README.md");
    assert.equal(problems.length, 1);
    assert.match(problems[0], /#gone/);
  });

  test("does not resolve an anchor against a heading inside a fence", () => {
    const quoted = NAV.replace("## License", "```\n## License\n```");
    const problems = checkMarkdown(quoted, "README.md");
    assert.equal(problems.length, 1);
    assert.match(problems[0], /#license/);
  });
});

describe("main", () => {
  test("reads its targets from the argv it is given, not process.argv", () => {
    // The hooks call this after check-reference-names.js has already
    // rewritten process.argv[2] for its own use. Point process.argv at a real
    // file with no nav, which would fail, and pass a missing file, which is
    // skipped: a 0 proves the parameter won.
    const saved = process.argv.slice();
    process.argv = [saved[0], saved[1], "scripts/git-hooks/check-readme-nav.test.js"];
    try {
      assert.equal(main(["no-such-file-here.md"]), 0);
    } finally {
      process.argv = saved;
    }
  });
});
