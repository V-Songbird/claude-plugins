# Contributing

This is a personal plugin collection, currently maintained by a single author. Contributions are welcome in the form of bug reports, suggestions, and pull requests.

## Before opening a PR

- Check existing issues first — the problem may already be tracked or intentionally deferred.
- For substantial changes (new skills, new plugins, significant refactors), open an issue first to align on direction before writing code.
- Each plugin is independently reviewed. Keep changes scoped to a single plugin per PR; cross-plugin concerns go in a separate PR.

## Plugin structure

Each plugin follows this layout:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json        # name, version, description, author, keywords
├── CHANGELOG.md           # Keep a Changelog format
├── LICENSE                # MIT
├── skills/
│   └── skill-name/
│       ├── SKILL.md       # Claude Code skill definition
│       └── references/    # Reference files loaded by the skill
├── scripts/               # Shell scripts (hooks, utilities)
├── hooks/
│   └── hooks.json         # Hook wiring (PreToolUse, PostToolUse, etc.)
└── tests/                 # Test suite
```

## Tests

All plugins with scripted behavior include a test suite. Run tests before submitting:

- **Shell-based plugins** (jetbrains-router, kairoi): `bash <plugin>/tests/run.sh`
- **Python-based plugins** (rulesense): `pytest <plugin>/tests/ -v`

PRs that change script behavior without updating tests will not be merged.

## Changelog

Add an entry to `CHANGELOG.md` under `[Unreleased]` for every user-visible change. Follow the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. Version bumps happen at release time, not per-PR.

## Code of conduct

This project follows the [Contributor Covenant 2.1](./CODE_OF_CONDUCT.md).
