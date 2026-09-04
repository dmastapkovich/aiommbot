# Dual sync/async API from one implementation: state of the art (Sep 2026)

> **Superseded in part.** §6.3 below recommends generating the synchronous REST client with
> `unasync`. Ticket #22 rejected that on later evidence — the tooling survey, the reference-set
> comparison and the mining of 0.4.8's own synchronous surface in
> [`18-execution-model-in-practice.md`](18-execution-model-in-practice.md) — and decided a sans-I/O
> core with two thin hand-written drivers instead
> ([ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md)). The findings
> in §1–§5 stand and are what that decision was argued from; only the recommendation in §6.3
> changed. §6.1 (async-only WebSocket runtime), §6.2 (sans-I/O core) and §6.4 (accept both handler
> colours) were adopted, the last one narrowed by
> [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md).

Research date: 2026-09-02. Primary sources only: library source (GitHub at the URLs in *Sources*, or the
locally installed wheels named inline: httpcore 1.0.9, httpx 0.28.1, anyio 4.12.1, urllib3 2.6.3,
starlette 0.51.0, h11 0.16.0, pymongo 4.17.0), official docs, PEPs. Values quoted from source are in
backticks; anything I could not open or confirm is marked **[unverified]**. Line counts are `wc -l` on the
installed wheels unless stated otherwise.

Question: how do modern Python libraries expose BOTH a sync and an async API from ONE implementation
without two hand-maintained code paths, and what should a bot framework whose hot path is an async
WebSocket consumer do? (Context: the aiommbot README promises "Async and sync, without copy-paste. One
implementation, two faces.")

Short answer: nobody has a free lunch. The field has converged on three real mechanisms — (1) a
sans-I/O protocol core with thin I/O drivers, (2) async-as-source-of-truth plus token-level code
generation of the sync twin (`unasync`), and (3) runtime bridging through threads (`BlockingPortal`,
`to_thread`) or greenlets (SQLAlchemy). The freshest large-scale example, PyMongo 4.9+, uses (2) for
~20k lines *and* for its test suite, and MongoDB is retiring Motor because of it. Hand-written twins
(httpx, redis-py, websockets' `sync` module) are still common and are the honest baseline to beat.

## 1. Sans-I/O core + thin drivers

**The manifesto** (sans-io.readthedocs.io): "By implementing network protocols without any I/O and
instead operating on bytes or text alone, libraries allow for reuse by other code regardless of their
I/O decisions." The user "drive[s] the network interactions themselves". Listed implementations
include h11, h2/hpack, wsproto, aioquic, jeepney.

**h11 0.16.0** (`h11/_connection.py`) is the canonical shape: `Connection.receive_data(data: bytes) ->
None` (line 364), `next_event() -> Event | type[NEED_DATA] | type[PAUSED]` (438), `send(event: Event)
-> bytes | None` (514, with `@overload`s), `start_next_cycle()` (235). The module header says it
contains "no networking code at all, loosely modelled on hyper-h2's ... `H2Connection`". **wsproto**
(README) is the same triad: `ws.receive_data(bytes)`, `ws.events()`, `ws.bytes_to_send()`.

**websockets** ships one sans-I/O `protocol.Protocol` (`receive_data`, `events_received`,
`data_to_send`, `close_expected`, `send_text/send_binary/send_close/send_ping/send_pong` — docs
`howto/sansio.rst`) and *two hand-written I/O layers on top of it*:

- `src/websockets/asyncio/connection.py` (~1,000 lines **[approximate, from fetched file]**):
  `Connection(asyncio.Protocol)`; `data_received()` feeds `self.protocol.receive_data(data)`, then
  `events_received()`; `send_context()` is an async CM that wraps `protocol.send_*` and flushes
  `protocol.data_to_send()` to the transport; futures for `send_in_progress`, `pending_pings`,
  `connection_lost_waiter`, `drain_waiters`.
- `src/websockets/sync/connection.py` (~1,100 lines **[approximate]**): a daemon thread runs
  `recv_events()` doing `socket.recv(self.recv_bufsize)` → `protocol.receive_data` under a
  `protocol_mutex: threading.Lock`; `recv_flow_control` lock for backpressure; `send_context()` is a
  `@contextlib.contextmanager` with the same shape; a keepalive thread; close deadlines.

The docs' feature matrix shows "asyncio (new)" and "threading" at near parity while the "Sans-I/O" row
lacks sockets, timeouts, keepalive and broadcast. Lesson: the protocol state machine is shared, but
*each* I/O face still costs ~1k lines of hand-written concurrency code with its own bugs; sans-I/O
removes protocol duplication, not I/O-layer duplication.

**httpcore 1.0.9** combines sans-I/O (h11/h2 inside `http11.py`/`http2.py`) with a two-flavoured
substrate: `_backends/base.py` defines `NetworkStream/NetworkBackend` (`read/write/close/start_tls`,
`connect_tcp/connect_unix_socket/sleep`) and `AsyncNetworkStream/AsyncNetworkBackend` (same names,
`async def`, `aclose`); `_synchronization.py` (318 lines) defines `AsyncLock/AsyncThreadLock/AsyncEvent/
AsyncSemaphore/AsyncShieldCancellation` that pick `trio.*` or `anyio.*` via `sniffio` at `setup()`,
and `Lock/ThreadLock/Event/Semaphore/ShieldCancellation` on `threading`. Shared, hand-written once:
`_models.py` (516 lines), `_synchronization.py`, backends. Duplicated: `_async/` and `_sync/` are
**each exactly 2,497 lines**; `diff _async/connection_pool.py _sync/connection_pool.py` yields 116
changed lines, all token-level (`AsyncConnectionPool`→`ConnectionPool`, `AsyncEvent`→`Event`,
`await` removed). That duplication is *generated*, see §2.

**httpx 0.28.1** does NOT generate: `scripts/` has no unasync script. `_client.py` (2,019 lines) has a
shared `BaseClient` (lines 188–593: `build_request`, `_merge_url/_merge_headers/_merge_cookies`,
redirect logic, `_build_request_auth`), then `Client` (594–1306, 713 lines) and `AsyncClient`
(1307–2019, 714 lines) written by hand. Applying a naive 18-token unasync map to `AsyncClient` and
diffing against `Client` leaves only 59 residual lines — docstrings, `auth.sync_auth_flow`/`next` vs
`auth.async_auth_flow`/`__anext__`/`asend`, `StopIteration` vs `StopAsyncIteration`. I.e. httpx carries
~700 lines of near-mechanical duplication by hand, kept in sync by review. The transport split
(`BaseTransport.handle_request` / `AsyncBaseTransport.handle_async_request`) and shared
`Request`/`Response` models are what make the sync face cheap to *use* from other libraries.

## 2. Code generation (unasync / synchro)

**`unasync`** (python-trio; PyPI 0.6.0, released 2024-05-03, `python>=3.8`). Tokenize-based, not regex:
it rewrites NAME (and STRING) tokens via a replacement dict, drops `async`/`await` tokens (so `async
with`/`async for` become `with`/`for`), and applies an automatic `Async*`→`Sync*` prefix rule. Default
`_ASYNC_TO_SYNC` = `{"__aenter__": "__enter__", "__aexit__": "__exit__", "__aiter__": "__iter__",
"__anext__": "__next__", "asynccontextmanager": "contextmanager", "AsyncIterable": "Iterable",
"AsyncIterator": "Iterator", "AsyncGenerator": "Generator", "StopAsyncIteration": "StopIteration"}`.
API: `Rule(fromdir, todir, additional_replacements=None)`; `unasync_files(paths, rules)`; setuptools
hook `cmdclass={'build_py': unasync.cmdclass_build_py()}` (generate at build time) — though every
large user below commits the generated tree instead and checks it in CI.

**httpcore** — `scripts/unasync.py` (regex, line-based, its own 20-pair `SUBS`: `AutoBackend`→
`SyncBackend`, `async def`→`def`, `await ` removed, `aclose`→`close`, `aiter_stream`→`iter_stream`,
`aread`→`read`, `@pytest.mark.anyio`/`@pytest.mark.trio` deleted). Maps `httpcore/_async`→
`httpcore/_sync` **and `tests/_async`→`tests/_sync`**; `--check` re-derives and exits 1 on mismatch;
also exits 1 if any `SUBS` pattern went unused (dead-rule guard).

**PyMongo 4.17.0** (`tools/synchro.py`, docstring: "Synchronization of asynchronous modules. Used as
part of our build system to generate synchronous code.") is the freshest large-scale case:

- Source of truth is async: `pymongo/asynchronous/` (25 files, 20,173 lines) → `pymongo/synchronous/`
  (25 files, 20,117 lines); same for `gridfs/asynchronous`→`gridfs/synchronous` and
  **`test/asynchronous/`→`test/`**. 65 top-level modules (`network_layer.py`, `lock.py`,
  `pool_shared.py`, `helpers_shared.py`, ...) hold code that is written once, e.g. `network_layer.py`
  has both `async def async_receive_message(...)` and `def receive_message(...)`, and
  `AsyncNetworkingInterface`/`NetworkingInterface` over a `NetworkingInterfaceBase`.
- `unasync_directory(files, src, dest, replacements)` → `unasync_files(files, [Rule(fromdir=src,
  todir=dest, additional_replacements=replacements)])`, with ~100 explicit names
  (`"AsyncMongoClient": "MongoClient"`, `"AsyncCursor": "Cursor"`, `"async_sendall": "sendall"`,
  `"asynchronous": "synchronous"`, ...).
- Custom passes: `apply_is_sync()` flips a mandatory module constant `_IS_SYNC = False`→`True` (and
  raises "Missing _IS_SYNC at top of async file" otherwise); `translate_coroutine_types()` rewrites
  `Coroutine[X, Y, Z]`→`Z` and `Awaitable[X]`→`X` with regexes; `asyncio.sleep(0)` lines are deleted;
  "an async"→"a" in docstrings. Behavioural forks live behind the flag in the *shared* source, e.g.
  `mongo_client.py:907` `if _IS_SYNC and connect: self._get_topology()  # type: ignore[unused-coroutine]`
  — the flag is what lets one file be both, and that `type: ignore` is the visible typing cost.
- Tests: converted wholesale except an explicit async-only list (`test_locks.py`,
  `test_concurrency.py`, `test_async_cancellation.py`, `test_async_loop_safety.py`,
  `test_async_contextvars_reset.py`, `test_async_loop_unblocked.py`, `test_async_network_layer.py`).
- Process: CONTRIBUTING.md — "All modifications within `pymongo` must be made in either the
  top-level `pymongo` directory when they have to exhibit differing behavior between sync and async
  contexts or the `pymongo/asynchronous` directory, not `pymongo/synchronous`. Any changes made
  directly to files in the `pymongo/synchronous` directory will be overwritten by the `synchro` hook".
  A pre-commit hook (`synchro`) fails if a sync file changes without its async twin
  (`OVERRIDE_SYNCHRO_CHECK=1` to bypass); in CI, `git diff --name-only -- <generated>` non-empty →
  "Sync files are out of date. Run `just lint --all-files synchro` to regenerate" and exit 1.
- Consequence: Motor (README) "deprecated as of May 14th, 2025", bug fixes until "May 14th, 2026",
  critical fixes until "May 14th, 2027"; migration target is the PyMongo Async API.

**elasticsearch-py** — `utils/run-unasync.py` converts `elasticsearch/_async/client/`→
`elasticsearch/_sync/client/` and `helpers/vectorstore/_async/`→`_sync/` with
`additional_replacements` (`AsyncTransport`→`Transport`, `AsyncElasticsearch`→`Elasticsearch`,
`async_bulk`→`bulk`, `_async`→`_sync`; `AsyncSearchClient` deliberately kept), a `sed
'/^import asyncio$/d'` pass, then black/isort, then `diff` in check mode. Tests are **not**
generated: `test_elasticsearch/test_async/` is a separate hand-written suite. **opensearch-py**: no
`run-unasync.py` in `utils/` (only `generate_api.py`, template-based) **[unverified beyond the
directory listing]**.

**urllib3** — the 2018 RFC (#1323, "we maintain one copy of the code – the version with async/await
annotations – and then a little script maintains the synchronous copy by automatically stripping
them out again") became `python-trio/hip`, archived 2022-04-14 ("async support is still experimental
and untested"). urllib3 2.x shipped sync-only: `src/urllib3` on `main` has no `_async`/`_sync`
directories; the local 2.6.3 wheel contains `async def` only in `contrib/emscripten/fetch.py`.

**redis-py** — the opposite choice: `redis/asyncio/client.py` (~2,100 lines) is a hand-written twin
of `redis/client.py` ("Added ASYNC support, merging with aioredis", 4.2.0rc1, 2022-02-22). Sharing is
by mixins, not codegen: `class Redis(AbstractRedis, AsyncRedisModuleCommands, AsyncCoreCommands,
AsyncSentinelCommands)` reuses `redis.commands`, `redis._parsers`, `redis.connection`. Command
*encoding* is shared; connection/pipeline/pubsub logic is duplicated by hand.

Typing of generated code: the output is as typed as the input because tokens are renamed, not
erased; the only rough edges are return annotations (`Awaitable[T]`→`T`, PyMongo's regex) and
flag-guarded branches (`# type: ignore[unused-coroutine]`). Every generator above commits the
output, so type checkers, IDEs and tracebacks see ordinary Python files.

## 3. Runtime bridging

Here one implementation exists (usually async) and the other face is produced *at run time*.

**Thread hand-off (async core, sync face).** anyio 4.12.1 `from_thread.run(func, *args, token=None)` →
`token.backend_class.run_async_from_thread(...)`; without a `token: EventLoopToken` (added 4.11.0) it
must be called from an AnyIO worker thread (`MissingTokenError`). `BlockingPortal.call()` is
`self.start_task_soon(func, *args).result()` → `_spawn_task_from_thread` → `run_sync(partial(
self._task_group.start_soon, ...), self._call_func, ..., token=self._token)`; `_call_func` awaits the
result inside a `CancelScope` so cancelling the `concurrent.futures.Future` cancels the task. Typing
is done with two `@overload`s: `Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]]` and
`Callable[[Unpack[PosArgsT]], T_Retval]`, both returning `T_Retval`. `start_blocking_portal()` starts a
daemon `Thread` that runs `run_eventloop(run_portal, backend=...)` and hands back the portal via a
`Future`; `wrap_async_context_manager()` and `BlockingPortalProvider` exist for `with`-blocks and for
sharing one portal across many sync calls. Docs: default worker-thread limiter is 40; an abandoned
thread "will still continue running – only its outcome will be ignored"; the context is copied to the
worker thread, changes do not propagate back. **asyncer** `syncify(async_fn, raise_sync_error=True)`
is a typed (ParamSpec) wrapper over `anyio.from_thread.run` that must be called from a worker thread;
`raise_sync_error=False` falls back to `anyio.run` when no loop exists. **asgiref** `AsyncToSync`
refuses `"You cannot use AsyncToSync in the same thread as an async event loop - just await the async
function directly."`; otherwise it reuses an outer loop via `call_soon_threadsafe` + a
`CurrentThreadExecutor`, or runs `asyncio.run()` in a fresh thread; `SyncToAsync(thread_sensitive=True)`
serialises all sync work onto one executor thread and copies `contextvars`. **Trio**:
`to_thread.run_sync(abandon_on_cancel=, limiter=)` with `DEFAULT_LIMIT = 40`; `from_thread.run` needs
a `trio_token` or a `to_thread` thread and raises `"this is a blocking function; call it from a
thread"` on the Trio thread itself.

**Greenlet (sync core, async face — SQLAlchemy 2.0).** `lib/sqlalchemy/util/concurrency.py`:
`greenlet_spawn(fn, ...)` runs the sync function inside `_AsyncIoGreenlet`; whenever the DBAPI layer
needs I/O it calls `await_only(awaitable)`, which does `current.parent.switch(awaitable)`; the driver
loop `while not context.dead: result = await ...` awaits whatever was switched out and switches the
value back in. Outside a greenlet it raises `"greenlet_spawn has not been called; can't call await_()
here. Was IO attempted in an unexpected place?"`. Docs: "There is no 'thread executor' or any
additional waiters or synchronization in use", but the design is "controversial" because "any
programming statement that can potentially result in IO being invoked **must** have an `await`", so
lazy loading/deferred columns fail under `AsyncSession`, and `greenlet` is a C extension "installed
by default on common machine platforms" only. **greenback** generalises this (`ensure_portal()`,
`await_()`); README: slower per task, unusable with C extensions that hold C stack pointers, in
finalizers, signal handlers or weakref callbacks.

**Measured cost** (my micro-benchmark, Python 3.14.7, anyio 4.12.1, macOS arm64, single run, no-op
callee; order-of-magnitude only): direct `await` 0.10 µs; `asyncio.to_thread(sync_noop)` 49.7 µs;
`anyio.to_thread.run_sync` 79.5 µs; `BlockingPortal.call(async_noop)` from a foreign thread 49.9 µs;
`asyncio.run()` per call 133 µs; `asyncio.Runner.run()` reused 40.7 µs. Bridging is ~500× a direct
await but still ≥10× cheaper than one network round trip, so it is fine for scripts and wrong for
hot paths.

**No-sync libraries.** aiohttp offers no sync client (its docs have only `async` APIs) **[absence
claim, unverified as an explicit statement]**; aiogram has no sync face; Trio has none by design.

## 4. Language-level help and typing tricks

- **`asyncio.Runner`** (3.11+; `Runner(*, debug=None, loop_factory=None)`, `run(coro, *, context=None)`,
  `close()`, `get_loop()`): a reusable embedded loop + `contextvars.Context`; lazy-initialised; signal
  handling only on the main thread. In 3.14 the policy system (`get/set_event_loop_policy`,
  `AbstractEventLoopPolicy`, ...) is deprecated for removal in 3.16 — "Users should use `asyncio.run()`
  or `asyncio.Runner` with *loop_factory*". This is the sanctioned way to give a sync script a
  long-lived loop without a second thread (40 µs/call above vs 133 µs for `asyncio.run` per call).
- **`asyncio.iscoroutinefunction()`** is deprecated (removal 3.16) → `inspect.iscoroutinefunction()`.
  Any "is this handler async?" check must use `inspect` (and unwrap `functools.partial`, as Starlette
  does).
- **`TaskGroup`** (3.11), **`eager_task_factory`** ("Immediate execution of the coroutine is a semantic
  change"), 3.14 **PEP 779** "Free-threaded Python is officially supported", `InterpreterPoolExecutor`,
  `python -m asyncio ps/pstree`, `create_task(**kwargs)`. Free-threading does not create a sync API,
  but it makes the *threaded* face (websockets `sync`, `to_thread`) genuinely parallel; see
  `04-modern-python-library-engineering-2026.md` §1 for the version table.
- **`@overload` on the callable's type** (anyio `BlockingPortal.call`, above) types "sync or async
  callable → T" cleanly. **`TypeIs` narrowing**: Starlette 0.51.0 `_utils.is_async_callable(obj:
  AwaitableCallable[T]) -> TypeIs[AwaitableCallable[T]]` (unwraps `functools.partial`), used in
  `routing.request_response`: `func if is_async_callable(func) else functools.partial(run_in_threadpool,
  func)`; `concurrency.run_in_threadpool(func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T`
  is `await anyio.to_thread.run_sync(func)`; `iterate_in_threadpool` pumps sync iterators one `next`
  per hop. FastAPI docs: "When you declare a *path operation function* with normal `def` instead of
  `async def`, it is run in an external threadpool that is then awaited" — same for `def` dependencies,
  with the warning that this costs more, not less, than `async def` for trivial functions.
- **aiogram** does the same for handlers: `CallableObject.__post_init__` sets `self.awaitable =
  inspect.isawaitable(callback) or inspect.iscoroutinefunction(callback)`; `call()` does `if
  self.awaitable: return await wrapped()` else `return await asyncio.to_thread(wrapped)`.
- **Awaitable method objects** (aiogram, third approach): `class TelegramMethod(BotContextController,
  BaseModel, Generic[TelegramType], ABC)` with `__api_method__`/`__returning__` and `def __await__(self)
  -> Generator[Any, None, TelegramType]: ... return self.emit(bot).__await__()`, `async def emit(self,
  bot) -> TelegramType: return await bot(self)`. The request is a pure data object; I/O is decided by
  whoever consumes it. aiogram only consumes it asynchronously, but the shape is exactly a sans-I/O
  REST request and would accept a sync consumer for free.
- **`@overload` on a `sync: bool` flag** returning `T | Awaitable[T]`: I found no major library using
  it **[unverified]**; the union return leaks to every caller and defeats strict checkers, so it is
  listed only to be rejected. **Paired `Protocol`s** (`RequestInterface`/`AsyncRequestInterface`,
  `NetworkBackend`/`AsyncNetworkBackend` in httpcore) are fine, but only codegen keeps the pair in step.

## 5. Cost model per approach

| Approach (exemplar) | Typing under strict checkers | Test duplication | Contributor burden | Runtime overhead / call | Debuggability | Streams / iterators / CMs | User handlers (sync or async) |
|---|---|---|---|---|---|---|---|
| Sans-I/O core + hand-written drivers (h11, wsproto, websockets, httpx `Client`/`AsyncClient`) | Excellent; plain code | Core tested once; each driver needs its own I/O tests (websockets: two ~1k-line layers) | Edit core once; every driver edited twice (httpx: ~700 near-identical lines by hand) | None | Best: ordinary stack traces | Natural in each face; state machine unaware of them | N/A (library layer) |
| Async source + `unasync` codegen (httpcore, PyMongo, elasticsearch-py) | Good; output is real typed Python; warts: `Awaitable[T]`→`T` regex, `_IS_SYNC` branches with `type: ignore` | Generate tests too (httpcore, PyMongo) or hand-write sync tests (elasticsearch-py) | Edit `_async/` only; CI `--check` + pre-commit guard; must design names so tokens map 1:1 | None | Good: generated files are committed and readable; traceback points into `_sync/` | Mechanical: `async for`→`for`, `__aiter__`→`__iter__`, `asynccontextmanager`→`contextmanager` | N/A |
| Thread bridge (anyio `BlockingPortal`, asyncer, asgiref) | Good (`ParamSpec`/overloads) | One suite; add thread/cancellation tests | Zero duplication | ~50 µs + a second thread/loop; 40-thread limiter | Worse: cross-thread stacks, cancellation cannot stop a running thread | CMs via `wrap_async_context_manager`; iterators need per-item hops | This is how Starlette/FastAPI/aiogram run sync handlers |
| Greenlet (SQLAlchemy `greenlet_spawn`/`await_only`, greenback) | Sync core typed normally; async face is generated wrappers | One suite | Zero duplication; but "implicit I/O" becomes a runtime error class | Near zero ("no thread executor") | Worst: switches invisible in tracebacks; C-extension constraints | Works, with the lazy-I/O caveat | Reverse direction; not applicable to an async core |
| Awaitable request objects (aiogram `TelegramMethod`) | Excellent (`Generic[T]`) | Request models tested once | One object per API method | None | Good | Not for streams | N/A |

## 6. Recommendation for aiommbot

Decide per surface, not globally.

1. **Event loop / WebSocket runtime — async only.** Its state is inherently concurrent (reconnect,
   heartbeat, backpressure). websockets shows a threaded twin costs ~1k lines of new concurrency code
   with its own bug class, and the sync face would have no users (a bot process *is* the loop). Do
   not build it.
2. **Protocol/domain core — sans-I/O.** Event models, filter evaluation, routing decisions, FSM
   admission, payload builders, and the Mattermost REST *request specs* (method, path, body, response
   model) are pure functions/objects. Enforce with an import-linter contract (`aiommbot.core` may not
   import any I/O module). This is where "one implementation" is literally true and needs no tooling.
3. **REST API client — the one surface that deserves a sync face** (scripts, migrations, CLI,
   Taskiq/cron jobs, tests). Model each call as a typed request object (aiogram shape: data + response
   type, no I/O), then two *thin* drivers: async over `httpx.AsyncClient`, sync over `httpx.Client` —
   httpx already shares `Request`/`Response`, so each driver is "build request → send → parse", tens
   of lines. Keep the drivers in `aiommbot/api/_async/` and generate `aiommbot/api/_sync/` with
   `unasync` (PyMongo/httpcore precedent), committed, with `scripts/unasync.py --check` in CI and a
   pre-commit guard that fails when `_sync` changes without `_async`. Generate the driver tests too
   (`tests/api/_async/` → `tests/api/_sync/`, httpcore style). Design names so tokens map 1:1
   (`AsyncMattermostApi`→`MattermostApi`, `aclose`→`close`); avoid `Awaitable[T]` in public
   annotations so no regex pass is needed; avoid `_IS_SYNC` forks — if a behaviour differs, push it
   into the driver, not the shared core.
4. **Handlers — accept both, run sync in a threadpool.** Detect with `inspect.iscoroutinefunction`
   (unwrapping `functools.partial`), narrow with `TypeIs`, dispatch via `anyio.to_thread.run_sync`
   (or `asyncio.to_thread` if the framework stays asyncio-only), exactly as Starlette/FastAPI/aiogram.
   Document the 40-thread default limiter, that cancellation cannot interrupt a running sync handler,
   and that `contextvars` are copied one way.
5. **Escape hatch, not architecture:** a `BlockingPortal`/`asyncio.Runner`-based sync wrapper over
   the async client is acceptable for REPL use, but at ~50 µs and a second loop it should not be the
   documented sync API. Greenlet is the wrong direction for an async core and adds a C dependency.

Suggested layout: `aiommbot/core/` (sans-I/O, no I/O imports), `aiommbot/api/_async/` (source of
truth) + `aiommbot/api/_sync/` (generated), `aiommbot/runtime/` (WebSocket consumer, async only),
`aiommbot/dispatch/` (handler invocation incl. threadpool path), `scripts/unasync.py`. Tests:
core tests once; `tests/api/_async` generated to `_sync`; runtime tests async only; a typing test
that both `MattermostApi` and `AsyncMattermostApi` satisfy their `Protocol`s.

## Sources

- Sans-I/O manifesto — https://sans-io.readthedocs.io/
- h11 0.16.0 `h11/_connection.py`, `h11/__init__.py` (local wheel) — https://github.com/python-hyper/h11
- wsproto README — https://github.com/python-hyper/wsproto/blob/main/README.rst
- websockets: `src/websockets/sync/connection.py`, `src/websockets/asyncio/connection.py`,
  `docs/howto/sansio.rst`, features matrix — https://github.com/python-websockets/websockets ;
  https://websockets.readthedocs.io/en/stable/reference/features.html
- httpcore 1.0.9 (`_async/`, `_sync/`, `_backends/base.py`, `_synchronization.py`; local wheel);
  `scripts/unasync.py`, `tests/_async`, `tests/_sync` — https://github.com/encode/httpcore
- httpx 0.28.1 `httpx/_client.py` (local wheel); `scripts/` listing — https://github.com/encode/httpx
- unasync — https://github.com/python-trio/unasync ; `src/unasync/__init__.py` ;
  https://pypi.org/project/unasync/
- PyMongo 4.17.0 (local wheel: `pymongo/asynchronous`, `pymongo/synchronous`, `network_layer.py`,
  `mongo_client.py`); `tools/synchro.py` and `CONTRIBUTING.md` —
  https://github.com/mongodb/mongo-python-driver ; `test/` tree
- Motor README deprecation notice — https://github.com/mongodb/motor/blob/master/README.md
- elasticsearch-py `utils/run-unasync.py`, `test_elasticsearch/` — https://github.com/elastic/elasticsearch-py
- opensearch-py `utils/` — https://github.com/opensearch-project/opensearch-py/tree/main/utils
- urllib3 `src/urllib3` (main; local 2.6.3), issue #1323 — https://github.com/urllib3/urllib3/issues/1323 ;
  hip — https://github.com/python-trio/hip
- redis-py `redis/asyncio/client.py`; release v4.2.0rc1 — https://github.com/redis/redis-py
- anyio 4.12.1 `anyio/from_thread.py`, `anyio/to_thread.py` (local wheel); threads docs —
  https://anyio.readthedocs.io/en/stable/threads.html
- asyncer syncify — https://asyncer.tiangolo.com/tutorial/syncify/
- asgiref `asgiref/sync.py` — https://github.com/django/asgiref/blob/main/asgiref/sync.py
- Trio `src/trio/_threads.py` — https://github.com/python-trio/trio
- SQLAlchemy 2.0 asyncio docs — https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html ;
  `lib/sqlalchemy/util/concurrency.py` — https://github.com/sqlalchemy/sqlalchemy
- greenback — https://github.com/oremanj/greenback
- Starlette 0.51.0 `starlette/_utils.py`, `starlette/concurrency.py`, `starlette/routing.py` (local wheel)
- FastAPI "Concurrency and async / await" — https://fastapi.tiangolo.com/async/
- aiogram `aiogram/methods/base.py`, `aiogram/dispatcher/event/handler.py` (dev-3.x) — https://github.com/aiogram/aiogram
- Python docs: `asyncio.Runner` — https://docs.python.org/3.14/library/asyncio-runner.html ;
  tasks — https://docs.python.org/3.14/library/asyncio-task.html ; What's New 3.14 —
  https://docs.python.org/3.14/whatsnew/3.14.html ; pending removal in 3.16 —
  https://docs.python.org/3.14/deprecations/pending-removal-in-3.16.html
- Micro-benchmark: `bench.py` run in this session (Python 3.14.7, anyio 4.12.1, macOS); numbers are
  single-run, order-of-magnitude only.
