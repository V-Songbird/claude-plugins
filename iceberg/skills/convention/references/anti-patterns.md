# Anti-Patterns — The Curse-of-Knowledge Detector

Senior engineers violate the Iceberg Convention most often by producing code that looks correct to them (the author) and is lethal to a junior (the reader). This file catalogues the shapes those violations take. Use it during audit mode and during authoring mode when refactoring or reviewing your own draft.

**Code examples are pseudocode.** The shapes are language-independent. Translate to the target language's syntax when diagnosing or fixing.

Each anti-pattern has: why seniors reach for it, what the junior experiences, which rule it violates, and the recommended remediation.

---

## Signature shapes

### AP-1 — The Boolean Flag Parameter

```
function fetchUsers(includeInactive: Bool, retry: Bool) -> List<User>

# Junior call site:
fetchUsers(true, false)
```

- **Why seniors write it:** "Two modes of one function, DRY."
- **What the junior sees:** an opaque positional boolean. Must jump to the declaration to understand what `true` means. Six months later nobody remembers.
- **Violates:** §2.3 (cognitive hazards); spiritually §1.4 (must leave the file to decode).
- **Fix:** split into two named functions (`fetchAllUsers`, `fetchActiveUsers`) or use a named-argument / keyword-argument style: `fetch(includeInactive = true, retry = false)` where the language supports it.

### AP-2 — The Raw Scalar Domain API

```
function transfer(from: String, to: String, amount: Number) -> Void
```

- **Why seniors write it:** "Primitive types are simpler."
- **What the junior sees:** a signature accepting any three of the infinite string×string×number combinations, 99.9% of which are bugs.
- **Violates:** §3.1.
- **Fix:** branded types. `function transfer(from: AccountId, to: AccountId, amount: Money)`.

### AP-3 — The Optional-Field State Bag

```
record FetchState<T> {
    data?:       T
    error?:      Error
    loading?:    Bool
    hasRetried?: Bool
}
```

- **Why seniors write it:** "Flexible, extensible."
- **What the junior sees:** 16 representable combinations, maybe 4 legal. Must test `if (state.data && !state.error && !state.loading)` at every consumption point. Tests grow quadratically.
- **Violates:** §3.2, §4.1.
- **Fix:** discriminated union / sum type.

```
type FetchState<T> =
    | Idle
    | Loading
    | Success(data: T)
    | Failure(error: Error)
```

### AP-4 — The Async-Everywhere Tip

```
# In features/checkout/submit.*
export async function submitOrder(req: OrderRequest) -> Promise<OrderConfirmation>:
    result = await orderService.submit(req)
    return result
```

- **Why seniors write it:** "It's the language idiom."
- **What the junior sees:** must mentally model the event loop at every call site. Error boundaries unclear. Cancellation unaddressed.
- **Violates:** §1.1.
- **Fix:** expose the async via the framework's suspense/effect primitive so the call site reads synchronously. Shape varies by framework (server-rendered components, data-loading hooks, sagas, structured-concurrency blocks, channels-with-receive); the principle does not.

---

## Structure shapes

### AP-5 — The Single-Implementation Interface

```
# domain/ports/UserRepository.*
interface UserRepository:
    findById(id: UserId) -> Option<User>
    save(user: User) -> Void

# infra/persistence/PostgresUserRepository.*
class PostgresUserRepository implements UserRepository { ... }
```

- **Why seniors write it:** "Hexagonal architecture! Swappable!"
- **What the junior sees:** a type with one implementation. To follow code, must jump interface → impl → impl's dependencies. Three files to read one call.
- **Violates:** §1.4.
- **Fix:** if there is literally one implementation and no evidence of a second coming, skip the interface. Expose the class/module directly. Introduce the interface when the second implementation arrives. YAGNI applied to abstraction; consistent with Axiom A5.

### AP-6 — The Fluent Builder of Death

```
QueryBuilder<User>()
    .select('id', 'name')
    .where('active', equals, true)
    .join('orders').on('user_id')
    .groupBy('region')
    .having(...)
    .orderBy(...)
    .execute()
```

- **Why seniors write it:** "Discoverable via autocomplete!"
- **What the junior sees:** 47 methods that may or may not be valid in the current chain state. Runtime errors from invalid combinations. No compile-time guidance about order.
- **Violates:** §3.2 (the chain state is itself a state machine — make it one).
- **Fix:** either typed phantom-state builders (type-level state machine — advanced) or a plain function with a config record. The config record is almost always the right answer above the airgap. Below the airgap, either is fine.

### AP-7 — The Decorator/Middleware Chain

```
@Authenticated
@RateLimit(100)
@Cached('5m')
@Traced
@Transactional
function createOrder(req: OrderRequest) { ... }
```

- **Why seniors write it:** "Separation of concerns via aspects."
- **What the junior sees:** five things happen before `createOrder` runs. Order matters. Rationale is invisible. Debugging a failure means stepping through five wrappers.
- **Violates:** §1.4; often §5.2 (rationale for the stack is nowhere).
- **Fix:** if the stack is stable and short (≤2), decorators/middleware are fine. If long or varied, make composition explicit: `createOrder = compose(authenticated, rateLimit(100), cached('5m'), traced, transactional)(createOrderCore)`. The call is visible and the order is greppable.

### AP-8 — The Config Switchboard

```
# features.yml
checkout:
  strategy: 'optimistic'
  retry:
    enabled: true
    max: 3
    backoff: 'exponential'
  fallback: 'legacy_flow_v2'

# The code
if config.checkout.strategy == 'optimistic':
    if config.checkout.retry.enabled:
        ...
```

- **Why seniors write it:** "Now non-engineers can tweak it!"
- **What the junior sees:** behavior is not in the code. Must cross-reference config to understand control flow. Type system no longer constrains behavior. Tests must run against every config combination to be meaningful.
- **Violates:** §1.4, §3.2.
- **Fix:** if the switch is truly needed (feature flags, A/B tests), type the config so invalid combinations don't compile, and centralize the switch at one boundary. If the switch isn't needed, delete it — config-driven design hides code-smell behind a configuration-format fig leaf.

---

## Control-flow shapes

### AP-9 — The Accumulator Soup

```
summary = orders.reduce((acc, order) -> {
    total:    acc.total + order.amount,
    byRegion: merge(acc.byRegion, { [order.region]: (acc.byRegion[order.region] ?? 0) + order.amount }),
    largest:  order.amount > (acc.largest?.amount ?? 0) ? order : acc.largest,
}, { total: 0, byRegion: {}, largest: undefined })
```

- **Why seniors write it:** "Functional, immutable, one-pass."
- **What the junior sees:** must mentally simulate accumulator state across all iterations. The accumulator type is inferred and obscure.
- **Violates:** §2.3.
- **Fix:** explicit loop with named variables, or multiple passes with named intermediate collections. Sometimes two loops are more readable than one fused accumulator. Language idioms for "iterate with a named accumulator" vary; the principle is: make the accumulator visible.

### AP-10 — The Silent Catch

```
try:
    await riskyOperation()
catch e:
    log.error(e)
```

- **Why seniors write it:** "Robustness. Don't crash the app."
- **What the junior sees:** the error is logged and forgotten. Upstream thinks the operation succeeded. Bugs become ghost stories.
- **Violates:** §2.3 (silent catch is a top-5 cognitive hazard).
- **Fix:** every catch must rethrow, translate to a domain error, or transition an FSM. If "just log it" is really the answer, at minimum wrap in a tracing span with a failure attribute so observability catches it. Logging is not handling.

### AP-11 — The Nested Conditional Expression

```
label = user
    ? (user.isAdmin
        ? 'Admin'
        : (user.isActive ? 'Active' : 'Inactive'))
    : 'Anonymous'
```

- **Why seniors write it:** "Expression-form is elegant."
- **What the junior sees:** must parse nesting and trace branches. A single misplaced delimiter changes meaning silently.
- **Violates:** §2.3.
- **Fix:** early returns, a lookup table, or a discriminated union on the user state.

### AP-12 — The Implicit Time / Locale / Currency

```
label = formatDateTime(date)          # no locale, no timezone
price = formatNumber(amount, 2)       # no currency, no precision spec
now   = currentTime()                 # no clock injection; not testable
```

- **Why seniors write it:** "Standard APIs, they just work."
- **What the junior sees:** they work until they don't — server/client hydration mismatches, currency truncation bugs, cross-timezone chaos that is undiagnosable without weeks of investigation.
- **Violates:** §2.3.
- **Fix:** require explicit timezone, locale, precision, and currency on every such call. Enforce via AST-level linter that flags missing parameters. Inject `Clock` abstractions so "now" is testable.

---

## Rationale shapes

### AP-13 — The Narrator Comment

```
# Increment the counter
counter = counter + 1
# Loop through users
for user in users:
    # Check if active
    if user.active:
        ...
```

- **Why seniors write it:** "Documentation."
- **What the junior sees:** noise. Trains them to skip comments, which kills the signal when a real comment exists.
- **Violates:** §5.3.
- **Fix:** delete narrator comments. Write comments only where the code cannot say *why*: `# Stripe returns 402 on insufficient funds, not a 4xx-client error; see BUG-4412`.

### AP-14 — The Missing ADR

A senior introduces a new adapter pattern, a new caching layer, or a new framework integration — with no written rationale. Six months later, the team is divided on whether the pattern is canonical.

- **Why seniors write it:** "It's self-explanatory."
- **What the junior sees:** uncertainty about whether to follow the pattern or not. Divergence. Eventually, rewrite pressure.
- **Violates:** §5.2.
- **Fix:** every non-obvious architectural decision gets an ADR. Template: context, decision, consequences, alternatives rejected. 200 words minimum, 2 pages maximum.

### AP-15 — The "We Decided This in Slack" Rule

A team convention exists in chat history, tribal memory, or a senior's head — but nowhere in the code or docs.

- **Why seniors rely on it:** "It's obvious, we all know it."
- **What the junior sees:** nothing. They violate the rule, get a PR comment, internalize it as "random senior opinion."
- **Violates:** §2.1 (meta-rule).
- **Fix:** if you notice yourself typing the rule in a PR comment, stop. Open a PR that encodes the rule as a lint or an ADR and reference that from the original comment.

---

## Detection heuristics (for audit mode)

The anti-patterns above are shape-based; detecting them is a pattern-match on syntax. Adapt these searches to the target language's syntax but the concepts are universal.

| Anti-pattern | What to search for |
|---|---|
| AP-1 (boolean params) | function signatures with boolean parameters in domain/tip files |
| AP-2 (raw scalars) | function signatures with primitive-type parameters in domain files |
| AP-3 (optional state bag) | records/interfaces/structs with ≥2 optional fields in domain/state files |
| AP-4 (async tip) | async-primitive return types in tip-layer function signatures |
| AP-5 (single-impl interface) | interface/protocol/trait declarations with exactly one implementation in the repo |
| AP-6 (fluent builder) | class/type names ending in `Builder` with >5 chainable methods |
| AP-7 (decorator chain) | functions with ≥3 decorators/middlewares in tip-layer files |
| AP-8 (config switchboard) | deep property-access chains on config objects gating control flow in tip-layer files |
| AP-9 (accumulator soup) | accumulator-based reductions with object/record accumulators in tip files |
| AP-10 (silent catch) | exception/error catch blocks that only log, do not rethrow, translate, or transition |
| AP-11 (nested conditional) | nested conditional expressions with >1 level of nesting |
| AP-12 (implicit locale) | date/number formatting calls without explicit locale/timezone/precision/currency arguments |
| AP-13 (narrator comment) | comments whose content token-overlaps heavily with the following code line |
| AP-14 (missing ADR) | infrastructure-path commits that are not accompanied by ADR directory changes |

Use these as starting points. False positives require interpretation — AP-4 is not a violation in a framework where the async return type is the framework-provided suspense seam.
