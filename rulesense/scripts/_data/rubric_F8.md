Level 3 (0.85–1.00): Not mechanically enforceable — the rule requires judgment, context, or understanding that no deterministic tool can provide. The instruction layer is the correct enforcement mechanism.

> "Use CachedValuesManager for expensive computations over PSI trees."
> "Expensive" is subjective — no linter can determine which computations are expensive. Only an LLM can apply this judgment. Score: 0.90.

> "When adding new grammar rules, add corresponding PSI visitor methods and test coverage."
> The correspondence between grammar rules and visitor methods requires domain understanding. Score: 0.90.

> "The site must feel alive, playful, and aquatic — but remain scannable, fast, and recruiter-friendly."
> "Alive" and "playful" are aesthetic judgments no tool can verify. Correctly placed in the instruction layer. Score: 0.95.

> "Read `DESIGN_SYSTEM.md` for all visual patterns, `ADDENDUM.md` for content schemas"
> Cannot mechanically verify the model read the files. The instruction is doing
> real work — there's no hook that forces file reading before task start. This
> sits at the low end of Level 3: the rule is judgment-only, but unlike pure
> aesthetic charters, the action is a concrete checkable behavior. Score: 0.90.

Level 2 (0.55–0.80): Partially enforceable — a linter or tool could catch some violations but not all. The rule has a component that requires judgment and a component that's deterministic.

> "Use functional components for all new React files."
> eslint-plugin-react can flag class components, but can't distinguish "new" from "existing" files, and edge cases (HOCs, error boundaries) require judgment. Score: 0.70.

> "Each test file must import from the module it tests, not from barrel exports."
> An ESLint rule could flag barrel imports in test files, but determining "the module it tests" requires understanding the test's intent. Score: 0.65.

Level 1 (0.30–0.50): Mostly enforceable — a hook or linter could enforce the rule's core requirement. The instruction exists as a stopgap until the mechanical enforcement is configured.

> "NEVER edit files in src/main/gen/ directly."
> A PreToolUse hook on Edit/Write matching `src/main/gen/**` could block this entirely. The instruction is a weak substitute for the hook. Score: 0.35.

> "Every commit modifying src/ MUST end with [State: SYNCED]"
> A pre-commit hook could grep the commit message for the required suffix. Score: 0.35.

Level 0 (0.10–0.25): Fully enforceable — a shell command, linter, or hook can fully verify compliance. The rule has no component that requires judgment.

> "Run prettier on modified files before committing"
> A pre-commit hook running `prettier --check` does this with exit-code enforcement. Score: 0.15.

> "Ensure no TypeScript errors exist before pushing"
> A pre-push hook running `tsc --noEmit` does this. Score: 0.15.

Score higher within a level when:
- The mechanical tool doesn't exist or isn't configured for this project
- The rule has nuances the mechanical tool can't capture (e.g., "for all new files" — the "new" qualifier)

Score lower when:
- The mechanical tool exists and is commonly available
- The rule's phrasing maps 1:1 to a tool's capability
