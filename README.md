<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg" />
    <img src="assets/logo.svg" alt="foundry" width="240" />
  </picture>
  <h1>foundry</h1>
  <p><strong>Claude Code plugins that keep the plan, cut the chatter, and stop the over-building.</strong></p>
</div>

<p align="center">
    <a href="https://github.com/V-Songbird/foundry/stargazers"><img src="https://img.shields.io/github/stars/V-Songbird/foundry?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/V-Songbird/foundry/blob/main/LICENSE"><img src="https://img.shields.io/github/license/V-Songbird/foundry" alt="License"/></a>
    <a href="https://docs.anthropic.com/en/docs/claude-code"><img src="https://img.shields.io/badge/Claude_Code-E5582B" alt="Claude Code"/></a>
</p>

> **TL;DR** — Three small plugins for Claude Code. foreman keeps your project plan alive between sessions. hush cuts the chatter and the cost. razor stops code nobody needed. Install one or all three — they stay out of each other's way.

---

## New here?

[Claude Code](https://code.claude.com/docs/en/overview) is Anthropic's AI coding assistant. **Plugins** extend it: they teach Claude new habits, add guardrails, or change how it behaves. One-line install, no setup.

This is a small, hand-picked collection. Each plugin does one job well and works on its own.

## Install

Inside Claude Code, run:

```
/plugin marketplace add V-Songbird/foundry
/plugin install <plugin-name>@foundry
```

The first command registers this collection — you only do it once. The second installs whichever plugin you want. Changed your mind? `/plugin uninstall <plugin-name>@foundry` and it's gone.

---

## The plugins

### [foreman](https://github.com/V-Songbird/foreman) — Your plan survives the session

Every Claude Code session forgets everything when it ends. Foreman keeps your plan in the repo, committed like code. Ask "what's next?" and you get the recommended task, the reason it's first, and a ready-to-run prompt whose paths were checked against your code. After each commit, it spots the task that looks finished and asks before checking it off.

```
/plugin install foreman@foundry
```

### [hush](https://github.com/V-Songbird/hush) — Less chatter, lower cost

Claude bills you for every word it says while it works — narration, previews, walls of command output. hush trims that bulk at the source, before it hits your bill. You get silence while it works, then one clear answer-first summary at the end. Big output is saved whole to a local file before it's shortened, so nothing is lost.

```
/plugin install hush@foundry
```

### [razor](https://github.com/V-Songbird/razor) — Stops Claude from over-building

AI assistants love to add: a new library here, five helper files there, an abstraction "for later." razor makes Claude run a short checklist first — is it needed, does it already exist, does the platform do it for free? The first reach for a new dependency gets one challenge, with your project's declared-dependency list right in the message. Never a hard block — always one forced second thought.

```
/plugin install razor@foundry
```

### Which one first?

| You want to… | Install |
| --- | --- |
| Keep a project plan that outlives the session | **foreman** |
| Cut token cost and noise | **hush** |
| Keep the codebase lean | **razor** |

hush and razor are natural partners: hush governs how Claude *talks*, razor governs what it *builds*.

---

## Repository layout

```
foundry/
├── foreman/
├── hush/
└── razor/
```

Every plugin lives in its own repo, mounted here as a git submodule (see [`.gitmodules`](.gitmodules)). Each ships its metadata in `.claude-plugin/plugin.json` and carries its own `README.md`, `CHANGELOG.md`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md`. The root copies of the community files govern contributions to this marketplace repo itself. The marketplace index is [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). It is the single owner of every plugin's version number — the plugin.json files carry no version field.

---

## Development

Run this once after cloning, to switch on the commit gates:

```
git config core.hooksPath scripts/git-hooks
```

`.claude/settings.json` (committed) registers two repo-wide dev hooks. Both are dev-only. Neither fires for anyone who merely *installed* a plugin from this repo — only for edits made inside the source tree itself:

- `.claude/hooks/run-tests-on-edit.js` reruns a plugin's own test suite after an `Edit`/`Write` lands in that plugin's `scripts/` or `hooks/` dir. It finds the right suite by walking up to the nearest `.claude-plugin/plugin.json` marker, so it works for any plugin here. Silent when green; it surfaces a failure when red.
- `.claude/hooks/nudge-manifest-curator.js` nudges a follow-up `manifest-curator` audit after an edit lands in `.claude-plugin/marketplace.json` or any plugin's `.claude-plugin/plugin.json`. Manifest edits are easy to get subtly wrong, so the reminder earns its keep.

Tests, for a plugin that has them:

```
node --test <plugin>/tests/*.test.js
```

---

## Community

- Bug reports and suggestions: [GitHub Issues](https://github.com/V-Songbird/foundry/issues)
- Security reports: [SECURITY.md](./SECURITY.md)
- Contribution guidelines: [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## License

MIT — see [LICENSE](./LICENSE).
