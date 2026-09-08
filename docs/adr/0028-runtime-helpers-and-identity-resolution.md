---
status: accepted
date: 2026-09-03
ticket: "#21"
amended-by: ADR-0029
---

# The Runtime is a thin Event-aware layer over the API client with a fixed helper set; user and channel resolution lives in the Runtime without a cache, and caching is an optional adapter-specific plugin

A Handler reaches for the same few operations on every platform event — answer, update, delete,
open a dialog, read the post or user behind the Event — and a script or worker without an Event
needs to message a channel or a user. Each is one line over the API client, and a helper set that
grows past that becomes a second API. Resolving a user by id, e-mail, username, nickname or full
name is the one lookup every bot performs, and a cache for it — TTL, invalidation, sharing across
replicas — is a policy the framework must not choose for the application. We decided:

- **Helpers bound to the Event**: `answer`, `reply` (in thread), `update`, `delete`,
  `open_dialog` — channel, `root_id` and `trigger_id` come from the Event.
- **Addressed helpers**, on the Event-free `Workspace` (ADR-0029), for scripts and workers without
  an Event: `send(channel_id, ...)`,
  `send_direct(UserRef, ...)` (resolves the user, creates the direct channel), `ephemeral`.
- **File helpers**: `upload(...) -> file_ids` and `download(file_id)`, streaming, as thin wrappers
  over the files and uploads operations. Everything else — reactions, pins, teams, preferences —
  is reached through `runtime.api.<resource>` (ADR-0026).
- **Resolution without a cache.** `runtime.users.resolve(UserRef)` takes a typed union
  (`UserId | Email | Username | Nickname | FullName`) and queries the API in that priority;
  `runtime.channels.direct(user_id)` creates or fetches the direct channel. Ambiguous and missing
  matches are typed outcomes, not silent first hits.
- **Caching is a plugin.** `IdentityCache` is an optional adapter-specific plugin on the Core
  `KeyValueStore` (ADR-0022) with a one-hour default TTL, invalidated by `user_updated` and
  `channel_updated` events; when enabled, the Runtime consults it through a Protocol. The Adapter
  and the Core hold no identity state (ADR-0003).
- **Out of this decision**: message composition builders (attachments, buttons, selects, dialog
  elements and the embedding of Callback tokens) and the file API beyond the two thin helpers
  (limits, resumable uploads, streaming ergonomics) are separate tickets graduated from #21.

## Considered options

- *An always-on in-process cache inside the Adapter* — rejected: not shared across replicas and it
  blurs the stateless rule onto the Adapter.
- *No resolution helpers* — rejected: every application would copy-paste the same lookup.
- *Reactions and pins as helpers* — rejected: one line over the API client when needed.

## Consequences

- The helper set splits along the Event boundary: the addressed helpers, the file helpers and the
  resolvers live in the independently constructible Event-free `Workspace` that the Runtime composes
  and that carries the synchronous face; the Event-bound helpers stay asynchronous on the Runtime
  ([ADR-0029](0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md)).
