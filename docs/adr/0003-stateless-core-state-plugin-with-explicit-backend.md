---
status: accepted
date: 2026-09-03
ticket: "#13"
---

# The core is stateless; conversation state is a plugin that cannot start without an explicit backend

A bot process may be replicated on its webhook side while its WebSocket consumer is a singleton
(`docs/research/01`), so any process-local state silently breaks the moment a second replica
appears; aiogram's `MemoryStorage` default is the canonical example of that trap. We decided that
the **Core holds no state between events**. It defines only the types (state key, `State`,
`StatesGroup`) and the storage and lock Protocols. FSM behaviour, per-key event isolation and the
backends live in the first-party **State** Plugin, which refuses to start without an explicit
backend. An in-memory backend exists for tests and local development and requires an explicit
single-process declaration; without it a startup check (Django-checks style) fails fast.

## Considered options

- *FSM in core with an in-memory default* (aiogram) — rejected: convenient for the first hour,
  wrong in production, and impossible to detect from inside the process.
- *No framework-provided state at all* — rejected: per-key isolation of conversation state is
  chat-specific logic with no library equivalent, which is exactly what ADR-0002 keeps first-party.

## Consequences

- Backend choice, the storage Protocol shape and a shared conformance test suite are decided in
  #18; the single-process declaration and the checks framework are designed in #14 and #40.
