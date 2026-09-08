---
status: accepted
date: 2026-09-03
ticket: "#13"
amended-by: [ADR-0022]
---

# The core is stateless; conversation state is a plugin that cannot start without an explicit backend

A bot process may be replicated on its webhook side while its WebSocket consumer is a singleton
(`docs/research/01`), so any process-local state silently breaks the moment a second replica
appears; aiogram's `MemoryStorage` default is the canonical example of that trap. We decided that
the **Core holds no state between events**. It defines only the Protocols — `KeyValueStore`, `LockProvider`,
`StateKeyProvider` — and the `StateKey` type. FSM behaviour, per-key event isolation and the
backends live in the first-party **State** Plugin (ADR-0022), which refuses to start without an
explicit backend. An in-memory backend exists for tests and local development and requires an explicit
single-process declaration; without it a startup check (Django-checks style) fails fast.

## Considered options

- *FSM in core with an in-memory default* (aiogram) — rejected: convenient for the first hour,
  wrong in production, and impossible to detect from inside the process.
- *No framework-provided state at all* — rejected: per-key isolation of conversation state is
  chat-specific logic with no library equivalent, which is exactly what ADR-0002 keeps first-party.

## Consequences

- The backends, the Protocol shapes and the conformance suite are
  [ADR-0022](0022-state-plugin-model.md); the single-process declaration and the Checks are
  [ADR-0016](0016-three-phase-start-and-checks.md).
