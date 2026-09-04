---
status: accepted
date: 2026-09-04
ticket: "#22"
---

# A Handler or Provider may be synchronous only by an explicit `sync_to_thread` declaration and runs in the Bot's own bounded executor; Filters and Extractors run inline; everything else the framework calls is a coroutine function

The reference set splits three ways: Starlette/FastAPI, FastStream and aiogram decide the colour
themselves and thread synchronous callables with no opt-out; Litestar refuses to guess and requires
`sync_to_thread`, warning in both directions; python-telegram-bot and Falcon refuse synchronous
callables outright — PTB's maintainer sketched the automatic branch in 2021 and deliberately never
shipped it, and Falcon named its inline wrapper `wrap_sync_to_async_unsafe`. Middleware is
asynchronous-only in **every** one of them. For a bot the decisive property is not throughput but
cancellation: neither Python nor the operating system can stop a function already running in a
thread, and `anyio.to_thread.run_sync` defaults to `abandon_on_cancel=False` — documented as
ignoring cancellation in the host task *until the operation has completed*. FastStream's issue
#1648 (reporter's comment of 2024-08-07) shows the price in production: `FastStream app shut down
gracefully.` at 19:04:35, `Done processing message.` at 19:05:52 — seventy-seven seconds later, with
the middleware chain cancelled mid-way and the message going UNACK → READY. The handler's side
effect happened; its acknowledgement never did. Our own evidence: all 225 handlers across eleven
bots are `async def`, and 0.4.8's dispatcher could not have called a synchronous one
(`docs/research/18`). We decided:

- **Explicit declaration, Litestar's design.** `sync_to_thread: bool | None = None` at the
  subscription of a Handler and at the declaration of a Provider. `None` on a synchronous callable
  raises an `AiommbotWarning` asking for a deliberate decision; `True` on a coroutine function
  warns too; `False` means the callable is declared non-blocking and is awaited inline on the loop.
  Both implicit defaults are footguns — inline blocks the loop, threading taxes trivial callables —
  and 225/225 asynchronous handlers means explicitness costs our users nothing.
- **The colour is resolved at registration, not at the first event.** `inspect.iscoroutinefunction`
  (`asyncio.iscoroutinefunction` is removed in 3.16) unwrapping `functools.partial` and testing
  `__call__`, narrowed with `TypeIs`; a mismatch is a Check error in the check phase (ADR-0016).
  aiogram's detection misses callable objects, so such a handler silently never runs (upstream
  #1721, open) — the check phase is where that class of bug dies.
- **Filters and Extractors may be synchronous and always run inline.** They are declared pure, cheap
  predicates and parsers (ADR-0014); threading them is what makes every aiogram magic filter a
  separate serialised thread hop before the handler even starts. PTB's shape — synchronous filters,
  asynchronous handlers — is the right one here.
- **Everything else is a coroutine function**: Middleware, Signal subscribers, plugin lifecycle,
  `RequestObserver`, `Codec`. No reference framework in the set allows synchronous middleware, and
  the two that tolerate synchronous lifecycle hooks run them inline on the loop with no opt-out,
  which is the hazard without the benefit.
- **The Bot owns the executor.** A bounded `ThreadPoolExecutor` belonging to the Bot, its size a
  setting, with a Check that it is not smaller than the worker count of ADR-0023, and `contextvars`
  copied explicitly into each call. Not the loop's default executor and not anyio's limiter: in every
  automatic implementation in the reference set the budget is invisible and unrelated to the
  framework's own backpressure — anyio's arbitrary 40 tokens, undocumented in FastAPI, or CPython's
  `min(32, cpu + 4)`. Starlette 1.4.0 gave gzip its own limiter for exactly this reason.
- **At drain the wait is dropped, the thread is abandoned, and the abandonment is reported.** Nobody
  can stop the thread, so the only real choice is whether the drain waits for it — and waiting turns
  a promised 25-second grace period into an unbounded one. The standard-library
  `loop.run_in_executor` future is therefore dropped on the deadline instead of deferring the
  cancellation as anyio's default does: the drain completes on time (ADR-0023), the abandoned thread
  runs on as a daemon, and a typed `HandlerAbandoned` Signal makes it visible rather than silent.
  The documentation states the contract plainly — **a synchronous Handler must be idempotent,
  because it may be abandoned** — and the reason is the FastStream case above: the danger is not the
  lost thread but the half-finished chain around it.
- **Blocking work inside an asynchronous Handler is the application's `asyncio.to_thread` recipe**
  on the loop's default executor, not our pool. It is one standard-library call, so it fails the
  two-condition admission test (ADR-0002), and routing it through the Bot's executor would let user
  code starve dispatch out of the same budget. Genuinely CPU-bound work belongs in a process pool,
  and the documentation says so.

## Considered options

- *Automatic threading, as Starlette/FastAPI, FastStream and aiogram do* — rejected: it decides for
  the user in both directions and hides the budget. FastAPI's own docs advertise the `def` path
  ("if you just don't know, use normal `def`") while its maintainer's public tips warn that
  exhausting the 40 tokens blocks the application; Litestar's docs call the same mechanism "very
  high overhead, greatly reducing an application's performance".
- *Refusing synchronous handlers, as PTB and Falcon do* — considered and rejected by the maintainer:
  the framework should behave like its peers here, and refusal is the one direction that cannot be
  relaxed later without breaking users.
- *Requiring `sync_to_thread` as a hard registration error* — rejected: a warning already forces the
  decision, and an error would greet a newcomer's first `def` with a traceback.
- *Waiting for in-flight threads at drain* — rejected: the reporter of FastStream #1648 measured
  exactly this and got the answer *"we can't wait forever; sometimes we should decide that the
  broker is dead and kill it"*; a grace period that must exceed the slowest possible handler is not
  a grace period.
- *The loop's default executor* — rejected: ADR-0023 promises N workers and per-kind overflow
  policies, and a shared invisible pool silently overrides both.
- *`anyio.to_thread` with a dedicated limiter* — unavailable: anyio is never a Core dependency
  (ADR-0008), and its default defers the host task's cancellation until the thread finishes.

## Consequences

- `AiommbotWarning` is public API: users filter it, and an environment variable silences the
  implicit-colour warning for a whole project.
- ruff's explained-ignore list (ADR-0011) gains `ASYNC109` — our timeouts are parameters by
  ADR-0026 — and `RUF029`, because a coroutine function here is a contract of the Protocol it
  implements, not a consequence of containing an `await`.
- The executor size, the Check and the `HandlerAbandoned` Signal join the settings model, the Check
  catalogue and the Signal list; the drain contract is a §6 runtime view and a §10 quality scenario.
