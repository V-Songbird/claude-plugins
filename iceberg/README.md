# iceberg

Architectural convention enforcement for Claude Code.

Iceberg encodes senior-authored structural rules as compiler/lint errors — not PR comments. The core convention: public interfaces should be small and stable; complexity lives inside implementations, not on boundaries. Language-agnostic — rules describe patterns; Claude translates each to the idiomatic enforcer for the detected ecosystem (TypeScript, Python, Rust, JVM, .NET, Go).

> **Version:** 1.0.0-alpha — interfaces may change between minor releases.

## Modes

| Mode | What it does |
|------|-------------|
| **Author** | Applies the iceberg convention while writing code. Keeps public interfaces stable, pushes complexity inward. |
| **Audit** | Reviews an existing codebase for structural debt. Returns a prioritized finding list with concrete remediation steps. |
| **Bootstrap** | Scaffolds enforcement infrastructure in a fresh project: linter config, CI gates, ADR template. |

## Skills

| Skill | Description |
|-------|-------------|
| `/iceberg:convention` | Main entry point. Accepts `--mode author`, `--mode audit`, or `--mode bootstrap`. |
| `/iceberg:patterns` | Identifies recurring structural patterns and evaluates them against the convention. |

## Templates

`iceberg/skills/convention/assets/templates/` contains ready-to-use templates:

- `ADR-0001-adopt-iceberg-convention.md` — architectural decision record for adopting iceberg
- `CLAUDE.md-fragment.md` — rule fragment to paste into your project's CLAUDE.md
- `PULL_REQUEST_TEMPLATE.md` — PR template enforcing convention checks
- `adr.md` — generic ADR template

## Installation

Clone this repository and register the `iceberg/` directory as a Claude Code plugin.

## License

MIT — see [LICENSE](./LICENSE).
