---
globs: "src/api/**/*.ts"
default-category: mandate
---

# API Rules

- Validate all request bodies at the handler boundary.
- Return consistent error shapes: `{ error: string, code: number }`.
  This ensures clients can parse errors uniformly.
- Use middleware for cross-cutting concerns (auth, logging) — not inline checks.

## Database Access

<!-- category: preference -->
- Prefer transactions for queries spanning multiple tables.
- Consider using read replicas for heavy read operations where latency is acceptable.

The API layer uses Express with TypeScript strict mode enabled.
