---
status: accepted
date: 2026-09-04
ticket: "#22"
---

# The Core runs on standard-library asyncio under a fixed structured-concurrency discipline, and the framework never chooses the event loop

The Core is asynchronous throughout — a second, synchronous dispatch path as in Django's WSGI and
ASGI pair would have no host, since the only Transports are asyncio-hosted, and would double every
test — but asyncio alone fixes neither the discipline inside it nor who owns the loop. Both gaps are
where reference frameworks bleed: uvicorn's graceful shutdown has no timeout by default, and it
silently prefers uvloop whenever the import succeeds without logging the decision
([`docs/research/18`](../research/18-execution-model-in-practice.md)). We decided:

- **Standard library only, asyncio only.** `asyncio.TaskGroup`, `asyncio.timeout`, `asyncio.Lock`.
  trio is explicitly unsupported and `anyio` is never a Core dependency
  ([ADR-0008](0008-python-floor-3-12-with-typing-extensions.md)); httpx2 brings anyio transitively
  into the Adapter's extra, which is not a reason to build on it.
- **Every task has a named owner.** A task exists only inside a `TaskGroup` owned by a named
  component; a bare `create_task` or `ensure_future` is a lint error (ruff `RUF006` and the `ASYNC`
  family, [ADR-0011](0011-lint-format-and-architecture-toolchain.md)).
- **Every await that touches I/O is under an explicit `asyncio.timeout`.** A timeout never wraps
  `__anext__`: a bounded queue sits between a producer and its consumer, so a cancellation cannot
  finalise an async generator mid-iteration (PEP 789).
- **`CancelledError` is never caught.** Cleanup is `try/finally` and `except*`, and it is bounded in
  time — an unbounded `finally` is how a graceful stop becomes a SIGKILL. `asyncio.shield` is
  permitted in exactly one named place: the drain of
  [ADR-0023](0023-websocket-gateway-resilience.md).
- **Exception groups are unwrapped without loss.** A solitary exception is lifted out of a
  `BaseExceptionGroup` with `__cause__` and `__context__` preserved before it reaches user-facing
  API; sibling exceptions are never discarded.
- **Two entry points.** `run(*, loop_factory=None)` blocks, owns an `asyncio.Runner`, and is the
  only synchronous `def` of the framework — a process boundary, not a Face (it has no synchronous
  pair, so [ADR-0029](0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) does not apply
  to it). `serve()` is the coroutine for embedding a Bot in a loop the application already runs.
  Start-up remains compose → check → start ([ADR-0016](0016-three-phase-start-with-checks.md)).
- **The loop belongs to the application.** No `uvloop`/`winloop` extra, no auto-installation, no
  event-loop policy — that API is deprecated for removal in 3.16
  ([`docs/research/06`](../research/06-dual-sync-async-api.md)). `loop_factory` takes a plain
  `Callable[[], AbstractEventLoop]`, so choosing uvloop costs the application one documented line
  and costs us no dependency. Litestar holds the same position
  ([`docs/research/18`](../research/18-execution-model-in-practice.md)).
- **Free threading is claimed only where it is tested.** The blocking 3.14t job of
  [ADR-0008](0008-python-floor-3-12-with-typing-extensions.md) covers the Core and the Exchange. The
  synchronous face makes no thread-safety promise and documents one client instance per thread
  ([ADR-0029](0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md)).

## Considered options

- *`anyio` in the Core for trio support* — rejected: it breaks the single-runtime-dependency rule of
  [ADR-0008](0008-python-floor-3-12-with-typing-extensions.md) and doubles the test matrix for a
  consumer that does not exist.
- *Our own scheduler Protocol to stay loop-agnostic* — rejected: a third code path with one
  implementation and no user.
- *Automatic uvloop selection, as uvicorn does* — rejected: an unrelated transitive install would
  silently change the event loop, and uvicorn does not even log the decision.
- *An `aiommbot[uvloop]` extra with an explicit flag* — rejected: the same dormant extra, one
  indirection later.
- *Leaving the discipline to the style rulebook* — rejected: rules that only exist in prose are
  enforced by memory; these are enforced by lint rules and reviewed per component document.

## Consequences

- The rules above are the `ST-ASY` rules of [`engineering-style.md`](../design/engineering-style.md)
  ([ADR-0033](0033-identified-tiered-rules-with-a-derived-review-checklist.md)), and every LLD
  answers them in its typing-and-async section.
- Deployment documentation must state that the process's graceful-shutdown budget has to exceed the
  [ADR-0023](0023-websocket-gateway-resilience.md) drain deadline, or `lifespan`-equivalent shutdown
  never runs — uvicorn's default is to wait forever and lose it (#40).
