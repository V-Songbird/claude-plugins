'use strict';

// Draws the README's side-by-side replay (hush/assets/demo.svg) from two real
// runs of one task: every message the baseline sent, in order, beside the one
// message hush sent, each appearing at its share of the recorded wall clock.
//
//   node runner/demo.js --records records/rm320-99a236ff --task failing-suite \
//     --baseline failing-suite__baseline__r4 --hush failing-suite__hush__r1 \
//     --out ../../hush/assets/demo.svg
//
// Without --baseline/--hush it takes, per arm, the run whose final message is
// the median length — never the best-looking one. Both themes ride on
// prefers-color-scheme, like bench-cuts.svg.

const fs = require('node:fs');
const path = require('node:path');
const { readRecords } = require('./records.js');

const W = 700, PAD = 28, GAP = 22;
const COL = Math.floor((W - 2 * PAD - GAP) / 2);
const FS = 13.5, LH = 18, CPL = 46, CODE_CPL = 40;
const RUN_S = 8, HOLD_S = 6, DUR = RUN_S + HOLD_S;
const MAX_FINAL_LINES = 14;
const Y0 = 154;

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

// Markdown -> [{ text, kind }] with kind in text | bold | head | code | gap.
function mdLines(md) {
  const out = [];
  let code = false;
  for (const raw of md.split('\n')) {
    if (raw.trim().startsWith('```')) { code = !code; continue; }
    if (code) { for (const w of wrap(raw.trimEnd(), CODE_CPL, '    ')) out.push({ text: w, kind: 'code' }); continue; }
    let s = raw.trim();
    if (!s) { out.push({ text: '', kind: 'gap' }); continue; }
    let kind = 'text';
    if (s.startsWith('#')) { s = s.replace(/^#+/, '').trim(); kind = 'head'; }
    else if (/^\*\*[^*]+\*\*/.test(s)) kind = 'bold';
    s = s.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*/g, '').replace(/`/g, '');
    for (const w of wrap(s, CPL)) out.push({ text: w, kind });
  }
  return out;
}

const fadeIn = (t) => `<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;${(t / DUR).toFixed(3)};${Math.min((t + 0.25) / DUR, 1).toFixed(3)};1" dur="${DUR}s" repeatCount="indefinite"/>`;

function block(x, y, lines, t, dot) {
  const parts = [`<g opacity="0">${fadeIn(t)}`];
  if (dot) parts.push(`<circle class="${dot}" cx="${x + 5}" cy="${y - 4}" r="4"/>`);
  let yy = y;
  for (const { text, kind } of lines) {
    if (kind === 'gap') { yy += LH / 2; continue; }
    const mono = kind === 'code' ? ' font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"' : '';
    const weight = kind === 'head' || kind === 'bold' ? ' font-weight="700"' : '';
    const cls = kind === 'code' ? 'ink2' : 'ink';
    parts.push(`<text class="${cls}" x="${x + 16}" y="${yy}" font-size="${kind === 'code' ? 13 : FS}"${mono}${weight}>${esc(text)}</text>`);
    yy += LH;
  }
  parts.push('</g>');
  return { svg: parts.join(''), height: yy - y };
}

function column(x, run, dot, slowMs) {
  const parts = [];
  let y = Y0;
  const n = run.narrationTexts.length + 1;
  const times = Array.from({ length: n }, (_, i) => (run.wallMs * RUN_S / slowMs) * (i + 1) / n);
  run.narrationTexts.forEach((msg, i) => {
    const b = block(x, y, mdLines(msg), times[i], dot);
    parts.push(b.svg); y += b.height + 10;
  });
  let lines = mdLines(run.finalText);
  const cut = lines.length > MAX_FINAL_LINES;
  if (cut) lines = lines.slice(0, MAX_FINAL_LINES);
  const b = block(x, y, lines, times[n - 1], dot);
  parts.push(b.svg); y += b.height;
  if (cut) {
    parts.push(`<g opacity="0">${fadeIn(times[n - 1])}<text class="mut" x="${x + 16}" y="${y}" font-size="${FS}">…and on. ${run.finalWords} words in all.</text></g>`);
    y += LH;
  }
  return { svg: parts.join(''), bottom: y, answerAt: times[n - 1] };
}

function demoSvg(base, hush, prompt) {
  const slow = Math.max(base.wallMs, hush.wallMs);
  const xr = PAD + COL + GAP;
  const left = column(PAD, base, 'bp', slow);
  const right = column(xr, hush, 'ac', slow);
  const H = Math.max(left.bottom, right.bottom) + 56;
  const msgs = base.narrationTexts.length + 1;
  const label = `The same job played twice, side by side. The prompt: ${prompt} `
    + `Without hush, Claude sends ${msgs} messages: ${base.narrationTexts.length} progress notes while it works, `
    + `then a ${base.finalWords}-word write-up. With hush, nothing until the work is done, then one ${hush.finalWords}-word answer. `
    + 'Both sessions left the suite green. One real session each on Claude Opus 5, replayed on the recorded wall clock.';
  const style = '<style>.card{fill:#fcfcfb;stroke:rgba(11,11,11,.07)}.ink{fill:#0b0b0b}.ink2{fill:#52514e}.mut{fill:#898781}'
    + '.bp{fill:#dcd9d0}.ac{fill:#2a78d6}.pill{fill:#f0efeb}.pillt{fill:#52514e}.you{fill:#52514e}'
    + '@media(prefers-color-scheme:dark){.card{fill:#161b22;stroke:#30363d}.ink{fill:#e6edf3}.ink2{fill:#b0b8c0}.mut{fill:#9198a1}'
    + '.bp{fill:#3d3c37}.ac{fill:#4c9be8}.pill{fill:#2b2b29}.pillt{fill:#9198a1}.you{fill:#b0b8c0}}</style>';
  const pill = (x, cls, tcls, text) => `<rect class="${cls}" x="${x}" y="100" width="${COL}" height="28" rx="14"/>`
    + `<text class="${tcls}" x="${x + COL / 2}" y="119" font-size="15" font-weight="700" text-anchor="middle">${esc(text)}</text>`;
  const head = [`<text class="ink" x="${PAD + 8}" y="40" font-size="21" font-weight="800">Same job, same files, both ways</text>`];
  let yy = 62;
  for (const p of wrap(`you: ${prompt}`, 96)) { head.push(`<text class="you" x="${PAD + 8}" y="${yy}" font-size="14" font-style="italic">${esc(p)}</text>`); yy += LH; }
  head.push(pill(PAD, 'bp', 'pillt', 'no plugin'), pill(xr, 'ac', 'card', 'hush'));
  const th = right.answerAt;
  head.push(`<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;${(th / DUR).toFixed(3)};${Math.min((th + 0.25) / DUR, 1).toFixed(3)};1" dur="${DUR}s" repeatCount="indefinite"/>`
    + `<text class="mut" x="${xr + 16}" y="${Y0}" font-size="${FS}" font-style="italic">working, quietly</text></g>`);
  const foot = `<text class="mut" x="${PAD + 8}" y="${H - 22}" font-size="13.5">one real session each, Claude Opus 5 · replayed on the recorded clock · both finished green</text>`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif" role="img" aria-label="${esc(label)}">`
    + style
    + '<filter id="s" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#0b0b0b" flood-opacity=".10"/></filter>'
    + `<rect class="card" x="8" y="6" width="${W - 16}" height="${H - 12}" rx="18" filter="url(#s)"/>`
    + head.join('') + left.svg + right.svg + foot + '</svg>';
  return { svg, label };
}

// The run whose final message sits at the median length — a typical one, not a flattering one.
function medianRun(runs) {
  const sorted = [...runs].sort((a, b) => a.finalWords - b.finalWords);
  return sorted[Math.floor((sorted.length - 1) / 2)];
}

function main() {
  const argv = process.argv.slice(2);
  const flag = (n, d) => { const i = argv.indexOf(`--${n}`); return i >= 0 ? argv[i + 1] : d; };
  const root = path.resolve(__dirname, '..');
  const dir = path.resolve(flag('records', path.join(root, 'records')));
  const taskId = flag('task', 'failing-suite');
  const out = path.resolve(flag('out', path.join(root, '..', '..', 'hush', 'assets', 'demo.svg')));
  const { runs } = readRecords(dir);
  const ofTask = runs.filter((r) => r.task === taskId && r.check?.pass);
  const pick = (arm, key) => {
    const arms = ofTask.filter((r) => r.arm === arm);
    if (!arms.length) throw new Error(`no passing ${arm} run of ${taskId} under ${dir}`);
    if (!key) return medianRun(arms);
    const hit = arms.find((r) => r.key === key);
    if (!hit) throw new Error(`no run ${key} among ${arms.map((r) => r.key).join(', ')}`);
    return hit;
  };
  const base = pick('baseline', flag('baseline'));
  const hush = pick('hush', flag('hush'));
  const tasks = JSON.parse(fs.readFileSync(path.join(root, 'tasks.json'), 'utf8'));
  const task = tasks.find((t) => t.id === taskId);
  if (!task) throw new Error(`no task ${taskId} in tasks.json`);
  const { svg, label } = demoSvg(base, hush, task.prompt);
  fs.writeFileSync(out, svg);
  console.log(`wrote ${out} from ${base.key} (${base.finalWords} words, ${base.assistantMsgs} messages) and ${hush.key} (${hush.finalWords} words, ${hush.assistantMsgs} message${hush.assistantMsgs === 1 ? '' : 's'})`);
  console.log(`alt text for the README:\n${label}`);
}

module.exports = { demoSvg, mdLines, wrap, medianRun };

if (require.main === module) main();
