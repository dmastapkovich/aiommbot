# Execution model in practice: synchronous callables, dual faces and async→sync tooling (Sep 2026)

Research date: 2026-09-04, for ticket #22. Primary sources only: library source at the cited paths,
official docs, upstream issues and PRs, PyPI metadata, and a read-only survey of the frozen
`aiommbot` 0.4.8 tree with the eleven company bots beside it. It extends two earlier files rather
than repeating them: `06-dual-sync-async-api.md` (the mechanisms of a dual API — note that its
recommendation to generate the sync client with `unasync` was **rejected** in #22 on the evidence
below) and `09-usage-mining-0.4.x-bots.md` (§4 here is the synchronous slice of the same mining).
Anything not confirmed is marked **[unverified]**.

**Re-verified directly on 2026-09-04**, after the surveys and before the ADRs were written:
PyPI metadata for `unasync` (0.6.0, 2024-05-03, `>=3.8`, one release in the preceding six years),
`unasyncd` (0.10.1, 2026-06-22, `>=3.10`, libcst-based), `httpx2` (2.12.0, 2026-08-18, `>=3.10`,
depending on `anyio>=4.10`, `httpcore2==2.12.0`, `truststore>=0.10`) and `litestar` (2.24.0,
2026-06-11); Litestar's `warn_implicit_sync_to_thread` text, its `LitestarWarning` category and the
`LITESTAR_WARN_IMPLICIT_SYNC_TO_THREAD` variable compared against `"0"`; anyio's `run_sync`
signature and its `abandon_on_cancel: bool = False` default with the surrounding docstring; httpx2
PR #1153 (open, 2026-08-21, h2 state-machine corruption when a `Client(http2=True)` is shared across
threads); uvicorn's `timeout_graceful_shutdown: int | None = None` and `LOOP_FACTORIES` with
`loop="auto"`. One correction came out of that pass: the seventy-seven-second FastStream
overshoot lives in a **comment** on issue #1648, not in the issue body, and the issue itself is a
closed enhancement request titled "k8s gracefully shutdown" — cited accordingly below.

Three questions:

1. Do high-quality async Python frameworks accept synchronous user callables, and exactly how?
2. How do they, and mature clients, expose a dual synchronous/asynchronous public API?
3. What is the state of async→sync code generation tooling, and what does it cost?

Plus the local question the decision turned on: what did 0.4.8's synchronous surface consist of, and
who used it?

## 1. Synchronous callables in the reference set

Versions established from PyPI and repository metadata: DMR 0.14.0 (2026-08-14) · Starlette 1.6.0
(2026-08-08) · FastAPI 0.141.1 (2026-07-29) · Litestar 2.24.0 (2026-06-11) · FastStream 0.7.5
(2026-08-27) · aiogram 3.31.0 (2026-08-26) · python-telegram-bot 22.8 (2026-06-12).

| Framework | Sync handlers | Sync deps | Sync middleware | Mechanism | Policy |
|---|---|---|---|---|---|
| django-modern-rest | yes | n/a | yes (Django's) | no bridge of its own: colour fixed at import, two hand-written pipelines, adaptation by Django's `sync_to_async(thread_sensitive=True)` — **one serialised thread** | refuses to mix colours in one controller |
| Starlette / FastAPI | yes | yes | **no** | `is_async_callable` → `run_in_threadpool` → `anyio.to_thread`, 40 shared tokens, `shield=True` | automatic, no opt-out |
| Litestar | yes (HTTP only) | yes | **no** | own `run_in_executor` / `trio.to_thread` via sniffio | **explicit tri-state `sync_to_thread`, warns both ways** |
| FastStream | yes | yes | **no** (hard failure) | `to_async` → `anyio.to_thread`, 40 shared | automatic, no knob |
| aiogram 3.x | yes (docs say prohibited) | filters, incl. every magic filter | no | `asyncio.to_thread` → loop default executor | automatic, undocumented |
| python-telegram-bot | **no** | filters sync-mandatory, inline | n/a | zero threads library-wide | async-only by decree |
| Falcon (ASGI) | **no** | no | no | user calls `sync_to_async` explicitly | refusal |
| Sanic | yes | yes | yes | **inline**, no threads | automatic |

Findings that carried weight in #22:

- **Litestar requires the declaration and argues for it.** `sync_to_thread: bool | None = None` on
  the HTTP decorators (`litestar/handlers/http_handlers/decorators.py:91`); `None` on a synchronous
  callable emits `LitestarWarning` via `warn_implicit_sync_to_thread`, and an *asynchronous* callable
  with `sync_to_thread` set warns too (`litestar/handlers/http_handlers/base.py:308-314`,
  `litestar/utils/warnings.py:15-28`); `sync_to_thread=False` calls the function inline
  (`litestar/routes/http.py:178-182`). WebSocket handlers refuse synchronous callables outright
  (`handlers/websocket_handlers/route_handler.py:99-100`). Rationale, `docs/topics/sync-vs-async.rst`:
  *"Running in a thread pool has a very high overhead, greatly reducing an application's
  performance… This warning was introduced to prevent accidentally using blocking functions, by
  having to make a deliberate decision."* Three env vars compared against the literal string `"0"`
  are the only silencers; there is **no** app-level config knob, and `NoSyncToThreadWarning` does
  not exist in any version.
- **Litestar does not use anyio for this.** Since 2.5.0 (2024-01-06, PR #2937) it dispatches through
  `asyncio.get_running_loop().run_in_executor(get_asyncio_executor(), …)` with `contextvars` copied,
  or `trio.to_thread` under sniffio (`litestar/concurrency.py:35-41`). A capacity limiter exists only
  on the trio path; `set_asyncio_executor` is process-global and refuses to run inside a loop.
- ⭐ **A threaded synchronous callable cannot be stopped by anyone.** Trio states the underlying
  limit plainly (`trio/_threads.py:305-307`): *"neither Python nor the operating systems it runs on
  provide any general mechanism for cancelling an arbitrary synchronous function running in a
  thread."* `anyio.to_thread.run_sync` therefore defaults to `abandon_on_cancel: bool = False`,
  documented as ignoring *"cancellations in the host task until the operation has completed"*, and
  enters `CancelScope(shield=not abandon_on_cancel)`
  (verified directly in `anyio/to_thread.py` and `anyio/_backends/_asyncio.py:2670-2671`).
  So the framework's only real choice is whether the drain waits for the thread.
- ⭐ **The consequence, measured in production.** FastStream
  [#1648](https://github.com/ag2ai/faststream/issues/1648) is titled "k8s gracefully shutdown"
  (opened 2024-08-06, closed, `enhancement`); the evidence is in the reporter's **comment of
  2024-08-07**, reproducing with a `def` handler and `time.sleep`:
  `FastStream app shut down gracefully.` at `19:04:35,129`, `Done processing message.` at
  `19:05:52,065` — seventy-seven seconds later. `CancelledError` surfaced in the awaiting side at
  `run_sync_in_worker_thread`, so the middleware chain was cut off mid-way (*"no 'Done
  TestMiddleware' message in log"*) while the thread ran on to completion, and *"in RabbitMQ
  Management UI I see that one (1) message was UNACK … but then it return back to READY. So, it was
  not acknowledged and then will be processed again in another pod."* The maintainer's answer names
  the constraint: *"we can't wait forever. Sometimes we should decide, that broker is dead and kill
  it."* The lesson is not the lost thread but the half-finished chain around it: the handler's side
  effect happened and its acknowledgement did not.
- **Corroboration from the other side.** FastStream
  [#1639](https://github.com/ag2ai/faststream/issues/1639), "Can not proper handle long running
  task" (2024-08-05): a `def` subscriber calling `time.sleep(1000)` and acknowledging at the end —
  RabbitMQ closes the connection for want of a heartbeat, so the ack is impossible. A synchronous
  handler is not merely slow; it silently changes what the surrounding protocol can still do.
- **The thread budget is invisible everywhere.** anyio's default limiter is 40 tokens
  (`anyio/_backends/_asyncio.py:3157-3164`), a number trio's own source calls arbitrary
  (`trio/_threads.py:54-56`, *"I pulled this number out of the air"*). The figure appears nowhere in
  FastAPI's documentation; FastAPI costs **two or more** tokens per request with a synchronous
  endpoint (handler plus synchronous response validation, `fastapi/routing.py:317-319`). Starlette's
  own `docs/threadpool.md` warns that the limit is shared with FastAPI's dependencies "and some
  other scenarios that may not be documented".
- **Precedent for a dedicated pool**: Starlette 1.4.0 gave GZip its own `RunVar`-scoped limiter,
  *"Keep gzip compression isolated from AnyIO's default worker-thread capacity limiter"*
  (`starlette/middleware/gzip.py:29-41`); anyio's author proposed the same for the request path in
  Starlette [#1724](https://github.com/encode/starlette/issues/1724), still open.
- **Colour detection is where aiogram fails.** `aiogram/dispatcher/event/handler.py:34-36` checks
  `isawaitable(callback) or iscoroutinefunction(callback)` and misses callable objects, so such a
  handler is threaded and never runs — open [#1721](https://github.com/aiogram/aiogram/issues/1721),
  PR [#1858](https://github.com/aiogram/aiogram/pull/1858). Starlette's `is_async_callable` handles
  the case (`starlette/_utils.py:34-46`, `iscoroutinefunction(obj.__call__)`, `partial` unwrapping,
  `TypeIs` on both overloads). A sync aiogram handler is also nearly useless: every `FSMContext`
  method and all ~188 `Bot` methods are coroutines, and `Message.answer` returns an un-awaited
  object, so from a thread it silently sends nothing.
- **The refusals are considered, not lazy.** PTB designed the aiogram branch and did not ship it —
  Bibo-Joshi, 2021-01-31 sketched `if inspect.iscoroutinefunction(callback): … else: return
  callback(…)`; `telegram/ext/_handlers/basehandler.py:159` in 22.8 still has one unguarded await,
  and v13's `@run_async`/`workers=4` pool was deleted with the note *"PTB doesn't use threads
  anymore. It is also not thread safe!"*. Falcon names its inline wrapper
  `wrap_sync_to_async_unsafe` (`falcon/util/sync.py:72-86`) and raises `CompatibilityError`
  otherwise (`falcon/asgi/app.py:1082-1086`).
- **The doc-vs-doc collision worth remembering:** FastAPI says the `def`-vs-`async def` difference is
  *"about 100 nanoseconds"* and advises *"if you just don't know, use normal `def`"*; Litestar calls
  the same mechanism *"very high overhead"*; Starlette's maintainer warns *"if you use all of them,
  your application will be blocked."*
- **Trio names the principle the whole question turns on** (`docs/source/design.rst:231-266`):
  *"Rule 4: in Trio, only the potentially blocking functions are async."* Silently threading a `def`
  erases that signal.

## 2. Dual faces in practice

| Project | Dual face | How | Public? |
|---|---|---|---|
| django-modern-rest | yes, pervasive | **hand-written twins** for every collaborator (`SyncAuth`/`AsyncAuth`, throttles, caches, controllers) plus a `SyncOrAsync*` resolver in settings; test client = shared mixin + four thin subclasses over Django's twins | both |
| httpx / httpx2 | yes | **hand-written twins in one file** over a shared `BaseClient`, plus thin per-face transports; `Request`/`Response` shared | both |
| httpcore / httpcore2 | yes | sans-I/O-ish core; `_sync/` **generated** by an in-repo regex script; `_synchronization.py` and `_backends/` hand-written | both |
| psycopg 3 | yes | **AST codegen** on `ast_comments`, deletes async-only branches; `_acompat.py` paired primitives hand-written | both |
| PyMongo 4.13+ | yes | `unasync` + custom passes; **three tiers**: async source, generated sync, hand-written shared | both |
| Litestar | vestigial | `unasyncd`, **one file pair** left of the original two | both |
| advanced-alchemy | yes | `unasyncd`, three pairs, 60 hand-maintained replacements | both |
| sqlspec (same org) | yes | ⭐ **hand-written**, ~4,300 twinned lines + shared `_common.py` | both |
| FastStream | **no** | requested and refused ([#1289](https://github.com/ag2ai/faststream/issues/1289)); a `start_blocking_portal` recipe was promised in 2023 and never shipped | — |
| Starlette / FastAPI | one adapter only | `TestClient` over `anyio.from_thread.start_blocking_portal` behind `httpx.BaseTransport`, inheriting httpx's sync API | yes |
| urllib3 | **no** | tried (`hip`, issue #1323), abandoned 2022-04-14 | — |

Invariants across all of them:

1. **Direction is always async → sync**, never the reverse: the async source is a superset, so
   stripping is mechanical while adding is not (njsmith, urllib3 #1323).
2. ⭐ **Nobody generates the interesting part.** Every generator covers the wide, boring API surface
   and hand-writes concurrency primitives, cancellation and the socket layer. PyMongo's
   never-converted list names them exactly: `test_locks`, `test_concurrency`,
   `test_async_cancellation`, `test_async_loop_safety`, `test_async_contextvars_reset`,
   `test_async_loop_unblocked`, `test_async_network_layer` (`tools/synchro.py:184-194`).
   PyMongo's `CONTRIBUTING.md:508-525` states the rule: shared or divergent code lives at the top
   level because it *"cannot be generated from the async version"*.
3. **Generate-and-commit beat generate-at-build.** `unasync`'s own README recommends a setuptools
   `build_py` hook; none of PyMongo, elasticsearch-py, httpcore, Litestar or advanced-alchemy uses
   it — all commit the tree and gate it in CI.
4. **The bill is paid in refactoring, not in running the generator.** psycopg's PR #657 commit
   subjects: *"harmless manipulation to minimize async conversion diff"*, *"light refactor to align
   async and sync pool"*.
5. **urllib3's revert was capacity, not codegen**: pquentin, 2022-04-14 — the sync face came out
   working, but *"making each test to pass in async was going to be yet another slog… It was
   becoming lonely and urllib3 was continuing to move fast."*

httpx2 specifics that make thin drivers cheap for us: 2.12.0 (2026-08-18), `requires-python >=3.10`,
depends on `httpcore2==2.12.0`, `anyio>=4.10`, `idna`, `truststore`, `typing_extensions`. `Client`
(~834 lines) and `AsyncClient` (~836) are hand-written over a shared `BaseClient` in one
`_client.py`; `unasync` is applied only to `httpcore2`. `BaseTransport.handle_request` /
`AsyncBaseTransport.handle_async_request` are **plain classes, not Protocols or ABCs**
(`_transports/base.py`), `Request`/`Response` are single shared classes, and `MockTransport`
implements **both faces in one class** (`_transports/mock.py`). Streaming bodies are face-bound and
raise `RuntimeError` when crossed; a fully-read body is consumable by either face. There is **no**
free-threaded job in httpx2's CI, no thread-safety statement about `Client`, and a shared
`Client(http2=True)` corrupts the h2 state machine — discussion
[#1152](https://github.com/pydantic/httpx2/discussions/1152), PR
[#1153](https://github.com/pydantic/httpx2/pull/1153), open at the time of writing.

## 3. Async→sync tooling

| Tool | Latest | Engine | Verdict |
|---|---|---|---|
| `unasync` | 0.6.0, 2024-05-03 (`python>=3.8`) | tokens via `tokenize-rt` | repository alive (last commit 2026-07-31), release stale; no `--check` since issue #69 (2020); public customisation API only on master |
| `unasyncd` | 0.10.1, 2026-06-22 (`python>=3.10`) | libcst | the only actively released dedicated tool; 27 stars, 1 open issue, single maintainer |
| `libcst` / `ast-comments` / `tokenize-rt` | current | — | the DIY route (psycopg, neo4j) |
| in-repo scripts | — | regex or AST | the dominant form: httpcore's `scripts/unasync.py`, PyMongo's `tools/synchro.py`, neo4j's `bin/make-unasync` |

Reproduced warts (run against CPython 3.12/3.13/3.14):

- Modern syntax is **not** a problem for `unasync`: PEP 695/696/701/750 constructs round-trip
  byte-exact, because soft keywords and bracketed type parameters are ordinary tokens, and 0.6.0
  moved to `tokenize-rt` for exactly this.
- `unasync` **overwrote the source file** on a `fromdir`/path mismatch (relative input plus a
  `"/_async/"`-style rule); it invents `SyncExitStack` from `AsyncExitStack`; it leaves
  `await asyncio.sleep(0)` as a live coroutine; it never unwraps `Awaitable[T]`.
- `unasyncd --check` **reports success against a stale target**: source edited, target untouched,
  `unasyncd --check --no-cache --force` printed `0 files would be transformed, 1 would be left
  unchanged` and exited 0. Litestar and advanced-alchemy are safe only because their gate runs the
  generator in **write** mode under pre-commit. Not filed upstream at the time of writing.
- ⭐ **The two tools are exactly complementary on typed code.** With `TypeVar`/`ParamSpec`/`Protocol`
  pairs, `unasyncd` fixes the annotations but leaves `TypeVar("AsyncRepoT")` and `bound="AsyncRepo"`
  unrenamed — mypy strict, pyright, ty and pyrefly all complain — while `unasync` fixes the names in
  strings (its prefix heuristic reaches `STRING` tokens) and leaves `Awaitable[bytes]` in the
  signature. `Coroutine[Any, Any, T] → T` is handled by **neither**; PyMongo patches it with a regex
  (`tools/synchro.py:238-249`).
- **No project generates a sync `Protocol` twin as a load-bearing part of its public typed API**, so
  a library that tries will be first to hit the above.
- AST output is **interpreter-version-dependent**: psycopg pins `PYVER = "3.14"` and offers
  `--docker`/`--podman` for reproducibility.
- Guard designs, weakest to strongest: line-compare with `--check` (httpcore, format-fragile);
  generate to a shadow directory and diff after formatting both sides (elasticsearch-py);
  **generate in write mode and fail if anything changed** (neo4j, PyMongo, Litestar). PyMongo alone
  also refuses to proceed when a human edited a generated file
  (`if sync_name in modified_files … "Refusing to overwrite"`), and unit-tests its own generator.
- `advanced_alchemy` has carried `update_docstrings = true` in `[tool.unasyncd]` for years; the real
  key is `transform_docstrings`, the loader ignores unknown keys silently, so the feature was never
  on. New modules also drift out of the map by default — AA PR #722 notes a file *"intentionally
  async-only and… not picked up."*

## 4. The 0.4.8 synchronous surface, and who used it

- **`SyncBotRuntime`** (`aiommbot/runtime/bot_runtime.py:816`) is a hand-written facade — 14 mirrored
  methods, one line each — over `_SyncRuntimeLoop` (`:769-813`): a daemon thread running
  `asyncio.new_event_loop()` + `run_forever()`, driven by `asyncio.run_coroutine_threadsafe` and a
  blocking `future.result()` **with no timeout**. Kept honest by one reflection test
  (`tests/test_runtime.py:523-531`) and by a release chore ("Все методы зеркалированы в
  `SyncBotRuntime`", `CHANGELOG.md:214`).
- **Its documented hazard is `fork()`**: `docs/reference/runtime.md:135`,
  `docs/how-to/distributed-processing.md:310-312, 784`, `llms.txt:67` and
  `examples/distributed_bot/sync_worker_runtime.py:1-12` all repeat that the thread must be opened
  after the fork or every prefork child gets a dead loop. It also never receives the optimised event
  loop, because `install_event_loop_policy` is reachable only from `Bot.run()`.
- ⭐ **Zero consumers.** `SyncBotRuntime`, `bot.connect()`, `runtime_context(`,
  `run_until_complete`, `nest_asyncio`, `BlockingPortal`, `anyio.from_thread` — no hits in any of
  the eleven bots, including tests and scripts. No Celery and no Django anywhere, which was the
  stated justification. The only in-repo consumer is the framework's own example.
- **The need it served is real and served asynchronously**: backoffice-bot, duty-bot and
  postmortem-bot all message users from outside a handler, all through the async `bot.runtime`.
- **Sync handlers: zero of ~225**, and the dispatcher could not have run one —
  `build_handler_invoker` is typed `Callable[..., Awaitable[R]]` and `Observer.handle` awaits
  unconditionally (`dispatcher/injection.py:47`, `dispatcher/base.py:85-87`). Filters, middlewares
  and lifespans are structurally async-only; the two sync tolerances in use are
  `TransitionGuardFilter`'s `isawaitable` normalisation and Starlette's `run_in_threadpool` for
  FastAPI exception handlers, which duty-bot exercises.
- **The demand is the opposite direction**: expenses-bot pushes blocking QR/PDF decoding off the loop
  with `asyncio.to_thread` (`src/services/receipt_processor.py:299-346`).
- **uvloop was a dormant capability**: `runtime/event_loop.py` installs it automatically with an
  opt-out and skips free-threaded builds, but **no bot installs the extra** — zero hits for
  `uvloop|winloop|use_optimized_event_loop|prefer_uvloop` across all eleven.
- What a runtime-only process loses is documented at `docs/reference/runtime.md:145-148`: state and
  FSM, filters, `matched_params`, `answer()`/`reply()`, every middleware and `send_dialog()`. The
  sync face was never a smaller async face; it was a 14-method outbound-only slice.

## Recommendation

1. **Accept synchronous handlers, but require the declaration** — Litestar's tri-state
   `sync_to_thread` with a warning in both directions is the only design in the set that argues for
   itself, and both implicit defaults are footguns.
2. **Own the executor.** A bounded pool belonging to the framework, sized against the framework's own
   worker count, is the only way the promised backpressure means anything; the shared 40 tokens are
   invisible and unrelated.
3. **Make the drain honest about threads.** Cancel the wait, abandon the thread, signal it, and
   document idempotency — FastStream #1648 is what waiting looks like.
4. **Build the dual face from thin drivers over a sans-I/O core, not from a generator.** Every
   precedent hand-writes exactly the layer a bot framework cares about, both tools mangle typed
   `Protocol`/`TypeVar` code, `unasyncd --check` cannot be trusted, and the surface here is a few
   dozen lines per face.
5. **Reserve code generation for the wide typed surface already generated from the spec** — the
   Operation descriptors and resource methods of ADR-0025 — where emitting a second face costs
   nothing.
6. **Do not choose the event loop.** Litestar ships no `--loop` flag at all; uvicorn silently prefers
   uvloop on any successful import without logging it; a `loop_factory` parameter costs no dependency
   and keeps the deprecated policy API out of the design.

## Sources

- django-modern-rest 0.14.0 — `dmr/endpoint.py:190-197, 344-414`, `dmr/validation/controller.py:48-68`,
  `dmr/validation/endpoint_metadata.py:493-520, 697-713`, `dmr/internal/io.py:11-13, 27-34`,
  `dmr/test/client.py:123-183`, `docs/pages/structure/sync-and-async.rst`, `CHANGELOG.md:110-113, 316-319, 392-394`
- asgiref `asgiref/sync.py:393-409`; Django `django/core/handlers/base.py:250-252`, `topics/async/`
- Starlette 1.6.0 — `starlette/_utils.py:13-19, 34-46, 82-93`, `starlette/concurrency.py:32-34`,
  `starlette/routing.py:54-56`, `starlette/middleware/base.py:14, 119-125, 193`,
  `starlette/middleware/gzip.py:29-41`, `starlette/testclient.py:207-223, 349-351, 423-428, 679-710`,
  `docs/threadpool.md`; issue https://github.com/encode/starlette/issues/1724
- FastAPI 0.141.1 — `fastapi/routing.py:317-319, 351-354, 562-596, 6373-6377`,
  `fastapi/concurrency.py:17-41`, `fastapi/dependencies/utils.py:673-676`, `docs/en/docs/async.md`
- Litestar 2.24.0 — `litestar/handlers/http_handlers/decorators.py:91`,
  `litestar/handlers/http_handlers/base.py:308-314, 586-594`, `litestar/routes/http.py:178-182`,
  `litestar/utils/warnings.py:15-28`, `litestar/concurrency.py:35-41, 70-81`, `litestar/di.py:66-119`,
  `litestar/app.py:630-659`, `litestar/channels/subscriber.py:109, 127-137`,
  `litestar/handlers/websocket_handlers/route_handler.py:99-100`, `docs/topics/sync-vs-async.rst`,
  `docs/onboarding/fastapi.rst`, `pyproject.toml:434-513`, `.pre-commit-config.yaml:22-26`
- FastStream 0.7.5 — `faststream/_internal/utils/functions.py:49-63`, `_internal/di/config.py:74-80`,
  `_internal/endpoint/subscriber/mixins.py:31-69`, `_internal/endpoint/subscriber/utils.py:64-71`,
  `faststream/app.py:91-98`, `faststream/middlewares/acknowledgement/middleware.py:105-106`,
  `_internal/cli/main.py:241-245`, `ruff.toml:29-43`, `getting-started/subscription/index.md:156-158`;
  issues https://github.com/ag2ai/faststream/issues/1289 · /1639 (2024-08-05, `def` subscriber with
  `time.sleep`, heartbeat lost) · /1648 (2024-08-06, closed, `enhancement`; the log excerpt and the
  UNACK→READY observation are in the reporter's comment of 2024-08-07, and the maintainer's
  "we can't wait forever" is in the same thread) · /2249 · /3000 · PR /3010 · discussion /854
- aiogram 3.31.0 — `aiogram/dispatcher/event/handler.py:34-36, 68-72, 83-84, 117-122`,
  `docs/dispatcher/router.rst:31-34`, `docs/dispatcher/filters/index.rst:28-40`;
  issue https://github.com/aiogram/aiogram/issues/1721 · PR /1858 · 3.20.0 changelog (PR #1661)
- python-telegram-bot 22.8 — `telegram/ext/_handlers/basehandler.py:117, 159`,
  `telegram/ext/_utils/types.py:44`, `telegram/ext/_application.py:1021-1084`;
  issues https://github.com/python-telegram-bot/python-telegram-bot/issues/2288 · /4993 ·
  discussion /2351; v13.15 `telegram/ext/dispatcher.py:65, 184-185, 332-338, 404-442`
- Falcon — `falcon/asgi/app.py:1082-1086`, `falcon/util/sync.py:72-86, 197-201`
- Sanic 25.12.1 — `sanic/app.py:1373-1375`, `docs/handlers.md:54-68`
- Quart 0.22.0 `quart/app.py:1156-1182`; quart-trio `quart_trio/utils.py:19`
- anyio 4.12 — `anyio/to_thread.py:30`, `anyio/_backends/_asyncio.py:2670-2671, 3157-3164`
- Trio — `trio/_threads.py:54-56, 305-307`, `docs/source/design.rst:231-266`,
  `docs/source/reference-core.rst:1820-1838`
- httpx2 2.12.0 / httpcore2 2.12.0 — `src/httpx2/httpx2/_client.py:179-2237`,
  `_transports/base.py`, `_transports/mock.py`, `_models.py:871-1066`, `_api.py`, `_auth.py:38-85`,
  `scripts/unasync.py`, `scripts/check`, root `pyproject.toml`;
  https://pypi.org/pypi/httpx2/json · discussion https://github.com/pydantic/httpx2/discussions/1152 ·
  PR /1153 · discussion /1033
- httpcore 1.0.9 — `scripts/unasync.py`, `scripts/check`, `httpcore/_synchronization.py`,
  `httpcore/_backends/`
- psycopg 3 — `tools/async_to_sync.py:27-30, 152, 244-249`, `psycopg/psycopg/connection.py:1-4`,
  `psycopg_pool/_acompat.py`, `.github/workflows/lint.yml:40-41`, PR #657
- PyMongo 4.17 — `tools/synchro.py:29, 184-194, 238-249`, `CONTRIBUTING.md:508-525`,
  `tools/test_synchro.py`
- elasticsearch-py — `utils/run-unasync.py`, `noxfile.py`; neo4j driver — `bin/make-unasync`,
  `CONTRIBUTING.md`
- unasync — https://pypi.org/pypi/unasync/json, `src/unasync/__init__.py`,
  `docs/source/history.rst`, issues #64 · #69 · #78 · #79 · PR #87
- unasyncd — https://pypi.org/pypi/unasyncd/json, `README.md`, `unasyncd/config.py:76`, PR #31 · #48
- advanced-alchemy 1.11.0 `pyproject.toml:569-643`, PR #722; litestar-org/sqlspec
  `sqlspec/driver/_async.py`, `_sync.py`, `_common.py`
- urllib3 — issue https://github.com/urllib3/urllib3/issues/1323 (njsmith 2018-02-01,
  pquentin 2022-04-14)
- redis-py — `redis/asyncio/client.py`, PR #3991
- uvicorn — `uvicorn/config.py:231`, `uvicorn/server.py:288-302`, `uvicorn/loops/auto.py`
- aiommbot 0.4.8 (local, frozen) — `aiommbot/runtime/bot_runtime.py:123-1068`,
  `aiommbot/runtime/event_loop.py`, `aiommbot/bot.py:195-366`, `aiommbot/cli/main.py:64-113`,
  `aiommbot/channels/webhook.py:186-199`, `aiommbot/filters/transition_guard.py:11-37`,
  `aiommbot/dispatcher/injection.py:47-84`, `aiommbot/dispatcher/base.py:70-87`,
  `tests/test_runtime.py:523-531`, `docs/reference/runtime.md:135, 145-148, 212`,
  `docs/how-to/distributed-processing.md:310-312, 784, 790-792`, `CHANGELOG.md:214`,
  `examples/distributed_bot/sync_worker_runtime.py`; the eleven bots' `src/`, `tests/`, `scripts/`
  and `pyproject.toml`
