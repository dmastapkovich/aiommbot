---
status: accepted
date: 2026-09-03
ticket: "#17"
amended-by: [ADR-0048]
---

# The Core owns a narrow, non-removable error boundary: log without payload, report, return a typed `Failed`; a failing process is an explicit policy

Should the Core intercept unexpected exceptions at all, or is the process meant to fail? The
question was researched against twelve frameworks and task systems
([`docs/research/12`](../research/12-error-boundary-conventions.md)): none lets a handler exception
kill the process, almost all log without payload, and "let it crash" works only under a supervisor
that restarts the crashed unit — an asyncio task that dies without a handler is silently lost.

We decided:

- **An outermost `ErrorBoundary` is part of the Core and cannot be removed.** It catches
  `Exception` only; `BaseException` (cancellation, `SystemExit`, `KeyboardInterrupt`) passes
  through untouched.
- **Its default does exactly two things**: writes one ERROR record **without payload** (event kind,
  handler, correlation id, exception class and — uniquely in the framework — the traceback, because
  a traceback ends in `str(exc)` and this is the one place that risk is worth taking,
  [ADR-0052](0052-log-levels-by-frequency-and-audience.md)); and returns the typed outcome
  **`Failed(error)`** to the Transport, which decides
  the transport-level reaction (ack, nack, HTTP status, reply-channel default) the way FastStream's
  `AckPolicy` does ([`docs/research/12`](../research/12-error-boundary-conventions.md)). It never
  swallows silently and never composes a user-facing message. `Failed(error)` carries the exception,
  so returning it is also how the failure reaches Middleware and whatever the application
  registered there ([ADR-0048](0048-observability-is-not-a-core-seam.md)) — there is no second
  channel for the same fact.
- **A failing process is an explicit choice**, never the default: a boundary policy
  (`on_failure=FailProcess`) or a typed `FatalError` that the boundary lets through, carrying a
  typed reason — `AuthRevoked`, raised by the `AuthLossDetector` of
  [ADR-0023](0023-websocket-gateway-resilience.md), is the one the taxonomy of
  [ADR-0027](0027-api-error-taxonomy.md) defines. Without a supervisor, a crash is a loss of events,
  not honesty.
- **Everything else stays outside the Core**: user-facing "something went wrong" replies, retries,
  dead-lettering and cooldowns are Handler-layer middleware from plugins or the application, and
  expected domain outcomes remain values
  ([ADR-0014](0014-filters-and-extractors-with-closed-handler-signatures.md)).

## Considered options

- *Log and always re-raise into the transport (Starlette model)* — rejected: every transport
  would re-implement the rules and the typed `Outcome` would lose its `Failed` branch.
- *No boundary in the Core* — rejected: no surveyed framework does this; the exception would take
  the transport loop down and lose queued events.
- *A default user-facing reply from the Core* — rejected: the Core knows neither the platform nor
  the user's language.
