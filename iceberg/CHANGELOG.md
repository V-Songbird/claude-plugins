# Changelog

All notable changes to iceberg are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html); alpha releases may introduce breaking changes in minor versions.

## [Unreleased]

## [1.0.0-alpha] — 2026-04-29

### Added

- `/iceberg:convention` skill with three modes:
  - **Author mode**: applies the iceberg asymmetric-complexity convention while writing code; keeps public interfaces stable, pushes complexity inward
  - **Audit mode**: reviews an existing codebase for structural debt that violates the convention; produces a prioritized finding list with concrete remediation steps
  - **Bootstrap mode**: scaffolds enforcement infrastructure in a fresh project (linter config, CI gates, ADR template)
- `/iceberg:patterns` skill: identifies recurring structural patterns in a codebase and evaluates them against the iceberg convention
- Language-agnostic: rules describe patterns; Claude translates each to the idiomatic enforcer for the detected ecosystem
- Template assets: ADR adoption record (`ADR-0001-adopt-iceberg-convention.md`), CLAUDE.md fragment for rule injection, PR template, generic ADR template
- 6 reference files covering convention rules, anti-patterns, enforcement patterns, and per-mode procedures
