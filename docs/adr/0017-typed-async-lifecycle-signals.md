---
status: accepted
date: 2026-09-03
ticket: "#14"
---

# Lifecycle notifications are typed asynchronous Signals separate from platform events

Plugins need to react to what the process does — started, stopping, a transport connected,
disconnected or resumed — without those notifications competing with user events in the router
tree, where first-match semantics would let only one subscriber win.

We decided on a small **Signal** facility in the Core (the Observer of ADR-0006): `Signal[T]` with
typed asynchronous subscribers, subscription by signal type, a closed set of Core and Transport
signals, and the ability for plugins to declare their own. There is no synchronous variant, which
avoids the sync/async retrofits pluggy and its users had to make. A subscriber's failure is not
swallowed and does not stop other subscribers: it is collected, reported to observability and
returned in the signal's typed outcome.

## Considered options

- *Only start/stop hooks on plugins* — rejected: transport-level events would be invisible to
  plugins such as State (clear caches on resume) or observability.
- *Routing signals through the event routers* — rejected: mixes process signals with user events
  and first-match dispatch defeats multiple subscribers.
