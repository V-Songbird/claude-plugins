'use strict';

// Draws the README's replay (foreman/assets/demo.svg) from a real recorded
// exchange: what the user typed, what Foreman answered, in order, each reply
// landing at its share of the recorded wall clock, then the opening of the
// prompt Foreman wrote.
//
//   node runner/demo.js --exchange records/demo-2026-09-04/exchange.json \
//     --out ../../foreman/assets/demo.svg
//
// exchange.json names the project, the model, and one entry per turn: the
// text the user sent and the `claude -p --output-format stream-json`
// transcript of Foreman's answer. Transcripts stay under records/ (local,
// never committed); the drawn SVG ships. Both themes ride on
// prefers-color-scheme, like paper-trail.svg.

const fs = require('node:fs');
const path = require('node:path');

const W = 700, PAD = 28;
const COL = W - 2 * PAD;
const FS = 13.5, LH = 18, CPL = 88, CODE_CPL = 80;
const RUN_S = 8, HOLD_S = 6, DUR = RUN_S + HOLD_S;
const GAP_S = 0.4;                 // the user's next line lands this long after a reply
const MAX_REPLY_LINES = 5;         // applies to every reply after the first

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function wrap(text, width, indent = '') {
  const out = [];
  let line = '';
  for (const word of text.split(/\s+/).filter(Boolean)) {
    const next = line ? `${line} ${word}` : word;
    if (next.length > width && line) { out.push(line); line = indent + word; } else line = next;
  }
  if (line) out.push(line);
  return out.length ? out : [''];
}

// One transcript -> { reply, ms, prompt }. `reply` is the text of the final
// assistant message; `prompt` is the handoff a tool call returned, if any.
function parseTranscript(text) {
  let reply = '', ms = 0, prompt = null;
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    let ev;
    try { ev = JSON.parse(line); } catch { continue; }
    if (ev.type === 'result') { reply = ev.result || reply; ms = ev.duration_ms || ms; }
    if (ev.type === 'user' && Array.isArray(ev.message?.content)) {
      for (const b of ev.message.content) {
        if (b.type !== 'tool_result') continue;
        const s = typeof b.content === 'string' ? b.content : (b.content || []).map((x) => x.text || '').join('');
        const i = s.indexOf('{');
        if (i < 0 || !s.includes('"prompt":"<task_context>')) continue;
        try { prompt = JSON.parse(s.slice(i)).prompt; } catch { /* not the handoff result */ }
      }
    }
  }
  return { reply, ms, prompt };
}

// Markdown -> [{ text, kind }], kind in text | bold | head | gap.
function mdLines(md) {
  const out = [];
  for (const raw of md.split('\n')) {
    const s = raw.trim();
    if (!s) { out.push({ text: '', kind: 'gap' }); continue; }
    let kind = 'text';
    let t = s;
    if (t.startsWith('#')) { t = t.replace(/^#+/, '').trim(); kind = 'head'; }
    else if (/^\*\*[^*]+\*\*$/.test(t)) kind = 'bold';
    t = t.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*/g, '').replace(/\*/g, '').replace(/`/g, '');
    const indent = /^\d+\.\s/.test(t) || /^-\s/.test(t) ? '   ' : '';
    for (const w of wrap(t, CPL, indent)) out.push({ text: w, kind });
  }
  while (out.length && out[out.length - 1].kind === 'gap') out.pop();
  return out;
}

// Keep whole paragraphs while they fit in `budget` lines. A paragraph that
// ends with a colon belongs with the next one, so a cut never lands after it.
function cutParagraphs(md, budget) {
  const paras = md.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  const kept = [];
  let used = 0;
  for (let i = 0; i < paras.length; i++) {
    let group = [paras[i]];
    while (group[group.length - 1].endsWith(':') && i + 1 < paras.length) group.push(paras[++i]);
    const lines = group.reduce((n, p) => n + mdLines(p).length, 0) + (kept.length ? 1 : 0);
    if (used + lines > budget) return { text: kept.join('\n\n'), cut: true };
    kept.push(...group); used += lines;
  }
  return { text: kept.join('\n\n'), cut: false };
}

const words = (s) => s.split(/\s+/).filter(Boolean).length;
const plain = (s) => s.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/[*`]/g, '').replace(/\s+/g, ' ').trim();

const fadeIn = (t) => `<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;${(t / DUR).toFixed(3)};${Math.min((t + 0.25) / DUR, 1).toFixed(3)};1" dur="${DUR}s" repeatCount="indefinite"/>`;

function badge(x, y, cls, tcls, text) {
  const w = text.length * 8 + 16;
  return `<rect class="${cls}" x="${x}" y="${y - 13}" width="${w}" height="20" rx="10"/>`
    + `<text class="${tcls}" x="${x + w / 2}" y="${y + 1}" font-size="12.5" font-weight="700" text-anchor="middle">${esc(text)}</text>`;
}

function block(y, lines, t, who) {
  const parts = [`<g opacity="0">${fadeIn(t)}`];
  parts.push(who === 'you' ? badge(PAD, y, 'bp', 'pillt', 'you') : badge(PAD, y, 'ac', 'card', 'Foreman'));
  let yy = y;
  for (const { text, kind } of lines) {
    if (kind === 'gap') { yy += LH / 2; continue; }
    const mono = kind === 'code' ? ' font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"' : '';
    const weight = kind === 'head' || kind === 'bold' ? ' font-weight="700"' : '';
    const style = who === 'you' ? ' font-style="italic"' : '';
    const cls = who === 'you' ? 'you' : kind === 'code' ? 'ink2' : kind === 'mut' ? 'mut' : 'ink';
    parts.push(`<text class="${cls}" x="${PAD + 84}" y="${yy}" font-size="${kind === 'code' ? 13 : FS}"${mono}${weight}${style}>${esc(text)}</text>`);
    yy += LH;
  }
  parts.push('</g>');
  return { svg: parts.join(''), bottom: yy };
}

// The opening of the handoff: its task_context and relevant_files blocks —
// the part that shows the files Foreman checked — then an ellipsis.
function promptLines(prompt) {
  const out = [];
  for (const tag of ['task_context', 'relevant_files']) {
    const m = prompt.match(new RegExp(`<${tag}>[\\s\\S]*?</${tag}>`));
    if (!m) continue;
    if (out.length) out.push({ text: '', kind: 'gap' });
    for (const l of m[0].split('\n')) for (const w of wrap(l, CODE_CPL, '  ')) out.push({ text: w, kind: 'code' });
  }
  out.push({ text: '…', kind: 'code' });
  return out;
}

function demoSvg(exchange, turns) {
  const total = turns.reduce((s, t) => s + t.ms, 0) + GAP_S * 1000 * (turns.length - 1);
  const scale = RUN_S / total;
  const parts = [];
  let y = 128, clock = 0;
  const times = [];
  turns.forEach((t, i) => {
    const youAt = clock * scale;
    const you = block(y, [{ text: `you: ${t.you}`, kind: 'text' }], youAt, 'you');
    parts.push(you.svg); y = you.bottom + 8;
    clock += t.ms;
    const replyAt = clock * scale;
    times.push(replyAt);
    let md = t.reply, cut = false;
    if (i > 0) ({ text: md, cut } = cutParagraphs(t.reply, MAX_REPLY_LINES));
    const lines = mdLines(md);
    if (cut) lines.push({ text: '', kind: 'gap' }, { text: `…and on. ${words(t.reply)} words in all.`, kind: 'mut' });
    const reply = block(y, lines, replyAt, 'foreman');
    parts.push(reply.svg); y = reply.bottom + 14;
    if (t.prompt) {
      const lead = [{ text: 'The prompt it wrote opens like this. The files and line numbers were checked a moment earlier:', kind: 'text' }, { text: '', kind: 'gap' }, ...promptLines(t.prompt)];
      const p = block(y, lead, replyAt, 'foreman');
      parts.push(p.svg); y = p.bottom + 8;
    }
    clock += GAP_S * 1000;
  });
  const H = y + 48;
  const label = `One real exchange with Foreman on ${exchange.project}. `
    + turns.map((t, i) => `You: ${t.you} Foreman answers after ${(t.ms / 1000).toFixed(0)} seconds: ${plain(t.reply).slice(0, 220)}${plain(t.reply).length > 220 ? '…' : ''}`).join(' ')
    + ` The prompt Foreman wrote names the files it checked, with line numbers. ${exchange.model}, replayed on the recorded wall clock.`;
  const style = '<style>.card{fill:#fcfcfb;stroke:rgba(11,11,11,.07)}.ink{fill:#0b0b0b}.ink2{fill:#52514e}.mut{fill:#898781}'
    + '.bp{fill:#dcd9d0}.ac{fill:#16a34a}.pillt{fill:#52514e}.you{fill:#52514e}'
    + '@media(prefers-color-scheme:dark){.card{fill:#161b22;stroke:#30363d}.ink{fill:#e6edf3}.ink2{fill:#b0b8c0}.mut{fill:#9198a1}'
    + '.bp{fill:#3d3c37}.ac{fill:#22c55e}.pillt{fill:#9198a1}.you{fill:#b0b8c0}}</style>';
  const head = `<text class="ink" x="${PAD + 8}" y="40" font-size="21" font-weight="800">One morning with Foreman</text>`
    + `<text class="mut" x="${PAD + 8}" y="64" font-size="14.5">${esc(exchange.project)}</text>`
    + `<text class="mut" x="${PAD + 8}" y="84" font-size="14.5">the roadmap is a plain file in the repo; nothing here was typed for the picture</text>`;
  const foot = `<text class="mut" x="${PAD + 8}" y="${H - 22}" font-size="13.5">one real exchange, ${esc(exchange.model)} · replayed on the recorded clock</text>`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif" role="img" aria-label="${esc(label)}">`
    + style
    + '<filter id="s" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#0b0b0b" flood-opacity=".10"/></filter>'
    + `<rect class="card" x="8" y="6" width="${W - 16}" height="${H - 12}" rx="18" filter="url(#s)"/>`
    + head + parts.join('') + foot + '</svg>';
  return { svg, label, times };
}

function main() {
  const argv = process.argv.slice(2);
  const flag = (n, d) => { const i = argv.indexOf(`--${n}`); return i >= 0 ? argv[i + 1] : d; };
  const root = path.resolve(__dirname, '..');
  const exchangePath = path.resolve(flag('exchange', path.join(root, 'records', 'demo-2026-09-04', 'exchange.json')));
  const out = path.resolve(flag('out', path.join(root, '..', '..', 'foreman', 'assets', 'demo.svg')));
  const exchange = JSON.parse(fs.readFileSync(exchangePath, 'utf8'));
  const turns = exchange.turns.map((t) => ({ you: t.you, ...parseTranscript(fs.readFileSync(path.join(path.dirname(exchangePath), t.transcript), 'utf8')) }));
  const { svg, label } = demoSvg(exchange, turns);
  fs.writeFileSync(out, svg);
  console.log(`wrote ${out} from ${turns.length} turns (${turns.map((t) => `${(t.ms / 1000).toFixed(1)} s`).join(', ')})`);
  console.log(`alt text for the README:\n${label}`);
}

module.exports = { demoSvg, parseTranscript, mdLines, cutParagraphs, wrap };

if (require.main === module) main();
