---
status: accepted
date: 2026-09-03
ticket: "#14"
amended-by: [ADR-0048]
---

# Lifecycle notifications are typed asynchronous Signals separate from platform events

Plugins need to react to what the process does — started, stopping, a transport connected,
disconnected or resumed — without those notifications competing with user events in the router
tree, where first-match semantics would let only one subscriber win.

We decided on a small **Signal** facility in the Core (the Observer of
[ADR-0006](0006-architectural-tenets-of-the-core.md)): `Signal[T]` with typed asynchronous
subscribers, subscription by signal type, a closed set of Core and Transport signals, and the
ability for plugins to declare their own. There is no synchronous variant, which avoids the
sync/async duality pluggy and its users retrofit at runtime
([`docs/research/10`](../research/10-plugin-systems.md)). A subscriber's failure is not swallowed
and does not stop other subscribers: it is collected, logged at WARNING and returned in the
signal's typed outcome, which is what the publisher's caller acts on — an observer, whose caller
could act on nothing, is only caught and logged
([ADR-0048](0048-observability-is-not-a-core-seam.md)).

## Considered options

- *Only start/stop methods on plugins* — rejected: transport-level events would be invisible to
  plugins such as State (clear caches on resume) or the observability Plugin
  ([ADR-0051](0051-first-party-observability-plugin.md)).
- *Routing signals through the event routers* — rejected: mixes process signals with user events
  and first-match dispatch defeats multiple subscribers.
