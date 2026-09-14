---
status: accepted
date: 2026-09-03
ticket: "#14"
amended-by: [ADR-0058, ADR-0063, ADR-0066, ADR-0069, ADR-0071, ADR-0074]
---

# The Bot starts in three phases — compose, check, start — and stops on the full list of check failures

Django's staged `setup()` and its checks framework are the model
([`docs/research/10`](../research/10-plugin-systems.md)): nothing with side effects runs until the
configuration has been validated as a whole, and problems are reported together.

1. **Compose.** Collect plugin declarations in the order the composition lists them
   ([ADR-0071](0071-plugins-start-in-list-order-and-declare-no-dependency-on-each-other.md)), gather
   contributions (routers, middleware, dependencies, event types, checks), freeze the router tree
   and the middleware chain, build `HandlerSpec`s.
2. **Check.** Run every check without side effects and, if any has severity *error*, stop with the
   **complete list**, not the first failure. A check is a typed object (`id`, `severity`, `message`,
   `hint`). The Core contributes the structural checks (duplicate plugin and handler names, the
   capability a Plugin was handed being the same object the composition lists and listed before it
   ([ADR-0070](0070-plugins-do-not-collaborate-the-composition-hands-one-instance-to-both.md),
   [ADR-0072](0072-duplicate-names-are-refused-and-every-refusal-is-one-catalogue-row.md)),
   dependency cycles, adapter binding, unresolvable handler parameters, unreachable handlers, event
   registry conflicts, the shutdown arithmetic of
   [ADR-0063](0063-the-process-declares-its-shutdown-budget-and-the-bot-bounds-the-stop.md)); the
   Adapter and plugins contribute their own (the in-memory storage backends: a process-local store
   without a single-process declaration is an error,
   [ADR-0066](0066-the-in-memory-backends-own-the-single-process-check.md); Webhook: a
   Callback-token key of sufficient length unless authenticity is explicitly off,
   [ADR-0024](0024-webhook-ingress-and-callback-security.md)).
3. **Start.** Enter plugin lifecycles in the order the composition lists them
   ([ADR-0071](0071-plugins-start-in-list-order-and-declare-no-dependency-on-each-other.md)), then
   start the Transports; stop in reverse. A lifecycle that raises ends the start, and the Bot runs
   the same stop phase a stop signal enters over whatever started
   ([ADR-0074](0074-a-failed-start-enters-the-same-stop-phase-and-never-retries.md)).

The process declares a typed **`ProcessProfile`** — `single_process`, `websocket_consumer` and
`shutdown_budget`
([ADR-0063](0063-the-process-declares-its-shutdown-budget-and-the-bot-bounds-the-stop.md)) — that
checks are evaluated against. Phases 1–2 run without phase 3 as `aiommbot check`, the shipped
command of
[ADR-0058](0058-the-command-is-a-console-script-behind-the-click-extra.md), which exits non-zero on
the full list of failures.

## Considered options

- *Checks inside each plugin's start-up* — rejected: failure halfway through start-up, one error
  at a time.
- *Only Core checks* — rejected: the single-process Check of
  [ADR-0003](0003-stateless-core-state-plugin-with-explicit-backend.md) belongs to the storage
  backend that is process-local
  ([ADR-0066](0066-the-in-memory-backends-own-the-single-process-check.md)), so plugins must be able
  to contribute.
