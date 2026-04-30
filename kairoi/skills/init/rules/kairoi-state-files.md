---
globs: ".kairoi/**"
default-category: mandate
---

# kairoi state files

- `.kairoi/buffer.jsonl` and `.kairoi/receipts.jsonl` are append-only hook-owned logs. Never rewrite, reorder, or truncate them — the reflection pipeline treats them as immutable history and truncation loses the `guards_fired` / `guards_disputed` signal that reflection depends on.
- To correct kairoi's understanding of a module — wrong purpose, wrong dependencies, pin a guard, mark a guard `protected` — write to `.kairoi/overrides.json`. Use existing entries as the schema reference; the module files themselves are not the correction surface.
- Files matching `.kairoi/.*` are transient hook scratch space — don't create, edit, or commit them.
