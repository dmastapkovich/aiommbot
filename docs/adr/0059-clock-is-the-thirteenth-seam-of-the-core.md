---
status: accepted
date: 2026-09-09
ticket: "#30"
amends: [ADR-0006, ADR-0038, ADR-0047, ADR-0048, ADR-0050]
---

# Time is a Core-owned `Clock` Protocol, the thirteenth seam, and `FakeClock` is its second implementation

`ST-TST-09` requires every timeout, TTL and backoff to be driven by `FakeClock` instead of sleeping,
and `FakeClock` was listed as a part of the testing toolkit — but nothing said what it
*substitutes*. The framework is full of durations a test must be able to advance without waiting:
the 30 s heartbeat and the 60 s silence monitor, full-jitter backoff to 300 s and the 25 s Drain
([ADR-0023](0023-websocket-gateway-resilience.md)), the 10 s reply deadline and the token's
`clock_leeway` ([ADR-0024](0024-webhook-ingress-and-callback-security.md)), the sliding one-hour
state TTL ([ADR-0022](0022-state-plugin-model.md)) and the retry backoff of
[ADR-0026](0026-standalone-typed-api-client-over-an-http-transport-protocol.md). We decided that
**`Clock` is a Core-owned Protocol and a `required` seam row of
[§5.4](../design/05-building-block-view.md#54-the-seams-of-the-core)** — the Core calls out through
it and the implementation arrives from outside, exactly like `KeyValueStore`.

It is a seam and not a settings field because the alternative is the same substitution repeated per
component with no contract behind it: a monotonic reading that never goes backwards, a wall-clock
reading that may, and a sleep that is cancellable are three promises an implementer has to keep
together, and the only way this project states a promise an outsider must keep is a Protocol with a
conformance suite ([ADR-0047](0047-a-conformance-suite-per-core-seam.md)). The Core ships the
standard-library implementation over `time.monotonic`, `datetime.now` and `asyncio.sleep`; the
testing toolkit ships `FakeClock`; both run the same suite.

A Plugin receives its `Clock` in its typed settings object rather than by injection, because
[ADR-0015](0015-plugin-contract-and-composition.md) gives a Plugin a constructor and not a
resolution plan; a Handler that needs the time receives it from the `DependencyProvider` like any
other App-scoped dependency ([ADR-0019](0019-handler-parameter-resolution-rules.md)).

## Considered options

- *A built-in dependency of the `DependencyProvider` and no seam row* — rejected: it reaches
  Handlers and reaches nothing else. The components whose timing actually needs substituting — the
  WebSocketTransport's backoff, the Webhook's deadline — are Plugins, which are constructed and not
  injected, so the mechanism would cover the easy half and leave the hard half undescribed.
- *`now` and `sleep` as callables in each component's settings* — rejected: it satisfies
  `ST-TST-09` and states no contract, so nothing checks that a substituted clock is monotonic or
  that its sleep is cancellable, and `FakeClock` would be wired differently in every component.
- *Freezing time in tests with a library such as `time-machine`* — rejected: it patches a process,
  not a seam, so it cannot express "advance this bot's clock by 31 seconds" while another test runs,
  and it would be a test dependency doing what a Protocol does for free.

## Consequences

- The inventory becomes **sixteen Protocols on thirteen seam rows — twelve required, one provided**,
  and the conformance suites become **fourteen**. The count is stated in
  [§5.4](../design/05-building-block-view.md#54-the-seams-of-the-core) and
  [§5.10](../design/05-building-block-view.md#510-inventory-summary),
  [ADR-0006](0006-architectural-tenets-of-the-core.md),
  [ADR-0038](0038-seam-inventory-records-the-direction-of-the-call.md),
  [ADR-0047](0047-a-conformance-suite-per-core-seam.md),
  [ADR-0048](0048-observability-is-not-a-core-seam.md),
  [ADR-0050](0050-bounded-resource-state-is-read-not-pushed.md),
  [`engineering-style.md` §1](../design/engineering-style.md) and
  [`TRACKER.md` §C](../design/TRACKER.md), and it moves in all of them together.
- Every component document that states a duration names `Clock` in its structural section, and
  `ST-ASY` gains no rule: `asyncio.timeout` still bounds I/O, and `Clock.sleep` is what a delay
  between attempts goes through.
- `FakeClock` stops being a bare helper and becomes the second shipped implementation of a seam,
  listed as such in
  [§5.9](../design/05-building-block-view.md#59-level-3--the-testing-toolkit).
