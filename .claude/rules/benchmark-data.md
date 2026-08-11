# Benchmark run data never publishes

The public repos — this marketplace and every plugin submodule — carry
benchmark **setup only**: tasks, fixtures, runners, validators, settings, and
the tests that prove them. Run **data** of any kind stays on the operator's
machine: results, transcripts, per-run JSON, retained records, generated claim
sets, trial logs of measurements, and report output.

- When adding or generating any benchmark output file, keep it out of git:
  every harness's `.gitignore` already covers `results/`, `records/`, and
  `records-archive/` — extend the ignore rather than committing an exception.
- Never `git add` an archive or records directory wholesale; the
  reference-name commit gate exempts only `benchmarks/<plugin>/records/`
  paths, so archived copies will hard-block the commit anyway.
- A README may state measured numbers; its backing records stay local, and
  the harness in the repo is the published way to regenerate them. The hush
  readiness gate reads records from disk, not from git.
- Decided 2026-08-11 (ADR 0004, local docs/adr): supersedes the older
  committed-records evidence policy across hush, foreman, and razor.
