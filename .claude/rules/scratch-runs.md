# Benchmarks and headless runs live under X:/tmp

Anything disposable — benchmark arms, throwaway fixtures, headless `claude -p`
probe workspaces, scratch git repos — is created under the benchmark root,
never inside this repository and never in `/tmp` or `os.tmpdir()`:

```
X:/tmp/claude/<project-slug>/<session-id>/scratchpad/
```

`X:/tmp` is for benchmarking and probe work only, which is what makes it safe
to delete wholesale. A session that does ordinary work keeps the scratchpad
path from its own system prompt and never writes here. A session that runs
benchmarks is launched with `TEMP`/`TMP` set to `X:\tmp`, so the path above is
the scratchpad path in its system prompt — use it verbatim.

- One subdirectory per run or per arm, named for what it is (`variants/vctl`,
  `p3-probe`), so a run's inputs, transcripts and results stay together.
- Nothing is copied back into the repo except the prose or number a doc cites.
  Raw records, transcripts and run logs stay under `X:/tmp` and are never
  committed.
- A headless run isolates itself: `--setting-sources project` and
  `--strict-mcp-config`, so this machine's user-scope plugins cannot leak into
  an arm and void the control.
