---
status: accepted
date: 2026-09-09
ticket: "#29"
amended-by: [ADR-0061]
amends: [ADR-0023]
---

# Every fact the framework makes observable travels on a mechanism that already exists, and storage is observed by decorating its Protocol rather than by instrumenting the caller

With no observability Protocol of its own
([ADR-0048](0048-observability-is-not-a-core-seam.md)), the question is which facts are observable
at all and on which existing mechanism each one rides. The answer has to be a closed table, because
an open one is how a framework acquires a second telemetry channel per release. We decided the four
mechanisms below carry everything, and nothing in the framework emits a metric or a span by itself:

| Fact | Mechanism | Ships by default |
|---|---|---|
| One dispatched event: kind, outcome class, duration, queue latency, matched Handler | Middleware, Inbound and Handler layer ([ADR-0020](0020-two-layer-middleware-chain.md)) | nothing |
| One HTTP attempt | `RequestObserver` / `SyncRequestObserver` ([ADR-0026](0026-standalone-typed-api-client-over-an-http-transport-protocol.md)) | nothing — the empty tuple |
| A transport or process transition | the Signals of ADR-0023 and [ADR-0030](0030-synchronous-callables-by-explicit-declaration.md) | the Signals themselves |
| One storage call | a decorator over `KeyValueStore` / `LockProvider` ([ADR-0022](0022-state-plugin-model.md)) | nothing |
| A bounded resource's depth | the frozen snapshot of [ADR-0050](0050-bounded-resource-state-is-read-not-pushed.md) | the snapshot |
| Whether the process is alive, and whether it is ready | the two paths of the Health Plugin ([ADR-0061](0061-health-is-a-generic-plugin-over-application-supplied-checks.md)) | nothing — the Plugin is composed explicitly |
| Anything a human has to read | the log ([ADR-0052](0052-log-levels-by-frequency-and-audience.md)) | the records, at their levels |

Two entries in that table are decisions rather than bookkeeping.

- **Storage is observed by decoration, not by instrumentation.** `KeyValueStore` and `LockProvider`
  are seams whose implementation belongs to the application or to us over `redis`, so the caller
  cannot instrument them without knowing them. The first-party plugin therefore ships
  `ObservedKeyValueStore` and `ObservedLockProvider`, each holding an inner implementation and
  delegating — the third level of adoption ADR-0026 already describes, applied to storage. Each
  must pass its Protocol's conformance suite unchanged (`ST-SOL-03`), which is what keeps a
  decorator from quietly changing compare-and-set or lock semantics.
- **The Webhook's verification outcome stays a log line**, as
  [ADR-0024](0024-webhook-ingress-and-callback-security.md) fixed it, and the event a callback
  produces reaches the Middleware layers like any other, so a rejected callback is counted where
  every other rejected delivery is counted.

Nothing else is instrumented in 0.5.0: not the Sync executor beyond its `HandlerAbandoned` Signal
and the start-up Check on its size, not the Router walk beyond the `Outcome`, and not the Codec.

## Considered options

- *Instrument storage from the calling side, inside State and the IdentityCache* — rejected: it
  measures our call and not the backend, and it puts the same timing code in three components.
- *No storage observability at all, documented as the application's decorator to write* — rejected
  by the maintainer: a bot's slowest dependency is usually its store, and a decorator we do not
  ship is a decorator nobody writes.
- *One metric per Signal, emitted by the Core* — rejected: it makes the Core emit telemetry, which
  ADR-0002 refuses; a plugin subscribing to the Signals gets the same numbers and costs nothing
  when absent.

## Consequences

- `ObservedKeyValueStore` and `ObservedLockProvider` are public names on the plugin's package path
  ([ADR-0042](0042-a-public-name-is-documented-at-its-package-path.md)) and appear in both storage
  conformance suites' shipped-implementation lists, so the suites run against them in CI.
- The plugin sits on the data path for storage and only beside it for everything else; its
  component document states that asymmetry and the failure modes it creates.
