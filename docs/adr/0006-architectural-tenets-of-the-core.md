---
status: accepted
date: 2026-09-03
ticket: "#13"
---

# The core is built by composition over Protocols it owns, with named patterns and strict typing

The 0.4.8 core inherited `Bot` from `Router`, resolved dependencies by introspecting untyped
callables, carried ~555 `Any` and relied on module-level state. We decided the tenets every
component document must argue against, in this order of authority:

1. **Composition over inheritance.** `Bot` *has* routers, plugins, a transport and an adapter; it
   is not a `Router`. No framework class is designed to be subclassed by users.
2. **Dependency inversion through Core-owned Protocols.** The Core defines the `Protocol`s
   (transport, storage, lock, API client, observability hooks); adapters and plugins implement
   them; nothing in the Core imports an implementation.
3. **Named patterns, each justified.** Candidates the Core is expected to use: Strategy for
   filters, Chain of Responsibility for middleware, Observer for lifecycle events, Adapter for the
   platform, Facade for the public API, Mediator for the dispatcher, Builder for message
   composition. Every LLD names the pattern as on refactoring.guru, the problem it solves there
   and the rejected alternative, and may replace a candidate with a reason.
4. **No singletons, no global context.** No module-level mutable state, no `get_current()`; one
   `Bot` per process is the documented model, and several must still work in tests.
5. **Immutable inbound events**, keyword-only constructors, typed result objects instead of
   dictionaries and tuples.
6. **Declarative thin handlers.** Filters, state gates, payload parsing and dependency injection
   happen outside the handler body; the body makes one service call and answers; unexpected
   exceptions propagate to middleware and observability; handlers, filters and events are
   introspectable as data so a handler catalogue (#34) can be generated.
7. **Typing as the contract.** Python 3.12+ features as the baseline: PEP 695 generics, `Protocol`,
   `TypeIs`, `Final`, `@override`, `slots=True`; no `Any`, `cast`, `getattr`/`hasattr`/`setattr`
   or `TYPE_CHECKING` imports in the public contract; several strict checkers keep it honest.
8. **Fail closed.** Unknown handler parameters, missing plugin dependencies, an in-memory backend
   without a single-process declaration and a contradicted import contract stop start-up.

## Consequences

- `docs/design/engineering-style.md` (#36) turns these tenets into rules with examples; every LLD
  has a SOLID section that argues them for its component.
