---
default-category: mandate
---

# kairoi

- This project uses the kairoi plugin to maintain a self-model of its modules, dependencies, and invariants. Durable state lives under `.kairoi/`.
- When inspecting `.kairoi/` state, treat `.kairoi/model/*.json` as per-module self-models written by the kairoi agents, `.kairoi/overrides.json` as the user-correction surface, `.kairoi/build-adapter.json` as stack detection output, and any `.kairoi/.*` dotfile as transient hook scratch space.
- When first engaging with a module (reading or editing files you haven't touched this session), resolve its module via `.kairoi/model/_index.json` (`modules.<id>.source_paths`), then read `.kairoi/model/<module>.json` for purpose, dependencies, and accumulated invariants — these aren't visible in the code itself.
- For a read-only view of a module's model, run `/kairoi:show <module>` — don't `cat` model files.
- For trust/accuracy rebuild on one module, run `/kairoi:audit <module>` — don't manually rewrite guards.
- For a structural health report, run `/kairoi:doctor` — don't diagnose `.kairoi/` files by hand.
- When relying on a `purpose` or `dependencies` value from `.kairoi/model/<module>.json`, trust it only if `purpose` is non-null and `tasks_since_validation < 5`. Past that threshold or when `purpose` is null, re-read the source files listed under `modules.<id>.source_paths` to verify before acting on the recorded value.
- When `/kairoi:show <module>` output disagrees with what the source files actually contain, run `/kairoi:audit <module>` to rebuild the model from source. If the audit confirms the divergence is intentional, persist the correction in `.kairoi/overrides.json` per the kairoi-state-files rules.
- `kairoi-complete` runs via hook signal. When a kairoi hook emits a "Dispatch the kairoi-complete agent" system reminder in your context (after a commit that crossed the buffer threshold, or at SessionStart with stale state), follow it via the Agent tool — that IS the automated sync path. Hooks cannot dispatch subagents directly; they can only inject context that you then act on. Don't dispatch `kairoi-complete` on your own initiative (e.g., because the user casually said "sync" without a hook signal).
