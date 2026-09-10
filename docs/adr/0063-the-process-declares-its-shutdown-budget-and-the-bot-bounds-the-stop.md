---
status: accepted
date: 2026-09-10
ticket: "#40"
amends: [ADR-0016, ADR-0023, ADR-0031]
---

# `ProcessProfile` carries three fields, the third being the budget the host gives the process, and the Bot bounds its whole stop phase inside it

[ADR-0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md) requires cleanup to be
bounded in time, yet only the WebSocketTransport's Drain has a deadline
([ADR-0023](0023-websocket-gateway-resilience.md)); plugin stop in reverse topological order has
none, and neither uvicorn nor granian bounds an ASGI lifespan shutdown at all
([`docs/research/29`](../research/29-kubernetes-fields-a-drain-depends-on.md) §10). A budget nobody
compares against a deadline is a comment. We decided:

- **`ProcessProfile` is `single_process`, `websocket_consumer` and `shutdown_budget`.** The first
  two are the roles Checks are already evaluated against
  ([ADR-0003](0003-stateless-core-state-plugin-with-explicit-backend.md),
  [ADR-0023](0023-websocket-gateway-resilience.md)); the third is the time the host promises between
  its stop signal and its kill. This is the full field list
  [ADR-0016](0016-three-phase-start-with-checks.md) deferred here. Its default is **30 s**, which is
  what `terminationGracePeriodSeconds` defaults to (same note, §2).
- **The Bot's `stop_timeout` bounds the whole stop phase**, under one `asyncio.timeout` around the
  Drain, the plugin stops and every close. Its default is `shutdown_budget` less a **2 s** reserve
  for signal delivery and interpreter exit, so the shipped arithmetic is a 25 s Drain inside a 28 s
  stop inside a 30 s budget. On expiry the remaining tasks are cancelled; the Drain's own
  `DrainTimedOut(count)` still reports what it left.
- **One Check of the Bot's, `drain_grace < stop_timeout <= shutdown_budget`.** It is an error, so
  `aiommbot check` ([ADR-0058](0058-the-command-is-a-console-script-behind-the-click-extra.md))
  fails in CI rather than the first rollout failing in production. This is the mechanism that
  discharges ADR-0031's obligation; the deployment view states the same arithmetic for a reader.
- **The profile records a promise, and the framework says so.** No process can read the budget its
  host will actually honour: a delete may shorten it (`deletionTimestamp` "may be shortened"), a
  force deletion removes it, and a node shutdown has a clock of its own (same note, §2). The Check
  compares our deadlines against the declared number and nothing else, and
  [§7](../design/07-deployment-view.md) names the three failures that make the declaration false.

## Considered options

- *A `stop_bound` field on every `PluginSpec`, summed by the Bot* — rejected: an eighth field on a
  frozen declaration, an estimate every plugin author must invent, and a sum that is pessimistic
  because plugins stop in sequence.
- *The Check alone, with the stop phase left unbounded* — rejected: it verifies an arithmetic the
  runtime does not obey, and a plugin whose store has stopped answering still consumes the budget in
  silence.
- *A closed `shape` enumeration instead of the two booleans* — rejected: it forbids compositions the
  design permits, and [ADR-0015](0015-plugin-contract-and-composition.md) makes composition free.
- *Reading the budget from the environment* — rejected: the framework reads no environment variable
  for configuration ([ADR-0015](0015-plugin-contract-and-composition.md)), and no host publishes the
  number to the process in a portable way.

## Consequences

- `ProcessProfile`, `stop_timeout` and the Check are parts of `bot.md`, beside `run()` and
  `serve()`.
- The 2 s reserve is a floor, not a margin for slow plugins: everything a process must do to stop
  belongs inside `stop_timeout`, including an ASGI host's lifespan shutdown when the Bot is embedded
  in one.
