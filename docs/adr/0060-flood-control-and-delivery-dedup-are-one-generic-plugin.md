---
status: accepted
date: 2026-09-09
ticket: "#30"
amends: [ADR-0002, ADR-0021, ADR-0022, ADR-0023]
---

# Flood control and delivery dedup ship as one generic Plugin of two Inbound middlewares over `KeyValueStore`, and a declined Event is `Unhandled` with a published reason

[ADR-0002](0002-core-scope-two-condition-test.md) lists flood control keyed on chat identity among
the capabilities that are ours because they are chat-specific with no library equivalent, and
[ADR-0023](0023-websocket-gateway-resilience.md) promised cross-resync dedup by the platform's own
id as "an optional Inbound middleware on `KeyValueStore`" without saying whose. Both are the same
shape — decide, before the Router walk, whether this Event is processed at all, using a chat
identity and a compare-and-set — so they are **one first-party generic Plugin, `FloodControl`**. It
is not the Core's: the Core holds no state between events
([ADR-0003](0003-stateless-core-state-plugin-with-explicit-backend.md)), and both halves need a
store.

- **`Cooldown` is a Flag**, carried by a Handler at its subscription
  ([ADR-0020](0020-two-layer-middleware-chain.md)), so the window is declared where the expensive
  Handler is and not in a global table. This is what aiogram lacked when it deleted
  `dispatcher.throttle()` in v3 on the grounds that the right cache key is application-specific
  ([`docs/research/08`](../research/08-peer-responsibility-boundaries.md) §2.1), and what Litestar's
  global `RateLimitConfig` — which shipped a spoofing advisory — does not offer.
- **The key comes from the seam that already turns an Event into a chat identity**, the Core
  `StateKeyProvider` of [ADR-0022](0022-state-plugin-model.md), whose strategy becomes a setting of
  whichever Plugin asks rather than the State plugin's alone.
- **Delivery dedup identifies a delivery by a value only the platform knows**, so a generic Plugin
  cannot read it: the identity is a typed callable in the Plugin's frozen settings, and the Adapter
  ships one the composition passes in. `CorrelationId` is deliberately not that value — a
  redelivery is a second CorrelationId ([`CONTEXT.md`](../../CONTEXT.md)).
- **A declined Event returns `Unhandled` and publishes a typed `Suppression`.** No fourth `Outcome`
  member is added, because the Transport branches identically on both — the Webhook answers an empty
  200 either way — and
  [ADR-0034](0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md) admits a
  typed outcome only where the immediate caller must branch. The reason is instead an Event-scope
  publication that an Inbound Middleware registered outside `FloodControl` reads after `call_next`
  returns, which is how the observability plugin counts suppressions without a new mechanism
  ([ADR-0049](0049-what-the-framework-makes-observable.md)).
- **Both halves fail open.** A store that is unreachable must not silence a bot: the middleware logs
  one WARNING and admits the Event. Suppressing traffic because Redis blinked turns a degraded
  dependency into an outage, and a duplicate post is a smaller harm than a lost one.
- **Order is declared, not implied.** Dedup runs before cooldown — an already-seen delivery should
  not consume a window — and the Plugin declares that with the `after` mechanism of
  [ADR-0015](0015-plugin-contract-and-composition.md) rather than relying on list position.

The Plugin contributes its own Checks: an in-memory backend under a profile that is not a single
process is an error, as it already is for State
([ADR-0016](0016-three-phase-start-with-checks.md)), and a `Cooldown` Flag with the Plugin absent is
the Flag-without-consumer error ADR-0020 already defines.

## Considered options

- *Two Plugins, `FloodControl` and `DeliveryDedup`* — rejected: two `PluginSpec`s, two component
  documents and two entries in every composition, over one store, one key strategy and one
  middleware layer.
- *A documented how-to instead of a Plugin, as aiogram concluded* — rejected: ADR-0002 already
  classifies flood control as chat-specific, and ADR-0023 already promised the dedup middleware, so
  a recipe would leave two commitments unmet. What aiogram removed was a global throttle with a
  fixed key; the Flag and the `StateKeyProvider` strategy are exactly the parts it did not have.
- *Folding both into the State plugin* — rejected: cooldown and dedup need no `Flow`, no schema
  version and no isolation lock, and a bot that wants a cooldown would have to adopt conversation
  state to get one.
- *A fourth `Outcome` member, `Suppressed`* — rejected above on ADR-0034's rule.
- *Failing closed when the store is unreachable* — rejected: it converts a storage incident into a
  silent bot, which is the failure mode
  [ADR-0023](0023-websocket-gateway-resilience.md) spends its whole design avoiding.

## Consequences

- `FloodControl` is a component of §5.7 with a `LLD: FloodControl` ticket in the writing order of
  [ADR-0035](0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md), after the
  `KeyValueStore` backends, the Router, the Middleware and the State documents whose contracts
  appear in its structural section.
- `StateKeyProvider` gains a second consumer in
  [§5.4](../design/05-building-block-view.md#54-the-seams-of-the-core); the seam itself is unchanged
  and the count does not move.
- The generic-plugin diagram of
  [§5.7](../design/05-building-block-view.md#57-level-3--generic-plugins) gains a box, and the same
  layering argument applies as for State: it reaches the Adapter's key strategy through a Core
  Protocol and never by import
  ([ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md)).
- A cooldown is Inbound and not Handler-layer, because an Event declined for coming too soon has to
  be declined before the Router walk; [ADR-0021](0021-core-error-boundary.md) places it there.
