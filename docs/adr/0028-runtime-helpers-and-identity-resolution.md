---
status: accepted
date: 2026-09-03
ticket: "#21"
---

# The Runtime is a thin Event-aware layer over the API client with a fixed helper set; user and channel resolution lives in the Runtime without a cache, and caching is an optional adapter-specific plugin

Usage mining shows what the eleven bots asked of 0.4.8's `ApiManager` and `BotRuntime`:
`answer`, `update_post`, `send_dialog`, `get_post` and `get_user` in 11 of 11, direct messages in
5, files in 3, and zero calls to `reply`, reactions, pins or ephemeral posts — the last because the
API had none (`docs/research/09`, #21 resolution). `EventPreparer` resolved users by id, e-mail,
username, nickname and full name for 6 bots over a cache with no TTL and no invalidation. We
decided:

- **Helpers bound to the Event**: `answer`, `reply` (in thread), `update`, `delete`,
  `open_dialog` — channel, `root_id` and `trigger_id` come from the Event.
- **Addressed helpers** for scripts and workers without an Event: `send(channel_id, ...)`,
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
- *No resolution helpers* — rejected: six bots would return to copy-pasted lookups.
- *Reactions and pins as helpers* — rejected: zero usage; one line over the API client when needed.
