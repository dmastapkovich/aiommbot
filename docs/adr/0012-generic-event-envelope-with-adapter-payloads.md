---
status: accepted
date: 2026-09-03
ticket: "#15"
---

# Inbound events are one generic envelope `Event[P]`; payload types and their registry belong to the Adapter

0.4.8 modelled thirteen parallel request classes with a dispatcher per kind; eight of them had no
user in eleven bots, and every new Mattermost event needed a new class and a new dispatch path.
Mattermost itself emits over a hundred event names plus `custom_<plugin>_*`, so any closed list is
wrong on arrival. We decided:

- **The Core owns one immutable generic envelope** `Event[P]` (PEP 695): `kind` (the platform
  event name), `payload: P`, and `meta` — transport that delivered it, receive time, correlation
  id, transport sequence, the raw wire data, and an optional typed **reply channel** with a
  deadline so request/response transports (webhook callbacks) can join the same model if #20
  decides so. The Core knows no concrete payload.
- **The Adapter owns the payload types and a declarative `EventRegistry`** mapping event name →
  payload type. A payload type declares its event name and decoding schema as class metadata, with
  no import-time side effects; the registry is filled explicitly at composition. Plugins and
  applications register additional payload types (including `custom_<plugin>_*`); a duplicate name
  is a start-up error.
- **First-class payloads in 0.5.0**: `Posted`, `PostEdited`, `PostDeleted`, `ReactionAdded`,
  `ReactionRemoved`, `DirectAdded`, `GroupAdded`, `UserAdded`, `UserRemoved`, `StatusChange`,
  `Typing`, `EphemeralMessage`, `Hello`, plus `InteractiveAction` and `DialogSubmission` from the
  webhook path. **Every other name decodes to `RawEvent`** (name + undecoded data) and stays
  routable by name. Typed coverage of the full catalogue is a separate ticket that only adds
  registry entries, possibly generated from the webapp's `websocket_messages.ts`.
- The Adapter handles wire quirks (double-encoded `data.post`, `broadcast` metadata) once, at
  decode time; the Core never sees them.

## Considered options

- *One class per event kind with its own dispatcher (0.4.8)* — rejected: O(kinds) code paths, the
  Core learns platform vocabulary, and unused kinds still cost maintenance.
- *Envelope with an untyped payload* — rejected: contradicts ADR-0006; typing the payload is the
  point.
- *Typing all 89 webapp-known payloads now* — deferred to its own ticket: the mechanism must be
  right first; volume follows.
