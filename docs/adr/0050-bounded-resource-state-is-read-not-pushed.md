---
status: accepted
date: 2026-09-09
ticket: "#29"
amends: [ADR-0015, ADR-0023]
---

# The depth of a bounded resource is read from a frozen `bot.stats()` snapshot, contributed by a seventh `Contributes*` Protocol, never pushed

[ADR-0023](0023-websocket-gateway-resilience.md) promises that queue depth and consumer saturation
are metrics, and a push mechanism cannot deliver them: a depth is a value you sample, not an event
you receive, and pushing one on every enqueue and dequeue taxes the hot path twice per event to
duplicate state the queue already holds. Both backends want it pulled anyway — a
`prometheus_client` collector is asked to `collect()` at scrape time and an OpenTelemetry
observable gauge is asked through a callback. We decided:

- **The Bot answers with a frozen typed snapshot**, `bot.stats()`, assembled from the snapshots of
  the parts that own a bounded resource — the WebSocketTransport's queue and the Sync executor's
  pool. It is the same move as `bot.routes()` and `bot.middleware()`
  ([ADR-0013](0013-type-driven-routing-with-a-typed-dispatch-outcome.md),
  ADR-0020): state a reader wants is exposed as data rather than inferred from output, and it is
  useful to a test and to a debugger with no telemetry installed at all.
- **A part contributes its snapshot through a seventh `Contributes*` Protocol** on `PluginSpec`
  ([ADR-0015](0015-plugin-contract-and-composition.md)), which is what keeps imports pointing at the
  Core: the observability plugin is generic and may not import the WebSocketTransport, which is
  adapter-specific ([ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md)), so it
  cannot read a concrete transport by type and must read the Bot's aggregate instead.
- **Counters and histograms stay pushed** — from the Middleware layers and the observers of
  [ADR-0049](0049-what-the-framework-makes-observable.md). The split is the rule: a monotonic count
  or a duration is pushed at the moment it happens, and a level is read when asked.

## Considered options

- *A new Core seam Protocol implemented by the transport and the executor* — rejected: it is the
  thirteenth seam row, the fourteenth conformance suite and a recount in five documents, bought for
  two integers, and [ADR-0048](0048-observability-is-not-a-core-seam.md) has just declined a new
  seam for a larger reason.
- *Reading the concrete components directly* — unavailable: a generic plugin may not import an
  adapter-specific one (ADR-0032), which is exactly the property that makes "generic" checkable.
- *Deriving everything from the plugin's own Middleware — in-flight and saturation are countable
  there* — rejected as incomplete: raw queue depth is not derivable, and it is the one number that
  says a bot is about to start losing events rather than that it already has.
- *Pushing a gauge from the transport* — rejected: it taxes the hot path and needs the seam above.

## Consequences

- `Contributes*` grows from six Protocols to seven, so the rank #85 is deciding covers seven; the
  ticket is told, and nothing about the twelve seam rows of
  [§5.4](../design/05-building-block-view.md) changes, because a `Contributes*` Protocol is not a
  row there.
- `bot.stats()` is a public name and its snapshot types are public
  ([ADR-0042](0042-a-public-name-is-documented-at-its-package-path.md)); a field of the snapshot is
  therefore covered by the deprecation policy of #28, and a component that gains a bounded resource
  later adds a field rather than a mechanism.
- Sampling is the reader's problem: a value read at scrape time can miss a spike between scrapes,
  and the plugin's component document says so rather than pretending otherwise.
