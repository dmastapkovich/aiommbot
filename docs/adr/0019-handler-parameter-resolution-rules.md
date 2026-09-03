---
status: accepted
date: 2026-09-03
ticket: "#16"
---

# Handler parameters resolve from extractors first, then providers; the Core injects a minimal built-in set and never the Bot; overrides exist only in the testing toolkit

One resolution mechanism serves both sources of handler parameters (ADR-0014): extractor values
and dependencies. The rules:

- **Extractors are declared at the subscription** (`@router.on(Command("/start"), ChatType.DIRECT)`),
  beside the filters, because they also decide whether the handler matches. When the resolution
  plan is compiled, each extractor's result type is matched to the parameter of that type and
  **takes precedence over a provider with the same key**. Two extractors with the same result type
  and no `Qualifier`, an extractor without a consuming parameter, or a parameter with no source
  are check errors.
- **Built-in dependencies** are minimal. Positionally: `Event[P]`. By type: `EventMeta`
  (transport, correlation id, reply channel), `Signals`, `ProcessProfile`, `CorrelationId` from
  the Core; `Runtime` and its client Protocols from the Adapter; plugins add theirs (State →
  `StateContext`). **The Bot itself is never injected**: `bot.state`-style access was the god
  object and hidden dependency of 0.4.8. Application services are ordinary providers, which
  retires the forty-odd hand-written `_deps.py` accessors seen in the fleet.
- **Overrides only in tests.** `aiommbot.testing` offers a typed override by key
  (`TestBot(bot).override(Storage, FakeStorage())`) that re-validates the graph; production code
  has no override API — a different implementation is composed with a different plugin.
- **Execution.** Providers are asynchronous by preference or cheap synchronous constructions;
  blocking synchronous work is the author's responsibility to move off the loop and is caught by
  the `ASYNC` lint rules. Event-scoped values are created on first request within an event and
  reused by middleware and the handler; clean-up runs in reverse order under an exit stack even
  when the handler raises.

## Considered options

- *Extractors as `Annotated[T, Extract(...)]` on the parameter* — rejected: the matching role of
  an extractor (`NoMatch`) belongs at the subscription, not inside a parameter.
- *Injecting the Bot* — rejected: reopens the door to reaching everything through one object.
- *`override()` in production* — rejected: invites patching dependencies after start.
- *Async-only providers* — rejected: wrapping every data-class constructor in a coroutine is
  noise without benefit.
