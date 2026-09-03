---
status: accepted
date: 2026-09-03
ticket: "#18"
---

# Conversation state is a typed `Flow[Data]` keyed by a `StateKey`, stored through two Core Protocols with compare-and-set, isolated per key by default

ADR-0003 made the Core stateless and put conversation state into the State plugin with an explicit
backend. This decision fixes the model of that plugin. Evidence: aiogram's `StorageKey` /
`FSMStrategy` / event-isolation design and Bot Framework's eTag storage are the tested precedents
(`docs/research/03`, `07`); three of eleven company bots used state groups, most gated on plain
strings and lost types (`docs/research/09`).

- **Key.** `StateKey` is a frozen data class of platform identifiers — channel, user, thread root —
  plus a scope name so several independent flows can run for one user. A **strategy**
  (`USER_IN_CHANNEL` default, `CHANNEL`, `GLOBAL_USER`, `THREAD`) is a plugin setting, overridable
  per Flow. The Adapter builds the key from an Event through the Core Protocol
  `StateKeyProvider`; the State plugin only consumes it.
- **Flow with typed data.** `class Order(Flow[OrderData]): choosing = State(); confirming = State()`.
  A Flow declares its states and a frozen data model that is serialised and versioned; there is
  no `dict[str, Any]`. Handlers receive `StateContext[Order]` with typed `state`, `data`,
  `set_state()`, `update()`. State and data are stored under one key but separately. Business
  data belongs to the application; the Flow's data is the draft of the current dialogue. Gating
  is an ordinary Filter, `InState(Order.confirming)`.
- **Two Core Protocols, not one profile.** `KeyValueStore` — get/set/delete of bytes by key with a
  version for compare-and-set, TTL as an optional capability; `LockProvider` — `lock(key, ttl)`
  as an async context. Both are Core-owned and shared with other plugins (webhook dedup); the
  split follows Rasa and aiogram; no precedent exists for one profile serving state, locks and
  idempotency. The State plugin adds serialisation and namespaces on top.
- **Backends.** In-memory (tests and single-process development) and Redis (TTL and distributed
  lock) are first-party. MongoDB and SQL are separate packages — possibly ours, later — that pass
  the shared conformance suite in `aiommbot.testing`; the industry treats Mongo as a late
  community add-on without TTL indexes, and it would pull `pymongo` into the distribution.
- **Isolation by default.** The State plugin contributes an Inbound middleware: for events that
  yield a `StateKey` it takes `LockProvider.lock(key, ttl)` for the walk and the handler, then
  publishes `StateContext` into the Event scope (state is read after the lock is held). Locks
  carry a TTL and a wait timeout; expiry is a typed outcome reported to observability, never a
  leaked lock (aiogram's unfixed clean-up TODO). Isolation is on unless disabled explicitly; an
  in-memory lock is legal only under the single-process declaration (ADR-0003).
- **Writes are compare-and-set.** `StateContext` reads a versioned record and writes through CAS;
  under the isolation lock a conflict cannot happen, without it the caller receives a typed
  `Conflict` with the current record and decides. No silent last-write-wins.
- **Schema versions.** A record stores the Flow name, the data schema version and the state name.
  An unknown state, another version or invalid data yields the typed outcome `StaleState`; the
  default resets the record and emits a Signal, a Flow may declare `upgrade(old_version, raw) ->
  Data`, and a handler may subscribe to `StateContext[Order] | StaleState` to explain the reset.
- **Lifetime is bounded and logical.** Every record carries `expires_at`, checked on read, so
  expiry means the same on in-memory, Redis or any external backend; a backend's native TTL is
  garbage collection only. The plugin default is **one hour of inactivity, sliding on every CAS
  write** — Rasa's exact default, between Dialogflow CX's 30 minutes and Lex's 24-hour cap
  (`docs/research/13`); a Flow may override it, and `ttl=None` is an explicit opt-in that is
  visible in code. Expiry is the typed outcome `StaleState(Expired)`: a quiet reset for the
  user, a Signal for the system, and a subscription point for handlers that want to explain.
  Locks and dedup keys are fixed-from-issue and short (60 s, the aiogram and Rasa precedent).
- **Stateless where possible.** Single-step interactions carry their state in the message —
  Mattermost button `context` and dialog `state` — and need no store; the State plugin exists for
  free text and multi-step accumulation. Business data, transcripts and tokens are never stored
  in it.

## Considered options

- *String keys assembled by the application* — rejected: eleven bots would assemble them eleven
  ways.
- *`State`/`StatesGroup` with `dict` data (aiogram)* — rejected: untyped data (ADR-0006).
- *One wide `StateStorage` with `get_state`/`set_data`* — rejected: locks and dedup would need a
  second contract and backends would duplicate logic.
- *MongoDB first-party in 0.5.0* — rejected: late community add-on elsewhere, no TTL indexes, a
  driver in the distribution; available as a conformant external package.
- *Isolation off by default* — rejected: races on double clicks are the bug FSM exists to prevent.
- *Last-write-wins* — rejected: lost updates in silence.
- *Declarative scenes inside the State plugin now* — deferred to #48: Flow + Filter covers what
  the bots do today; scenes are designed typed on top.
