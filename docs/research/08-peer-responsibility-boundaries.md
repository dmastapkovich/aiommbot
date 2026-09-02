# Peer responsibility boundaries: what framework peers own vs. delegate

Research date: 2026-09-02. Sources are primary (framework source on GitHub, official docs, PyPI
`pyproject.toml`/`setup.cfg` extras). Claims I could not confirm from a primary source are marked
**[unverified]**.

Question: aiommbot 0.4.8 shipped, inside the bot framework itself, a taskiq-based cron/interval
scheduler, Prometheus metrics for every subsystem, a CLI runner, retry/idempotency/dead-letter
middlewares, a circuit breaker (purgatory), a bounded backpressure queue with drop policies,
storage profiles, Sentry middleware, and uvloop switching. 0.5.0 wants a small core and as few
dependencies as possible. Where do comparable frameworks draw the core/extra/recipe/absent line
for the same capabilities, and what do they point users at instead of owning it themselves?

## 1. Capability × framework matrix

Legend: **Core** = ships in the main package, no extra install. **Extra** = first-party
optional-dependency group or official companion package, one `pip install X[extra]` away.
**Recipe** = documented pattern, but the dependency and code are entirely the user's. **Absent** =
not mentioned in the framework's own docs at all. Superscript numbers are footnotes into
[Sources](#sources).

### 1.1 Bot/chat frameworks

| Capability | aiogram 3 | Slack Bolt (py) | discord.py 2 | hikari | PTB v21+ |
|---|---|---|---|---|---|
| (a) cron/interval scheduling | Absent — recipe: APScheduler/asyncio loop¹ | Absent — recipe | Core — bundled `discord.ext.tasks.loop`² | Absent — recipe | **Extra** — `JobQueue` wraps APScheduler, `pip install "python-telegram-bot[job-queue]"`³ |
| (b) metrics + tracing | Absent | Absent | Absent | Absent | Absent |
| (c) CLI runner/dev server | Absent — plain `asyncio.run(main())` | Absent — `app.start()` or host adapter | Absent — `client.run()` is a library call, not a CLI | Absent — `GatewayBot.run()` | Absent |
| (d) retries w/ backoff | Absent | **Adjacent SDK** — `slack_sdk.http_retry.RateLimitErrorRetryHandler`, opt-in, not Bolt itself⁴ | Core (partial) — HTTP client retries within Discord's own rate-limit window only⁵ | Core (partial) — REST client retries within Discord's rate-limit window (same constraint as discord.py) | Absent — `RetryAfter` surfaces as an exception the app must catch |
| (e) idempotency/dedup | Absent | Absent — app must dedupe `X-Slack-Retry-Num` itself | Absent | Absent | Absent |
| (f) dead-letter | Absent | Absent | Absent | Absent | Absent |
| (g) circuit breaker | Absent | Absent | Absent | Absent | Absent |
| (h) rate limiting | Absent — throttling removed in v3, recipe: `TTLCache` middleware⁶ | **Adjacent SDK** — same `RateLimitErrorRetryHandler`⁴ | Core — bucket-tracked `HTTPClient`, mandatory because Discord enforces it⁵ | Core — same reason as discord.py | Absent |
| (i) backpressure/concurrency | Core (partial) — `handle_as_tasks` bounded by `tasks_concurrency_limit`⁷ | Core (partial) — `listener_executor` bounds lazy-listener concurrency | Core (partial) — sharding, bounded message cache | Core (partial) — pluggable cache/event-manager components | **Core** — `BaseUpdateProcessor.max_concurrent_updates`, `Application.concurrent_updates()`⁸ |
| (j) error reporting (Sentry) | Absent — no official aiogram integration⁹ | Absent | Absent | Absent | Absent |
| (k) event-loop selection | Absent — user runs `uvloop.install()` themselves | Absent | Absent — docs recommend `asyncio.run()`, uvloop is BYO | Absent | Absent |
| (l) graceful shutdown/lifespan | Core (partial) — `emit_startup`/`emit_shutdown` router hooks⁷ | Core (partial) — adapter-level connect/close | **Core** — `async with client:`, `setup_hook()`, signal handling¹⁰ | **Core** — `run()→start()→join()`, `close()` dispatches Stopping/StoppedEvent, `enable_signal_handlers`¹¹ | **Core** — `run_polling()`/`run_webhook()` manage signals and shutdown |
| (m) health endpoints | Absent | Absent (host adapter's concern) | Absent — no HTTP server exists | Absent | Absent — webhook mode's tiny HTTP server has no health route |

### 1.2 Web/service frameworks and Django

| Capability | FastStream 0.7 | Litestar | FastAPI/Starlette | Sanic | Django |
|---|---|---|---|---|---|
| (a) cron/interval scheduling | **Extra** — official `taskiq-faststream` companion package¹² | **Extra** — official `litestar-saq` plugin (SAQ-backed)¹³ | Absent — recipe: APScheduler/arq beside lifespan | Absent — recipe: `sanic-scheduler` third-party¹⁴ | Absent — no built-in scheduler; recipe: `django-celery-beat`/cron¹⁵ |
| (b) metrics + tracing | **Extra** — `otel`/`prometheus` optional-dependency groups in `pyproject.toml`¹⁶ | Absent — recipe: ASGI middleware, no official package found | Absent — recipe: `prometheus-fastapi-instrumentator`, `opentelemetry-instrumentation-fastapi`¹⁷ | Absent | Absent — recipe: `django-prometheus` |
| (c) CLI runner/dev server | **Core** — `faststream run`, gunicorn/uvicorn-backed¹⁸ | **Core** — click-based CLI, "hard dependencies included by default"¹⁹ | **Core-adjacent** — `fastapi-cli` ships and is installed by `fastapi[standard]`²⁰ | **Core** — `sanic path.to.server:app`²¹ | **Core** — `manage.py`/management-command framework |
| (d) retries w/ backoff | Absent — `retry=True` shortcut was *removed* as "a design mistake"²² | Absent | Absent | Absent | Absent |
| (e) idempotency/dedup | Absent — in-memory nack counter only, not scalable per maintainer²² | Absent | Absent | Absent | Absent |
| (f) dead-letter | Absent — pushed to broker-native DLX/JetStream config²² | Absent | Absent | Absent | Absent |
| (g) circuit breaker | Absent | Absent | Absent | Absent | Absent |
| (h) rate limiting | Absent | **Core** — `RateLimitConfig` built-in middleware²³ | Absent — recipe: `slowapi`/`aiolimiter` | Absent | Absent — recipe: `django-ratelimit` |
| (i) backpressure/worker concurrency | Absent in framework — broker prefetch config only | Absent core; concurrency lives in the `litestar-saq` extra | Absent — delegated to ASGI server (`--workers`) | Core — `app.add_task`/`app.tasks`/`workers=` in `app.run()`²⁴ | Absent — delegated to WSGI/ASGI server |
| (j) error reporting (Sentry) | Absent — no official integration listed | **Adjacent SDK** — `sentry-sdk` auto-enables for Litestar²⁵ | **Adjacent SDK** — `sentry-sdk[fastapi]`/`[starlette]`, auto-enabled²⁶ | **Adjacent SDK** — listed integration²⁵ | **Adjacent SDK** — `sentry-sdk[django]`²⁵ |
| (k) event-loop selection | Absent — not surfaced in FastStream's API | Absent — delegated to `uvicorn --loop` | Absent — delegated entirely to `uvicorn --loop auto\|asyncio\|uvloop`²⁷ | Absent — delegated to server config | N/A — owned by the WSGI/ASGI server, not Django |
| (l) graceful shutdown/lifespan | **Core** — ASGI lifespan wrapper, broker connect/close hooks¹⁸ | **Core** — ASGI lifespan / `on_startup`/`on_shutdown` | **Core** — Starlette `lifespan` context manager²⁸ | **Core** — `before_server_start`/`after_server_stop` listeners | N/A — owned by the server |
| (m) health endpoints | **Core (helper)** — `faststream.asgi.make_ping_asgi` for readiness, liveness is a plain route¹⁸ | Recipe — plain `@get` route, "no built-in health-check plugin"²⁹ | Absent — plain route recipe | Absent — plain route recipe | Absent — plain view recipe |

### 1.3 Celery / taskiq / arq — the ecosystem's answer

| Capability | Celery | taskiq | arq |
|---|---|---|---|
| (a) cron/interval scheduling | **Core** — `beat_schedule`/`django-celery-beat`¹⁵ | **Core** — `TaskiqScheduler` + `LabelScheduleSource`, `cron`/`interval`/`time` labels³⁰ | **Core** — `arq.cron.cron()` in `WorkerSettings.cron_jobs`³¹ |
| (d) retries w/ backoff | **Core** — `autoretry_for`, `retry_backoff`, `retry_kwargs`³² | Core (thinner) — task-level retry exists; exact backoff knobs less documented **[unverified]** | Core (thinner) — `max_tries` per job; backoff strategy less documented **[unverified]** |
| (e) idempotency/dedup | Precondition-only — `acks_late=True` requires the task be idempotent; Celery does not dedupe for you³² | Same pattern, not automatic **[unverified — no primary doc found]** | Same pattern, not automatic **[unverified]** |
| (f) dead-letter | Absent as a native construct — "not a native Celery construct," pattern = catch terminal exception, dispatch to a handler task, or configure broker DLQ³² | Absent — no native DLQ | Absent — no native DLQ |
| (i) backpressure/concurrency | **Core** — `worker_prefetch_multiplier`, `--concurrency` | Core (buggy) — `max_async_tasks`/`sync_tasks_pool_size`, but semaphore not applied in all code paths as of 0.11.10³³ | **Core** — `max_jobs` on `Worker` |
| (j) Sentry | **Adjacent SDK** — `sentry-sdk[celery]`, official integration²⁵ | Absent — no official integration found | Absent |

## 2. Per-framework notes

### 2.1 aiogram 3

The only "Core" cell aiogram earns anywhere in the matrix is `handle_as_tasks`'s
`tasks_concurrency_limit`. Everything else — including throttling, which was a built-in
`dispatcher.throttle()` in v2 — was deliberately deleted in v3; the migration guide tells users to
"use middlewares to control the execution context and implement any throttling mechanism you
desire"⁶. This is the sharpest "small core" example in the survey: aiogram owns routing/FSM/DI and
nothing that looks like ops infrastructure.

### 2.2 Slack Bolt for Python

Bolt owns the listener pipeline and delegates the rest: outbound retry/rate-limit handling lives one
layer down in `slack_sdk.http_retry.builtin_handlers.RateLimitErrorRetryHandler`, off by default,
opt-in per client⁴. No scheduler, metrics, circuit breaker, or Sentry integration; even testing is
unofficial (open issue #380), maintainers point at copying Bolt's own `mock_web_api_server` fixture.

### 2.3 discord.py 2

The one bot framework here that owns real scheduling (`discord.ext.tasks.loop`, bundled in the same
package²) and real reliability code (`HTTPClient`'s per-route rate-limit bucket tracking⁵) — but both
exist only because the Discord API contract makes them mandatory, not as general-purpose
infrastructure. Lifecycle (`async with client:`, `setup_hook()`) is core¹⁰; metrics, generic retry,
circuit breaker, Sentry, and health endpoints (no HTTP server exists) are all absent.

### 2.4 hikari

Mirrors discord.py for the same reason (mandatory REST rate-limit compliance) but pushes command
routing/DI to companion packages (lightbulb v3 + **linkd**, hikari-arc + Alluka). Lifecycle
(`run()→start()→join()`, `enable_signal_handlers`)¹¹ is core; no scheduler, metrics, retry, circuit
breaker, or Sentry integration was found for hikari itself.

### 2.5 python-telegram-bot v21+

The cleanest in-repo precedent for demoting a feature from core to extra: `JobQueue` was bundled
unconditionally in the v13.x line and became `pip install "python-telegram-bot[job-queue]"` from
v20.0 onward³. Update-processing concurrency (`BaseUpdateProcessor.max_concurrent_updates`,
`ApplicationBuilder.concurrent_updates(...)`, with an explicit warning against combining it with
stateful `ConversationHandler` flows⁸) is the right-sized "cap in core, correctness is the caller's
job" pattern aiommbot should aim for. Retries, dead-letter, circuit breaking, and metrics are absent.

### 2.6 FastStream 0.7

The most direct precedent for "own the wiring, extra the observability, delete built-in reliability
once it's learned to be wrong." `otel`/`prometheus` are two-line optional-dependency groups¹⁶; CLI
and a minimal ASGI health-check helper (`make_ping_asgi`) are core¹⁸. The standout data point:
FastStream's `retry=True` subscriber shortcut was **removed** on the record as "a design mistake" —
it was just an unscalable in-memory `message.nack()` counter, and the maintainers concluded manual
ack/nack plus the broker's own native DLQ/backoff was the right owner, not the framework²².

### 2.7 Litestar

The outlier that argues against a hard "frameworks never own rate limiting" rule:
`RateLimitConfig`/`RateLimitMiddleware` is genuine built-in middleware with a pluggable Redis-backed
store²³ — and it shipped with a real CVE-class bug (GHSA-hm36-ffrh-c77c, X-Forwarded-For spoofing),
a concrete cost of owning this in core. CLI is core (click-based)¹⁹; scheduling is an official but
separately versioned plugin (`litestar-saq`)¹³; health checks are a documented plain-route recipe,
explicitly not a bundled plugin²⁹.

### 2.8 FastAPI / Starlette

Starlette owns only the ASGI lifespan contract (`@asynccontextmanager`, teardown deferred until
background tasks finish)²⁸ and `BackgroundTasks`. FastAPI's CLI (`fastapi dev`/`run`) is a *separate*
PyPI package, `fastapi-cli`, installed by default via `fastapi[standard]` but architecturally its own
`pyproject.toml`²⁰ — a clean "core-adjacent, one extra away" precedent. Metrics, tracing, retries,
rate limiting, and health endpoints are uniformly absent; event-loop selection is entirely Uvicorn's
job (`--loop auto|asyncio|uvloop`)²⁷. Sentry is the one first-party exception: auto-enabled on
import²⁶.

### 2.9 Sanic

Owns a CLI (`sanic path.to.server:app`)²¹ and a named, cancellable background-task registry
(`add_task`/`get_task`/`cancel_task`/`purge_tasks`)²⁴ — the closest thing in this survey to a
framework-owned worker registry outside the task-queue libraries — but explicitly has no cron: a
feature request was filed and never merged, and the documented answer is the third-party
`sanic-scheduler`¹⁴.

### 2.10 Django

`manage.py` is a first-party CLI, but a per-invocation batch mechanism, not a scheduler — Django owns
none of scheduling, metrics, retries, or rate limiting. The decade-old ecosystem answer is
`django-celery-beat`'s `DatabaseScheduler`¹⁵; process lifecycle and event-loop selection belong to
the WSGI/ASGI server, not Django. Sentry is first-party-adjacent (`sentry-sdk[django]`)²⁵.

### 2.11 Celery / taskiq / arq — the ecosystem's answer

What every other peer above points at instead of owning scheduling/task-queue reliability. All three
own cron/interval scheduling in core (Celery `beat_schedule`, taskiq `TaskiqScheduler` +
`LabelScheduleSource`, arq `cron()`)¹⁵ ³⁰ ³¹. Celery is most mature on retries
(`autoretry_for`/`retry_backoff`), but its own docs frame `acks_late=True` as a **precondition**
("make sure your tasks are idempotent"), not automatic dedup³². None of the three has a native
dead-letter construct — the pattern is always "catch the terminal exception, dispatch to a handler
task, or configure the broker's own DLQ." Concurrency is core-but-uneven: Celery's
`worker_prefetch_multiplier` and arq's `max_jobs` are solid; taskiq's `max_async_tasks` has a live
correctness bug (GH #396) where the semaphore isn't applied on every code path³³ — a reminder that
"core" doesn't always mean "correct."

## 3. Ecosystem alternatives catalogue

### 3.1 Scheduling: APScheduler 4, taskiq, arq

**APScheduler 4 is still pre-release**: latest tag `4.0.0a6` (Apr 2025), the project's own docs say
"do NOT use this release in production," stable is 3.x (3.11.3, Jun 2026)⁹ — not yet a safe
recommendation over taskiq/arq. taskiq's `LabelScheduleSource` (`@broker.task(schedule=[{"cron":
"*/5 * * * *"}])`, one scheduler process, `preserve_all`/`only_unique` merge functions) is a clean
declarative primitive and closest to aiommbot's own stack³⁰. arq is the lightest-weight (Redis-only,
`cron()` + `WorkerSettings`, no broker abstraction)³¹. All three require exactly one scheduler
process — never one per replica — the same multi-replica hazard aiommbot already flags.

### 3.2 Retries: stamina, tenacity

**tenacity** is the general-purpose, unopinionated toolkit³⁶. **stamina** is hynek's opinionated
wrapper over it: narrower surface, jittered exponential backoff by default, preserves type hints,
ships Prometheus/structlog instrumentation, and a first-party `stamina.set_testing()` mode that
disables backoff for fast deterministic tests³⁵. For a framework that wants to *recommend* a retry
story without owning one, stamina's small-and-typed shape maps directly onto "recipe, not core."

### 3.3 Observability: prometheus-client, opentelemetry-instrumentation

`prometheus-client`'s multiprocess mode (`PROMETHEUS_MULTIPROC_DIR`, a request-scoped
`MultiProcessCollector` to avoid duplicate registration, `remove()`/`clear()` unsupported) is already
solved generically upstream²²; a framework only needs to expose the DI/lifecycle seam, not reimplement
it. OpenTelemetry's answer is `opentelemetry-python-contrib` — one `opentelemetry-instrumentation-
<lib>` package per library — plus a genuinely code-free path: `opentelemetry-bootstrap` auto-detects
dependencies and `opentelemetry-instrument <cmd>` activates them with zero application changes²⁴.

### 3.4 CLI: typer, click

Every "core" CLI in this survey is core *because* it's thin: FastStream's and Litestar's are
click-based¹⁸ ¹⁹, `fastapi-cli` is Typer-based²⁰. None of these frameworks wrote their own
argument-parsing layer — they wrote a handful of commands (`run`, `dev`, app discovery) on top of an
existing toolkit, and Litestar adds an entry-point extension mechanism (`CLIPlugin`) on top¹⁹.

### 3.5 Circuit breaking: purgatory, aiobreaker, pybreaker

**pybreaker** (the original, Nygard's pattern) is the most actively maintained per Snyk³³.
**aiobreaker** (asyncio fork) shows minimal recent activity³³. **purgatory** — what aiommbot 0.4.8
already used — was built specifically to fix limitations its author hit in aiobreaker, and is the
only one of the three with a pluggable Redis backend so circuit state can be shared across
replicas³³. That Redis option is why purgatory remains defensible to keep recommending even if
demoted from core to a documented plugin/extra — an in-memory-only breaker is near-useless across
more than one replica, the same hazard as the scheduler.

### 3.6 Rate limiting: aiolimiter

`aiolimiter.AsyncLimiter` is a leaky-bucket limiter as an async context manager, MIT-licensed,
single-process, with no framework opinions at all³⁴ — exactly why it composes as a recipe ingredient:
wrap it in a thin adapter kept in DI, with Redis-backed alternatives (`aiopylimit`, `PyrateLimiter`)
available if multi-replica sharing is later needed.

### 3.7 Error reporting: sentry-sdk integrations

Sentry's SDK auto-enables integrations purely by import detection for Django, Flask, FastAPI,
AIOHTTP, Bottle, Falcon, Pyramid, Quart, Sanic, Starlette, Starlite/Litestar, and Tornado²⁵ ²⁶.
**aiogram is not on that list** — no official Sentry↔aiogram integration exists, so any bot wanting
structured Sentry capture already has to wire it manually today, which is exactly the "Sentry
middleware" aiommbot 0.4.8 shipped in-framework. That's evidence Sentry support for a *chat-bot*
framework specifically isn't solved upstream the way it is for ASGI web frameworks — a thin
first-party adapter remains defensible, but it should be a narrow Protocol-shaped wrapper around
`sentry_sdk`, not a bespoke redaction pipeline.

## 4. What "small core + extras" looks like in practice (FastStream, Litestar)

FastStream and Litestar are the two frameworks in this survey that most resemble aiommbot's stated
0.5.0 goal — an async framework with real infrastructure needs (brokers/ASGI, observability, ops
tooling) that still keeps its dependency graph small. Both converge on the same three-tier shape:

1. **Core = wiring + lifecycle + CLI.** FastStream's core owns the broker abstraction, the ASGI
   lifespan wrapper, and `faststream run`¹⁸; Litestar's core owns routing, the ASGI lifespan, and its
   click-based CLI¹⁹. Neither core does anything a peer-review would call "infrastructure" beyond
   process startup/shutdown and command dispatch.
2. **Named optional-dependency extras for things that are genuinely just "install one more package
   and flip a flag."** FastStream's `otel`/`prometheus` groups are two-line entries in
   `pyproject.toml` that pin the upstream library, nothing more¹⁶ — the framework doesn't wrap
   `prometheus_client`'s API, it just declares the dependency and exposes the collector at the right
   lifecycle hook. This is the naming convention worth copying: extras are named after the concern
   (`otel`, `prometheus`, `cli`), not after a bundled implementation.
3. **Official but separately versioned/repo'd plugins for anything stateful or with its own failure
   modes.** Scheduling and job queues get pushed one repo out: `taskiq-faststream`¹² and
   `litestar-saq`¹³ are both maintained by the same GitHub orgs as the core framework, but ship, tag,
   and release independently, and both explicitly document the "run exactly one scheduler process"
   hazard rather than hiding it. Litestar's `RateLimitConfig` is the one deliberate exception to
   "reliability infra lives in a plugin" — and it came with a real CVE-class bug (X-Forwarded-For
   spoofing) that a plugin boundary would have let a narrower team own and patch faster²³.

The lesson for aiommbot 0.5.0 is less "never own X" and more "own only the things where getting them
wrong breaks every consumer identically (lifespan, CLI, DI wiring), extra everything with an
official-but-versioned-separately boundary once it has its own failure modes or storage
requirements (scheduling, circuit breaking, rate limiting), and recipe everything that's just
composition of an existing, well-maintained upstream primitive (retries via stamina, metrics via
prometheus-client, error reporting via sentry-sdk)."

## 5. Recommendation matrix for aiommbot 0.5.0

| Capability | Placement | Justification |
|---|---|---|
| (a) cron/interval scheduling | **Plugin** (`aiommbot-taskiq` or keep the taskiq dependency but move scheduler wiring to an optional extra) | Every peer that owns scheduling ships it as a separately versioned companion (`taskiq-faststream`, `litestar-saq`) or a gated extra (PTB `[job-queue]`), never core¹²·¹³·³ — and it carries the single-instance-only hazard aiommbot already knows about. |
| (b) metrics (Prometheus) | **Extra**, named `prometheus` | FastStream's exact precedent: a two-line optional-dependency group pinning `prometheus-client`, framework exposes the collector at the DI/lifecycle seam and does not wrap the client's API¹⁶. |
| (b) tracing (OpenTelemetry) | **Recipe** (document `opentelemetry-bootstrap`/`opentelemetry-instrument`) | No peer core or extra reimplements OTel; the zero-code auto-instrumentation path already covers HTTP/Mongo clients aiommbot uses²⁴. |
| (c) CLI runner | **Core**, kept thin | Every framework that has one keeps it to `run`/`dev`/discovery on top of click or Typer, not a bespoke parser¹⁸·¹⁹·²⁰ — this is wiring, not infrastructure, and it's the one thing every consumer needs identically. |
| (d) retries with backoff | **Recipe** (document `stamina`) | FastStream *removed* its built-in retry shortcut specifically because a framework-owned in-memory retry counter doesn't scale and duplicates what `stamina`/`tenacity` already do correctly with jitter and typed decorators²²·³⁵. |
| (e) idempotency/dedup | **Recipe**, bot-specific guidance only | Peers treat this as a precondition of `acks_late`/at-least-once delivery, never automated³² — but aiommbot's specific dedup case (Mattermost webhook replay, duplicate action callbacks) is a domain concern, see §6. |
| (f) dead-letter | **Recipe** (broker-native DLQ/DLX, or a documented "terminal-failure handler task" pattern) | No peer — not Celery, not taskiq, not FastStream — implements this as generic framework code; it is universally pushed to the broker or hand-rolled³²·²². |
| (g) circuit breaker | **Plugin/extra**, keep `purgatory` as the recommended library, not framework-owned | purgatory's own value (Redis-backed shared state across replicas) only matters if wired consistently; keeping it a documented DI-injected dependency rather than framework code lets it be swapped/upgraded independently, matching how *every* peer treats circuit breaking (absent from framework core, always a separate library)³³. |
| (h) rate limiting — outbound (Mattermost API) | **Recipe** (`aiolimiter` + adapter) | Same shape as Slack's `RateLimitErrorRetryHandler`⁴ — an SDK-adjacent concern, not a framework concern; wrap `AsyncLimiter` in the HTTP client mixin aiommbot already has for outbound instrumentation. |
| (h) rate limiting — inbound (chat flood control) | **Recipe**, but consider a thin optional middleware | This is closer to Litestar's `RateLimitConfig` case²³ — genuinely bot-specific (per-user/per-channel cooldown, not per-IP) — see §6 for why it isn't a clean "just extra a library" case. |
| (i) backpressure/bounded queues | **Core (thin cap only)** | PTB's `max_concurrent_updates` and aiogram's `tasks_concurrency_limit` show the right-sized version: a single concurrency-limit knob in the dispatch loop⁸·⁷ — not a full bounded-queue-with-drop-policies subsystem, which duplicates what the broker/taskiq layer already owns. |
| (i) worker concurrency (taskiq side) | **Delegate to taskiq's own knobs**, document the known bug | taskiq's `max_async_tasks` has a live correctness bug (GH #396)³³ — don't reimplement backpressure in aiommbot on top of a taskiq feature that isn't reliable yet; track upstream or pin a version where it's fixed. |
| (j) error reporting (Sentry) | **Extra**, thin adapter only | No peer bot framework (aiogram, Bolt, discord.py, hikari, PTB) has an official Sentry integration — this is BO-specific value, but it should be a narrow Protocol-shaped adapter around `sentry_sdk`, not the redaction/formatting pipeline 0.4.8 built in-house. |
| (k) event-loop selection (uvloop) | **Recipe** (one line in the composition root, or delegate entirely like Uvicorn's `--loop auto`) | Every peer either delegates this to the ASGI server (`uvicorn --loop`)²⁷ or leaves it to the user (`uvloop.install()`); none of the bot frameworks switch loops themselves. |
| (l) graceful shutdown/lifespan | **Core** | Universal: every framework surveyed, without exception, owns this in core²⁸·¹⁰·¹¹ — it's the one true "wiring" concern with no safe delegation target. |
| (m) health endpoints | **Core (helper), not a plugin** | FastStream's `make_ping_asgi` is the right size — a tiny helper that pings what the framework already knows how to ping (broker/Mongo/Mattermost connectivity), left for the app to mount¹⁸; a bespoke health *subsystem* would be over-scoped for what every peer treats as "a plain route." |

## 6. Bot-specific vs. generic-infrastructure capabilities

None of the eleven peers is a chat-bot framework with durable per-user state and webhook callbacks
the way aiommbot is, so this split is argued from first principles, not read off a peer's docs.

**Genuinely bot-specific — keep as first-class framework concepts, not delegable to a generic
library:**

- **Per-user/event isolation and FSM admission.** aiogram's `StorageKey(bot_id, chat_id, user_id,
  thread_id)`/`FSMStrategy`/`BaseEventIsolation` lock has no generic-library equivalent — it's domain
  logic about how a chat protocol's identifiers compose into a state key. aiommbot's own
  `Context.state`/FSM belongs here, not in any "small core" trim.
- **Webhook callback signing/verification.** Bolt's `RequestVerification`/`UrlVerification`
  middlewares are the closest precedent: protocol-specific signature schemes are core to every
  framework that has webhooks, never delegated to a generic library. aiommbot's protected-hook-segment
  and callback enforcement is the same category and should stay core.
- **Stale-action/duplicate-callback handling** (double-clicked dialog button, action replay). Dedup,
  but keyed on chat-protocol semantics (post id, action id, dialog submission id) no generic
  idempotency library knows about — needs a protocol-aware compare-and-set in the repository layer.
- **Inbound flood control keyed on chat identity.** Unlike outbound rate limiting (a solved,
  "adjacent SDK" problem — Bolt's `RateLimitErrorRetryHandler`⁴, discord.py's `HTTPClient` buckets⁵),
  inbound throttling keys on the bot's own identifiers (user/channel/dialog) — why aiogram deleted its
  built-in version instead of keeping a generic one: the right cache key is app-specific⁶.

**Generic infrastructure — no peer treats these as bot-specific, and every §5 placement assumes so:**
scheduling (identical problem for any consumer, solved by taskiq/arq/Celery); metrics/tracing/Sentry
(identical regardless of what's instrumented); circuit breaking, generic retries, dead-letter
(identical patterns over any external dependency — Mattermost's API is just one more `dependency`
label); CLI runner, graceful shutdown, event-loop selection (process-lifecycle, zero chat-protocol
content).

Practical implication: trim the generic-infrastructure list aggressively (where 0.4.8's
Prometheus-for-every-subsystem, purgatory-in-core, and Sentry-middleware-in-core sit) while treating
the bot-specific list as protected surface — cutting FSM/webhook-signing/stale-action handling to
"save dependencies" would cut the actual product, not trim bloat.

## Sources

1. aiogram + APScheduler community recipes (middleware injection, `asyncio.gather` pattern) — <https://nztcoder.com/2022/10/24/kak-ispolzovat-apscheduler-v-aiogram/>
2. discord.py `ext.tasks` — <https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html>
3. python-telegram-bot `JobQueue` (`[job-queue]` extra) — <https://docs.python-telegram-bot.org/en/stable/telegram.ext.jobqueue.html>
4. `slack_sdk.http_retry.builtin_handlers.RateLimitErrorRetryHandler` — <https://docs.slack.dev/tools/python-slack-sdk/reference/http_retry/builtin_handlers.html>
5. discord.py `HTTPClient` rate-limit bucket handling (source + community reports) — <https://github.com/Rapptz/discord.py/issues/2320>
6. aiogram 2→3 migration guide (`dispatcher.throttle()` removed) — <https://docs.aiogram.dev/en/latest/migration_2_to_3.html>
7. aiogram `Dispatcher`/`Router` internals (`handle_as_tasks`, `tasks_concurrency_limit`, `emit_startup`/`emit_shutdown`) — prior in-repo research, `docs/research/03-bot-framework-architectures.md`, citing `aiogram` source `dispatcher/dispatcher.py`, `dispatcher/router.py` — <https://github.com/aiogram/aiogram>
8. PTB `BaseUpdateProcessor`/`concurrent_updates` — <https://docs.python-telegram-bot.org/en/stable/telegram.ext.baseupdateprocessor.html>
9. Sentry Python integrations overview (aiogram absent from the list) — <https://docs.sentry.io/platforms/python/integrations/>
10. discord.py `setup_hook()`/lifecycle (`migrating.html`) — <https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html>; Sanic background tasks (`app.add_task`, listeners) — <https://sanic.dev/en/guide/basics/tasks.html>
11. hikari `GatewayBot` lifecycle (`run()`/`start()`/`join()`, `enable_signal_handlers`) — prior in-repo research, `docs/research/03-bot-framework-architectures.md`, citing `hikari` source — <https://github.com/hikari-py/hikari>
12. `taskiq-faststream` companion package — <https://github.com/taskiq-python/taskiq-faststream>
13. `litestar-saq` official SAQ plugin — <https://github.com/litestar-org/litestar-saq>
14. `sanic-scheduler` third-party package — <https://pypi.org/project/sanic-scheduler/>; Sanic cron feature request (unresolved) — <https://github.com/sanic-org/sanic/issues/2233>
15. `django-celery-beat` (`DatabaseScheduler`) — <https://github.com/celery/django-celery-beat>; Celery periodic tasks — <https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html>
16. FastStream `pyproject.toml` (`otel`, `prometheus` extras) — <https://github.com/ag2ai/faststream/blob/main/pyproject.toml>
17. `prometheus-fastapi-instrumentator` — <https://github.com/trallnag/prometheus-fastapi-instrumentator>; `opentelemetry-instrumentation-fastapi` — <https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation/opentelemetry-instrumentation-fastapi>
18. FastStream CLI + ASGI health checks (`faststream run`, `make_ping_asgi`) — <https://faststream.ag2.ai/latest/getting-started/observability/healthcheks/>, <https://faststream.ag2.ai/latest/getting-started/asgi/>
19. Litestar CLI (click-based, `CLIPlugin`, entry points) — <https://docs.litestar.dev/main/usage/cli.html>
20. FastAPI CLI (`fastapi-cli`, `fastapi[standard]`) — <https://fastapi.tiangolo.com/fastapi-cli/>, <https://github.com/fastapi/fastapi-cli/blob/main/pyproject.toml>
21. Sanic CLI (`sanic path.to.server:app`) — <https://sanic.dev/en/guide/running/running.html>
22. FastStream removed `retry=True` shortcut — <https://github.com/ag2ai/faststream/discussions/1161>; release notes — <https://faststream.ag2.ai/latest/release/>
23. Litestar `RateLimitConfig` + X-Forwarded-For advisory — <https://docs.litestar.dev/2/reference/middleware/rate_limit.html>, <https://github.com/litestar-org/litestar/security/advisories/GHSA-hm36-ffrh-c77c>
24. Sanic background-task registry (`get_task`/`cancel_task`/`purge_tasks`) — <https://sanic.dev/en/guide/basics/tasks.html>; OpenTelemetry auto-instrumentation (`opentelemetry-bootstrap`) — <https://github.com/open-telemetry/opentelemetry-python-contrib>
25. Sentry SDK auto-enabled framework integrations list — <https://docs.sentry.io/platforms/python/integrations/>
26. Sentry FastAPI/Starlette integrations — <https://docs.sentry.io/platforms/python/integrations/fastapi/>, <https://docs.sentry.io/platforms/python/integrations/starlette/>
27. Uvicorn event-loop selection (`--loop auto|asyncio|uvloop`) — <https://uvicorn.dev/concepts/event-loop/>, <https://uvicorn.dev/settings/>
28. Starlette `lifespan` — <https://www.starlette.io/lifespan/>
29. Litestar testing docs (plain `@get` health-check pattern, no bundled plugin) — <https://docs.litestar.dev/latest/usage/testing.html>
30. taskiq scheduling (`TaskiqScheduler`, `LabelScheduleSource`) — <https://taskiq-python.github.io/guide/scheduling-tasks.html>, <https://taskiq-python.github.io/available-components/schedule-sources.html>
31. arq `cron()`/`WorkerSettings.cron_jobs` — <https://arq-docs.helpmanual.io/>, <https://github.com/python-arq/arq/blob/main/arq/worker.py>
32. Celery `autoretry_for`/`retry_backoff`, `acks_late` idempotency requirement, no native DLQ — <https://docs.celeryq.dev/en/stable/userguide/tasks.html>
33. Circuit breaker maintenance comparison (purgatory/aiobreaker/pybreaker) — <https://github.com/mardiros/purgatory>, <https://github.com/arlyon/aiobreaker>, <https://github.com/danielfm/pybreaker>; APScheduler 4 pre-release status — <https://github.com/agronholm/apscheduler/issues/465>, <https://pypi.org/project/APScheduler/4.0.0a6/>; taskiq `max_async_tasks` semaphore bug — <https://github.com/taskiq-python/taskiq/issues/396>
34. `aiolimiter` (`AsyncLimiter` leaky bucket) — <https://github.com/mjpieters/aiolimiter>
35. `stamina` (opinionated wrapper over tenacity) — <https://github.com/hynek/stamina>, <https://stamina.hynek.me/>
36. `tenacity` — <https://github.com/jd/tenacity>
