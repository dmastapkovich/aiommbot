---
status: accepted
date: 2026-09-03
ticket: "#16"
---

# The Core owns a type-keyed dependency resolver with two scopes, declared providers and a graph compiled at start-up; external containers plug in behind a Protocol

Handlers receive everything but the event by annotation
([ADR-0014](0014-filters-and-extractors-with-closed-handler-signatures.md)) and plugins contribute
dependencies ([ADR-0015](0015-plugin-contract-and-composition.md)), so the Core needs a resolver,
and [ADR-0002](0002-core-scope-two-condition-test.md) and
[ADR-0008](0008-python-floor-3-12-with-typing-extensions.md) forbid a third-party one in the Core.
We decided:

- **Ownership.** The Core owns a deliberately small resolver on the standard library, built to the
  quality bar of dishka ([`docs/research/03`](../research/03-bot-framework-architectures.md);
  validated graph, scopes, typed providers) but limited to what handlers and plugins need — not a
  general IoC container for applications. It sits behind the Core-owned `DependencyProvider`
  Protocol, so an external container can serve dependencies through a plugin. **First-party bridge
  plugins for dishka and wireup ship in 0.5.0** as extras, so no bot has to hand-roll its own
  wiring.
- **Key = type.** A dependency is identified by its annotation type; the parameter name means
  nothing. Two dependencies of one type are told apart with `Annotated[T, Qualifier("name")]` or a
  `NewType` — the same `Annotated`-marker convention django-modern-rest uses for its request
  components ([`docs/research/20`](../research/20-reply-slot-variance-and-capability-typing.md)).
  Protocol types as keys are the preferred way to depend on abstractions (DIP). Annotations are read
  with `include_extras` through `get_type_hints`/`annotationlib`
  ([ADR-0008](0008-python-floor-3-12-with-typing-extensions.md)).
- **Two scopes.** `App`: one instance per Bot, created in the start phase and closed at shutdown
  (clients, pools, services). `Event`: one instance per dispatched event, created lazily on first
  request, shared by middleware and handler, closed after them in reverse order even on failure. An
  `App` provider depending on an `Event` dependency is a check error. No further scopes until a need
  is proven; Signals ([ADR-0017](0017-typed-async-lifecycle-signals.md)) cover connection
  lifecycles.
- **Providers.** `Provider[T]` = key (type + qualifier), scope, factory. A factory is an async or
  a cheap synchronous callable, or an async generator whose `yield` marks clean-up; its own
  parameters are injected, forming a graph. Plugins contribute providers through
  `ContributesDependencies`; applications through `Bot(dependencies=[...])`.
- **Graph compiled in the check phase** ([ADR-0016](0016-three-phase-start-with-checks.md)):
  duplicate keys, cycles, scope violations and unresolvable parameters of handlers or providers are
  check errors. For every handler a frozen **resolution plan** is compiled once; there is no
  introspection on the hot path. "If it starts, it works."

## Considered options

- *dishka as a Core dependency* — rejected: a second runtime dependency of the Core and a foreign
  model in the public API; offered as a bridge plugin instead.
- *Only a Protocol in the Core, implementation exclusively by plugins* — rejected: every bot needs
  resolution identically ([ADR-0002](0002-core-scope-two-condition-test.md) test 1).
- *Name-based injection (aiogram, Bolt —
  [`docs/research/03`](../research/03-bot-framework-architectures.md))* — rejected in
  [ADR-0014](0014-filters-and-extractors-with-closed-handler-signatures.md).
- *Explicit markers on every parameter (`Depends()`, `FromDishka[T]`)* — rejected: noise a closed
  signature makes unnecessary.
- *Lazy resolution at first call* — rejected: graph errors must surface at start-up.
