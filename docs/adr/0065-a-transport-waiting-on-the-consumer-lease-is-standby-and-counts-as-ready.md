---
status: accepted
date: 2026-09-10
ticket: "#40"
amends: [ADR-0023, ADR-0061]
---

# A WebSocketTransport waiting on the consumer lease is `Standby`, and readiness counts a standby Transport as connected

[ADR-0023](0023-websocket-gateway-resilience.md) lets a second consumer replica wait on a
`LockProvider` lease and take over when the lease lapses, and
[ADR-0061](0061-health-is-a-generic-plugin-over-application-supplied-checks.md) defines readiness as
every Transport being connected — so the replica that is doing exactly what it was deployed to do
reports not ready for its whole life. For a Pod no Service selects that is not a traffic question
but a rollout one: the `Ready` condition drives `minReadySeconds`, `maxUnavailable`,
`progressDeadlineSeconds` and PodDisruptionBudget, "which defines healthy strictly as the Pod Ready
condition" ([`docs/research/27`](../research/27-application-contributed-readiness-checks.md) §3). A
permanent standby therefore fails every rollout after ten minutes and is never protected from a
voluntary eviction. We decided:

- **`Standby` is a third state of the WebSocketTransport and a Signal beside `Connected` and
  `Disconnected(reason)`.** It is published when the Transport begins waiting for the lease and each
  time it returns to waiting after losing it; taking the lease publishes `Connected` as usual.
- **Readiness counts a Transport as ready when its last Signal was `Connected` **or** `Standby`.**
  The conjunction of ADR-0061 is otherwise unchanged: started, not draining, every Transport
  connected-or-standby, every `ReadinessCheck` passing.
- **A Transport that holds the lease and has lost its socket stays `Disconnected` and is not
  ready.** Standby is the absence of a lease, never the absence of a connection; the two cannot both
  be true.
- **Readiness is not a report of activity.** A standby process handles no Event, and the operator
  learns that from the Signal and its INFO record, not from a probe — the probe body is empty and
  stays empty (ADR-0061).

## Considered options

- *Leaving a standby not ready and documenting it* — rejected: the normal mode of a two-replica
  consumer would be indistinguishable from a failed one, and the deployment view would have to tell
  operators to disable the check that protects the active replica.
- *A `standby_is_ready` setting on the Health Plugin* — rejected: the other value breaks the rollout
  in every deployment rather than in some, so it is a knob with one usable position, which
  [ADR-0002](0002-core-scope-two-condition-test.md) does not admit.
- *An eighth `Contributes*` Protocol so a Plugin answers "am I ready?"* — rejected for the reason
  ADR-0061 already gives: the Signals carry every transport transition, and #85's question about the
  rank of the seven stays untouched.
- *Reporting standby on liveness instead* — rejected: liveness runs no check at all, and a probe
  that distinguishes standby from active would restart the waiting replica.

## Consequences

- The Signal list of ADR-0023 gains `Standby`; `websocket-transport.md` owns its exact publication
  points and `health.md` owns the aggregate.
- No workload kind removes the need for the lease: `Recreate` bounds upgrades only, a StatefulSet's
  "at most one" is voided by force deletion and by partitions
  ([`docs/research/29`](../research/29-kubernetes-fields-a-drain-depends-on.md) §6), so a bot that
  must never double-process configures the lease and reads `Standby` to know it worked.
