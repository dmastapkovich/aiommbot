---
status: accepted
date: 2026-09-03
ticket: "#16"
amended-by: [ADR-0030]
---

# Handler parameters resolve from extractors first, then providers; the Core injects a minimal built-in set and never the Bot; overrides exist only in the testing toolkit

One resolution mechanism serves both sources of handler parameters
([ADR-0014](0014-filters-and-extractors-with-closed-handler-signatures.md)): extractor values and
dependencies. The rules:

- **Extractors are declared at the subscription** (`@router.on(Command("/start"),
  ChatType.DIRECT)`), beside the filters, because they also decide whether the handler matches. When
  the resolution plan is compiled, each extractor's result type is matched to the parameter of that
  type and **takes precedence over a provider with the same key**. Two extractors with the same
  result type and no `Qualifier`, an extractor without a consuming parameter, or a parameter with no
  source are check errors.
- **Built-in dependencies** are minimal. Positionally: `Event[P]`. By type: `EventMeta` (transport,
  correlation id, reply channel), `Signals`, `ProcessProfile`, `CorrelationId` from the Core;
  `Runtime` and its client Protocols from the Adapter; plugins add theirs (State → `StateContext`,
  [ADR-0022](0022-state-plugin-model.md)). **The Bot itself is never injected**: reaching every
  dependency through one object makes it a god object and a hidden dependency of every Handler.
  Application services are ordinary providers.
- **Overrides only in tests.** `aiommbot.testing` offers a typed override by key
  (`TestBot(bot).override(KeyValueStore, InMemoryKeyValueStore())`,
  [ADR-0022](0022-state-plugin-model.md)) that re-validates the graph; production code has no
  override API — a different implementation is composed with a different plugin.
- **Execution.** Providers are coroutine functions or cheap synchronous constructions; a blocking
  synchronous Provider declares `sync_to_thread` and runs in the Sync executor
  ([ADR-0030](0030-synchronous-callables-by-explicit-declaration.md)), and an undeclared one is
  caught by the `ASYNC` lint rules. Event-scoped values are created on first request within an event
  and reused by middleware and the handler; clean-up runs in reverse order under an exit stack even
  when the handler raises.

## Considered options

- *Extractors as `Annotated[T, Extract(...)]` on the parameter* — rejected: the matching role of
  an extractor (`NoMatch`) belongs at the subscription, not inside a parameter.
- *Injecting the Bot* — rejected: reopens the door to reaching everything through one object.
- *`override()` in production* — rejected: invites patching dependencies after start.
- *Async-only providers* — rejected: wrapping every data-class constructor in a coroutine is
  noise without benefit.
