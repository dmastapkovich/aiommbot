# 26. Schedule, reliability and probe primitives

**Question.** What primitives exist in Python as of September 2026 for cron and interval scheduling,
retries, rate limiting and circuit breaking; what do peer frameworks ship for scheduling and what
reason did they record for the placement; and what contract does a health probe have to satisfy?

Gathered for GitHub issue #94. [`docs/research/08`](08-peer-responsibility-boundaries.md) records
the placement each peer chose for these capabilities and names the candidate libraries one line
each. Choosing a placement *and*, where a capability is ours, a library needs three things that
were not written down anywhere: the state of the cron parsers, the recorded reason behind
python-telegram-bot's demotion of `JobQueue`, and the Kubernetes probe contract.

Findings only. Sources are primary — PyPI JSON metadata, project source and release notes on
`raw.githubusercontent.com` and the GitHub API, `docs.python.org`, `kubernetes.io`, the IETF
datatracker and each project's own documentation — read on 2026-09-09. Anything a primary source did
not confirm is marked **[unverified]**.

## 1 The standard library schedules nothing on a calendar

The only event scheduler in the standard library is
[`sched`](https://docs.python.org/3/library/sched.html), whose class is
`sched.scheduler(timefunc=time.monotonic, delayfunc=time.sleep)`. It schedules single events by
absolute time (`enterabs`) or relative delay (`enter`), delegates all time handling to the two
injected callables — `timefunc` must "return a number (the 'time', in any units whatsoever)" — and
its documentation page contains no cron or crontab syntax at all. It offers no recurrence, no
timezone awareness and no catch-up semantics; a repeating event must re-enter itself. It has been
documented as thread-safe since 3.3, and there is no asyncio-native equivalent.

Enumerating the [module index](https://docs.python.org/3/library/index.html), the
scheduling-adjacent modules are `sched`, `time`, `datetime`, `zoneinfo` and `calendar`. **No
standard-library module
parses a cron expression**, so a cron-driven schedule requires a dependency or an implementation of
one's own.

asyncio's timers are monotonic, not wall clock: `loop.time()` returns "the current time … according
to the event loop's internal monotonic clock", `loop.call_at(when, …)` "uses the same time reference
as loop.time()", and callbacks "may run up to one clock-resolution early"
([asyncio event loop](https://docs.python.org/3/library/asyncio-eventloop.html)).

## 2 The cron-expression parsers

| Package | Version | Date | Licence | Runtime dependencies | `requires_python` | State |
|---|---|---|---|---|---|---|
| `croniter` | 6.2.4 | 2026-07-10 | MIT | `python-dateutil` | `>=3.9` | maintained by Pallets-Eco; classifier still "4 - Beta" |
| `cron-converter` | 2.0.1 | 2026-08-17 | MIT | `python-dateutil` | `>=3.8` | maintained, low traffic (50 stars) |
| `crontab` (parse-crontab) | 1.0.5 | 2025-07-09 | **LGPL-2.1** | none | not declared | no commit in ~14 months |
| `pycron` | 3.2.0 | 2025-06-05 | MIT | none | `<4,>=3.9` | no commit in ~11 months |
| `APScheduler` | 3.11.3 | 2026-06-28 | MIT | `tzlocal>=3.0` | `>=3.8` | very active repository |

**`croniter` was declared dead and then adopted.** Its README at tag 6.0.0 (2024-12-17) opened with
the heading "UNMAINTAINED/ABANDONED CODE / DO NOT USE", cited the EU Cyber Resilience Act and told
users not to rely on it after 15 March 2025. Its own changelog records both halves: 6.0.0 "Announce
for now that croniter dev is ended (CRA)." and 6.1.0 (2026-03-14) "Announce back that croniter is
maintained now as part of pallets-eco." The current README carries the Pallets Community Ecosystem
notice instead. The post-adoption cadence is bursty — 6.1.0 through 6.2.3 were all published on
2026-07-02, then 6.2.4 on 2026-07-10.

`croniter` still has open DST correctness defects: issue #258, "get_next skips a fire time when the
DST shift is not a whole hour" (opened 2026-08-02), with open pull requests #266 and #267. Its
README requires the caller to supply an aware start datetime — "Be sure to init your croniter
instance with a TZ aware datetime for this to work!" — and its unreleased 6.3.0 changelog warns that
fixing `{max}/{step}` expansion "changes existing schedules, silently and substantially":
`* * * * 6/1` "meant *every day* and now means *Saturdays only*", `59/1 * * * *` "meant *every
minute* and now
means *minute 59*". A cron dialect is a contract, and this one moved under its users.

**APScheduler 4 is still not releasable.** The newest 4.x artefact on PyPI is `4.0.0a6`, uploaded
2025-04-27, and the complete 4.x history is a1 (2022-08-16) through a6 — no beta, no release
candidate, no final, and ~17 months of silence on that line. The project's own README says: "The
v4.0 series is provided as a **pre-release** and may change in a backwards incompatible fashion
without any migration pathway, so do NOT use this release in production!" The 4.x documentation's
version history has no released entry newer than a6; its top heading is "UNRELEASED". Under
[PEP 440](https://peps.python.org/pep-0440/) a pre-release is "implicitly excluded from all version
specifiers" unless explicitly requested, so `pip install APScheduler` resolves to the maintained
3.x line. 3.11.0 added ZoneInfo support and dropped `six`, which is why 3.11.3 carries only
`tzlocal` unconditionally; every backend is an extra.

`pycron` is a **matcher, not an iterator**: its only public functions are `is_now(s, dt=None)` and
`has_been(s, since, dt=None)`, and it cannot compute the next matching datetime — `has_been` steps
minute by minute calling `is_now`. That shapes its consumer: **taskiq depends on `pycron>=3.0.0` as
a core dependency and therefore polls**, sleeping to the next whole second and looping with a
`loop_interval` defaulting to one second. Its timezone handling is a shift applied to `now` before
matching.

**arq has no cron dependency at all.** Its runtime dependencies are `redis[hiredis]` and `click`; it
implements its own matcher over an `Options` dataclass whose month, day, weekday, hour, minute,
second and microsecond fields are each an exact `int` or a membership set. There is no cron string
syntax. `next_cron` starts one second after the previous fire and repeatedly calls `_get_next_dt`,
which walks the fields coarsest first and, on the first mismatch, returns a jumped datetime. Fields
are read from the wall-clock components of `Worker.timezone`; `microsecond` defaults to `123456`
"as the world is busier at the top of a second". Timezone support was retrofitted — issue #351
(2022-10-09) reported that a job scheduled for 12 o'clock ran at 12 o'clock *local* time on the
worker's host, PR #354 added `Worker.timezone`, and PR #383 then fixed timezone info being dropped
when the month field incremented. arq's PyPI description states the project is "in maintenance only
mode".

## 3 Why scheduling is harder than it looks

Five hazards, each from a primary source.

- **Monotonic against wall clock.** `time.monotonic()` is "a clock that cannot go backwards … not
  affected by system clock updates", while `time.time()` "can return a lower value than a previous
  call if the system clock has been set back". An interval measured with wall-clock timestamps can
  fire twice or stall on an NTP step ([`time`](https://docs.python.org/3/library/time.html)).
- **`timedelta` arithmetic ignores DST.** The
  [`datetime`](https://docs.python.org/3/library/datetime.html) documentation states, for both
  addition and subtraction, "Note that no time zone adjustments are done even if the input is an
  aware object." Stepping a schedule with `dt + timedelta(hours=1)` moves the wall clock, not the
  instant — which is exactly the arithmetic arq's matcher performs.
- **Ambiguous wall times need `fold`.** `datetime.fold` disambiguates "a repeated interval … when
  clocks are rolled back", and
  [`zoneinfo`](https://docs.python.org/3/library/zoneinfo.html) implements PEP 495: the offset from
  before the transition applies when `fold=0` and the one after when `fold=1`. A cron implementation
  must decide which of the two occurrences fires.
- **Cron semantics are wall-clock semantics, and the anomalies are by design.** APScheduler's
  `CronTrigger` documentation states that with DST "it may cause unexpected behavior … it may
  execute more often or less often than expected. This is not a bug." A cron implementation must
  also detect non-existent times; APScheduler 4.x ships `time_exists(dt)`, "``False`` if the given
  datetime falls within a gap created by a forward daylight savings shift", implemented as
  `dt == datetime.fromtimestamp(dt.timestamp(), dt.tzinfo)`.
- **This class of bug does not get finished.** Two of APScheduler 3.x's three most recent releases
  are DST fixes, in a fifteen-year-old project with 7,627 stars. Issue #1103 (2026-03-09, closed
  2026-06-28) reported sub-minute interval jobs stalling for exactly one hour during the 2026-03-08
  spring forward, and the 3.11.3 changelog names the cause: "the wakeup delay being computed from
  the naive wall-clock difference instead of the actual UTC difference". APScheduler 3.x's weekday
  numbering also diverges from Vixie cron — "Due to a historical mistake … APScheduler treats 0 as
  Monday while the original crontab treats it as Sunday. This has been rectified in the v4.x series
  but cannot be changed in the 3.x series due to backwards compatibility."

A scheduler additionally needs a policy for fires it missed. APScheduler defines *misfire*
("Sometimes the scheduler may be unable to execute a scheduled job at the time it was scheduled to
run"), checks each missed run against `misfire_grace_time`, and separately offers `coalesce`, which
collapses several queued executions into one and is "turned off for new jobs by default".

## 4 What peers ship for scheduling, and the reasons they recorded

**python-telegram-bot** is the clearest recorded demotion. Its base install pulls only `httpx` (plus
`httpcore` on Python ≥ 3.14); `APScheduler>=3.10.4,<3.12.0` appears solely under the `job-queue`
extra and the two extras that include it. The recorded rationale is footprint, from the v20
transition guide: "Since these features are optional to use and we aim to keep the footprint of
python-telegram-bot small, we have reduced the number of 3rd party dependencies that automatically
get's installed along with python-telegram-bot to a minimum", and its README states the policy as a
principle — "python-telegram-bot tries to use as few 3rd party dependencies as possible. However,
for some features using a 3rd party library is more sane than implementing the functionality again."
The change is PR #3267 (opened 2022-09-30, merged 2022-10-31, +461/−167 over 30 files), shipped in
v20.0a5 on 2022-11-22 as "Make Almost All 3rd Party Dependencies Optional (#3267)"; the v20.0 final
notes do not mention it, so the v20 release page alone will not find the reason.

The mechanics are worth copying. `telegram/ext/_jobqueue.py` guards the import with a module-level
flag rather than a hard import, so `import telegram.ext` still succeeds; constructing `JobQueue`
raises `RuntimeError` with the message "To use `JobQueue`, PTB must be installed via
`pip install \"python-telegram-bot[job-queue]\"`."; and `ApplicationBuilder` catches exactly that
error — narrowed on the message string — and leaves `Application.job_queue` as `None`, so the
failure surfaces when scheduling is attempted rather than at build time. One documented knock-on
effect: without the extra, `ConversationHandler.conversation_timeout` stops working, "as this uses
telegram.ext.Application.job_queue internally."

The earlier history is the contrast. Issue #2257, "[FEATURE] APScheduler should be optional
dependency", was opened 2020-12-20 by an Apache Airflow maintainer and closed thirty minutes later:
"We use APScheduler as a library to provide our job queue, which tightly integrates with the rest of
our library … I do not think any current maintainer is willing to provide this effort to apply to
your rather specific use case."

**discord.py** is the one bot framework shipping scheduling in the base wheel, and it ships the
narrow version. `discord.ext.tasks` is listed in the package list beside `discord.ext.commands`, and
`loop` is keyword-only over `seconds`, `minutes`, `hours`, `time`, `count`, `reconnect` and `name`.
There is **no cron support** — the only calendar-shaped option is a list of `datetime.time` values,
and "Duplicate times will be ignored, and only run once." With `reconnect=True`, the default, it
retries a fixed five-member exception tuple — `OSError`, `discord.GatewayNotFound`,
`discord.ConnectionClosed`, `aiohttp.ClientError`, `asyncio.TimeoutError` — with exponential
backoff "similar to the one used in discord.Client.connect()"; any other exception reaches a default
handler that only logs, after which the loop re-raises and ends. It corrects clock drift explicitly,
re-sleeping and logging "Clock drift detected for task %s" whenever it wakes at or before the last
iteration. The documentation frames the whole extension as abstracting three worries: "How do I
handle asyncio.CancelledError? What do I do if the internet goes out? What is the maximum number of
seconds I can sleep anyway?"

**FastStream** ships nothing scheduling-shaped: none of its nine extras contains `taskiq`,
`apscheduler` or `croniter`. `taskiq-faststream` is a separate distribution in the *taskiq*
organisation (0.4.1, 2026-06-10) depending on both, and is "a wrapper for FastStream objects to make
them compatible with Taskiq library" — it registers publish-shaped tasks carrying a cron label and
runs them from a `StreamScheduler`; the consumer must be running separately. FastStream's own
documentation recommends the split: "Creating a separated Scheduler service is the best way to make
a really distributed and sustainable system."

**Litestar** is the same shape one layer out: `litestar-saq` (0.8.0, 2026-06-03) depends on
`litestar` and `saq`, and the cron parsing belongs to `saq`, whose single base dependency is
`croniter>=0.3.18`. `litestar-saq`'s own `CronJob` is a thin subclass adding import-string
resolution of the target function.

**aiogram** ships nothing and refused explicitly. Issue #1195, "Task scheduler (Similar to Jobqueue
of Python Telegram Bot)", was closed `not_planned` on 2023-07-02 by maintainer JrooTJunior: "This
task is not related to aiogram by itself … there is not one most universal solution for that … So,
you can use any scheduler with aiogram that you want", listing APScheduler, aiocron, a Kubernetes
CronJob, a systemd timer, RabbitMQ delayed messages and Kafka. (aiogram's own CLI is likewise an
opt-in separate distribution, `aiogram-cli`, behind its `cli` extra.)

**hikari** ships nothing; scheduling lives in `hikari-lightbulb` (3.2.6), which offers
`uniformtrigger` and `crontrigger` and gates the second behind an extra — "To use this trigger you
need to install Lightbulb with the optional dependency [crontrigger]" — with `croniter>=6.2.4,<7`
under `extra == "crontrigger"`. Two of its documented semantics are the ones any owner must choose:
"The crontab is always evaluated using UTC time", and there is no catch-up — an execution that
overruns pushes the next to "the next suitable time after the execution completed", so a 5-minute
crontab whose run takes 6 minutes next fires at minute 10.

## 5 Exactly one scheduler process, and what each project does about it

Celery states the constraint and the reason together: "You have to ensure only a single scheduler is
running for a schedule at a time, otherwise you'd end up with duplicate tasks. Using a centralized
approach means the schedule doesn't have to be synchronized, and the service can operate without
using locks." Its beat state lives in a local file, `celerybeat-schedule`, relocatable with `-s`.

taskiq states it more sharply: "Please always run only one instance of the scheduler! If you run
more than one scheduler at a time, please be careful since it may execute one task N times, where N
is the number of running scheduler instances." Its scheduler is a pure dispatcher — "The scheduler
doesn't execute tasks. It only sends them." — and it ships **no lock and no leader election**; open
issue #438 (2025-04-02) asks for a Celery-style embedded scheduler that does not exist.

Two projects solve it rather than warn about it.

- **arq** attaches cron jobs to the Worker and supports several workers, because `unique=True` (the
  default) derives a deterministic job id from the name and the millisecond timestamp of the next
  run — `f'{cron_job.name}:{to_unix_ms(cron_job.next_run)}'` — so every worker computes the same id
  and Redis accepts one. "If unique is true (the default) the job will only be run once even if
  multiple workers are running." No lock is involved.
- **celery-redbeat** takes the lock route: it stores the schedule in Redis and lists "Prevent
  accidentally running multiple Beat servers" as a feature, with `redbeat_lock_key` (default
  `<prefix>:lock`) and `redbeat_lock_timeout`, whose default of 1500 seconds is "five times of the
  default scheduler's loop interval (300 seconds)". Setting `redbeat_lock_key = None` disables it.

`django-celery-beat` documents neither a warning nor a lock; it inherits the constraint from
Celery's own page, and it does document an embedded development mode,
`celery -A proj worker --beat --scheduler django`.

## 6 The reliability libraries

| Library | Version | Date | Licence | Runtime dependencies | `requires_python` | State |
|---|---|---|---|---|---|---|
| `stamina` | 26.1.0 | 2026-04-13 | MIT | `tenacity` | `>=3.10` | active — last push 2026-09-07, 1 open issue |
| `tenacity` | 9.1.4 | 2026-02-07 | Apache-2.0 | none | `>=3.10` | active |
| `aiolimiter` | 1.3.0 | 2026-09-07 | MIT | none | `>=3.10` | active |
| `PyrateLimiter` | 4.5.0 | 2026-08-30 | MIT | none (backends are extras) | `>=3.10` | active |
| `limits` | 5.8.0 | 2026-02-05 | MIT | `deprecated`, `packaging`, `typing-extensions` | `>=3.10` | active |
| `purgatory` | 3.0.1 | 2024-11-02 | MIT | none (`redis` extra) | `>=3.9` | **no commit on main since 2024-11-07** |
| `pybreaker` | 1.4.1 | 2025-09-21 | BSD-3-Clause (GitHub only) | none | `>=3.9` | last code commits 2025-09-21 |
| `aiobreaker` | 1.2.0 | 2021-05-17 | BSD | none (`redis` extra) | `>=3.6` | last commit 2021-12-27 |
| `aiopylimit` | 1.0.1 | 2022-07-25 | — | none | not declared | abandoned |
| `sentry-sdk` | 2.69.1 | 2026-09-08 | MIT | `urllib3>=1.26.11`, `certifi` | `>=3.6` | active |

**Retries are solved.** `stamina` still depends on `tenacity` and uses it as an internal engine only
— `import tenacity as _t`, referencing `Retrying`, `AsyncRetrying`, `RetryCallState` — behind a
twelve-name public surface. It is asyncio-native at the iterator level: its retry-context iterator
defines `__iter__`, `__aiter__` and `async def __anext__`, so the same object serves `for` and
`async for`, and `retry()` dispatches at decoration time on `isgeneratorfunction`,
`isasyncgenfunction` and `iscoroutinefunction`. It ships a first-party testing mode,
`set_testing(testing, *, attempts=1, cap=False)`, which disables backoff and is usable as a context
manager. Note one packaging fact: a GitHub release `tenacity` 9.2.0 exists (2026-08-05) that is not
on PyPI, so the newest installable version is 9.1.4.

**Circuit breaking is not solved.** Of the four candidates, `pybreaker` has a Redis-backed shared
store but **no asyncio at all** — the whole library contains zero occurrences of `asyncio`,
`async def`, `await` or `iscoroutinefunction`, and its only asynchronous path is Tornado generator
coroutines through `call_async`; its `CircuitRedisStorage` issues blocking Redis commands.
`aiobreaker` is asyncio-native in its core but its Redis storage is not, and it has had no commit
since 2021-12-27. `aiocircuitbreaker` is one 2022 release with no backend and no declared licence.
`purgatory` is genuinely asyncio-native with an `AsyncRedisRepository` and is the only one combining
both properties — and its main branch has not moved in about twenty-two months. **As of September
2026 there is no maintained, asyncio-native circuit breaker with shared state** **[unverified as an
exhaustive statement — four packages were checked, not every package tagged circuit-breaker]**.

**Rate limiting splits by scope.** `aiolimiter`'s `AsyncLimiter` guarantees `max_rate` acquisitions
per `time_period` and explicitly permits a burst of `max_rate` at once; its documented scope limit
is one event loop per instance, and it offers no shared or distributed state at all.
`PyrateLimiter` 4.x is the maintained distributed alternative with a real async path —
`try_acquire` and `try_acquire_async` over `InMemoryBucket`, `RedisBucket`, `SQLiteBucket`,
`PostgresBucket` and
`MultiprocessBucket`. `limits` is the other maintained option, with storage behind extras.

**Error reporting needs no framework integration.** `sentry-sdk` carries exactly two runtime
dependencies and puts everything else behind roughly fifty extras. Its integrations directory holds
71 modules and 9 sub-packages and contains **no module for telegram, aiogram, discord, hikari, slack
or mattermost**; the documentation's integrations index lists no chat-bot framework either. Eight
integrations are enabled with no framework at all — Argv, Atexit, Excepthook, Deduplication, Stdlib,
Modules, Logging, Threading — and capturing an exception the application has already caught is
documented as plain `try`/`except` plus `sentry_sdk.capture_exception(e)`, with the argument
optional.

## 7 The probe contract

### 7.1 What Kubernetes actually specifies

From the [probes reference](https://kubernetes.io/docs/concepts/workloads/pods/probes/) — note the
detail moved off the pod-lifecycle page, which now only summarises and links.

- Four mechanisms: `exec`, `grpc`, `httpGet`, `tcpSocket`.
- For `httpGet`, the kubelet counts a response as success **if and only if the status code is ≥ 200
  and < 400**. Success is decided by the status code; the body is not parsed. The kubelet stops
  reading the body after 10 KiB and closes the connection, which can appear in an application log as
  a reset peer, and the documentation "strongly recommend[s] dedicated health endpoints returning a
  minimal body".
- Each execution yields Success, Failure or Unknown; on Unknown no action is taken.
- **Liveness Failure kills the container** and applies its restart policy, after `failureThreshold`
  consecutive failures. **Readiness Failure removes the Pod's address from the EndpointSlices** of
  every matching Service and does not restart anything. **Startup Failure kills the container**, and
  while a startup probe is configured and not yet succeeding, liveness and readiness are withheld.
- A probe that is not defined is treated as Success; readiness before the initial delay is treated
  as Failure.
- Defaults: `initialDelaySeconds` 0, `periodSeconds` 10, `timeoutSeconds` 1, `successThreshold` 1
  (and it must be 1 for liveness and startup), `failureThreshold` 3. Probe-level
  `terminationGracePeriodSeconds` inherits the Pod value, itself 30 seconds when unspecified.
- The cascading-failure caution: an incorrect liveness implementation restarts containers under high
  load, fails client requests and increases load on the survivors, so liveness must indicate only an
  unrecoverable failure such as a deadlock. Dependency checking belongs in **readiness**: the
  liveness probe passes when the application itself is healthy, while readiness additionally checks
  that each required back-end is available.
- A liveness probe is not necessarily needed at all when the process crashes on its own; a common
  documented pattern is to point liveness at the same low-cost endpoint as readiness with a higher
  `failureThreshold`.
- `exec` probes "fork multiple processes on every execution", so at high pod density or low
  `periodSeconds` they add measurable node CPU overhead, and other mechanisms are recommended there.

### 7.2 There is no standard for the response

The only IETF attempt, `draft-inadarei-api-health-check`, *Health Check Response Format for HTTP
APIs*, reached revision -06, was published 2021-10-16, **expired 2022-04-19**, was never adopted by
a working group and never became an RFC. It proposed `application/health+json` with a mandatory
`status` restricted to `pass`, `fail` and `warn`. The de facto shape is Spring Boot Actuator's
`/actuator/health` — a top-level `status` plus a `components` map — whose statuses are `UP`, `DOWN`,
`OUT_OF_SERVICE` and `UNKNOWN`, which maps `DOWN` and `OUT_OF_SERVICE` to 503 and everything else to
200, and whose detail visibility defaults to `never`. Spring gives the same dependency rule as
Kubernetes: the liveness probe must not depend on checks of external systems, because Kubernetes
responds to a broken liveness state by restarting the instance.

### 7.3 What the Python peers expose

- **FastStream** is the only one shipping a helper: `make_ping_asgi` awaits `broker.ping(timeout)`
  and answers `204` with an empty body when true and `500` when false. It is **not mounted by
  default** — `AsgiFastStream`'s `asgi_routes` defaults to the empty tuple — and its meaning differs
  per broker: the Redis broker issues a real `PING` round trip in a retry loop with a default
  timeout of 3, while the RabbitMQ broker only polls a local `connected` flag. So the same 204
  carries different guarantees.
- **Django, FastAPI, Litestar and Sanic core ship nothing.** Django's URL reference enumerates its
  complete built-in surface and no health view is in it; for FastAPI and Litestar the finding rests
  on repository code searches returning zero results **[unverified as a positive statement]**. Sanic
  Extensions ships a worker *health monitor* whose optional HTTP route at `/__health__` is
  unsecured and exposes worker PIDs and restart timestamps, disabled by default.
- **Celery** has no HTTP endpoint; liveness is the broker-mediated `ping` remote control, replying
  `pong` with a one-second default reply timeout, plus worker-heartbeat events.
- **arq** writes a liveness sentinel into Redis with `psetex` and a TTL of
  `(health_check_interval + 1) * 1000` milliseconds, so the key's existence alone proves recency;
  `health_check_interval` defaults to 3600 seconds. `arq --check` reads the key and exits 0 when
  present, 1 when absent, logging "Health check failed: no health check sentinel value found". arq's
  documentation never mentions Kubernetes.
- **taskiq** has no health, liveness or readiness mechanism **[unverified as a positive
  statement — established by a repository code search returning zero results]**.

### 7.4 Probing a process whose only connection is outbound

Kubernetes supports `exec` (success only on exit 0) and `tcpSocket` (success when the port is open)
for a workload that serves no HTTP, but its probe reference is written around inbound-server
semantics and contains **no guidance for a workload whose main job is a long-lived outbound
connection** **[unverified — established by reading the page and finding no such section]**. The
readiness contract in particular is expressed purely as EndpointSlice and Service membership, which
a Pod with no listening port never has.

Both primary examples solve it the same way — a small HTTP server in the same container reporting
the outbound client's state.

- `slackapi/bolt-python` ships `examples/socket_mode_healthcheck.py`, which runs Flask on port 8080
  solely to host the probe: `/health` returns 200 "OK" when `socket_mode_handler.client` is not
  `None` and `client.is_connected()`, and 503 "The Socket Mode client is inactive" otherwise. The
  structure is deliberate — the WebSocket client is started non-blocking, annotated "does not block
  the current thread", and the main thread is handed to the HTTP server. The readiness signal itself
  is a **local flag**: `SocketModeClient.is_connected()` returns
  `self.current_session is not None and self.current_session.is_active()` and sends no ping at probe
  time. Asked for a built-in endpoint (issue 439, 2021), the maintainers pointed at composing Bolt
  with an ordinary HTTP framework instead.
- `cloudflared` exposes `/ready` on its metrics server, 200 when `CountActiveConns() > 0` and 503
  otherwise, commented in the source as "Intended for k8s readiness checks". Cloudflare's own
  Kubernetes tutorial then wires that endpoint as a **livenessProbe** with `failureThreshold: 1` —
  a dependency check on liveness, which is precisely what the Kubernetes caution warns against.
  FastStream's single `/health` has the same shape: a broker ping used as the only endpoint.

## 8 What the evidence supports

- **Scheduling is a capability with a maintenance tail, not a feature.** Every bot framework that
  owns one either keeps it interval-only in the base wheel (discord.py, with explicit drift
  correction and no cron) or pushes it behind an extra or a separate distribution (PTB, hikari via
  lightbulb, FastStream via taskiq-faststream, Litestar via litestar-saq); aiogram refused outright.
  Owning cron means owning a dialect that moved under its users this year and a DST class of bug
  that a fifteen-year-old project still ships fixes for.
- **The single-scheduler hazard has exactly two known answers**: a distributed lock (redbeat) or a
  deterministic, fire-time-keyed job id that makes a duplicate a no-op (arq). Warning the operator,
  which is what Celery and taskiq do, is the third and weakest.
- **Retries have a good answer and breakers do not.** `stamina` is small, typed, asyncio-native and
  actively maintained; nothing in the circuit-breaker set is all four.
- **Distributed rate limiting has moved on** from `aiolimiter`, which is explicitly single-loop, to
  `PyrateLimiter` and `limits`.
- **Sentry needs nothing from a framework** beyond a place to call `capture_exception`, and it has
  never shipped a chat-bot integration.
- **A probe is a status code, not a document.** Kubernetes reads only 200–399, recommends a minimal
  body, and puts dependency checks in readiness and never in liveness. For a process whose only
  connection is outbound, the practised answer is a tiny HTTP surface reporting a locally held
  connection flag — not a ping at probe time.

## Sources

Standard library and specifications:

- <https://docs.python.org/3/library/sched.html> · <https://docs.python.org/3/library/index.html> · <https://docs.python.org/3/library/asyncio-eventloop.html> · <https://docs.python.org/3/library/time.html> · <https://docs.python.org/3/library/datetime.html> · <https://docs.python.org/3/library/zoneinfo.html>
- <https://peps.python.org/pep-0440/>
- <https://datatracker.ietf.org/doc/draft-inadarei-api-health-check/> · <https://www.ietf.org/archive/id/draft-inadarei-api-health-check-06.html>

Cron parsers and schedulers:

- <https://pypi.org/pypi/croniter/6.2.4/json> · <https://raw.githubusercontent.com/pallets-eco/croniter/main/pyproject.toml> · <https://raw.githubusercontent.com/pallets-eco/croniter/main/README.rst> · <https://raw.githubusercontent.com/pallets-eco/croniter/main/CHANGELOG.rst> · <https://raw.githubusercontent.com/pallets-eco/croniter/6.0.0/README.rst> · <https://github.com/pallets-eco/croniter/issues/258>
- <https://raw.githubusercontent.com/Sonic0/cron-converter/main/pyproject.toml> · <https://pypi.org/pypi/crontab/json> · <https://raw.githubusercontent.com/josiahcarlson/parse-crontab/master/crontab/_crontab.py> · <https://pypi.org/pypi/pycron/json> · <https://raw.githubusercontent.com/kipe/pycron/main/pycron/__init__.py>
- <https://pypi.org/pypi/APScheduler/json> · <https://raw.githubusercontent.com/agronholm/apscheduler/master/README.rst> · <https://apscheduler.readthedocs.io/en/master/versionhistory.html> · <https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html> · <https://apscheduler.readthedocs.io/en/3.x/userguide.html> · <https://raw.githubusercontent.com/agronholm/apscheduler/3.x/docs/versionhistory.rst> · <https://raw.githubusercontent.com/agronholm/apscheduler/master/src/apscheduler/_utils.py> · <https://github.com/agronholm/apscheduler/issues/1103>
- <https://raw.githubusercontent.com/taskiq-python/taskiq/master/pyproject.toml> · <https://raw.githubusercontent.com/taskiq-python/taskiq/master/taskiq/cli/scheduler/run.py> · <https://raw.githubusercontent.com/python-arq/arq/main/pyproject.toml> · <https://raw.githubusercontent.com/python-arq/arq/main/arq/cron.py> · <https://raw.githubusercontent.com/python-arq/arq/main/arq/worker.py> · <https://github.com/python-arq/arq/issues/351> · <https://pypi.org/pypi/arq/json>

Peer scheduling:

- <https://raw.githubusercontent.com/python-telegram-bot/python-telegram-bot/master/pyproject.toml> · <https://raw.githubusercontent.com/python-telegram-bot/python-telegram-bot/master/README.rst> · <https://raw.githubusercontent.com/python-telegram-bot/python-telegram-bot/master/src/telegram/ext/_jobqueue.py> · <https://raw.githubusercontent.com/python-telegram-bot/python-telegram-bot/master/src/telegram/ext/_applicationbuilder.py> · <https://github.com/python-telegram-bot/python-telegram-bot/wiki/Transition-guide-to-Version-20.0> · <https://github.com/python-telegram-bot/python-telegram-bot/pull/3267> · <https://github.com/python-telegram-bot/python-telegram-bot/releases/tag/v20.0a5> · <https://github.com/python-telegram-bot/python-telegram-bot/issues/2257>
- <https://raw.githubusercontent.com/Rapptz/discord.py/master/discord/ext/tasks/__init__.py> · <https://raw.githubusercontent.com/Rapptz/discord.py/master/pyproject.toml> · <https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html>
- <https://raw.githubusercontent.com/ag2ai/faststream/main/pyproject.toml> · <https://github.com/ag2ai/faststream/blob/main/docs/docs/en/scheduling.md> · <https://github.com/taskiq-python/taskiq-faststream> · <https://raw.githubusercontent.com/taskiq-python/taskiq-faststream/master/pyproject.toml>
- <https://pypi.org/pypi/litestar-saq/json> · <https://pypi.org/pypi/saq/json> · <https://raw.githubusercontent.com/cofin/litestar-saq/main/litestar_saq/base.py> · <https://raw.githubusercontent.com/cofin/litestar-saq/main/litestar_saq/config.py>
- <https://raw.githubusercontent.com/aiogram/aiogram/dev-3.x/pyproject.toml> · <https://github.com/aiogram/aiogram/issues/1195> · <https://raw.githubusercontent.com/hikari-py/hikari/master/pyproject.toml> · <https://pypi.org/pypi/hikari-lightbulb/json> · <https://hikari-lightbulb.readthedocs.io/en/latest/api-references/lightbulb/tasks.html>
- <https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html> · <https://taskiq-python.github.io/guide/scheduling-tasks.html> · <https://github.com/taskiq-python/taskiq/issues/438> · <https://arq-docs.helpmanual.io/> · <https://raw.githubusercontent.com/celery/django-celery-beat/main/README.rst> · <https://raw.githubusercontent.com/sibson/redbeat/main/README.rst> · <https://redbeat.readthedocs.io/en/latest/config.html>

Reliability libraries:

- <https://pypi.org/pypi/stamina/json> · <https://raw.githubusercontent.com/hynek/stamina/main/pyproject.toml> · <https://raw.githubusercontent.com/hynek/stamina/main/src/stamina/_core.py> · <https://stamina.hynek.me/en/stable/api.html> · <https://pypi.org/pypi/tenacity/json>
- <https://pypi.org/pypi/aiolimiter/json> · <https://aiolimiter.readthedocs.io/en/stable/> · <https://pypi.org/pypi/pyrate-limiter/json> · <https://raw.githubusercontent.com/vutran1710/PyrateLimiter/master/README.md> · <https://pypi.org/pypi/limits/json> · <https://pypi.org/pypi/aiopylimit/json>
- <https://pypi.org/pypi/purgatory/json> · <https://raw.githubusercontent.com/mardiros/purgatory/main/src/purgatory/service/_async/repository.py> · <https://pypi.org/pypi/pybreaker/json> · <https://raw.githubusercontent.com/danielfm/pybreaker/main/src/pybreaker/__init__.py> · <https://pypi.org/pypi/aiobreaker/json> · <https://pypi.org/pypi/aiocircuitbreaker/json>
- <https://raw.githubusercontent.com/getsentry/sentry-python/master/setup.py> · <https://pypi.org/pypi/sentry-sdk/json> · <https://docs.sentry.io/platforms/python/integrations/> · <https://docs.sentry.io/platforms/python/integrations/default-integrations/> · <https://docs.sentry.io/platforms/python/usage/>

Probes:

- <https://kubernetes.io/docs/concepts/workloads/pods/probes/> · <https://docs.spring.io/spring-boot/reference/actuator/endpoints.html>
- <https://github.com/ag2ai/faststream/blob/main/faststream/asgi/factories/ping.py> · <https://github.com/ag2ai/faststream/blob/main/faststream/asgi/app.py> · <https://github.com/ag2ai/faststream/blob/main/faststream/redis/broker/broker.py> · <https://github.com/ag2ai/faststream/blob/main/faststream/rabbit/broker/broker.py> · <https://faststream.ag2.ai/latest/getting-started/asgi/>
- <https://docs.djangoproject.com/en/5.2/ref/urls/> · <https://sanic.dev/en/plugins/sanic-ext/health-monitor.html> · <https://github.com/sanic-org/sanic-ext/blob/main/sanic_ext/config.py> · <https://docs.celeryq.dev/en/stable/userguide/workers.html> · <https://github.com/python-arq/arq/blob/main/arq/worker.py>
- <https://github.com/slackapi/bolt-python/blob/main/examples/socket_mode_healthcheck.py> · <https://github.com/slackapi/python-slack-sdk/blob/main/slack_sdk/socket_mode/builtin/client.py> · <https://github.com/slackapi/bolt-python/issues/439> · <https://github.com/cloudflare/cloudflared/blob/master/metrics/readiness.go> · <https://developers.cloudflare.com/cloudflare-one/tutorials/many-cfd-one-tunnel/>
