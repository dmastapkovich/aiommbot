---
status: accepted
date: 2026-09-03
ticket: "#17"
---

# Middleware is an asynchronous chain in two named layers with typed outcomes, typed Event-scope publication and typed handler flags

aiogram's `(handler, event, data)` contract passes an untyped dictionary the checkers cannot see;
0.4.8 auto-wired a reliability stack nobody used. We decided the following model
(Chain of Responsibility, ADR-0006):

- **Two named layers.** **Inbound** middleware runs on every event before the router walk
  (dedup, state isolation, correlation, inbound metrics). **Handler** middleware wraps the matched
  handler and knows it (timeouts, permissions, rate limits). Both register globally on the Bot
  and on any Router for its subtree; a router's Inbound layer applies when the walk enters that
  subtree. The names replace aiogram's "outer/inner".
- **Contract.** A middleware is a class with `async def __call__(self, event, call_next, *deps)
  -> Outcome`. `call_next(event)` returns the typed `Outcome` (`Handled | Unhandled`, plus the
  failure variant decided in ADR-0021). App-scoped dependencies arrive through the constructor
  via providers; Event-scoped ones by annotation on `__call__`, with a resolution plan compiled
  like a handler's (ADR-0018). Middleware is asynchronous only; there is no `data: dict`.
- **Allowed moves.** Return an `Outcome` without calling `call_next` (short-circuit: dedup, ban,
  rate limit); pass a derived envelope with enriched `meta` (events are immutable); wrap the call
  in a timeout, lock or retry; publish Event-scope values; observe the outcome. **Not allowed:**
  choosing another handler or altering the payload — routing belongs to routers and filters.
  Calling `call_next` twice is an error.
- **Typed publication instead of `data`.** A middleware declares `provides = (CurrentUser, …)` and
  writes each key once into the Event scope; handlers receive the value by annotation through
  the ordinary plan. The check phase knows every key's source: a handler that needs `CurrentUser`
  with no providing middleware on its path, or a second write of a key, is a start-up error.
- **Flags.** After a match the Core publishes `MatchedHandler` (the `HandlerSpec` and the resolved
  extractor values) into the Event scope. Handlers parametrise middleware with **typed flags**
  declared by the middleware or plugin and passed at the subscription
  (`@router.on(..., flags=[Timeout(30), RequiresRole("admin")])`); flags are stored in
  `HandlerSpec` by type. A flag with no consuming middleware in the stack is a check error.
- **Ordering.** The application lists its middleware explicitly, first = outermost (as Starlette).
  Plugins contribute through `ContributesMiddleware` with a declaration: layer, name, `before`/
  `after` by name. The final order is topological, a cycle is a check error, the stack is frozen
  at start and exposed as data (`bot.middleware()`), so the order is read, not inferred.

## Considered options

- *Single layer around the handler* — rejected: dedup and state isolation must also cover events
  that match nothing.
- *`(handler, event, data)` functions* — rejected: untyped dictionary (ADR-0006, ADR-0014).
- *Phase hooks (before/after/on_error) without wrapping* — rejected: cannot wrap a call in a
  timeout, lock or retry.
- *Numeric priorities* — rejected as for handlers (ADR-0013).
- *Free mutation of payloads* — rejected: handlers must trust what they receive.
