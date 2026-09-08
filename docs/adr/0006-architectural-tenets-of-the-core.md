---
status: accepted
date: 2026-09-03
ticket: "#13"
---

# The core is built by composition over Protocols it owns, with named patterns and strict typing

A core that inherits its composition root from its router, resolves dependencies by introspecting
untyped callables, leans on `Any` and relies on module-level state can be neither replaced piecewise
nor checked mechanically. We decided the tenets every
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

## Amended by #36 on 2026-09-07: where inheritance is allowed

Tenet 1 said what inheritance is not for and left open where it is still the right tool. The
boundary, written as rules in [`engineering-style.md`](../design/engineering-style.md) §3:

- **A Protocol expresses a seam**; the fourteen Protocols on the twelve seam rows of the
  building-block view §5.4 are the only substitution points, and nothing in the Core imports an
  implementation. Eleven of those rows are *required* — the Core calls out through them — and one is
  *provided*, handed to a Handler to call
  ([ADR-0038](0038-seam-inventory-records-the-direction-of-the-call.md)).
- **`abc.ABC` is a *restricted* pattern**: permitted inside a single component, for a family of
  interchangeable implementations of that component's own concept, and only with an ADR naming the
  rejected alternative. It never crosses a component boundary and is never a user extension point.
- **Inheritance is otherwise for two purposes**: the error taxonomy (ADR-0027) and closed variant
  types whose members are frozen dataclasses.
- **A mixin is permitted only as a private `_Base…` class inside one component, and only to share
  behaviour between an asynchronous and a synchronous pair** (ADR-0029).
- **Template Method is banned as a user extension point** and restricted inside a component.
- **`@final` is the default** on every class the component's document does not say who subclasses.

The reference implementation we measured holds the mirror position — Protocols only for the shape
of *foreign* objects, ABC grids for its own implementation families — which is why the boundary is
worth stating rather than assuming.
