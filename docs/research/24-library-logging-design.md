# 24. Logging design for a zero-dependency async library

**Question.** What is the highest-quality logging design a zero-dependency async Python library can
ship, such that the convention is laid down once and never revisited? Concretely: the logger tree,
the level policy, how every record carries its correlation context without threading arguments
through every call, how a log line survives the thread boundary of a Sync executor, how an
application gets structured output and log-to-trace correlation with no dependency of ours, and
what a log call costs on a hot path.

Gathered for GitHub issue #29. The hygiene rules already exist — one logger per component,
`NullHandler`, identifiers never content, no content switch, one redaction list, a constant message
with the variables in `extra`, a correlation id on anything a user sees — and none of them answers
the questions above. [`docs/research/17`](17-http-client-observability.md) §4 covers logging hygiene
for an outbound HTTP client only and is not repeated;
[`docs/research/23`](23-dispatch-observability-in-async-frameworks.md) covers metrics and traces.

Findings only — the decisions are
[ADR-0052](../adr/0052-log-levels-by-frequency-and-audience.md) to
[ADR-0055](../adr/0055-one-redaction-list-over-two-sinks.md). All sources are primary
(`docs.python.org`, `peps.python.org`, RFC text, the OpenTelemetry specification, CPython source,
project source and documentation on GitHub), read on 2026-09-09. `structlog` is studied only as a
*consumer* of stdlib records and is never a dependency. Anything not confirmed from a primary source is marked
**[unverified]**.

## 1 Ambient context: the four stdlib mechanisms, compared

A library that wants a correlation identifier on every record has exactly four stdlib mechanisms,
and they differ in the one property that matters to a library — whether they touch state the
application owns.

| Mechanism | Scope | What it cannot do |
|---|---|---|
| `LoggerAdapter` | one `Logger` object | drops per-call `extra` unless `merge_extra=True`, added in **3.13** |
| a filter | one logger **or** one handler | a logger's filter does not see records from descendant loggers |
| `setLogRecordFactory` | **process-global**, one slot | coexist with another owner of the slot |
| `Formatter(defaults=…)` | one formatter on one handler | exist at all unless the application installed that formatter |

**`LoggerAdapter`.** The signature is
`logging.LoggerAdapter(logger, extra=None, merge_extra=False)`, and the default is destructive:
`merge_extra` is "an optional boolean … indicating whether or not the *extra* argument of individual
log calls should be merged with the `LoggerAdapter` extra. The default behavior is to ignore the
*extra* argument of individual log calls and only use the one of the `LoggerAdapter` instance", and
it is annotated "Changed in version 3.13: The *merge_extra* parameter was added"
([LoggerAdapter](https://docs.python.org/3/library/logging.html#logging.LoggerAdapter)). On a floor
below 3.13 an adapter that carries ambient context therefore **silently discards every per-call
field** — which disqualifies the mechanism for a design where the per-call fields are the point.

**Filters.** The propagation rule is asymmetric and decisive: "Note that filters attached to
handlers are consulted before an event is emitted by the handler, whereas filters attached to
loggers are consulted whenever an event is logged … This means that events which have been generated
by descendant loggers will not be filtered by a logger's filter setting, unless the filter has also
been applied to those descendant loggers"
([Filter Objects](https://docs.python.org/3/library/logging.html#filter-objects)). A filter on a
library's *root* logger therefore does nothing for its component loggers; a filter on a *handler*
sees every record that reaches that handler, including records from other libraries.

Two further properties make a filter the cheapest option for a library. It needs no inheritance —
"You don't actually need to subclass `Filter`: you can pass any instance which has a `filter` method
with the same semantics", and since 3.2 "you can use a function (or other callable) as a filter"
(same page). And since **3.12** it need not mutate: "You can now return a `LogRecord` instance from
filters to replace the log record rather than modifying it in place. This allows filters attached to
a `Handler` to modify the log record before it is emitted, without having side effects on other
handlers" (same page).

**`setLogRecordFactory`** replaces a single module-level callable used by every `Logger.makeRecord`
in the process. The documentation's only caution is about chaining — wrap `old_factory`, and "as
long as they don't overwrite each other's attributes … there should be no surprises"
([setLogRecordFactory](https://docs.python.org/3/library/logging.html#logging.setLogRecordFactory))
— but the slot has one owner, and §5 shows who already claims it.

**`Formatter(defaults=…)`**, added in 3.10, exists to keep a format string referencing a custom
`%(field)s` from failing on records that lack it:
`logging.Formatter('%(ip)s %(message)s', defaults={"ip": None})`
([Formatter](https://docs.python.org/3/library/logging.html#logging.Formatter)). It is the
application's object, so a library can only document it.

## 2 What a log call costs, and what an `extra` key must not be

**The reserved names raise, they do not warn.** The documentation is mild — "The keys in the
dictionary passed in *extra* should not clash with the keys used by the logging system"
([LogRecord attributes](https://docs.python.org/3/library/logging.html#logrecord-attributes)) — but
`Logger.makeRecord` is not:

```python
if extra is not None:
    for key in extra:
        if (key in ["message", "asctime"]) or (key in rv.__dict__):
            raise KeyError("Attempt to overwrite %r in LogRecord" % key)
        rv.__dict__[key] = extra[key]
```

(CPython, `Lib/logging/__init__.py`). So an `extra` key named `message`, `asctime`, or any existing
`LogRecord` attribute is a `KeyError` at the call site. The full reserved set is `args`, `asctime`,
`created`, `exc_info`, `exc_text`, `filename`, `funcName`, `levelname`, `levelno`, `lineno`,
`message`, `module`, `msecs`, `msg`, `name`, `pathname`, `process`, `processName`,
`relativeCreated`, `stack_info`, `thread`, `threadName` and `taskName` — a set that collides with
the vocabulary of a chat platform at `message`, `name`, `module`, `process` and `args`.

**Cost.** The HOWTO's guard is `isEnabledFor`: "you can call the `isEnabledFor()` method … so that
if the logger's threshold is set above `DEBUG`, the calls to `expensive_func1` and `expensive_func2`
are never made", and "In some cases, `isEnabledFor()` can itself be more expensive than you'd like …
you can cache the result … in a local or instance variable". Argument formatting is lazy —
"Formatting of message arguments is deferred until it cannot be avoided" — and four switches turn
off per-record work: `logging.logThreads`, `logging.logProcesses`, `logging.logMultiprocessing` and
`logging.logAsyncioTasks`, plus `logging._srcfile = None` to skip the caller lookup. The section
also notes that "the core logging module only includes the basic handlers. If you don't import
`logging.handlers` and `logging.config`, they won't take up any memory"
([Optimization](https://docs.python.org/3/howto/logging.html#optimization)). No sentence contrasting
`%`-style with f-strings by name was found **[unverified]**; the lazy-formatting sentence is the
whole basis.

**A raising handler never reaches the caller.** `logging.raiseExceptions` is "Used to see if
exceptions during handling should be propagated. Default: `True`. If `raiseExceptions` is `False`,
exceptions get silently ignored"
([raiseExceptions](https://docs.python.org/3/library/logging.html#logging.raiseExceptions)), and
`handleError` only writes `--- Logging error ---` with the traceback to `sys.stderr`. A log call
cannot break the caller, which is why logging is a safe last resort inside a failure path.

## 3 Blocking handlers: the docs address library authors directly

Standard handlers do blocking I/O, and the Cookbook says so about coroutines specifically: "when
logging from async code, network and even file handlers could lead to problems (blocking the event
loop) because some logging is done from `asyncio` internals. It might be best, if any async code is
used in an application, to use the above approach for logging, so that any blocking code runs only
in the `QueueListener` thread." The instruction to a library is explicit: "If you are a library
developer who has performance-critical threads in their code, be sure to document this (together
with a suggestion to attach only `QueueHandlers` to your loggers)"
([Dealing with handlers that block](https://docs.python.org/3/howto/logging-cookbook.html#dealing-with-handlers-that-block)).
Ownership sits with the application — the recipe calls `listener.start()`/`listener.stop()` around
application code, and since 3.14 `QueueListener` is also a context manager.

One property of the queue path matters for a record's contents. `QueueHandler.prepare()` "formats
the record to merge the message, arguments, exception and stack information, if present. It also
removes unpickleable items from the record in-place. Specifically, it overwrites the record's `msg`
and `message` attributes with the merged message … and sets the `args`, `exc_info` and `exc_text`
attributes to `None`"
([QueueHandler](https://docs.python.org/3/library/logging.handlers.html#queuehandler)). Fields
passed through `extra` live in `record.__dict__` and survive the queue; `exc_info` does not survive
as structured data. This is an argument for putting every variable in `extra` rather than in the
message, independent of the readability argument.

## 4 Correlation across every boundary

`contextvars` propagation, boundary by boundary:

| Boundary | Guaranteed? | Source |
|---|---|---|
| an awaited coroutine | yes — same context | [PEP 567](https://peps.python.org/pep-0567/) |
| `create_task`, `TaskGroup.create_task` | yes — "the Task copies the current context and later runs its coroutine in the copied context" | [asyncio-task](https://docs.python.org/3/library/asyncio-task.html) |
| `asyncio.to_thread` | yes — "the current `contextvars.Context` is propagated" | [asyncio-task](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread) |
| `loop.run_in_executor` | **no guarantee documented** | [asyncio-eventloop](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor) |
| `loop.call_soon` | yes — "Callbacks use the current context when no context is provided" | [asyncio-eventloop](https://docs.python.org/3/library/asyncio-eventloop.html) |

The executor is the one hole, and PEP 567 gives the fix in its own words: "It is possible to run
code in a separate OS thread using a copy of the current thread context:
`executor.submit(current_context.run, some_function)`". `contextvars` also states that "each thread
has its own context stack", behaving "in a similar fashion to `threading.local()`"
([contextvars](https://docs.python.org/3/library/contextvars.html)).

**`taskName` is free correlation from 3.12.** The attribute is `asyncio.Task` name "(if available)",
added in 3.12, and `LogRecord.__init__` fills it from `asyncio.current_task().get_name()` when
`logging.logAsyncioTasks` is on (default `True`), swallowing any failure
([LogRecord attributes](https://docs.python.org/3/library/logging.html#logrecord-attributes),
CPython `Lib/logging/__init__.py`, [gh-91513](https://github.com/python/cpython/pull/93193)). The
name is settable through `Task.set_name` or the `name=` argument of `create_task` and
`TaskGroup.create_task`
([asyncio-task](https://docs.python.org/3/library/asyncio-task.html)). Because the value is read at
record-creation time from whatever task is current, a *named* task labels every record emitted
inside it — including records from third-party libraries called within it — with no filter, no
adapter and no dependency. It does not reach a thread, because a thread has no current task.

## 5 Log-to-trace correlation, and who owns the record factory

The OpenTelemetry Logs Data Model names the joining fields `TraceId`, `SpanId` and `TraceFlags`, all
optional, with the rule "If SpanId is present TraceId SHOULD be also present"
([Logs Data Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/)).

In Python the component that puts them on **stdlib** records is
`opentelemetry-instrumentation-logging`, and it does so by claiming the global slot: `_instrument()`
calls `logging.setLogRecordFactory(record_factory)` and the factory sets
`record.otelTraceID = format(ctx.trace_id, "032x")`, `record.otelSpanID`,
`record.otelTraceSampled` and `record.otelServiceName`; `_uninstrument()` restores the previous
factory
([source](https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/instrumentation/opentelemetry-instrumentation-logging/src/opentelemetry/instrumentation/logging/__init__.py)).
The SDK's own `LoggingHandler` does not extract trace fields itself; it stamps the current context
onto the emitted record and defers extraction
([source](https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-sdk/src/opentelemetry/sdk/_logs/_internal/__init__.py)).

The recognised division is therefore that **the application installs the instrumentation that adds
trace ids**: OpenTelemetry ships it as an opt-in `Instrumentor` a user calls, precisely because the
factory is one slot with one owner. A library that claimed it would break, or be broken by, the
application's own instrumentation.

**Severity mapping is exact for the five stdlib levels and coarse for anything else.** RFC 5424
§6.2.1 defines eight severities ([RFC 5424](https://www.rfc-editor.org/rfc/rfc5424)); the Logs Data
Model defines `SeverityNumber` ranges TRACE 1–4, DEBUG 5–8, INFO 9–12, WARN 13–16, ERROR 17–20,
FATAL 21–24; and the SDK's `_STD_TO_OTEL` maps `{10: DEBUG, 20: INFO, 30: WARN, 40: ERROR, 50:
FATAL, …}` with the intermediate values filling the "2/3/4" sub-buckets and anything below 10
becoming `UNSPECIFIED`
([source](https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-sdk/src/opentelemetry/sdk/_logs/_internal/__init__.py)).
A library that uses only DEBUG, INFO, WARNING, ERROR and CRITICAL round-trips exactly through both
bridges; a custom level between them lands in a coarser bucket.

## 6 Structured output a library gets for nothing

All three consumers key off `record.__dict__` minus the reserved set, so a field passed through
`extra=` is machine-readable in every one of them with no adaptation:

- **structlog.** `ExtraAdder.__call__` reads `event_dict["_record"]` and copies every attribute not
  in its baseline `_LOG_RECORD_KEYS` set; `ProcessorFormatter` builds
  `{"event": …, "_record": record, "_from_structlog": False}` for a foreign stdlib record before
  running the processor chain
  ([stdlib.py](https://github.com/hynek/structlog/blob/main/src/structlog/stdlib.py)). Note that
  structlog's own message key is `event`, so an `extra` key of that name collides inside the event
  dict.
- **python-json-logger.** `merge_record_extra()` copies `record.__dict__` items whose key is not in
  `RESERVED_ATTRS` and does not start with `_`, applying `rename_fields` on the way out
  ([core.py](https://github.com/nhairs/python-json-logger/blob/main/src/pythonjsonlogger/core.py)).
- **plain `logging.Formatter`.** `%(key)s` reads `record.__dict__`, with `defaults=` as the fallback
  for records lacking the field (§1).

## 7 Logger trees and level policy in practice

| Project | Logger names | Anything at INFO by default? | Context mechanism | Configures logging or adds a level? |
|---|---|---|---|---|
| httpx | `httpx` (flat) | **yes** — one line per request | none | removed its custom `TRACE` and `HTTPX_LOG_LEVEL` in 0.24.0 |
| httpcore | `httpcore.connection`, `.http11`, `.proxy` | no — all DEBUG | none | no |
| urllib3 | `urllib3.connectionpool`, `.connection`, `.util.retry`, `.poolmanager` | only a redirect, at the pool-manager level | none | `NullHandler`; opt-in `add_stderr_logger()` |
| openai-python | `openai`, `openai.*` | no — only a retry | a `logging.Filter` redacting header values | `basicConfig` conditionally, on `OPENAI_LOG` |
| aiohttp | six flat: `aiohttp.access`, `.client`, `.internal`, `.server`, `.web`, `.websocket` | emits at INFO, suppressed by the default level | none | no; docs say logging "does not work out of the box" |
| uvicorn | `uvicorn`, `.error`, `.access` | **yes** — banner, startup, access | none | calls `dictConfig` itself; custom `TRACE` level |
| SQLAlchemy | root plus per-instance namespaces | no — root set to `WARNING` at import | `InstanceLogger` mapping `echo` to a per-instance level | sets its own root level; adds a handler only when `echo` is set |
| botocore / boto3 | deep, per module | essentially no | none | `NullHandler`; opt-in `set_stream_logger` |
| Celery | `celery`, `.task`, `.worker`, `.redirected` | **yes** — task success, retry, ignored | **a `Formatter` subclass** reading a thread-local | hijacks the root logger by default; `captureWarnings(True)` |
| Litestar | `litestar` | no — opt-in config object | a queue-based handler, no context injection | no |
| taskiq, arq, Dramatiq | worker-scoped, per module | yes once started | none found | the **CLI** calls `basicConfig`/`dictConfig`, not the library |
| discord.py | `discord.*` per module | no — silent | none | `NullHandler`; `setup_logging()` called by `run()` |
| aiogram | `aiogram.dispatcher`, `.event`, `.middlewares`, `.webhook`, `.scene` | **yes** — unconditionally, per update | none | no |
| hikari | `hikari.*` | yes, through `GatewayBot(logs="INFO")` | none | custom `TRACE_HIKARI` below DEBUG; calls its own config |

Three things stand out.

**INFO is split down the middle, and the noisy side is the one that gets complaints.** httpx logs
one INFO line per request, uvicorn a banner and an access line, Celery a line per task, aiogram a
line per update — and aiogram's is the subject of an open issue
([#1355](https://github.com/aiogram/aiogram/issues/1355)). httpcore, urllib3, openai, botocore,
SQLAlchemy, discord.py and Litestar say nothing at INFO on a normal path. SQLAlchemy states the
reason in a code comment beside `setLevel(WARNING)`: "set initial level to WARN. This so that log
statements don't occur in the absence of explicit logging being enabled"
([log.py](https://github.com/sqlalchemy/sqlalchemy/blob/482d46a3/lib/sqlalchemy/log.py#L44-L46)).

**Only Celery injects per-record context, and it does it with a `Formatter`.**
`TaskFormatter.format` calls `get_current_task()` and does
`record.__dict__.update(task_id=task.request.id, task_name=task.name)` before delegating, reading a
thread-local `LocalStack` pushed around task execution
([app/log.py](https://github.com/celery/celery/blob/7b76598/celery/app/log.py),
[utils/log.py](https://github.com/celery/celery/blob/7b76598/celery/utils/log.py)). The mechanism
only works when the application uses Celery's formatter, which is the price of putting the logic
there. The widely used third-party alternative for ASGI is a **contextvar plus a filter**:
`asgi-correlation-id` declares
`correlation_id: ContextVar[str | None] = ContextVar('correlation_id', default=None)`, sets it per
request, and its `CorrelationIdFilter.filter()` assigns `record.correlation_id`
([repo](https://github.com/snok/asgi-correlation-id)). Django does neither and simply passes
`extra={"request": request, …}` at the call site
([utils/log.py](https://github.com/django/django/blob/main/django/utils/log.py)).

**Configuration discipline splits four ways**: uvicorn calls `dictConfig` on every `Config()`
construction and adds a level; Celery hijacks the root logger by default; openai calls
`basicConfig` when an environment variable says so; urllib3, boto3 and discord.py ship an opt-in
helper; and taskiq, arq and Dramatiq push it into their CLI entry point rather than the import. Only
httpx has *removed* such a mechanism, stating "We no longer have a custom TRACE log level"
([CHANGELOG](https://github.com/encode/httpx/blob/b5addb64/CHANGELOG.md#L151)). A `NullHandler` is
shipped by urllib3, botocore, boto3 and discord.py, and not by httpx or aiohttp.

**Stable shape versus prose** splits too. httpx's `'HTTP Request: %s %s "%s %d %s"'`, urllib3's
`"Retry: %s"` and `"Redirecting %s -> %s"`, and Celery's
`"Task %(name)s[%(id)s] succeeded in %(runtime)ss: %(return_value)s"` have a fixed shape and always
the same fields; uvicorn's `"Uvicorn running on %s://%s:%d (Press CTRL+C to quit)"`, aiohttp's
`"Could not read .netrc file: %s"` and openai's `"Retrying request in %f seconds"` are prose. No
project in the set publishes its log records as a documented contract **[unverified]** — none was
found doing so.

## 8 One property no survey can supply

`NullHandler` and the standard default are alternatives, not complements. The HOWTO calls the
default "the best default behaviour" — "If the using application does not use logging, and library
code makes logging calls, then … events of severity `WARNING` and greater will be printed to
`sys.stderr`" — and introduces `NullHandler` for the opposite preference: "If for some reason you
*don't* want these messages printed in the absence of any logging configuration, you can attach a
do-nothing handler to the top-level logger for your library"
([Configuring Logging for a Library](https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library)).
The mechanism behind the default is `logging.lastResort`, "a `StreamHandler` writing to `sys.stderr`
with a level of `WARNING` … used to handle logging events in the absence of any logging
configuration", and it fires only when no handler is found
([lastResort](https://docs.python.org/3/library/logging.html#logging.lastResort)) — so installing
`NullHandler` silences it. Whether a long-running bot should be silent or should print its warnings
uninvited is a product judgement no source settles.

The same page carries the two rules that are not judgements: "It is strongly advised that you *do
not log to the root logger* in your library. Instead, use a logger with a unique and easily
identifiable name", and "It is strongly advised that you *do not add any handlers other than*
`NullHandler` *to your library's loggers*. This is because the configuration of handlers is the
prerogative of the application developer who uses your library."

## 9 Recommendation

**Mechanism.** Three layers, each doing only what it alone can do, compose better than any single
one. Per-call `extra` is the base: it always works, cannot be bypassed by configuration, survives a
`QueueHandler` (§3) and is machine-readable in all three structured consumers (§6). A **named
asyncio task** is the cheapest carriage for ambient context, because `%(taskName)s` lands on every
record made inside it, including records from libraries the framework merely calls (§4). A
**contextvar plus a duck-typed filter object the application attaches to its handler** is the only
way to reach records the library did not emit and did not enclose; it must be attached to a
*handler*, not to the library's own logger, because a logger's filter does not see descendant
records (§1). `LoggerAdapter` is disqualified below Python 3.13, and `setLogRecordFactory` belongs
to whoever installed the OpenTelemetry logging instrumentation (§5).

**Levels.** Following the quiet half of §7 is the option that no user files an issue about, and the
frequency of an event — per message, per connection, per process — is a sharper test than its
importance. Anything per-message above DEBUG is the choice aiogram is being asked to reverse. The
counter-argument is real and is about a bot specifically: a long-running consumer whose operator
configured nothing tells them nothing, and the first ten minutes of any adoption are spent asking
whether the process is alive. Staying inside the five standard levels costs nothing and buys an
exact mapping through both the RFC 5424 and the OpenTelemetry severity bridges (§5); a custom level
buys granularity and lands in a coarse bucket, which is why httpx removed theirs.

**Configuration.** Every mechanism in §7's right-hand column is something a library does to state
the application owns, and the HOWTO says whose prerogative that is (§8). The strictest position —
no `basicConfig`, no `dictConfig`, no `captureWarnings`, no `setLevel` anywhere including the
library's own root, no environment variable and no helper — is also the only one that no peer has
had to walk back. Its cost is that correct configuration is a paragraph of documentation rather than
a function call, which makes an executable example the thing to get right.

**A contract nobody else offers.** No surveyed project documents its log records as a contract
(§7). Doing so — level, message constant, fields and trigger per record, checked against the code in
both directions — is therefore not a way to fit in but a way to be better, and the cost is a table
per component and the discipline to treat a relevelled record as a documented change. The
counter-position is the ecosystem's: promise the logger names and what each level means, and leave
the strings free.

## Sources

Standard library and PEPs:
- https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library · https://docs.python.org/3/howto/logging.html#optimization
- https://docs.python.org/3/howto/logging-cookbook.html#dealing-with-handlers-that-block
- https://docs.python.org/3/library/logging.html · https://docs.python.org/3/library/logging.html#logrecord-attributes · https://docs.python.org/3/library/logging.html#filter-objects
- https://docs.python.org/3/library/logging.html#logging.LoggerAdapter · https://docs.python.org/3/library/logging.html#logging.Formatter · https://docs.python.org/3/library/logging.html#logging.setLogRecordFactory
- https://docs.python.org/3/library/logging.html#logging.raiseExceptions · https://docs.python.org/3/library/logging.html#logging.lastResort
- https://docs.python.org/3/library/logging.handlers.html#queuehandler · https://docs.python.org/3/library/logging.handlers.html#logging.NullHandler
- https://docs.python.org/3/library/contextvars.html · https://docs.python.org/3/library/asyncio-task.html · https://docs.python.org/3/library/asyncio-eventloop.html
- https://peps.python.org/pep-0282/ · https://peps.python.org/pep-0391/ · https://peps.python.org/pep-0567/
- https://github.com/python/cpython/blob/main/Lib/logging/__init__.py · https://github.com/python/cpython/pull/93193

Specifications:
- https://www.rfc-editor.org/rfc/rfc5424
- https://opentelemetry.io/docs/specs/otel/logs/data-model/
- https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-sdk/src/opentelemetry/sdk/_logs/_internal/__init__.py
- https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/instrumentation/opentelemetry-instrumentation-logging/src/opentelemetry/instrumentation/logging/__init__.py

Structured consumers:
- https://github.com/hynek/structlog/blob/main/src/structlog/stdlib.py
- https://github.com/nhairs/python-json-logger/blob/main/src/pythonjsonlogger/core.py

Projects:
- https://github.com/encode/httpx/blob/b5addb64/httpx/_client.py · https://github.com/encode/httpx/blob/b5addb64/docs/logging.md · https://github.com/encode/httpx/blob/b5addb64/CHANGELOG.md
- https://github.com/encode/httpcore/blob/10a65822/httpcore/_trace.py
- https://github.com/urllib3/urllib3/blob/3f587c61/src/urllib3/connectionpool.py · https://github.com/urllib3/urllib3/blob/3f587c61/src/urllib3/poolmanager.py · https://github.com/urllib3/urllib3/blob/3f587c61/src/urllib3/__init__.py
- https://github.com/openai/openai-python/blob/8011140b/src/openai/_utils/_logs.py
- https://github.com/aio-libs/aiohttp/blob/9e08ba02/aiohttp/log.py · https://github.com/aio-libs/aiohttp/blob/9e08ba02/aiohttp/web_log.py · https://docs.aiohttp.org/en/stable/logging.html
- https://github.com/encode/uvicorn/blob/fa324a41/uvicorn/config.py · https://github.com/encode/uvicorn/blob/fa324a41/uvicorn/server.py
- https://github.com/sqlalchemy/sqlalchemy/blob/482d46a3/lib/sqlalchemy/log.py · https://github.com/sqlalchemy/sqlalchemy/blob/482d46a3/lib/sqlalchemy/engine/base.py · https://github.com/sqlalchemy/sqlalchemy/blob/482d46a3/doc/build/core/engines.rst
- https://github.com/boto/botocore · https://github.com/boto/boto3
- https://github.com/celery/celery/blob/7b76598/celery/utils/log.py · https://github.com/celery/celery/blob/7b76598/celery/app/log.py
- https://github.com/litestar-org/litestar/blob/v2.24.0/litestar/logging/config.py
- https://github.com/taskiq-python/taskiq · https://github.com/python-arq/arq/blob/main/arq/worker.py · https://github.com/Bogdanp/dramatiq
- https://github.com/Rapptz/discord.py/blob/master/docs/logging.rst
- https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/loggers.py · https://github.com/aiogram/aiogram/issues/1355
- https://github.com/hikari-py/hikari/blob/master/hikari/internal/ux.py
- https://github.com/snok/asgi-correlation-id · https://github.com/django/django/blob/main/django/utils/log.py
