# 31. The anatomy of a first-party error-tracker integration

**Question.** What does a first-party error-tracker integration do that a `capture_exception` call
at the failure site does not, and what does the tracker's SDK already do with no framework
integration installed at all?

Gathered for GitHub issue #101.
[`docs/research/08`](08-peer-responsibility-boundaries.md) recorded that no peer bot framework owns
a Sentry adapter in core and [`docs/research/26`](26-schedule-reliability-and-probe-primitives.md)
§6 recorded that `sentry-sdk` ships dozens of integration modules and none for a chat platform.
Those two facts are what
[ADR-0057](../adr/0057-reliability-middlewares-and-error-reporting-stay-outside.md) decided on, and
neither of them answers the question above, which is what a decision to own or to refuse an
integration actually turns on. Findings only: this note takes no decision and argues against none.
The decision it is evidence for is #104.

Every source claim about the SDK is read from
[`getsentry/sentry-python`](https://github.com/getsentry/sentry-python) at `VERSION = "2.69.1"`
([`sentry_sdk/consts.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/consts.py)),
`master` commit `7e95b86bc31b0a1411f0e54c0397152b2201cb2f`, alongside Sentry's product and SDK
development documentation, the CPython standard library, PyPI JSON metadata and the issue trackers
of the frameworks named — read on 2026-09-10. Anything a primary source did not confirm is marked
**[unverified]**.

## 1 The integration contract

`Integration` is an `ABC` with two members that matter and one that does not
([`sentry_sdk/integrations/__init__.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/__init__.py)):

- `identifier: "str" = None` — "String unique ID of integration type".
- `install = None` — "Legacy method, do not implement."
- `@staticmethod @abstractmethod setup_once() -> None`, whose docstring states the whole contract:

> Initialize the integration.
>
> This function is only called once, ever. Configuration is not available at this point, so the
> only thing to do here is to hook into exception handlers, and perhaps do monkeypatches.

There is a second, later hook for the cases that need options: `setup_once_with_options(options)` —
"Called after setup_once in rare cases on the instance and with options since we don't have those
available above."

**When it runs.** `setup_integrations()` is called from `_Client._init_impl`
([`sentry_sdk/client.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/client.py),
line 701), i.e. inside `sentry_sdk.init()`. Per integration the sequence is
`type(integration).setup_once()` then `integration.setup_once_with_options(options)`, guarded by a
module-level `_installer_lock` and two module-level sets, `_processed_integrations` ("Set of all
integration identifiers we have attempted to install") and `_installed_integrations`. A second
`init()` in the same process therefore re-binds the client but does not patch a second time.

**Enabling and disabling.** `sentry_sdk.init` takes four relevant options
([`sentry_sdk/consts.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/consts.py),
lines 1309–1340): `integrations=[]`, `default_integrations=True`, `auto_enabling_integrations=True`,
`disabled_integrations=None`. The docstrings are precise:

> Setting `default_integrations` to `False` disables all default integrations **as well as all
> auto-enabling integrations**, unless they are specifically added in the `integrations` option

The precedence rule is not in `consts.py`; it is stated on `setup_integrations` itself
([`sentry_sdk/integrations/__init__.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/__init__.py),
lines 194–195):

> `disabled_integrations` takes precedence over `with_defaults` and
> `with_auto_enabling_integrations`.

A related mechanism, `_INTEGRATION_DEACTIVATES`, lets one integration switch others off to avoid
duplicate telemetry: `langchain` deactivates `{openai, anthropic, google_genai}`, `openai_agents`
deactivates `{openai}`, `pydantic_ai` deactivates `{openai, anthropic}`, unless the user named the
deactivated one explicitly.

**The two lists.** `_DEFAULT_INTEGRATIONS` holds eight; `_AUTO_ENABLING_INTEGRATIONS` holds
forty-one; every other integration module in the tree is in neither list and must be named by hand.

| Category | Count | Members |
|---|---|---|
| `_DEFAULT_INTEGRATIONS` | 8 | `argv`, `atexit`, `dedupe`, `excepthook`, `logging`, `modules`, `stdlib`, `threading` |
| `_AUTO_ENABLING_INTEGRATIONS` | 41 | `aiohttp`, `anthropic`, `ariadne`, `arq`, `asyncpg`, `boto3`, `bottle`, `celery`, `chalice`, `clickhouse_driver`, `cohere`, `django`, `falcon`, `fastapi`, `flask`, `gql`, `google_genai`, `graphene`, `httpx`, `httpx2`, `huey`, `huggingface_hub`, `langchain`, `langgraph`, `litestar`, `loguru`, `mcp`, `openai`, `openai_agents`, `pydantic_ai`, `pymongo`, `pyramid`, `quart`, `redis`, `rq`, `sanic`, `sqlalchemy`, `starlette`, `starlite`, `strawberry`, `tornado` |
| Neither — explicit only | — | `asyncio`, `otlp`, `opentelemetry`, `dramatiq`, `grpc`, `ray`, `spark`, `socket`, `typer`, `unleash`, `statsig`, `launchdarkly`, `openfeature`, `litellm`, `aiomysql`, `beam`, `aws_lambda`, `gcp`, `serverless`, `asgi`, `wsgi`, `trytond`, `pyreqwest`, `sys_exit`, `unraisablehook`, `pure_eval`, `executing`, `gnu_backtrace`, `cloud_resource_context`, `rust_tracing` |

The published documentation names the same two categories: auto-enabling integrations are
"automatically added if the SDK detects that you have a corresponding package (like Flask)
installed"; default integrations are "always enabled, regardless of what packages you have
installed, as long as the `default_integrations` option is True (default). They provide essential
SDK functionality like error deduplication or event flushing at interpreter shutdown"
([Integrations](https://docs.sentry.io/platforms/python/integrations/)).

**Absent dependency.** The mechanism is a single exception class, `DidNotEnable`, whose docstring is
the specification:

> The integration could not be enabled due to a trivial user error like `flask` not being installed
> for the `FlaskIntegration`.
>
> This exception is silently swallowed for default integrations, but reraised for explicitly enabled
> integrations.

It is raised at *module import time*, from a bare `try: import …` block — the arq module ends its
import guard with `raise DidNotEnable("Arq is not installed")`
([`sentry_sdk/integrations/arq.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/arq.py),
line 28). Two places catch it. `iter_default_integrations` catches `(DidNotEnable, SyntaxError)`
while importing the list entries and logs `"Did not import default integration %s: %s"`.
`setup_integrations` catches it around `setup_once()` and re-raises unless the identifier is in
`used_as_default_integration`, in which case it logs `"Did not enable default integration %s: %s"`.
Net effect: an auto-enabled integration whose library is missing silently does not install; an
explicitly named one raises `DidNotEnable` out of the application's own `from
sentry_sdk.integrations.arq import ArqIntegration`, because naming it means importing it, and a
`DidNotEnable` raised inside `setup_once()` — the version floor below — propagates out of
`sentry_sdk.init()`.

A version floor uses the same class. `_check_minimum_version` reads `_MIN_VERSIONS` (e.g.
`"arq": (0, 23)`, `"celery": (4, 4, 7)`, `"django": (1, 8)`) and raises
`DidNotEnable(f"Integration only supports {package} {'.'.join(map(str, min_version))} or newer.")`,
or `DidNotEnable(f"Unparsable {package} version.")` when the version tuple is `None`.

## 2 One representative integration, read whole: `ArqIntegration`

Read in full at
[`sentry_sdk/integrations/arq.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/arq.py)
(296 lines). `identifier = "arq"`, `origin = f"auto.queue.{identifier}"`.

**Patch points.** `setup_once()` does exactly six things: a version check, three monkeypatches, one
global registration and one logger silencing.

| Patch point | Replacement | Effect |
|---|---|---|
| `ArqRedis.enqueue_job` | `_sentry_enqueue_job` | child span on the producer side; `__kwdefaults__` copied back onto the wrapper |
| `Worker.run_job` | `_sentry_run_job` | forks an isolation scope and opens the transaction |
| `arq.worker.create_worker` | `_sentry_create_worker` | rewrites `functions` / `cron_jobs` so each coroutine is wrapped |
| `_control_flow_exception_classes` (global set in `sentry_sdk/utils.py`) | `_register_control_flow_exception((JobExecutionFailed, Retry, RetryJob))` | those three stop counting as errors SDK-wide |
| `_IGNORED_LOGGERS` | `ignore_logger("arq.worker")` | arq's own error log neither becomes an event nor a breadcrumb |

**Transaction and span.** On the consumer side, in static (default) trace mode:

```python
transaction = Transaction(
    name="unknown arq task",
    status="ok",
    op=OP.QUEUE_TASK_ARQ,
    source=TransactionSource.TASK,
    origin=ArqIntegration.origin,
)
```

`OP.QUEUE_TASK_ARQ == "queue.task.arq"` and `TransactionSource.TASK == "task"`
([`sentry_sdk/consts.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/consts.py),
line 1274;
[`sentry_sdk/tracing.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/tracing.py),
line 138). The name starts as the literal `"unknown arq task"` and is corrected later by the event
processor, because `Worker.run_job` receives only a `job_id`. The queue name, when set, becomes
`messaging.destination.name`. On the producer side `_sentry_enqueue_job` opens a child span with
`op=OP.QUEUE_SUBMIT_ARQ` (`"queue.submit.arq"`) and `name=function`. Under
`trace_lifecycle="stream"` the same two are `sentry_sdk.traces.start_span` calls: the producer span
carries only the attributes `sentry.op` and `sentry.origin`, and the consumer span adds
`sentry.segment.name.source` and `messaging.message.id` and passes `parent_span=None`, so it is a
root span. `has_span_streaming_enabled` returns `False` unless `trace_lifecycle` or
`_experiments["trace_lifecycle"]` is `"stream"`
([`sentry_sdk/tracing_utils.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/tracing_utils.py),
line 126), so the `Transaction` path is the default.

**Scope isolation.** One call, at the top of `_sentry_run_job`, wraps the whole job:

```python
with sentry_sdk.isolation_scope() as scope:
    scope._name = "arq"
    scope.clear_breadcrumbs()
```

So each job gets a forked isolation scope *and* a forked current scope (see §3), and starts with an
empty breadcrumb buffer.

**Tags, extra, contexts, breadcrumbs.** `_make_event_processor` is added to the isolation scope by
`_wrap_coroutine`, so it runs for every event raised during the job:

- `event["transaction"]` and `scope.transaction.name` are both set to `ctx["job_name"]`.
- `tags["arq_task_id"] = ctx["job_id"]`; `tags["arq_task_retry"] = ctx["job_try"] > 1`.
- `extra["arq-job"] = {"task": ctx["job_name"], "retry": ctx["job_try"], "args": …, "kwargs": …}`.
  Arguments are included only when `data_collection["queues"]` is on, or — when `_experiments`
  carries no `data_collection` key at all — when `should_send_default_pii()` is true. With
  `data_collection` set and `queues` off the two keys are omitted entirely; only in the remaining
  case are both replaced with `SENSITIVE_DATA_SUBSTITUTE`.
- No `set_context` call anywhere in the module — the integration sets no Sentry *context*.
- No breadcrumb is added by the integration; it only clears them and silences `arq.worker`.

The tests assert exactly these: `event["transaction"] == "division"`, `"cron:division"` for a cron
job, `event["tags"]["arq_task_id"] == job.job_id`, `event["extra"]["arq-job"]["retry"] == 2` on the
second try, and `spans[2]["attributes"]["sentry.op"] == "queue.task.arq"`
([`tests/integrations/arq/test_arq.py`](https://github.com/getsentry/sentry-python/blob/master/tests/integrations/arq/test_arq.py)).

**Error capture and re-raise.** `_wrap_coroutine` catches `Exception`, calls `_capture_exception`,
then `reraise(*exc_info)` — the job's exception continues to arq unchanged. `_capture_exception`
first sets the transaction status: `SPANSTATUS.ABORTED` for the three arq control-flow exceptions,
`SPANSTATUS.INTERNAL_ERROR` otherwise; for control-flow exceptions it then returns without sending
anything. Otherwise it builds the event with:

```python
mechanism={"type": ArqIntegration.identifier, "handled": False}
```

`handled: False` is the difference that matters. `sentry_sdk.capture_exception()` at a failure site
passes no mechanism at all, and `single_exception_from_error_tuple` then defaults to `{"type":
"generic", "handled": True}`
([`sentry_sdk/utils.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/utils.py),
lines 732–733).

**State.** `ArqIntegration` defines no `__init__` and stores nothing on the instance. All state is
either SDK-global (`_processed_integrations`, `_installed_integrations`,
`_control_flow_exception_classes`, `_IGNORED_LOGGERS`) or per-job scope state. The monkeypatches are
permanent and process-wide; there is no uninstall. Every patch re-checks
`sentry_sdk.get_client().get_integration(ArqIntegration) is None` and delegates to the original
function if the integration is no longer active — `_sentry_enqueue_job`, `_sentry_run_job` and
`_sentry_coroutine` inline the check, `_sentry_create_worker` takes it from the
`@ensure_integration_enabled(ArqIntegration, old_create_worker)` decorator — which is the rule the
contributor guide requires (§7).

## 3 The scope model

Storage and lifetime, from
[`sentry_sdk/scope.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/scope.py):

| Scope | Storage | Isolates | Forked by | Lifetime |
|---|---|---|---|---|
| Global | `_global_scope`, a module-level `Optional[Scope]` | nothing — one per process | never | the process |
| Isolation | `_isolation_scope = ContextVar("isolation_scope", default=None)` | one unit of work: request, task, job | `isolation_scope()`, `use_isolation_scope(scope)` | the `with` block, per context (so per asyncio task, not merely per thread) |
| Current | `_current_scope = ContextVar("current_scope", default=None)` | one span | `new_scope()`, `use_scope(scope)`, and implicitly by `isolation_scope()` | the `with` block |
| Merged | built on demand by `_merge_scopes` | n/a — read model | n/a | one event |

The module comments state the intent:

> Holds data that will be added to **all** events sent by this process. In case this is a http
> server (think web framework) with multiple users the data will be added to events of all users.
> Typically this is used for process wide data such as the release.

> Holds data for the active request. This is used to isolate data for different requests or users.
> The isolation scope is usually created by integrations, but may also be created manually

`new_scope()` "forks the current scope and runs the wrapped code in it. After the wrapped code is
executed, the original scope is restored." `isolation_scope()` forks two scopes: "Context manager
that forks the current isolation scope and runs the wrapped code in it. **The current scope is also
forked to not bleed data into the existing current scope.**" `_merge_scopes` composes them in fixed
order — global, then isolation, then current — into a `ScopeType.MERGED` copy per event.

Two consequences follow from where the SDK reads the scope. `sentry_sdk.add_breadcrumb` is
`get_isolation_scope().add_breadcrumb(...)`
([`sentry_sdk/api.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/api.py),
line 206), and `max_breadcrumbs` defaults to `DEFAULT_MAX_BREADCRUMBS = 100`. So without a forked
isolation scope, every concurrent unit of work in the process shares one 100-entry ring buffer, and
each event carries whatever the last hundred log records in the whole process happened to be.
`Scope.set_user`, `set_tag` and `set_context` called on the isolation scope have the same reach.

**The documented rationale.** Sentry's own SDK development documentation is explicit, and uses
RFC keywords ([Hub and Scope
Refactoring](https://develop.sentry.dev/sdk/miscellaneous/hub_and_scope_refactoring/)):

> The isolation scope **MUST** contain data specific to the current execution context: a single
> request (on a server), a single tab (in a browser), or a single user session (on mobile).

> SDK integrations **MUST** handle the forking of isolation scopes automatically. Users **MUST NOT**
> need to manage or think about isolation scope forking.

> SDKs **SHOULD** fork the isolation scope at natural isolation boundaries: Incoming HTTP request
> (server), New tab or navigation (browser), New user session (mobile), Queue job or background task

The user-facing documentation is thinner. It gives only the three definitions — "Global scope: A
single globally-shared scope storing data relevant for the whole app (such as the release)";
"Isolation scope: Thread-local scope created for each request-response lifecycle to store data
relevant to the request"; "Current scope: Thread-local scope created for each span to store data
relevant to the span" — and no statement of why a long-lived process needs the fork
([Scopes](https://docs.sentry.io/platforms/python/enriching-events/scopes/)). The closest
user-facing sentences are in the 2.0 migration guide
([`MIGRATION_GUIDE.md`](https://github.com/getsentry/sentry-python/blob/master/MIGRATION_GUIDE.md)):

> When to use `get_current_scope()` and `get_isolation_scope()` depends on how long the change to
> the scope should be in effect. If you want the changed scope to affect the whole request-response
> cycle or the whole execution of task, use the isolation scope. If it's more localized, use the
> current scope.

> The lifecycle of a single isolation scope roughly translates to the lifecycle of a transaction in
> most cases, so if you're looking to create a new separated scope for a whole request-response
> cycle or task execution, go for `isolation_scope()`.

So: the *specification* states the multi-tenant requirement as a MUST on the integration; the
*product documentation* only implies it through the phrase "for each request-response lifecycle".

## 4 What the defaults already catch

**Does `LoggingIntegration` turn `logger.error(..., exc_info=True)` into a Sentry event with no
framework integration installed? Yes.** The defaults are module constants
([`sentry_sdk/integrations/logging.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/logging.py),
lines 26–27):

```python
DEFAULT_LEVEL = logging.INFO
DEFAULT_EVENT_LEVEL = logging.ERROR
```

`LoggingIntegration.__init__` builds a `BreadcrumbHandler(level=level)` and an
`EventHandler(level=event_level)` from them. The deciding code is `EventHandler._emit`:

```python
if record.exc_info and record.exc_info[0] is not None:
    event, hint = event_from_exception(
        record.exc_info,
        client_options=client_options,
        mechanism={"type": "logging", "handled": True},
    )
```

The event then carries `level` from the record, `logger = record.name`, a `logentry` with
`message`/`formatted`/`params`, and `extra` built from every record attribute not in
`_BaseHandler.COMMON_RECORD_ATTRS`. `logger.exception(...)` is the same path, since the standard
library sets `exc_info=True` for it. The documentation states the same defaults: "`level` (default
`INFO`) … will record log records with a level higher than or equal to `level` as breadcrumbs";
"`event_level` (default `ERROR`) … will report log records with a level higher than or equal to
`event_level` as events"; "The logging integration is a default integration, so it will be enabled
automatically when you initialize the Sentry SDK"
([Logging](https://docs.sentry.io/platforms/python/integrations/logging/)).

The hook is not a handler. `setup_once()` replaces `logging.Logger.callHandlers` itself, calls the
original inside `try`, and does its own work in `finally`. The consequence is that the integration
fires for every logger in the process whether or not the application configured any handler, and it
cannot be removed by reconfiguring `logging`. Only the name-based ignore lists suppress it; they
start as `{"sentry_sdk.errors", "urllib3.connectionpool", "urllib3.connection"}`.

**An unhandled exception in an `asyncio` task.** `AsyncioIntegration` is in neither default list —
it is explicit-only. The documentation says "Add `AsyncioIntegration()` to your list of
`integrations`" and "All unhandled exceptions in tasks will be captured"
([Asyncio](https://docs.sentry.io/platforms/python/integrations/asyncio/)). With it installed, the
integration installs a task factory that wraps every non-internal coroutine, runs it inside `with
sentry_sdk.isolation_scope():`, and captures with `mechanism={"type": "asyncio", "handled": False}`
before re-raising
([`sentry_sdk/integrations/asyncio.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/asyncio.py)).
It needs a running loop at `init()` time or it logs `"There is no running asyncio loop so there is
nothing Sentry can patch. Please make sure you call sentry_sdk.init() within a running asyncio loop
for the AsyncioIntegration to work."`; `enable_asyncio_integration()` exists for the late case.

Without it, three different default paths cover three different fates of the same exception:

| Fate of the task exception | Captured? | By which integration | `mechanism` |
|---|---|---|---|
| propagates out to the top level (e.g. out of `asyncio.run`) | yes | `ExcepthookIntegration` (`sys.excepthook`) | `{"type": "excepthook", "handled": False}` |
| never retrieved — the `Task` is garbage-collected with an unconsumed exception | yes, when the object is collected | `LoggingIntegration` via the `asyncio` logger | `{"type": "logging", "handled": True}` |
| caught by the framework, logged, and swallowed | yes | `LoggingIntegration` | `{"type": "logging", "handled": True}` |
| caught and swallowed without logging | no | none | — |

The second row works because CPython's `Future.__del__` builds a context dict whose `'message'` is
`f'{self.__class__.__name__} exception was never retrieved'`, alongside `'exception'`, `'future'`
and, when set, `'source_traceback'`, then passes it to `self._loop.call_exception_handler(context)`
([`Lib/asyncio/futures.py`](https://github.com/python/cpython/blob/main/Lib/asyncio/futures.py),
lines 98–112) and `BaseEventLoop.default_exception_handler` ends with
`logger.error('\n'.join(log_lines), exc_info=exc_info)`
([`Lib/asyncio/base_events.py`](https://github.com/python/cpython/blob/main/Lib/asyncio/base_events.py),
line 1916), on the logger `logging.getLogger(__package__)` — that is, `asyncio`
([`Lib/asyncio/log.py`](https://github.com/python/cpython/blob/main/Lib/asyncio/log.py)). `asyncio`
is not in `_IGNORED_LOGGERS`, and no integration adds it. The captured event's message is therefore
the assembled multi-line handler text, not the exception's own message, and its arrival depends on
garbage collection rather than on the failure.

**Who owns which hook.** `sys.excepthook` belongs to `ExcepthookIntegration`, which is a default
integration; its `setup_once` is one line, `sys.excepthook = _make_excepthook(sys.excepthook)`, and
`_should_send` returns `False` when `hasattr(sys, "ps1")` — "Disable the excepthook for interactive
Python shells, otherwise every typo gets sent to Sentry." `sys.unraisablehook` belongs to
`UnraisablehookIntegration`, which exists in the tree but is in **neither** list, so it is not
installed by default. `threading.Thread.start` (and through it `run`) belongs to
`ThreadingIntegration`, a default integration; it does not touch `threading.excepthook`.

**Every default integration that fires for a framework that only logs an exception and returns.**

| Default integration | Fires? | What it contributes |
|---|---|---|
| `LoggingIntegration` | yes | creates the event itself from `record.exc_info`, plus INFO-level breadcrumbs from earlier records |
| `DedupeIntegration` | yes | drops the event if the *same exception object* was the previous one captured (weakref-compared `_last_seen`), logging `"DedupeIntegration dropped duplicated error event %s"` |
| `ArgvIntegration` | yes | `extra["sys.argv"]` |
| `ModulesIntegration` | yes | `event["modules"]`, the installed-package list |
| `StdlibIntegration` | yes | a `runtime` context, and HTTP-client / `subprocess` breadcrumbs recorded before the failure |
| `AtexitIntegration` | yes, at shutdown | ends the session and flushes the queue on interpreter exit |
| `ExcepthookIntegration` | no | the exception never reaches `sys.excepthook` |
| `ThreadingIntegration` | no | "Reports crashing threads" ([Default Integrations](https://docs.sentry.io/platforms/python/integrations/default-integrations/)) — the thread did not crash |

What the defaults do *not* produce: no transaction and therefore no `event["transaction"]` name, no
per-unit-of-work isolation scope (so tags, user and breadcrumbs from concurrent work land on the
same event), `handled: True` instead of `handled: False`, no messaging or queue attributes, and no
suppression of the framework's own error logger.

## 5 The overlap with tracing

Two OpenTelemetry integrations exist, pointing in opposite directions, and neither is in either
default list.

| | `OpenTelemetryIntegration` | `OTLPIntegration` |
|---|---|---|
| Module | `sentry_sdk/integrations/opentelemetry/integration.py` | `sentry_sdk/integrations/otlp.py` |
| Direction | Sentry **consumes** OTel spans: installs `SentrySpanProcessor()` on a new `TracerProvider` and maps `ReadableSpan` to Sentry `Transaction`/`Span` in-process | OTel spans are **exported to Sentry**: adds `BatchSpanProcessor(OTLPSpanExporter(endpoint, headers))` aimed at `auth.get_api_url(EndpointType.OTLP_TRACES)` from the DSN, or at `collector_url` |
| Status | deprecated; the file's own docstring says it is "part of a proof of concept and as such are experimental and not suitable for production use" | current; introduced in 2.45.0 |
| Enablement | explicit; also appended to `_DEFAULT_INTEGRATIONS` when `_experiments["otel_powered_performance"]` is set | explicit |
| Error linking | via the span processor and a global event processor | `setup_once` calls `register_external_propagation_context(otel_propagation_context)`, so error events carry the OTel `(trace_id, span_id)` |
| Exception capture | n/a | `setup_once_with_options` always calls `setup_capture_exceptions()`, which patches `Span.record_exception`; the patch captures only while the instance's `capture_exceptions` is true, and that defaults to `False` |
| Propagation | `set_global_textmap(SentryPropagator())` | `set_global_textmap(SentryOTLPPropagator())`, skippable with `setup_propagator=False` |

The deprecation is a runtime `DeprecationWarning`: `"OpenTelemetryIntegration is deprecated. Please
use OTLPIntegration instead: https://docs.sentry.io/platforms/python/integrations/otlp/"`. The same
`setup_once_with_options` refuses to run under span streaming, logging `"[OTel]
OpenTelemetryIntegration is not compatible with span streaming (trace_lifecycle='stream') and will
be disabled."` Its documentation page no longer exists:
`/platforms/python/integrations/opentelemetry/` returns Page Not Found.

**Running both without double instrumentation is documented, in one sentence.** The OTLP page
describes the integration as one that "configures the Sentry SDK to automatically send trace data
instrumented by an OpenTelemetry SDK to Sentry's OpenTelemetry Protocol ingestion endpoint" and then
states the rule: "Do not also set up tracing via the Python SDK (i.e. do not set
`traces_sample_rate` or `traces_sampler`)"
([OTLP](https://docs.sentry.io/platforms/python/integrations/otlp/)). The escape hatches are
constructor options: `setup_otlp_traces_exporter=False` ("Set to False to setup the TracerProvider
manually"), `collector_url=...` ("the exporter will send traces to this URL instead of the Sentry
OTLP endpoint derived from the DSN"), and `setup_propagator=False`. The page also warns that "The
automatic propagator setup will be removed in the next major version." On exception duplication it
concedes rather than solves: "Since Sentry already captures most exceptions, duplicate exceptions
might be dropped by `DedupeIntegration` but that should not affect your overall product experience
on the Issues page."

A framework's own reading of the same overlap is less favourable. FastStream's documentation says:
"Unfortunately, **Sentry** does not fully support **OpenTelemetry**. Specifically, **Sentry** uses
its own context format, which does not work well with **Python** implementations. The depth of
cached spans is insufficient to properly bind to the `root` span." Its recommended path is an
`opentelemetry-collector` with a `sentry` exporter, with the note "While this setup is somewhat
limited due to the lack of full support from the `sentry-sdk`, your code remains independent of the
tracing backend" ([Sentry
Support](https://github.com/ag2ai/faststream/blob/main/docs/docs/en/getting-started/observability/opentelemetry/sentry.md)).

## 6 The cost

**Runtime dependencies: two.**
[`setup.py`](https://github.com/getsentry/sentry-python/blob/master/setup.py) declares
`install_requires=["urllib3>=1.26.11", "certifi"]` and `python_requires=">=3.6"`. Everything else is
an extra — 46 of them, one per integration family. The published metadata agrees: for 2.69.1,
`requires_python` is `>=3.6` and the only `requires_dist` entries without an extra marker are
`urllib3>=1.26.11` and `certifi` ([PyPI JSON](https://pypi.org/pypi/sentry-sdk/json)).

**Wheel size.** `sentry_sdk-2.69.1-py3-none-any.whl` is 528,587 bytes; the sdist
`sentry_sdk-2.69.1.tar.gz` is 1,043,599 bytes ([PyPI JSON](https://pypi.org/pypi/sentry-sdk/json)).

**Importing without `init()`.** An AST scan of `sentry_sdk/` for module-level call statements finds
exactly three, of which two are reachable from the package `__init__`: `init_debug_support()` in
[`sentry_sdk/__init__.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/__init__.py)
line 67, and `_local.set(GLOBAL_HUB)` in the legacy
[`sentry_sdk/hub.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/hub.py),
which `__init__` imports last. The third, `ignore_logger('strawberry.execution')`, is inside an
integration module the package `__init__` never imports; `strawberry` is in
`_AUTO_ENABLING_INTEGRATIONS`, so that module loads only once `init()` walks the auto-enabling list.

`init_debug_support()` is therefore the whole import-time side effect
([`sentry_sdk/debug.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/debug.py)):
if the `sentry_sdk.errors` logger has no handlers, it attaches a `StreamHandler(sys.stderr)` with
formatter `" [sentry] %(levelname)s: %(message)s"`, calls `logger.setLevel(logging.DEBUG)`, and adds
a `_DebugFilter` that passes a record only while a client init is in progress (`_client_init_debug`)
or when `client.options["debug"]` is true. The SDK thus mutates one logger it owns, at DEBUG level,
gated by a filter — a library that would fail the standard-library `NullHandler` rule if the filter
were not there. Nothing else happens: no monkeypatching, no `sys.excepthook`, no `atexit`
registration, no thread, no network. `urllib3` is imported transitively through
`sentry_sdk/transport.py`. Until `init()` runs, `get_client()` returns a `NonRecordingClient` — "A
client that does not send any events to Sentry. This is used as a fallback when the Sentry SDK is
not yet initialized" — whose inherited `get_integration()` returns `None`, which is what every
integration patch checks before doing anything, and whose `is_active()` returns `False`, which is
what `EventHandler._emit` checks.

## 7 The framework author path

**Does Sentry document how to write an integration? Not for Python users.** The Python integrations
index has no custom-integration page
([Integrations](https://docs.sentry.io/platforms/python/integrations/)), and neither does the SDK
development site's SDK section ([develop.sentry.dev/sdk](https://develop.sentry.dev/sdk/)). The
equivalent page exists only for JavaScript: "In addition to the integrations that come with the SDK,
you can also write custom integrations", with a `name`/`setup`/`setupOnce`/`processEvent` interface
([Custom
Integrations](https://docs.sentry.io/platforms/javascript/guides/node/configuration/integrations/custom/)).

The only Python authoring guidance is [`CONTRIBUTING.md` § Adding a New
Integration](https://github.com/getsentry/sentry-python/blob/master/CONTRIBUTING.md), and it is
written for contributions *into* `getsentry/sentry-python`, not for a package you own. Its steps are
repo-internal: "document in `_MIN_VERSIONS` in `integrations/__init__.py`", "Create a new folder in
`tests/integrations/`", "Add the test suite to the script generating our test matrix", and "Write
the [docs](https://github.com/getsentry/sentry-docs)". Two of its rules read as constraints on any
integration author, wherever the code lives:

> Avoid registering a new client or the like. The user drives the client, and the client owns
> integrations.

> Allow the user to turn off the integration by changing the client. Check
> `sentry_sdk.get_client().get_integration(MyIntegration)` from within your signal handlers or
> patches to see if your integration is still active before you do anything impactful (such as
> sending an event). If it's not active, the patch my be no-op.

And the framing rule for the whole surface:

> The SDK runs as part of users' applications. Users do not expect their application to crash, the
> SDK to mutate object references, the SDK to swallow their exceptions, leaked file descriptors to
> eat their memory, SDK-initiated database requests, or the SDK to alter the signature of functions
> or coroutines.

**Does the SDK discover a third-party integration? No — nothing.** There is no entry-point group, no
registry and no plugin scan. Grepping `sentry_sdk/` for `entry_points`/`entry_point` returns only
`gcp.py`'s unrelated `ENTRY_POINT` environment variable, and `setup.py` declares exactly one entry
point group, `opentelemetry_propagator`, for `SentryPropagator` — not for integrations. The only
supported wiring is for the application to name the class:
`sentry_sdk.init(integrations=[MyIntegration()])`. A third-party distribution can therefore ship an
`Integration` subclass and it will work, but it can never be auto-enabled, because auto-enablement
is a hard-coded import-string list inside the SDK.

Two precedents show what the practice is. Donation into the SDK is documented in code — the
`DramatiqIntegration` docstring reads "This integration was originally developed and maintained by
https://github.com/jacobsvante and later donated to the Sentry project"
([`sentry_sdk/integrations/dramatiq.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/dramatiq.py),
lines 48–50) — and even after donation `dramatiq` is in neither list, so users still name it.
Independent distribution also happens: `aiogram-sentry` 0.1.0, summary "Sentry's Aiogram
integration", depends on `sentry-sdk` and `aiogram>=3,<4`, last released 2024-09-30 ([PyPI
JSON](https://pypi.org/pypi/aiogram-sentry/json)).

## 8 What framework maintainers say

**aiogram.** The clearest statement by a framework maintainer is Alex Root Junior (`JrooTJunior`,
aiogram's lead maintainer) on aiogram#1785, 2026-03-09, answering a request for native
OpenTelemetry support:

> I completely agree with this statement, it is much better to implement this integration inside a
> framework with a pluggable interface (even for seamless support of Sentry just like
> OpenTelemetry). Since patching internal components from outside reduces performance, native
> support is cheaper.

He was agreeing with a reply on the companion request the same reporter had opened there, by Lukas
Hering — whom JrooTJunior calls "the maintainer of OpenTelemetry contrib", though the contrib README
lists him under *Approvers*, not *Maintainers*: "Before going down the route of adding a new contrib
package, have you confronted the `aiogram` maintainers to see if they would support adding
OpenTelemetry support directly to their library. It is generally much more ergonomic to have the
original library authors support instrumentation directly"
([opentelemetry-python-contrib#4317](https://github.com/open-telemetry/opentelemetry-python-contrib/issues/4317#issuecomment-4020451642)).
In the same comment he explains why aiogram nevertheless has neither: "I don't have enough time to
implement such a feature right now (if I start doing it, it could take 6-9 months or more), nor do
the few volunteers I have", and points at the dead Sentry attempt — "#523: *Sentry performance
monitoring support* - since 2021, partially implemented for version 2.x, which is no longer
supported after migrating to 3.x" ([aiogram#1785](https://github.com/aiogram/aiogram/issues/1785)).
That pull request, "Sentry performance monitoring support" (2021-03-13), was closed unmerged with
the maintainer's comment "v2 will no more be supported, this PR should be reworked into v3"
([aiogram#523](https://github.com/aiogram/aiogram/pull/523)). Grepping the aiogram tree for `sentry`
returns nothing.

**Litestar and Sentry, on the same issue, from both sides.** Sentry opened the work as its own:
"Since we already have a Starlite integration, adding support for Litestar should in the ideal case
just be a matter of checking the changelog for the new major and creating a new integration based on
the existing one. … Write the new integration." A Litestar maintainer replied "we would love to see
native support for this as well", where "native" means inside the Sentry SDK, and Sentry answered
"if anyone feels like tackling this, we're happy to provide support"
([sentry-python#2413](https://github.com/getsentry/sentry-python/issues/2413)). Litestar's own
mirror-image ticket, "Enhancement: Add `Sentry` integration for 2.0", says "We have a sentry
integration for 1.x. We need to update that integration, but we did not write any docs" and routes
the documentation into Sentry's docs following Sentry's integration guide; it was labelled *Help
Wanted* and closed ([litestar#1514](https://github.com/litestar-org/litestar/issues/1514)). The
integration landed in the SDK, and the commit that switched on auto-enablement — "Auto enable
Litestar integration (#3540) by @provinzkraut"
([`CHANGELOG.md`](https://github.com/getsentry/sentry-python/blob/master/CHANGELOG.md)) — came from
a contributor listed with the maintenance badge in Litestar's own README
([litestar README](https://github.com/litestar-org/litestar/blob/main/README.md)). A Litestar
maintainer contributed to `sentry-python`, not to Litestar.

**Rasa** is the counter-example of a framework that owns its Sentry wiring, and its in-code comment
says why it distrusts the defaults: "this is a very defensive configuration, avoiding as many
integrations as possible. it also submits very little data (exception with error message and line
numbers)." It calls `sentry_sdk.init(..., default_integrations=False)` with exactly three
integrations — `ExcepthookIntegration()`, `DedupeIntegration()`, `AtexitIntegration(lambda _, __:
None)` — plus `send_default_pii=False`, `in_app_include=["rasa"]` and an `ignore_errors` list that
includes `asyncio.CancelledError`
([`rasa/telemetry.py`](https://github.com/RasaHQ/rasa/blob/3.6.x/rasa/telemetry.py)). This is a
framework reporting its *own* crashes, not offering an integration to its users.

**Sanic** ships an example, not an integration: `examples/sentry_example.py` imports
`SanicIntegration` from the SDK, and the guide points at the framework's own hook instead — "Sanic
has a signal that allows you to hook into the exception reporting process. This is useful if you
want to send exception information to a third party service like Sentry or Rollbar" ([exceptions
guide](https://github.com/sanic-org/sanic/blob/main/guide/content/en/guide/best-practices/exceptions.md)).
**Django** and **Dramatiq** both defer by hyperlink: "Consider using an error monitoring system such
as Sentry before your inbox is flooded by reports" ([deployment
checklist](https://github.com/django/django/blob/main/docs/howto/deployment/checklist.txt)); "You
should use an error reporting service such as Sentry so you get notified of these errors as soon as
they occur" ([best
practices](https://github.com/Bogdanp/dramatiq/blob/master/docs/source/best_practices.rst)).

**Who ships it in practice.**

| Framework | Ships the integration | Module or package | Auto-enabled by the SDK | Evidence |
|---|---|---|---|---|
| aiogram | nobody first-party; a third party | `aiogram-sentry` 0.1.0 (rocshers, GitLab) | no | [PyPI JSON](https://pypi.org/pypi/aiogram-sentry/json); `sentry` absent from the aiogram tree; [aiogram#523](https://github.com/aiogram/aiogram/pull/523) closed unmerged |
| FastStream | nobody | none — an `opentelemetry-collector` with a `sentry` exporter | no | [FastStream Sentry Support](https://github.com/ag2ai/faststream/blob/main/docs/docs/en/getting-started/observability/opentelemetry/sentry.md) |
| Litestar | the SDK | `sentry_sdk.integrations.litestar` | yes | [`_AUTO_ENABLING_INTEGRATIONS`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/__init__.py); [litestar#1514](https://github.com/litestar-org/litestar/issues/1514) |
| arq | the SDK | `sentry_sdk.integrations.arq` | yes | same list; `sentry` absent from the arq tree |
| Celery | the SDK | `sentry_sdk.integrations.celery` | yes | same list; only historical mentions in the Celery tree |
| Django | the SDK | `sentry_sdk.integrations.django` | yes | same list; Django's checklist links to Sentry's docs |
| Flask | the SDK | `sentry_sdk.integrations.flask` | yes | same list |
| FastAPI | the SDK | `sentry_sdk.integrations.fastapi` | yes | same list |
| Starlette | the SDK | `sentry_sdk.integrations.starlette` | yes | same list |
| Dramatiq | the SDK, by donation | `sentry_sdk.integrations.dramatiq` | **no** | [integration docstring](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/dramatiq.py) |

Eight of the ten frameworks named above have their integration in the SDK; the two async
frameworks closest in shape to a bot framework — aiogram and FastStream — have none there, and
neither ships one itself.

## 9 What the evidence supports

- A `capture_exception` at the failure site produces an event with
  `mechanism={"type": "generic", "handled": True}`, no transaction, and whatever the process-global
  isolation scope happens to hold. A first-party integration adds five things that call cannot:
  a forked isolation scope per unit of work, a named transaction, `handled: False`, per-unit tags
  and `extra` attached through a scope-local event processor, and suppression of the framework's own
  error logger so the same failure is not reported twice.
- The contract an integration must satisfy is small and fully documented in source: an `identifier`
  string and a `setup_once()` staticmethod that runs once per process from inside
  `sentry_sdk.init()`, with configuration unavailable at that point. A missing dependency is
  signalled by raising `DidNotEnable` at module import; that is silently swallowed for a default
  integration and re-raised for an explicitly named one.
- With no framework integration at all, six of the eight default integrations still fire for a
  framework that logs an exception and returns. `LoggingIntegration` alone turns
  `logger.error(..., exc_info=True)` into a full Sentry event with a stack trace, at
  `event_level=ERROR` by default, by patching `logging.Logger.callHandlers` rather than installing a
  handler — so no logging configuration can opt out of it.
- Unhandled exceptions in asyncio tasks are already covered by the defaults, but badly: through
  `sys.excepthook` only if they escape to the top level, and otherwise through the `asyncio` logger
  at garbage-collection time, where the event message is CPython's assembled handler text rather
  than the exception. `AsyncioIntegration`, which fixes both, is explicit-only.
- Scope isolation is the one thing the SDK will not do for a framework it does not know about.
  Sentry's own SDK development documentation states it as an obligation on the integration: the
  isolation scope "MUST contain data specific to the current execution context", and "SDK
  integrations MUST handle
  the forking of isolation scopes automatically. Users MUST NOT need to manage or think about
  isolation scope forking." Without a fork, one 100-entry breadcrumb buffer and one user/tag set are
  shared by every concurrent unit of work in the process.
- The whole worked example is 296 lines of patching and no state: `ArqIntegration` patches three
  functions, forks one isolation scope per job, sets two tags and one `extra` block, re-raises every
  exception it captures, and stores nothing on the instance.
- Cost is two runtime dependencies (`urllib3>=1.26.11`, `certifi`), a 529 KB wheel, and one
  import-time side effect: a stderr handler on the SDK's own `sentry_sdk.errors` logger, gated by a
  filter that checks `options["debug"]`. Importing `sentry_sdk` patches nothing and sends nothing.
- Sentry documents how to *contribute* an integration to its own repository, and documents custom
  integrations only for JavaScript. There is no discovery mechanism for Python at all: no entry
  points and no registry — the application names the class in `sentry_sdk.init(integrations=[...])`.
  A framework-owned integration is therefore always opt-in for the user, and the documented route to
  auto-enablement is donating the code to Sentry.
- Practice is one-sided: eight of the ten frameworks surveyed have their integration in the SDK,
  and in the two cases where a framework maintainer engaged, the Litestar maintainer contributed to
  `sentry-python` while aiogram's maintainer argued the opposite in principle — "it is much better
  to implement this integration inside a framework with a pluggable interface" — and shipped
  nothing, for lack of maintainer time.

## Sources

Every claim above carries its own link inline. This section names what was read end to end.

`getsentry/sentry-python` at 2.69.1, `master` commit `7e95b86bc31b0a1411f0e54c0397152b2201cb2f`:

- <https://github.com/getsentry/sentry-python> — `sentry_sdk/integrations/__init__.py`,
  `sentry_sdk/integrations/arq.py`, `sentry_sdk/integrations/logging.py`,
  `sentry_sdk/integrations/asyncio.py`, `sentry_sdk/integrations/dramatiq.py`,
  `sentry_sdk/integrations/opentelemetry/integration.py`, `sentry_sdk/integrations/otlp.py`,
  `sentry_sdk/scope.py`, `sentry_sdk/client.py`, `sentry_sdk/consts.py`, `sentry_sdk/api.py`,
  `sentry_sdk/utils.py`, `sentry_sdk/tracing.py`, `sentry_sdk/tracing_utils.py`,
  `sentry_sdk/debug.py`, `sentry_sdk/hub.py`, `sentry_sdk/__init__.py`, `setup.py`,
  `CONTRIBUTING.md`, `MIGRATION_GUIDE.md`, `CHANGELOG.md`,
  `tests/integrations/arq/test_arq.py`
- <https://github.com/getsentry/sentry-python/issues/2413>

Sentry documentation:

- <https://docs.sentry.io/platforms/python/integrations/> ·
  <https://docs.sentry.io/platforms/python/integrations/default-integrations/> ·
  <https://docs.sentry.io/platforms/python/integrations/logging/> ·
  <https://docs.sentry.io/platforms/python/integrations/asyncio/> ·
  <https://docs.sentry.io/platforms/python/integrations/otlp/> ·
  <https://docs.sentry.io/platforms/python/enriching-events/scopes/>
- <https://develop.sentry.dev/sdk/> ·
  <https://develop.sentry.dev/sdk/miscellaneous/hub_and_scope_refactoring/>
- <https://docs.sentry.io/platforms/javascript/guides/node/configuration/integrations/custom/>

The standard library:

- <https://github.com/python/cpython> — `Lib/asyncio/futures.py`, `Lib/asyncio/base_events.py`,
  `Lib/asyncio/log.py`

Package metadata:

- <https://pypi.org/pypi/sentry-sdk/json> · <https://pypi.org/pypi/aiogram-sentry/json>

What the frameworks themselves ship and say:

- <https://github.com/aiogram/aiogram/issues/1785> · <https://github.com/aiogram/aiogram/pull/523> ·
  <https://github.com/open-telemetry/opentelemetry-python-contrib/issues/4317>
- <https://github.com/litestar-org/litestar/issues/1514> ·
  <https://github.com/litestar-org/litestar/blob/main/README.md>
- <https://github.com/ag2ai/faststream/blob/main/docs/docs/en/getting-started/observability/opentelemetry/sentry.md>
- <https://github.com/RasaHQ/rasa/blob/3.6.x/rasa/telemetry.py> ·
  <https://github.com/sanic-org/sanic/blob/main/guide/content/en/guide/best-practices/exceptions.md>
- <https://github.com/django/django/blob/main/docs/howto/deployment/checklist.txt> ·
  <https://github.com/Bogdanp/dramatiq/blob/master/docs/source/best_practices.rst>
