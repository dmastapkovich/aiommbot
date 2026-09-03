---
status: accepted
date: 2026-09-03
ticket: "#14"
---

# The Bot starts in three phases — compose, check, start — and stops on the full list of check failures

Django's staged `setup()` and its checks framework are the model: nothing with side effects runs
until the configuration has been validated as a whole, and problems are reported together.

1. **Compose.** Collect plugin declarations, resolve `requires`/`after` into a topological order,
   gather contributions (routers, middleware, dependencies, event types, checks), freeze the
   router tree and the middleware chain, build `HandlerSpec`s.
2. **Check.** Run every check without side effects and, if any has severity *error*, stop with the
   **complete list**, not the first failure. A check is a typed object (`id`, `severity`,
   `message`, `hint`). The Core contributes the structural checks (dependency cycles, contract
   versions, adapter binding, unresolvable handler parameters, unreachable handlers, event
   registry conflicts); the Adapter and plugins contribute their own (State: an in-memory backend
   without a single-process declaration is an error; Webhook: a public URL and a secret of
   sufficient length).
3. **Start.** Enter plugin lifecycles in topological order, then transports; stop in reverse.

The process declares a typed **`ProcessProfile`** (at least `single_process`) that checks are
evaluated against; its full field list is designed with the deployment view in #40. A
"check only" entry point runs phases 1–2 and exits, for CI and for operators.

## Considered options

- *Checks inside each plugin's start-up* — rejected: failure halfway through start-up, one error
  at a time.
- *Only Core checks* — rejected: the in-memory-state guard of ADR-0003 belongs to the State
  plugin, so plugins must be able to contribute.
