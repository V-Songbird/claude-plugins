---
default-category: mandate
---

# kairoi — writing stance

When kairoi is active in this project, Claude is the sole developer. The
rules below flip Claude's default writing stance away from
human-readability conventions and toward Claude's own future re-reading.

- When writing or editing code in this project, optimize the result for your own future re-reading, not for human readability. kairoi makes Claude the sole developer here — human-legibility conventions lose when they conflict with Claude-legibility. Concretely: prefer `getUserByEmailAddress(email)` over `getUser(email)`; prefer `if (state === 'loading') return ...` over `return state === 'loading' ? ... : ...`; prefer a typed argument over `any`. If a choice is neutral, prefer the explicit form.
- When naming a function, variable, or file, prefer the long unambiguous form over the short idiomatic one. Future-Claude searches by substring, not by recall — `refreshAuthToken` is findable; `refresh` or `rt` is not. Local variables inside a short function are the only exception.
- When reusing a term across files, spell it identically every time. Do not introduce synonyms (`user` vs `account` vs `principal`) for the same concept — future-Claude's grep needs one canonical string per concept.
- When writing a function, expose any external state it depends on as a typed argument so the function reads correctly without opening other files. Good: `function saveOrder(order: Order, cartIsPending: boolean)` makes the caller's contract explicit. Bad: `function saveOrder(o)` silently assumes `cart.pending` was checked.
- When adding a comment, write it only when the why is non-obvious (a constraint, an invariant, or a bug workaround). Good: `// Auth0 rate-limits to 10/sec; throttle before hitting the endpoint` above a throttled call. Bad: `// increment counter` above `counter++` (restates what the code already says).
- When a compact idiom and an explicit form diverge, choose the explicit one. Bad: `const result = x ? a : y ? b : z ? c : d`. Good: `if (x) return a; if (y) return b; if (z) return c; return d;`. Character count is not a cost future-Claude pays; attention state is.
