'use strict';

// The README replay is drawn from recorded transcripts, never hand-edited.
// These pin what a hand edit would break first: the reply comes from the
// transcript, the cut never strands a colon, the handoff prompt is found, and
// no element carries an attribute twice.

const { test } = require('node:test');
const assert = require('node:assert');
const { demoSvg, parseTranscript, cutParagraphs } = require('../runner/demo.js');

const line = (o) => JSON.stringify(o);
const transcript = [
  line({ type: 'assistant', message: { content: [{ type: 'text', text: 'Routing.' }] } }),
  line({ type: 'user', message: { content: [{ type: 'tool_result', content: '{"ok":true,"prompt":"<task_context>\\nYou are a dev.\\n</task_context>"}' }] } }),
  line({ type: 'result', subtype: 'success', result: '**Task 001.** Done thinking.\n\nThe prompt is on your clipboard.', duration_ms: 50000 }),
].join('\n');

test('parseTranscript takes the final reply, the clock, and the handoff prompt', () => {
  const t = parseTranscript(transcript);
  assert.strictEqual(t.reply, '**Task 001.** Done thinking.\n\nThe prompt is on your clipboard.');
  assert.strictEqual(t.ms, 50000);
  assert.ok(t.prompt.startsWith('<task_context>'));
});

test('a cut keeps whole paragraphs and never lands after a colon', () => {
  const md = 'First paragraph.\n\nIt is also saved at:\n\nC:\\somewhere\\file.txt\n\nTwo notes:\n\n- one\n- two';
  const { text, cut } = cutParagraphs(md, 3);
  assert.strictEqual(text, 'First paragraph.');
  assert.ok(cut);
  assert.deepStrictEqual(cutParagraphs('Short.', 3), { text: 'Short.', cut: false });
});

const exchange = { project: 'a notes tool', model: 'Claude Opus 5' };

test('both turns land on the page in order, the second reply cut with a count', () => {
  const turns = [
    { you: "what's next?", reply: 'Two tasks are ready.\n\n1. **Save notes (001)** — recommended.', ms: 30000, prompt: null },
    { you: '1. Copy it.', reply: '**Task 001.** ' + 'word '.repeat(60) + '\n\nSaved at:\n\nC:\\x', ms: 50000, prompt: '<task_context>\nYou are a dev.\n</task_context>' },
  ];
  const { svg, times } = demoSvg(exchange, turns);
  const body = svg.slice(svg.indexOf('</style>'));   // past the alt text, which quotes the replies
  const at = (s) => body.indexOf(s);
  assert.ok(at("you: what's next?") < at('Two tasks are ready.'));
  assert.ok(at('Two tasks are ready.') < at('you: 1. Copy it.'));
  assert.ok(svg.includes('…and on. 65 words in all.'));
  assert.ok(!svg.includes('C:\\x'));
  assert.ok(svg.includes('You are a dev.'));
  assert.ok(times[0] < times[1] && times[1] <= 8);
});

test('every element has each attribute once', () => {
  const { svg } = demoSvg(exchange, [{ you: 'hi', reply: 'hello', ms: 1000, prompt: '<task_context>\nx\n</task_context>' }]);
  for (const tag of svg.match(/<[a-z]+ [^>]*>/g)) {
    const names = [...tag.matchAll(/ ([a-zA-Z-]+)="/g)].map((m) => m[1]);
    assert.strictEqual(new Set(names).size, names.length, tag);
  }
});
