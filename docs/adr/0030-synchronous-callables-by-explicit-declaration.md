---
status: accepted
date: 2026-09-04
ticket: "#22"
amends: [ADR-0014, ADR-0019, ADR-0023]
amended-by: [ADR-0048]
---

# A Handler or Provider may be synchronous only by an explicit `sync_to_thread` declaration and runs in the Sync executor; Filters and Extractors run inline; everything else the framework calls is a coroutine function

The reference frameworks split three ways on a synchronous callable — thread it automatically,
require an explicit declaration, or refuse it — and every one of them keeps Middleware
asynchronous-only ([`docs/research/18`](../research/18-execution-model-in-practice.md)). For a bot
the decisive property is not throughput but cancellation: neither Python nor the operating system
can stop a function already running in a thread, and `anyio.to_thread.run_sync` defaults to
`abandon_on_cancel=False`, deferring the host task's cancellation until the thread completes.
FastStream's issue #1648, in the same note, shows the price in production: a graceful shutdown that
waited seventy-seven seconds for a handler while the middleware chain around it was cancelled, so
the side effect happened and its acknowledgement never did. We decided:

- **Explicit declaration.** `sync_to_thread: bool | None = None` at the subscription of a Handler
  and at the declaration of a Provider. `None` on a synchronous callable raises an `AiommbotWarning`
  asking for a deliberate decision; `True` on a coroutine function warns too; `False` means the
  callable is declared non-blocking and is awaited inline on the loop. Both implicit defaults are
  footguns — inline blocks the loop, threading taxes trivial callables — which is why Litestar
  requires the declaration too; explicitness costs a handler author one keyword.
- **The colour is resolved at registration, not at the first event.** `inspect.iscoroutinefunction`
  (`asyncio.iscoroutinefunction` is deprecated for removal in 3.16,
  [`docs/research/06`](../research/06-dual-sync-async-api.md)) unwrapping `functools.partial` and
  testing `__call__`, narrowed with `TypeIs`; a mismatch is a Check error in the check phase
  ([ADR-0016](0016-three-phase-start-with-checks.md)). aiogram's detection misses callable objects,
  so such a handler silently never runs (aiogram issue 1721,
  [`docs/research/18`](../research/18-execution-model-in-practice.md)) — the check phase is where
  that class of bug dies.
- **Filters and Extractors may be synchronous and always run inline.** They are declared pure, cheap
  predicates and parsers
  ([ADR-0014](0014-filters-and-extractors-with-closed-handler-signatures.md)); threading them is
  what makes every aiogram magic filter a separate serialised thread hop before the handler even
  starts. python-telegram-bot's shape — synchronous filters, asynchronous handlers — is the right
  one here.
- **Everything else is a coroutine function**: Middleware, Signal subscribers, plugin lifecycle,
  `RequestObserver`, `Codec`. The one paired exception is the synchronous client's own observer,
  `SyncRequestObserver`, where the colour follows the face as it does for `SyncHTTPTransport`
  ([ADR-0048](0048-observability-is-not-a-core-seam.md)). No reference framework in the set allows
  synchronous middleware, and
  the two that tolerate synchronous lifecycle hooks run them inline on the loop with no opt-out,
  which is the hazard without the benefit.
- **The Bot owns the Sync executor.** A bounded `ThreadPoolExecutor` belonging to the Bot, its size
  a setting, with a Check that it is not smaller than the Dispatch concurrency of
  [ADR-0023](0023-websocket-gateway-resilience.md), and `contextvars` copied explicitly into each
  call. Not the loop's default executor and not anyio's limiter: in every automatic implementation
  in the reference set the budget is invisible and unrelated to the framework's own backpressure —
  anyio's arbitrary 40 tokens, undocumented in FastAPI, or CPython's `min(32, cpu + 4)`; Starlette
  1.4.0 gave gzip its own limiter for exactly this reason
  ([`docs/research/18`](../research/18-execution-model-in-practice.md)).
- **At the Drain the wait is dropped, the thread is abandoned, and the abandonment is reported.**
  Nobody can stop the thread, so the only real choice is whether the Drain waits for it — and
  waiting turns a promised 25-second grace period into an unbounded one. The standard-library
  `loop.run_in_executor` future is therefore dropped on the deadline instead of deferring the
  cancellation as anyio's default does: the Drain completes on time
  ([ADR-0023](0023-websocket-gateway-resilience.md)), the abandoned thread runs on as a daemon, and
  a typed `HandlerAbandoned` Signal makes it visible rather than silent. The documentation states
  the contract plainly — **a synchronous Handler must be idempotent, because it may be abandoned** —
  and the reason is the FastStream case above: the danger is not the lost thread but the
  half-finished chain around it.
- **Blocking work inside an asynchronous Handler is the application's `asyncio.to_thread` recipe**
  on the loop's default executor, not our pool. It is one standard-library call, so it fails the
  two-condition admission test ([ADR-0002](0002-core-scope-two-condition-test.md)), and routing it
  through the Sync executor would let user code starve dispatch out of the same budget. Genuinely
  CPU-bound work belongs in a process pool, and the documentation says so.

## Considered options

- *Automatic threading, as Starlette/FastAPI, FastStream and aiogram do* — rejected: it decides for
  the user in both directions and hides the budget.
- *Refusing synchronous handlers, as PTB and Falcon do* — considered and rejected by the maintainer:
  the framework should behave like its peers here, and refusal is the one direction that cannot be
  relaxed later without breaking users.
- *Requiring `sync_to_thread` as a hard registration error* — rejected: a warning already forces the
  decision, and an error would greet a newcomer's first `def` with a traceback.
- *Waiting for in-flight threads at the Drain* — rejected: FastStream #1648 is the record of exactly
  this wait; a grace period that must exceed the slowest possible handler is not a grace period.
- *The loop's default executor* — rejected: [ADR-0023](0023-websocket-gateway-resilience.md)
  promises a Dispatch concurrency of N and per-kind overflow policies, and a shared invisible pool
  silently overrides both.
- *`anyio.to_thread` with a dedicated limiter* — unavailable: anyio is never a Core dependency
  ([ADR-0008](0008-python-floor-3-12-with-typing-extensions.md)), and its default defers the host
  task's cancellation until the thread finishes.

## Consequences

- `AiommbotWarning` is part of the Public surface: users filter it, and an environment variable
  silences the implicit-colour warning for a whole project.
- The explained ruff ignores this decision needs, `ASYNC109` and `RUF029`, are recorded with their
  reasons in [ADR-0011](0011-lint-format-and-architecture-toolchain.md).
- The Sync executor's size, the Check and the `HandlerAbandoned` Signal join the settings model, the
  Check catalogue and the Signal list; the Drain contract is a §6 runtime view and a §10 quality
  scenario.
