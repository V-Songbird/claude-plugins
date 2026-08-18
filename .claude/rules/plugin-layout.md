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

Every plugin here lives in its own public GitHub repo, mounted in this one as a
git submodule (`.gitmodules` lists `foreman`, `hush`, `razor`). Editing a
plugin means editing inside that submodule and committing there; the parent
repo only records which commit each plugin is pinned to. Never commit plugin
source from the parent.

The canonical layout, community-file rules, and release sequence live in
[`CONTRIBUTING.md`](../../CONTRIBUTING.md) — read it rather than restating it.
What follows is only what is easy to get wrong at edit time.

## Layout

```
plugin-name/                  # a separate repo, mounted as a submodule
├── .claude-plugin/
│   └── plugin.json           # NO version field — see Versions below
├── README.md                 # from .github/PLUGIN_README_TEMPLATE.md
├── CHANGELOG.md              # dated entries, newest first
├── LICENSE                   # MIT
├── CONTRIBUTING.md           # verbatim from .github/PLUGIN_CONTRIBUTING_TEMPLATE.md
├── SECURITY.md               # verbatim from .github/PLUGIN_SECURITY_TEMPLATE.md, plus a plugin section
├── CODE_OF_CONDUCT.md        # verbatim from .github/PLUGIN_CODE_OF_CONDUCT_TEMPLATE.md
├── skills/<name>/SKILL.md    # plus references/ for files the skill loads
├── hooks/hooks.json          # hook event wiring
├── scripts/                  # helper CLIs, plus scripts/git-hooks/
└── tests/                    # required when the plugin has scripted behavior
```

All three community files are required, and the template body is copied from
this repo's `.github/` templates verbatim — don't hand-drift it. A plugin may
add its own section into that body when it has something plugin-specific to say
(hush's `SECURITY.md` adds a note on its `[hush …]` markers before the closing
`> [!NOTE]` block); every template block has to survive verbatim and in order.
The root copies of those files govern this marketplace repo itself, not the
plugins.

## Versions

`.claude-plugin/marketplace.json` at this repo's root is the single owner of
every plugin's version. Claude Code resolves a version from `plugin.json`
first, the marketplace entry second, and the commit SHA last — so a `version`
in a plugin's `plugin.json` would silently mask the marketplace entry and
installers would never see the bump. No `plugin.json` here sets one.

Because plugins are separate repos, each marketplace entry carries
`"source": {"source": "url", "url": …, "sha": …}`. The entry's `version` and
`source.sha` must change together in one parent commit, or installers get a
mismatched label or a silently skipped update.

Two scripts guard this, both under `scripts/git-hooks/`:
`check-marketplace-sync.js` runs from the parent `pre-commit` hook and blocks a
commit that moves a submodule pointer without the matching `source.sha`;
`verify-marketplace-pins.js` runs in CI and re-checks every pin. Neither one
checks the `version` bump itself — verify that by eye.

The local-only `.claude/skills/cut-release/` skill walks the whole sequence; if
you are reading this from a clone, see `CONTRIBUTING.md` → "Cutting a release".

## Adding a plugin

1. When onboarding a new plugin, create its own public GitHub repo matching the `## Layout` structure above.
2. Add it as a submodule here, then add a `marketplace.json` entry with the
   `url`/`sha` source shape and a `version`.
3. Run the local-only `manifest-curator` agent (audit mode) and
   `node scripts/git-hooks/verify-marketplace-pins.js`.

## Tests

Any plugin with scripted behavior carries a `node:test` suite under `tests/`:

```
node --test <plugin>/tests/*.test.js
```

Each plugin repo installs its own `pre-commit` hook (copied from
`scripts/git-hooks/plugin-pre-commit-template.js`) that runs this suite and
blocks the commit if it fails. Keep those copies in sync with the template.
CI in this repo validates the marketplace and the git-hook scripts' own tests —
it does not run the plugins' suites. The repo-wide `run-tests-on-edit` hook
reruns a plugin's suite when an edit lands in its `scripts/` or `hooks/`.

## Git hooks

Once after cloning, in this repo and in each plugin repo:

```
git config core.hooksPath scripts/git-hooks
```

In this repo that enables the marketplace-sync check plus the `pre-commit` and
`commit-msg` reference-name gates. See `public-docs.md` for the rule they
enforce.
