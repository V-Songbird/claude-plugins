<!--
  Pull Request Template — Iceberg Convention
  Copy to .github/PULL_REQUEST_TEMPLATE.md (GitHub), or
         .gitlab/merge_request_templates/Default.md (GitLab).

  The 8-question design-review checklist is for non-trivial changes (new
  features, new modules, new architectural seams). For small changes (bug
  fixes, typos, single-function modifications), strike it through or delete it.

  The "Layer affected" and "Rules invoked" sections are required for every PR.
-->

## Summary

<!-- 2-3 sentences. What does this PR do, at what layer, for what reason. -->

## Layer affected

<!-- Check one or both -->

- [ ] Tip (above the airgap) — business logic, domain, UI, feature handlers
- [ ] Berg (below the airgap) — infrastructure, adapters, platform, transport

## Rules invoked

<!--
  List the Iceberg Convention rules applied in this PR, by number.
  Examples:
    - §1.2 — no infra imports in src/features/
    - §3.1 — new branded type `InvoiceId` with validation constructor
    - §4.1 — replaced `isLoading + isError` booleans with FetchState union
-->

- §X.Y — ...
- §X.Y — ...

## ADR references

<!--
  Required if this PR touches src/infra/**, src/platform/**, or introduces a
  new architectural seam. List ADR numbers with a one-line description.
  If none, state "N/A — tip-layer change only" or "N/A — covered by ADR-NNNN."
-->

- ADR-NNNN — ...

## Enforcement gaps

<!--
  Optional. List any invariants introduced by this PR that are not yet
  mechanically enforced. Flag as review-only with a follow-up ticket.
  If none, delete this section.
-->

- §X.Y — ENFORCEMENT GAP: no automated check yet. Tracking: #NNNN

---

## Design-review checklist (non-trivial changes only)

<!--
  Required for: new features, new modules, new architectural seams, changes
  to public APIs in src/features/ or src/app/, any change touching more than
  one layer.

  Delete this entire section for small changes (bug fix, typo, single-function
  refactor).
-->

Answer each question. If any answer is "no," either fix before requesting review or explain why it's acceptable here.

1. **Can a junior ship a typical feature using this API by reading exactly one file?**
   - [ ] Yes
   - [ ] No — explanation:

2. **Can the junior write a structurally invalid call that compiles?** (If yes, the type system is insufficient.)
   - [ ] No
   - [ ] Yes — explanation:

3. **Can the junior catch-swallow an error and have it silently pass CI?**
   - [ ] No
   - [ ] Yes — explanation:

4. **Can the junior construct a domain value without the validation constructor?** (If yes, `as` casts are leaking.)
   - [ ] No
   - [ ] Yes — explanation:

5. **If I add a new state to this flow next quarter, which call sites compile-fail?**
   - Answer (list file paths or "all via exhaustiveness check"):

6. **Is there an ADR for every non-obvious choice embedded in this design?**
   - [ ] Yes — ADRs: ADR-NNNN, ADR-NNNN
   - [ ] No — explanation:

7. **Is every architectural assertion in this design backed by a lint rule, arch test, or type constraint — not a style-guide bullet?**
   - [ ] Yes
   - [ ] No — follow-up tracking:

8. **If this feature is built 20% wrong by an AI agent, which guardrail catches it?**
   - Answer (name the specific rule, lint, or type check):

---

## Testing

<!-- What tests were added/modified? What states/paths are covered? -->

## Screenshots / traces (if applicable)

<!--
  For UI changes: before/after screenshots.
  For backend changes: OpenTelemetry trace screenshot or link, showing the
  request flow through the airgap.
-->
