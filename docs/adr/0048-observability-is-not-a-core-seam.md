---
status: accepted
date: 2026-09-09
ticket: "#29"
amends: [ADR-0002, ADR-0006, ADR-0013, ADR-0017, ADR-0021, ADR-0022, ADR-0026, ADR-0030, ADR-0033, ADR-0038, ADR-0047]
---

# The Core has no observability Protocol of its own: a dispatch fact travels on the typed `Outcome` through the Middleware layers, and the observability seam is `RequestObserver` with its synchronous pair

The catalogue named an **Observability seam** that no document ever specified, and four ADRs
reported facts into it. The evidence says it should not exist: no surveyed framework introduces an
observation Protocol for its dispatch path — FastStream, Dramatiq, taskiq and Litestar reuse their
middleware chain and Celery its signals
([`docs/research/23`](../research/23-dispatch-observability-in-async-frameworks.md) §3) — and the
mechanism has to *wrap* the work, because a span must be the parent of what the Handler itself
records, which a record pushed after the fact can never be. We decided:

- **No new Protocol.** Dispatch observability is Middleware
  ([ADR-0020](0020-two-layer-middleware-chain.md)), which already receives
  `Handled | Unhandled | Failed` from `call_next` and already names inbound metrics and observing
  the outcome as its work. `Failed(error)` **is** the report: an ErrorBoundary that returns the
  typed outcome has already handed the exception to whatever wraps it, so a second channel for the
  same fact would be two mechanisms for one truth. A new Core Protocol would also fail the
  admission test of [ADR-0002](0002-core-scope-two-condition-test.md) on both conditions — not
  every bot needs it, and the equivalent mechanism is already in the Core.
- **The observability seam is the `RequestObserver` row of
  [§5.4](../design/05-building-block-view.md), and nothing else.** It gains a synchronous pair,
  `SyncRequestObserver`, in the same module, so the standalone synchronous client
  ([ADR-0029](0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md)) is observable at all:
  the colour follows the face, which is what httpx does with `Client` and `AsyncClient` hooks
  ([`docs/research/17`](../research/17-http-client-observability.md) §3). `RequestObserver` stays a
  coroutine Protocol, so [ADR-0030](0030-synchronous-callables-by-explicit-declaration.md) is
  unchanged in substance; the pair is the third row of §5.4 to carry two Protocols, which makes the
  count **fifteen Protocols on twelve seam rows — eleven required, one provided**
  ([ADR-0038](0038-seam-inventory-records-the-direction-of-the-call.md)) and leaves the thirteen
  conformance suites of [ADR-0047](0047-a-conformance-suite-per-core-seam.md) unchanged, because a
  paired row is one suite parametrised over both faces.
- **An observer's failure never reaches the caller.** It is caught, never changes the `Outcome` and
  never changes a retry decision, and is logged once at WARNING with the observer's class and the
  exception type. A Signal keeps the collected typed outcome of
  [ADR-0017](0017-typed-async-lifecycle-signals.md), and the difference has a reason: publishing a
  Signal returns a value its caller can act on, while an observation has no caller who could.

## Considered options

- *A `DispatchObserver` Core seam with one frozen record per dispatched event* — rejected: it is a
  substitution point no peer has, it cannot carry a span because it does not enclose the work, and
  it costs a thirteenth seam row, a fourteenth conformance suite and a recount in five documents to
  deliver facts the `Outcome` already carries.
- *Both a seam and Middleware — records through the first, spans through the second* — rejected:
  one fact on two mechanisms, and a first-party plugin that must register twice and take care not
  to count every event twice.
- *One generic `Observer` Protocol over a union of record types, absorbing `RequestObserver`* —
  rejected: an application that wants only HTTP metrics would have to know the whole union, and
  every new record kind would break every existing observer.
- *Retiring the observation seam entirely, leaving only the `HTTPTransport` decorator* — rejected:
  a decorator below the retry loop cannot see the operation, the path template or the attempt
  ordinal, which are the fields the conventions ask for.

## Consequences

- The four sentences that reported into the retired seam now name a real mechanism: the `Unhandled`
  walk ([ADR-0013](0013-type-driven-routing-with-a-typed-dispatch-outcome.md)) and the escaped
  exception ([ADR-0021](0021-core-error-boundary.md)) are the `Outcome` a Middleware receives, a
  failing Signal subscriber is in the Signal's own outcome (ADR-0017), and an expired lock
  ([ADR-0022](0022-state-plugin-model.md)) is a typed outcome with a WARNING beside it.
- **Observability seam** in `CONTEXT.md` now denotes exactly the `RequestObserver` pair and the
  laws that bind it, and the *Not yet specified* line ADR-0002 claimed for observability never
  existed — that sentence is rewritten rather than the map.
