# 42. What a host promises a unit whose lifecycle is an asynchronous context manager

**Question.** When a host drives a list of units through `__aenter__`/`__aexit__`, what does a unit
see on the way out, may it suppress the failure, is its teardown bounded in time, and may the host
object be run a second time?

[`32`](32-plugin-lifecycle-failure.md) measured what a host does with a lifecycle failure and
[`41`](41-reporting-which-lifecycle-unit-failed.md) what the failure says. This note measures the
contract in the other direction — what the *unit* is promised, and what the host object is
afterwards.

The decisions this note is evidence for are
[ADR-0074](../adr/0074-a-failed-start-enters-the-same-stop-phase-and-never-retries.md) and
[ADR-0076](../adr/0076-a-bot-runs-once.md).

Findings only, and no recommendation. Sources are primary — project source at the commit named
below, `docs.python.org` and CPython's own source — read on 2026-09-14. Anything a primary source
did not confirm is marked **[unverified]**.

Three of the four answers below are absences, and the absences are the useful part: almost nothing
is promised to a unit, almost nothing bounds it, and the one promise that *is* documented is
contradicted by the primitive most hosts build on.

## 1 What the unit sees on the way out

| Host | what the unit's `__aexit__` receives | suppression honoured | is the cause pushed down |
|---|---|---|---|
| dishka | not `__aexit__` at all — the cause is the value of the unit's own `yield` | impossible by construction | **yes** |
| `contextlib.AsyncExitStack` | recomputed per callback: **the previous unit's failure**, not the original cause | yes for `enter_async_context`; never for `push_async_callback` | only the latest, chained through `__context__` |
| aiohttp cleanup contexts | **always `(None, None, None)`** | ignored — the return value is discarded | no |
| litestar | via `AsyncExitStack`, so the rules above; `on_shutdown` hooks get nothing | managers yes, hooks no | no |
| starlette | one context manager, the real triple, then re-raised | in the ordinary `async with` sense | n/a — a single unit |
| anyio `TaskGroup` | the real triple | **yes**, used to swallow its own cancellation | yes, into the group it raises |

**`AsyncExitStack` does not hand a unit the original cause.** The exit loop rebuilds `exc_details`
from the running exception on every iteration, so when callback *n* raises, callback *n+1* is told
about *n* rather than about whatever ended the run; and a single suppression sets `exc = None` and
blinds every callback below it:

```python
        while self._exit_callbacks:
            is_sync, cb = self._exit_callbacks.pop()
            try:
                if is_sync:
                    cb_suppress = cb(*exc_details)
                else:
                    cb_suppress = await cb(*exc_details)

                if cb_suppress:
                    suppressed_exc = True
                    pending_raise = False
                    exc = None
            except BaseException as new_exc:
                _fix_exception_context(new_exc, exc)
                pending_raise = True
                exc = new_exc
```

([`Lib/contextlib.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/contextlib.py#L759-L815);
`exc_details` is recomputed from `exc` inside the loop.) `push_async_callback` is weaker still — its
wrapper drops all three arguments and returns `None`, so such a callback can neither see the failure
nor suppress it ([same
file](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/contextlib.py#L702-L705)).

**dishka is the one host that deliberately pushes the cause into every unit.** The container's
`close` synthesises the triple and the drain sends the exception into each generator, so a unit can
see *why* it is being torn down:

```python
    async def close(self, exception: BaseException | None = None) -> None:
        await self.__aexit__(None, exception, None)
```

([`async_container.py`](https://github.com/reagento/dishka/blob/929560592f51becf02b2182d5287c3ab87d909bd/src/dishka/async_container.py#L314-L315),
with `await agen.asend(exception)` at
[`:331-333`](https://github.com/reagento/dishka/blob/929560592f51becf02b2182d5287c3ab87d909bd/src/dishka/async_container.py#L326-L351).)
The unit-side contract is documented as `exc = yield conn`, "if an error occurs during process
handling (inside the `with` block), it will be sent to the generator"
([`docs/provider/provide.rst`](https://github.com/reagento/dishka/blob/929560592f51becf02b2182d5287c3ab87d909bd/docs/provider/provide.rst#L40-L50)).
The price is that a generator cannot signal suppression, and that the synthesised triple is
inconsistent: `exc_type` and `exc_tb` are `None` while the exception is not.

**Two documented assumptions exist in the whole corpus, and both are narrow.** aiohttp: "aiohttp
guarantees that cleanup code is called if and only if startup code was successfully finished"
([`docs/web_advanced.rst`](https://github.com/aio-libs/aiohttp/blob/9e08ba02abe573ce9e4cc541d4e3c3646adb43a7/docs/web_advanced.rst#L917)).
dishka: the `exc = yield` line above. **Nobody documents a deadline on a unit's teardown**, and
nobody documents whether the exception a unit sees is the original cause — which, under
`AsyncExitStack`, it demonstrably is not.

## 2 Bounding a teardown in time

| Host | one deadline or per unit | the number, and where it lives | the unit cut short |
|---|---|---|---|
| aiohttp, connections | per unit, one number fanned out | `shutdown_timeout: float = 60.0`; a per-connection fallback of `15.0` | cancelled silently — no record |
| aiohttp, cleanup contexts | **none** — they run outside the deadline entirely | — | unbounded; a hanging unit hangs the process |
| uvicorn | one, for connections and tasks | `timeout_graceful_shutdown: int \| None = None` — **no deadline by default** | cancelled and reported, with the reason in the cancel message |
| taskiq | two separate budgets, tasks then broker | `shutdown_timeout: float = 5`, `wait_tasks_timeout: float \| None = None` | tasks abandoned; the broker cancelled with a WARNING |
| sanic | one budget, decremented across phases | `GRACEFUL_SHUTDOWN_TIMEOUT: 15.0`, environment-overridable | cancelled, then forced; no record |
| dramatiq | one budget, **divided** across joinables | `stop(self, timeout: int = 600000)` | abandoned — the thread keeps running; no record |
| arq | one, for jobs | `job_completion_wait: int = 0`; zero means the handler is not installed | cancelled and reported; `close()` itself unbounded |
| hikari | per unit, hardcoded, websockets only | `asyncio.wait_for(self._ws.close(…), timeout=5)` | reported at DEBUG, then it proceeds |
| celery | neither — a blocking `sleep()` | `soft_shutdown_timeout` defaults to `0.0`, disabled | a WARNING naming the remaining seconds; the blueprint join is unbounded |
| litestar | **none** — confirmed absent from the lifespan path | — | hangs; only an exception surfaces, as `lifespan.shutdown.failed` |
| anyio, trio | primitives only; both group exits are unbounded and self-shielding | `fail_after(delay, shield=False)` | anyio shields its own wait against further cancellation |

**No host in the corpus bounds its extension units' teardown.** aiohttp's `shutdown_timeout` covers
connections, and `AppRunner._cleanup_server()` calls `app.cleanup()` *after and outside* it
([`web_runner.py`](https://github.com/aio-libs/aiohttp/blob/9e08ba02abe573ce9e4cc541d4e3c3646adb43a7/aiohttp/web_runner.py#L365-L366)
and
[`:500-501`](https://github.com/aio-libs/aiohttp/blob/9e08ba02abe573ce9e4cc541d4e3c3646adb43a7/aiohttp/web_runner.py#L495-L505));
litestar's `AsyncExitStack` lifespan has no deadline at all
([`app.py`](https://github.com/litestar-org/litestar/blob/7cccc5e52ce92683a13436a4be8ac77c1ccd1c12/litestar/app.py#L589-L612));
uvicorn's default is `None`
([`config.py`](https://github.com/encode/uvicorn/blob/fa324a415364563cf45908966435e2480a6b46bf/uvicorn/config.py#L237)).

Where a per-unit budget exists it is one configured number fanned out — **never a number the unit
declares**. And **a single `asyncio.timeout` around a whole stop phase has no precedent here**: the
nearest shapes are one-budget-divided, in dramatiq
([`common.py`](https://github.com/Bogdanp/dramatiq/blob/3ccb3562cf4169b7eb6fd64746790c9a88d1cb89/dramatiq/common.py#L128-L141))
and sanic
([`runners.py`](https://github.com/sanic-org/sanic/blob/5ffc7b3710838eaf016d2f9612a86a08626915e5/sanic/server/runners.py#L319-L325)).

## 3 Whether the host object may be run again

| Object | verdict | flag | verbatim refusal |
|---|---|---|---|
| `httpx.Client.__enter__` | single-use | `self._state: ClientState` | `Cannot open a client instance more than once.` · `Cannot reopen a client instance, once it has been closed.` |
| `httpx.Client.send` | refuses after close | `self._state` | `Cannot send a request, as the client has been closed.` |
| `aiohttp.web.Application` | frozen once started | `self._frozen` | `Changing state of started or joined application is forbidden` |
| `aiohttp.ClientSession` | refuses after close | `self._closed` | `Session is closed` |
| `telegram.ext.Application` | refuses a double start; restartable after `stop()` | `_running`, `_initialized` | `This Application is already running!` · `This Application is still running!` |
| `hikari.GatewayBot` | refuses a double start and use when dead | `_closed_event` | `bot is already running` · `bot is not running so it cannot be interacted with` |
| `django.apps.Apps.populate` | reentrancy-guarded, idempotent | `ready`, `loading` under a lock | `populate() isn't reentrant` |
| `anyio.TaskGroup` | strictly single-use | `self._entered` | `TaskGroup cannot be entered more than once` |
| `anyio.CancelScope` | strictly single-use | `self._active` | `Each CancelScope may only be used for a single 'with' block` |
| trio nursery | single-use | `self._closed` | `Nursery is closed to new arrivals` |
| `sqlalchemy.Engine` | **restartable, and documented as such** | the pool is recreated | — |
| dishka containers | restartable, unguarded — a later `get()` silently rebuilds | none | — |
| sanic, redis-py pools, httpcore pools, taskiq brokers, arq, celery, litestar and starlette lifespans, `aiohttp.AppRunner` | restartable, unguarded | — | — |
| `dramatiq.Worker.start()` | neither — a second call **appends more threads** | `self.workers` list | none |

Ten objects refuse reuse with an explicit error, eleven are restartable or unguarded, and one is
silently wrong. **Only SQLAlchemy documents restartability** rather than leaving it implicit: "A new
connection pool is created immediately after the old one has been disposed"
([`engine/base.py`](https://github.com/sqlalchemy/sqlalchemy/blob/482d46a377ce177fc3c553b4dede1f8b6a0951d5/lib/sqlalchemy/engine/base.py#L3144-L3145)).

**The best-worded refusal in the corpus** is httpx's, and it is worth copying for its shape rather
than its words: two different messages selected off one state field, so a double-enter and a
post-close enter are told apart.

```python
    def __enter__(self: T) -> T:
        if self._state != ClientState.UNOPENED:
            msg = {
                ClientState.OPENED: "Cannot open a client instance more than once.",
                ClientState.CLOSED: (
                    "Cannot reopen a client instance, once it has been closed."
                ),
            }[self._state]
            raise RuntimeError(msg)
```

([`_client.py`](https://github.com/encode/httpx/blob/b5addb64f0161ff6bfe94c124ef76f6a1fba5254/httpx/_client.py#L1276-L1285),
with the asynchronous twin at
[`:1991-2000`](https://github.com/encode/httpx/blob/b5addb64f0161ff6bfe94c124ef76f6a1fba5254/httpx/_client.py#L1985-L2005).)
"Once it has been closed" is the half that teaches the lifecycle rule rather than reporting a failed
call. Runner-up for teaching the fix is anyio's `Each CancelScope may only be used for a single
'with' block`
([`_asyncio.py`](https://github.com/agronholm/anyio/blob/51725067e46f39cced7686bc670997ba8b5a7fa9/src/anyio/_backends/_asyncio.py#L423-L425)),
which names the correct usage shape instead of the broken one.

## 4 What the evidence supports

- A unit driven through `AsyncExitStack` is told about its neighbour's failure rather than about the
  cause of the shutdown, and one suppression anywhere in the stack blinds every unit below it. A
  host that wants each unit to see the real cause has to drive the units itself.
- Pushing the cause down to the unit has exactly one precedent, dishka's, and it costs the ability
  to suppress, because the unit is a generator rather than a context manager.
- Suppression is the rule nobody states. aiohttp discards the return value, `push_async_callback`
  cannot express it, litestar honours it for managers and not for hooks, and no host documents which
  it does.
- Extension-unit teardown is unbounded across the whole corpus. Where a deadline exists it covers
  connections or tasks, never plugins, and no unit anywhere declares a budget of its own. The two
  hosts that divide one budget across units subtract elapsed time as they go.
- A run-once application object is a well-populated position — ten of twenty-two — and the shape
  worth copying is httpx's: one state field, and a distinct message for "already open" and for
  "closed once already", so the reader learns the lifecycle and not just that a call failed.
- Leaving the question unanswered is the larger group, and its cost is visible: dramatiq's second
  `start()` silently doubles the thread pool, and dishka's post-`close()` `get()` silently rebuilds
  everything it had just torn down.

## Sources

Every claim above carries its own link inline. This section names what was read.

CPython:

- <https://github.com/python/cpython> — `Lib/contextlib.py`, `Lib/asyncio/taskgroups.py`

Context-manager hosts:

- <https://github.com/aio-libs/aiohttp> — `aiohttp/web_app.py`, `aiohttp/web_protocol.py`,
  `aiohttp/web_runner.py`, `aiohttp/web_server.py`, `docs/web_advanced.rst`
- <https://github.com/agronholm/anyio> — `src/anyio/_backends/_asyncio.py`,
  `src/anyio/_core/_tasks.py`
- <https://github.com/encode/starlette> — `starlette/routing.py`
- <https://github.com/litestar-org/litestar> — `litestar/app.py`, `litestar/_asgi/asgi_router.py`
- <https://github.com/python-trio/trio> — `src/trio/_core/_run.py`
- <https://github.com/reagento/dishka> — `src/dishka/async_container.py`, `src/dishka/container.py`,
  `docs/provider/provide.rst`

Bounded and unbounded teardown:

- <https://github.com/Bogdanp/dramatiq> — `dramatiq/common.py`, `dramatiq/worker.py`
- <https://github.com/celery/celery> — `celery/app/defaults.py`, `celery/worker/worker.py`
- <https://github.com/encode/uvicorn> — `uvicorn/config.py`, `uvicorn/server.py`
- <https://github.com/hikari-py/hikari> — `hikari/impl/rest_bot.py`, `hikari/impl/shard.py`
- <https://github.com/python-arq/arq> — `arq/worker.py`
- <https://github.com/sanic-org/sanic> — `sanic/config.py`, `sanic/server/runners.py`
- <https://github.com/taskiq-python/taskiq> — `taskiq/cli/worker/args.py`,
  `taskiq/cli/worker/run.py`, `taskiq/receiver/receiver.py`

Run once or run again:

- <https://github.com/django/django> — `django/apps/registry.py`
- <https://github.com/encode/httpx> — `httpx/_client.py`
- <https://github.com/hikari-py/hikari> — `hikari/impl/gateway_bot.py`
- <https://github.com/python-telegram-bot/python-telegram-bot> — `src/telegram/ext/_application.py`
- <https://github.com/sqlalchemy/sqlalchemy> — `lib/sqlalchemy/engine/base.py`
