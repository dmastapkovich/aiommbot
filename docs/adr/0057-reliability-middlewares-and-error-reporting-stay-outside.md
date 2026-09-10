---
status: accepted
date: 2026-09-09
ticket: "#30"
---

# Retrying a delivery, dead-lettering, circuit breaking and error reporting stay outside the framework, and the breaker recipe names no library

[ADR-0021](0021-core-error-boundary.md) already put retries, dead-lettering and cooldowns outside
the Core and [ADR-0002](0002-core-scope-two-condition-test.md) already refused them; what was left
open was whether any of them becomes a first-party Plugin or an extra. **None does**, and for each
the reason is specific rather than a rule:

- **A delivery cannot be retried, because there is no redelivery.** A WebSocket event is never
  acknowledged and is gone once dequeued ([ADR-0023](0023-websocket-gateway-resilience.md)); a
  callback arrives once, with a reply deadline of ten seconds and no second attempt from the server
  ([ADR-0024](0024-webhook-ingress-and-callback-security.md)). Retrying the *work* a Handler does is
  the application's business, three lines of `stamina` inside the Handler or a Middleware of its
  own. FastStream removed its `retry=True` shortcut as a design mistake for the same reason
  ([`docs/research/08`](../research/08-peer-responsibility-boundaries.md) §2.6).
- **There is nowhere to dead-letter to.** The framework owns no durable queue; a dropped event is
  already the `Dropped` Signal and a failed dispatch is already `Failed(error)`, and both reach
  Middleware. A destination for the message is a broker the application chose, and the pattern is
  its own.
- **A breaker belongs on the outbound call, and we name no library for it.** The place is the
  `HTTPTransport` decorator that
  [ADR-0026](0026-standalone-typed-api-client-over-an-http-transport-protocol.md) already defines as
  the third level of adoption. There is nothing to recommend: as of September 2026 `pybreaker` has
  shared state and no `asyncio` at all, `aiobreaker` has had no commit since 2021, and `purgatory` —
  the only asyncio-native breaker with a shared backend — has not been committed to in about
  twenty-two months
  ([`docs/research/26`](../research/26-schedule-reliability-and-probe-primitives.md) §6). The how-to
  therefore shows the decorator and the three states, and leaves the choice open.
- **Error reporting is not a Plugin of ours.** `Failed(error)` carries the exception to Middleware,
  which is where an application attaches a tracker, and `sentry-sdk` ships integration modules for
  dozens of frameworks and not one for a chat platform, with no discovery mechanism that would
  auto-enable ours if we wrote it
  ([`docs/research/31`](../research/31-error-tracker-integration-anatomy.md)). What the application
  has to write is **decided by #104**: the tracker turns the ErrorBoundary's single ERROR record
  into an event through a default integration ([ADR-0021](0021-core-error-boundary.md),
  [ADR-0052](0052-log-levels-by-frequency-and-audience.md)),
  so a `capture_exception` Middleware produces a second event rather than the first, and the
  isolation-scope fork per Event is the part no call site supplies.

Outbound rate limiting is not reopened: the client already honours `Retry-After` and
`X-RateLimit-Reset` (ADR-0026), and a client-side token bucket was rejected there.

Each of the four is a how-to page of the user documentation in the form
[ADR-0056](0056-the-framework-owns-no-scheduler.md) fixes, and this decision owes #26 four:
*Retry an outbound call*, *React to a failed dispatch*, *Break a circuit on the transport* and
*Report exceptions to an error tracker*. A page names a library only where one is safe to name —
`stamina` for retries, as ADR-0026 already does, and `PyrateLimiter` where a limit must hold across
replicas.

## Considered options

- *A thin first-party `sentry` extra* — rejected: an extra would freeze one vendor's name into the
  distribution for everybody, and the SDK has no way to auto-enable an integration it does not
  itself ship, so ours would be opt-in in the application's `init()` either way. What such an
  integration would add over a call site is #104's.
- *Naming `purgatory` in the breaker how-to, as
  [`docs/research/08`](../research/08-peer-responsibility-boundaries.md) §5 suggested* — rejected on
  the maintenance evidence gathered since.
- *Naming no library anywhere* — rejected: ADR-0026 already names `stamina`, and withdrawing that
  would leave the reader with a seam and no starting point.
