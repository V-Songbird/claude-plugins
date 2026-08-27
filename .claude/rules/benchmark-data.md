# Benchmark run data never publishes

A PreToolUse guard (`.claude/hooks/assay-benchmark-records-guard.js`, wired
machine-locally) denies `git add`/`git commit` of `records/`,
`records-archive/` and `results/` paths, and every harness's `.gitignore`
plus the reference-name commit gate back it up.

- When writing a measured number into a README, take it from the local
  records under `benchmarks/<plugin>/` and commit only the prose or chart,
  never the record behind it; the shipped harness is how readers regenerate
  the number, and the hush readiness gate reads records from disk, not git.
- Decided 2026-08-11 (ADR 0004, local docs/adr): supersedes the older
  committed-records evidence policy across hush, foreman, and razor.
