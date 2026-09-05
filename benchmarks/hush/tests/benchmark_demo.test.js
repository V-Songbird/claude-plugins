"use strict";

// The README replay is drawn from records, never hand-edited. These pin the
// parts a hand edit would break first: every message lands on the page, the
// two columns stay inside the card, and the run picked by default is the
// typical one, not the flattering one.

const { test } = require("node:test");
const assert = require("node:assert");
const { demoSvg, mdLines, medianRun } = require("../runner/demo.js");

const run = (over) => ({
  key: "t__arm__r1", arm: "baseline", wallMs: 30000, finalWords: 40, assistantMsgs: 1,
  narrationTexts: [], finalText: "**Green.** One bug in `x.js`.", ...over,
});

test("every message of both runs is on the page, in order", () => {
  const base = run({ narrationTexts: ["first I look", "then I run it"], finalText: "done at last" });
  const hush = run({ arm: "hush", finalText: "**Green.** done" });
  const { svg } = demoSvg(base, hush, "fix it");
  const at = (s) => svg.indexOf(s);
  assert.ok(at("first I look") < at("then I run it") && at("then I run it") < at("done at last"));
  assert.ok(svg.includes("Green. done"));
  assert.ok(svg.includes("you: fix it"));
});

test("a long final message is cut with a count, never silently", () => {
  const base = run({ finalText: Array.from({ length: 40 }, (_, i) => `line ${i}`).join("\n"), finalWords: 254 });
  const { svg } = demoSvg(base, run({ arm: "hush" }), "p");
  assert.ok(svg.includes("254 words in all"));
  assert.ok(!svg.includes("line 39"));
});

test("the alt text carries the counts the picture makes", () => {
  const base = run({ narrationTexts: ["a", "b", "c"], finalWords: 200 });
  const { label } = demoSvg(base, run({ arm: "hush", finalWords: 42 }), "p");
  assert.match(label, /4 messages: 3 progress notes/);
  assert.match(label, /200-word write-up/);
  assert.match(label, /one 42-word answer/);
});

test("text never runs wider than a column, code included", () => {
  const long = "word ".repeat(60).trim();
  const lines = mdLines(`${long}\n\n\`\`\`\nconst ${"x".repeat(80)} = 1;\n\`\`\``);
  for (const { text, kind } of lines) {
    assert.ok(text.length <= (kind === "code" ? 90 : 46), `${kind}: ${text.length} chars`);
  }
  assert.ok(lines.some((l) => l.kind === "code"));
});

test("the default pick is the median-length reply, not the shortest", () => {
  const runs = [run({ key: "short", finalWords: 10 }), run({ key: "mid", finalWords: 40 }), run({ key: "long", finalWords: 300 })];
  assert.strictEqual(medianRun(runs).key, "mid");
});

test("every element has each attribute once", () => {
  const { svg } = demoSvg(run({ finalText: "```\ncode\n```" }), run({ arm: "hush" }), "p");
  for (const tag of svg.match(/<[a-z]+ [^>]*>/g)) {
    const names = [...tag.matchAll(/ ([a-zA-Z-]+)="/g)].map((m) => m[1]);
    assert.strictEqual(new Set(names).size, names.length, tag);
  }
});
