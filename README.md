# claude-plugins

A collection of Claude Code plugins by Songbird. Each plugin is an independently installable unit that extends Claude Code with new skills, hooks, and workflows.

> All plugins are currently in **1.0.0-alpha**. Interfaces may change between minor releases.

## Plugins

| Plugin                                 | Description                                                                                                                                                                         |
|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [forge](./forge)                       | Pre-code feature review pipeline. Stress-tests a design through parallel domain experts, an adversarial critic, and a user approval gate before any code is written.                |
| [iceberg](./iceberg)                   | Encode architectural rules as compiler/lint errors. Audits structural debt, applies the asymmetric-complexity convention, or bootstraps enforcement scaffolding in a fresh project. |
| [jetbrains-router](./jetbrains-router) | Routes Claude Code tools through a JetBrains IDE MCP server (WebStorm, Rider, IntelliJ IDEA) for live diagnostics and unsaved-buffer reads. Fails open when no IDE is connected.    |
| [kairoi](./kairoi)                     | Session safety for unfamiliar codebases. Edit-time guards, automatic commit capture, and cross-module reflection so Claude stays in sync across long sessions.                      |
| [rulesense](./rulesense)               | Audits and authors CLAUDE.md rule files. Scores rules for structural clarity, suggests rewrites, and creates new rules optimized for Claude's parsing.                              |
| [scriptorium](./scriptorium)           | Reference guide and proofreader for Claude Code instruction artifacts (SKILL.md, CLAUDE.md, plans, subagents, slash commands, hook scripts).                                        |

## Installation

Each plugin is installed individually. Clone this repository and register the plugin directory with Claude Code.

See each plugin's README for setup steps and requirements.

## Repository layout

```
claude-plugins/
├── forge/
├── iceberg/
├── jetbrains-router/
├── kairoi/
├── rulesense/
└── scriptorium/
```

## License

MIT — see [LICENSE](./LICENSE).

## Community

- Bug reports and suggestions: [GitHub Issues](https://github.com/V-Songbird/claude-plugins/issues)
- Security reports: [SECURITY.md](./SECURITY.md)
- Contribution guidelines: [CONTRIBUTING.md](./CONTRIBUTING.md)
