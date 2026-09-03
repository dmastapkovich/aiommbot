---
status: accepted
date: 2026-09-03
ticket: "#15"
---

# Handlers subscribe by annotation on a router tree walked depth-first to the first match, with a typed outcome and start-up reachability checks

Routing must be deterministic, readable from the code, extensible by plugins without touching
the router, and introspectable as data (ADR-0006, idea #34). We decided:

- **Type-driven subscription.** The Core has one registration point, `@router.on(*filters)`,
  which infers the event kind from the annotation of the handler's first parameter
  (`event: Event[Posted]`). The Adapter adds thin, statically typed aliases for readability
  (`@router.message(...)`, `@router.action(...)`, `@router.dialog(...)`) that reduce to `on`.
  Adding an event kind never changes the router.
- **Router tree, depth-first, first match wins.** `Router.include(child)` builds a tree and
  rejects cycles and re-attachment; a router may carry its own filter gates. Dispatch walks the
  tree in registration order; the first handler whose filters and extractors all pass runs and
  ends the walk. There are no numeric priorities: order is local to the code that declares it.
- **Typed dispatch outcome.** Dispatch returns `Handled | Unhandled`, not sentinel objects. An
  unhandled event completes quietly — a bot receives hundreds of server events it does not care
  about — but passes through an observability hook carrying the event name and never its
  content. A fallback is an ordinary handler without filters registered last. A handler may
  raise `Skip` to let the walk continue with the next candidate; this is documented as the rare
  exception it is.
- **Handlers are data.** Registration builds a frozen `HandlerSpec`: name, router path, event
  kind, filters and extractors rendered as data with a readable description, declared
  dependencies, docstring, module and line, and metadata flags for middleware. The tree freezes
  at start-up and is exposed as `bot.routes()` for the testing toolkit, start-up checks and the
  handler catalogue.
- **Fail closed on unreachable handlers.** At freeze time, a handler with no filters and no
  extractors followed in walk order by other handlers of the same kind makes them unreachable;
  that is a configuration error and start-up stops. General shadowing between arbitrary filters
  is undecidable and left to the testing toolkit (`assert_matches(event, handler)`).

## Considered options

- *Per-kind decorators only (aiogram, 0.4.8)* — rejected: O(kinds) decorators and no seam for
  plugin-defined kinds.
- *Numeric priorities* — rejected: they make order non-local and are the usual source of "why
  did this handler fire" bugs.
- *Pub/sub, all matching handlers run (hikari)* — rejected: a chat message deserves one answer.
- *`UNHANDLED`/`REJECTED` sentinels* — rejected in favour of a typed result object.
