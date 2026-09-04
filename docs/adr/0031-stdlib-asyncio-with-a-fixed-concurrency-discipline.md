---
status: accepted
date: 2026-09-04
ticket: "#22"
---

# The Core runs on standard-library asyncio under a fixed structured-concurrency discipline, and the framework never chooses the event loop

ADR-0004 fixed an asyncio engine but neither the discipline inside it nor who owns the loop. Both
gaps are where real frameworks bleed: Litestar has zero timeouts and no request-level timeout
mechanism at all, Starlette and FastAPI together contain exactly one, uvicorn's default graceful
shutdown waits forever and then loses `lifespan.shutdown()` to SIGKILL, and uvicorn silently prefers
uvloop whenever the import succeeds without logging the decision. The libraries that police
themselves — django-modern-rest and FastStream — enable flake8-async with almost no carve-outs;
Litestar, Starlette and FastAPI do not, and Starlette 0.47.0 had to fix by hand a framework-internal
`def` that was burning a thread token per request. We decided:

- **Standard library only, asyncio only.** `asyncio.TaskGroup`, `asyncio.timeout`, `asyncio.Lock`.
  trio is explicitly unsupported and `anyio` is never a Core dependency (ADR-0008); httpx2 brings
  anyio transitively into the Adapter's extra, which is not a reason to build on it.
- **Every task has a named owner.** A task exists only inside a `TaskGroup` owned by a named
  component; a bare `create_task` or `ensure_future` is a lint error, enforced by the ruff `ASYNC`
  rules already implied by ADR-0011.
- **Every await that touches I/O is under an explicit `asyncio.timeout`.** A timeout never wraps
  `__anext__`: a bounded queue sits between a producer and its consumer, so a cancellation cannot
  finalise an async generator mid-iteration (PEP 789).
- **`CancelledError` is never caught.** Cleanup is `try/finally` and `except*`, and it is bounded in
  time — an unbounded `finally` is how a graceful stop becomes a SIGKILL. `asyncio.shield` is
  permitted in exactly one named place: the drain of ADR-0023.
- **Exception groups are unwrapped without loss.** A solitary exception is lifted out of a
  `BaseExceptionGroup` with `__cause__` and `__context__` preserved before it reaches user-facing
  API; sibling exceptions are never discarded, which is the shortcut Litestar takes and Starlette
  deliberately does not.
- **Two entry points.** `run(*, loop_factory=None)` blocks, owns an `asyncio.Runner`, and is the
  only synchronous `def` of the engine — a process boundary, not a face (it has no twin, so ADR-0029
  does not apply to it). `serve()` is the coroutine for embedding a Bot in a loop the application
  already runs. Start-up remains compose → check → start (ADR-0016).
- **The loop belongs to the application.** No `uvloop`/`winloop` extra, no auto-installation, no
  event-loop policy — that API is deprecated for removal in 3.16. `loop_factory` takes a plain
  `Callable[[], AbstractEventLoop]`, so choosing uvloop costs the application one documented line
  and costs us no dependency. Litestar and django-modern-rest hold the same position; 0.4.8 held the
  opposite one and not one of the eleven bots ever installed the extra, so the capability was
  dormant, never delivered.
- **Free threading is claimed only where it is tested.** The blocking 3.14t job of ADR-0009 covers
  the Core and the sans-I/O parts. The synchronous face makes no thread-safety promise and documents
  one client instance per thread (ADR-0029).

## Considered options

- *`anyio` in the Core for trio support* — rejected: it breaks the single-runtime-dependency rule of
  ADR-0008 and doubles the test matrix for a consumer that does not exist.
- *Our own scheduler Protocol to stay loop-agnostic* — rejected: a third code path with one
  implementation and no user.
- *Automatic uvloop selection, as uvicorn does* — rejected: an unrelated transitive install would
  silently change the event loop, and uvicorn does not even log the decision.
- *An `aiommbot[uvloop]` extra with an explicit flag* — rejected: the same dormant extra, one
  indirection later.
- *Leaving the discipline to the style rulebook* — rejected: rules that only exist in prose are
  enforced by memory; these are enforced by lint rules and reviewed per component document.

## Consequences

- The rules above are what #36 turns into positive rules with do/don't examples, and what every LLD
  answers in its typing-and-async section.
- Deployment documentation must state that the process's graceful-shutdown budget has to exceed the
  ADR-0023 drain deadline, or `lifespan`-equivalent shutdown never runs — uvicorn's default is to
  wait forever and lose it (#40).
