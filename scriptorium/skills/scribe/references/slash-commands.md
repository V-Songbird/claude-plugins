# Slash command authoring reference

Custom slash commands and skills are now the same mechanism. This file covers what's specific to commands; for the full frontmatter table and invocation-control table, see [skill-authoring.md](skill-authoring.md).

## 1. Commands vs skills today

> "Custom commands have been merged into skills. A file at `.claude/commands/deploy.md` and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy` and work the same way." — [skills docs](https://code.claude.com/docs/en/skills)

`.claude/commands/*.md` files keep working with the same frontmatter as `SKILL.md`. Skills are the recommended format because they get a directory for supporting files, can be invoked automatically by Claude when relevant, and support the full feature set.

## 2. When to author a command vs a skill

Decision rules:

| Situation | Author as |
|---|---|
| Single-file workflow, no supporting scripts/templates, no auto-invocation desired | Command (`.claude/commands/<name>.md`) is fine |
| Needs supporting files (scripts, templates, examples, sub-references) | Skill (`.claude/skills/<name>/SKILL.md`) |
| Should fire automatically when Claude detects relevant context | Skill (commands without a directory still trigger from descriptions, but skills are the documented path for auto-invocation) |
| Bundled in a plugin alongside other components | Either works — plugins support both `commands/` and `skills/` |
| Migrating an existing `.claude/commands/` file you'll keep extending | Promote to a skill directory; move the body to `SKILL.md` |

Default: write a skill. Reach for a command file only when the workflow is a one-paragraph instruction with no supporting material.

## 3. Directory layout and discovery

| Scope | Command path | Skill path |
|---|---|---|
| Personal | `~/.claude/commands/<name>.md` | `~/.claude/skills/<name>/SKILL.md` |
| Project | `.claude/commands/<name>.md` | `.claude/skills/<name>/SKILL.md` |
| Plugin | `<plugin>/commands/<name>.md` | `<plugin>/skills/<name>/SKILL.md` |
| Enterprise | via [managed settings](https://code.claude.com/docs/en/settings#settings-files) | via managed settings |

Precedence: enterprise > personal > project. Plugin entries are namespaced (see §8) so they never collide with the other levels. **If a skill and a command share the same name, the skill takes precedence.**

Nested project layouts (monorepos) are auto-discovered: when working in `packages/frontend/`, Claude Code also loads `packages/frontend/.claude/skills/`. The same nesting rule does **not** apply to commands beyond the project root.

## 4. Frontmatter for commands

A command file uses the same YAML frontmatter as `SKILL.md`. The full field table — `name`, `description`, `when_to_use`, `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `effort`, `context`, `agent`, `hooks`, `paths`, `shell` — is defined once in [skill-authoring.md §1](skill-authoring.md). Every field listed there works in `.claude/commands/*.md`.

Recommended minimum for a command:

```markdown
---
description: One-line trigger description; front-load the key use case.
argument-hint: [issue-number]
---

Command body that Claude executes when invoked.
```

`name` is inferred from the filename. `description` drives both the autocomplete entry and (when not disabled) Claude's automatic invocation.

## 5. Argument handling

Substitutions available in command/skill bodies:

| Token | Expands to |
|---|---|
| `$ARGUMENTS` | Full argument string as typed. If the body omits this token, Claude Code appends `ARGUMENTS: <value>` automatically so the model still sees the input. |
| `$ARGUMENTS[N]` | Argument at 0-based index `N`. |
| `$N` | Shorthand for `$ARGUMENTS[N]`. `$0` is the first argument, `$1` the second. |
| `${CLAUDE_SESSION_ID}` | Current session ID. |
| `${CLAUDE_SKILL_DIR}` | Directory containing this `SKILL.md` (skill-only; reference scripts bundled with the skill). |

Indexed arguments use **shell-style quoting**. Multi-word values must be wrapped in quotes to count as one argument:

- `/migrate-component "Search Bar" React Vue` → `$0` = `Search Bar`, `$1` = `React`, `$2` = `Vue`
- `/migrate-component Search Bar React Vue` → `$0` = `Search`, `$1` = `Bar`, `$2` = `React`, `$3` = `Vue`

`$ARGUMENTS` always expands to the full unsplit string regardless of quoting.

## 6. Invocation control

Three modes, set via two frontmatter fields. Full table in [skill-authoring.md §2](skill-authoring.md):

| Frontmatter | User can invoke | Claude can invoke |
|---|---|---|
| (default) | yes | yes |
| `disable-model-invocation: true` | yes | no |
| `user-invocable: false` | no | yes |

Pick `disable-model-invocation: true` for commands with side effects (deploy, commit, send-message) where you control timing. Pick `user-invocable: false` for background knowledge that isn't meaningful as a typed command.

Note: `user-invocable: false` only hides the entry from the `/` menu; it does not block the Skill tool. To block programmatic invocation entirely, use `disable-model-invocation: true` or a `Skill(name)` deny rule (see [permissions.md](permissions.md)).

## 7. Built-in commands vs bundled skills

Built-in commands (CLI-coded) are **not** invocable by Claude through the Skill tool, with a small whitelist:

- Available through Skill tool: `/init`, `/review`, `/security-review`
- **Not** available through Skill tool: `/compact`, `/clear`, `/permissions`, `/plugin`, `/reload-plugins`, and other CLI-built-ins

Bundled skills (prompt-based, marked **[Skill]** in the [commands reference](https://code.claude.com/docs/en/commands)) — `/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api`, `/less-permission-prompts`, etc. — work like any user-authored skill: Claude can invoke them, and they obey skill permission rules.

Implication for authors: do not write a custom command that wraps `/compact` or `/clear` expecting Claude to call it programmatically. Wrap built-ins only when a human will type the wrapper.

## 8. Plugin commands

Plugin commands live at `<plugin_root>/commands/<name>.md` (or `<plugin_root>/skills/<name>/SKILL.md`). They are **namespaced** so they cannot collide with user/project entries:

```
/plugin-name:command-name
/plugin-name:skill-name
```

The plugin name comes from the plugin's `plugin.json`. Inside command bodies, `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin's install path — use it when invoking bundled scripts so paths work regardless of the user's cwd.

## 9. Anti-patterns

- **Name collision with a skill.** A command and a skill with the same name both exist? The skill wins silently. Either rename or convert the command into a skill directory.
- **Weak description.** Auto-invocation is matched against the description; vague text like "helper command" never fires. Front-load the trigger ("Use when…") in the first sentence; everything past 1,536 chars (combined with `when_to_use`) is dropped from the skill listing.
- **Instructing the user to type a command inside the command body.** The body runs *after* invocation. Telling the model "If the user wants X, suggest they run `/this-command`" is a no-op — they already did. Write the body as the action, not the offer.
- **Forgetting `disable-model-invocation` on side-effect commands.** Without it, Claude may run `/deploy` or `/send-slack-message` autonomously when context superficially matches the description.
- **Relying on plugin commands without the namespace.** Documenting `/foo` instead of `/my-plugin:foo` will mislead users; the plugin form always carries the prefix.
- **Putting a command in `.claude/commands/` and expecting `${CLAUDE_SKILL_DIR}` to work.** That variable is skill-only. Commands without a directory have no bundled-files location.

Sources: https://code.claude.com/docs/en/commands ; https://code.claude.com/docs/en/skills (fetched 2026-04-18).
