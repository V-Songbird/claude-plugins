---
paths:
  - "**/.claude-plugin/*.json"
  - "*/README.md"
  - "*/CHANGELOG.md"
  - "*/skills/**"
  - "*/hooks/**"
  - "*/scripts/**"
  - "*/tests/**"
---

# Plugin layout and release discipline

Every plugin in this repo lives in-tree — plain directories, one git history, no
submodules and no per-plugin repo. Experiments here get rewritten and deleted
freely; that is the point of the repo.

## Layout

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json        # name, description, author, keywords — NO version
│                          # field (the version is owned by
│                          # .claude-plugin/marketplace.json at the repo root)
├── CHANGELOG.md           # Keep a Changelog format
├── LICENSE                # MIT
├── README.md              # plain-language intro first, technical depth after
├── skills/                # if the plugin has skills
│   └── skill-name/
│       ├── SKILL.md       # Claude Code skill definition
│       └── references/    # Reference files loaded by the skill
├── hooks/
│   └── hooks.json         # Hook event wiring (PreToolUse, PostToolUse, etc.)
├── scripts/               # if the plugin has helper CLIs
└── tests/                 # required when the plugin has scripted behavior
```

A plugin carries only `README.md`, `CHANGELOG.md`, and `LICENSE`. It gets no
`CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/`, or git hooks
of its own — nobody is invited to contribute to an experiment, and a per-plugin
workflow file never runs from a subdirectory anyway.

Every plugin README shares one skeleton, tone, and style. Start from
[`.github/PLUGIN_README_TEMPLATE.md`](../../.github/PLUGIN_README_TEMPLATE.md):
copy it, fill the placeholders, and delete the guidance comments. The house
rules are documented inline in the template and in `public-docs.md`.

## Versions

`.claude-plugin/marketplace.json` is the single owner of every plugin's version.
Claude Code resolves a version from `plugin.json` first, the marketplace entry
second, and the git commit SHA last — so a `version` in a `plugin.json` here
would silently mask the marketplace entry and installers would never see the
bump. No `plugin.json` in this repo sets `version`;
`scripts/check-plugin-sources.js` fails CI if one does.

Because plugins are in-tree, a marketplace entry's `source` is a relative
`"./plugin-name"` path. There is no `source.sha` to keep in step with anything —
the marketplace and the plugin code move in the same commit by construction.

## Adding a plugin

1. Create the directory with the layout above.
2. Add an entry to `.claude-plugin/marketplace.json` with `"source": "./name"`
   and a `version`.
3. Run the `manifest-curator` agent (audit mode) and
   `node scripts/check-plugin-sources.js`.

## Tests

Any plugin with scripted behavior carries a `node:test` suite under `tests/`:

```
node --test <plugin>/tests/*.test.js
```

CI runs every plugin's suite plus the repo's own tooling tests. The
`run-tests-on-edit` hook reruns a plugin's suite automatically when an edit
lands in its `scripts/` or `hooks/`.

## Git hooks

Once after cloning:

```
git config core.hooksPath scripts/git-hooks
```

This enables the `pre-commit` and `commit-msg` reference-name gates. See
`public-docs.md` for the rule they enforce.
