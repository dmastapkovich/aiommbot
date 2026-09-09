---
status: accepted
date: 2026-09-03
ticket: "#15"
amended-by: [ADR-0036, ADR-0037]
---

# Inbound events are one generic envelope `Event[P, R]`; payload types and their registry belong to the Adapter

One class per platform event with a dispatcher per kind means a new class and a new dispatch path
for every new Mattermost event, and most of those classes go unused. Mattermost itself emits over a
hundred event names plus `custom_<plugin>_*`
([`docs/research/01`](../research/01-mattermost-websocket-protocol.md)), so any closed list is wrong
on arrival. We decided:

- **The Core owns one immutable generic envelope** `Event[P, R]` — `P` the Payload, `R` the type its
  Reply channel accepts, `Never` by default
  ([ADR-0036](0036-reply-slot-as-a-second-type-parameter-over-a-core-owned-reply-channel.md)); an
  enriched copy is obtained only through `derive`
  ([ADR-0037](0037-derive-is-the-only-enrichment-path-for-an-event.md)). It carries `kind` (the
  platform event name), `payload: P`, and `meta` — transport that delivered it, receive time,
  correlation id, transport sequence, the raw wire data, and an optional typed **Reply channel**
  with a deadline, through which request/response transports (webhook callbacks) join the same model
  ([ADR-0024](0024-webhook-ingress-and-callback-security.md)). The Core knows no concrete payload.
- **The Adapter owns the payload types and a declarative `EventRegistry`** mapping event name →
  payload type. A payload type declares its event name and decoding schema as class metadata, with
  no import-time side effects; the registry is filled explicitly at composition. Plugins and
  applications register additional payload types (including `custom_<plugin>_*`); a duplicate name
  is a start-up error.
- **First-class payloads in 0.5.0**: `Posted`, `PostEdited`, `PostDeleted`, `ReactionAdded`,
  `ReactionRemoved`, `DirectAdded`, `GroupAdded`, `UserAdded`, `UserRemoved`, `StatusChange`,
  `Typing`, `EphemeralMessage`, `Hello`, plus `InteractiveAction` and `DialogSubmission` from the
  webhook path. **Every other name decodes to `RawEvent`** (name + undecoded data) and stays
  routable by name. Typed coverage of the full catalogue is #45, which only adds registry entries.
- The Adapter handles wire quirks (double-encoded `data.post`, `broadcast` metadata) once, at
  decode time; the Core never sees them.

## Considered options

- *One class per event kind with its own dispatcher* — rejected: O(kinds) code paths, the
  Core learns platform vocabulary, and unused kinds still cost maintenance.
- *Envelope with an untyped payload* — rejected: contradicts
  [ADR-0006](0006-architectural-tenets-of-the-core.md); typing the payload is the point.
- *Typing all 89 webapp-known payloads now* — deferred to #45: the mechanism must be right first;
  volume follows.
