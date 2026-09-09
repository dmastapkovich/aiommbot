# 23. Dispatch-path observability in async frameworks

**Question.** How does a Python framework that dispatches inbound events offer observability
**without imposing a dependency**, and what shape would a reader of this ecosystem expect? What do
the top async frameworks instrument on the dispatch path, through which mechanism, under which
names, and how does the application decline it?

Gathered for GitHub issue #29. Two neighbouring notes answer different questions and are not
repeated here: [`docs/research/17`](17-http-client-observability.md) covers the *outbound HTTP*
observer surface, its record fields and its logging policy, and
[`docs/research/08`](08-peer-responsibility-boundaries.md) covers the *responsibility* question —
core, extra, recipe or absent. This note covers the *shape*: the mechanism, the names, the
ownership of process-global state and the cardinality rule.

Findings only — the decisions are
[ADR-0048](../adr/0048-observability-is-not-a-core-seam.md) to
[ADR-0051](../adr/0051-first-party-observability-plugin.md). All sources are primary
(specification text, PEPs, official documentation, source code on GitHub, PyPI metadata), read on
2026-09-09. Peer libraries
are evidence of practice, not authority. Anything not confirmed from such a source is marked
**[unverified]**.

## 1 What the standards prescribe

### 1.1 No PEP governs metrics or tracing

There is no PEP defining a metrics or tracing API for Python. A search of the PEP index returns
only tangential documents: [PEP 831](https://peps.python.org/pep-0831/) on frame-pointer
profiling, [PEP 799](https://peps.python.org/pep-0799/) on a profiling package, and
[PEP 752](https://peps.python.org/pep-0752/), which mentions OpenTelemetry once as a naming
example. None defines an interface a library could target.

Logging is the one observability signal the language standardises, and it standardises the
*mechanism*, never the policy. [PEP 282](https://peps.python.org/pep-0282/) is a rationale
document whose only sentence bearing on libraries is aspirational — "If a single logging mechanism
is enshrined in the standard library, … multiple libraries will be able to be integrated into
larger applications which can be logged reasonably coherently" — and it leaves every handler,
format and level decision to the application. [PEP 391](https://peps.python.org/pep-0391/)
specifies a configuration schema and is written entirely from the application's point of view; it
places no obligation on a library at all.

The consequence for a framework: for logs there is a standard to obey, and for metrics and traces
there is only a convention to follow or ignore.

### 1.2 What the standard library tells a library author

The [Logging HOWTO](https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library)
is prescriptive in three sentences: "If the using application does not use logging, and library
code makes logging calls, then … events of severity `WARNING` and greater will be printed to
`sys.stderr`. This is regarded as the best default behaviour"; "It is strongly advised that you *do
not log to the root logger* in your library. Instead, use a logger with a unique and easily
identifiable name, such as the `__name__` for your library's top-level package or module"; and "It
is strongly advised that you *do not add any handlers other than* `NullHandler` *to your library's
loggers*. This is because the configuration of handlers is the prerogative of the application
developer who uses your library."

Two mechanical constraints follow from the reference page rather than the HOWTO. First,
[`logging.lastResort`](https://docs.python.org/3/library/logging.html) is "a `StreamHandler`
writing to `sys.stderr` with a level of `WARNING`" used "in the absence of any logging
configuration", which is what makes the default above true. Second, and load-bearing for a
redaction list of field names: "The keys in the dictionary passed in *extra* should not clash with
the keys used by the logging system", where the keys in question are the
[LogRecord attributes](https://docs.python.org/3/library/logging.html#logrecord-attributes) —
`args`, `asctime`, `created`, `exc_info`, `exc_text`, `filename`, `funcName`, `levelname`,
`levelno`, `lineno`, `message`, `module`, `msecs`, `msg`, `name`, `pathname`, `process`,
`processName`, `relativeCreated`, `stack_info`, `thread`, `threadName` and `taskName`. The clash
raises rather than being dropped, as `Logger.makeRecord` shows
([`docs/research/24`](24-library-logging-design.md) §2), and the set overlaps the vocabulary of a
chat platform at `message`, `name`, `module`, `process` and `args`.

### 1.3 Context propagation is guaranteed across `await`, not across a thread pool

[PEP 567](https://peps.python.org/pep-0567/) gives an `asyncio.Task` its own context copied at
creation, and the
[`contextvars` documentation](https://docs.python.org/3/library/contextvars.html) states that
"each thread has its own context stack", behaving "in a similar fashion to `threading.local()`".
The two thread entry points differ, and the difference is documented asymmetrically:
[`asyncio.to_thread`](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread) states
that "the current `contextvars.Context` is propagated, allowing context variables from the event
loop thread to be accessed in the separate thread", while
[`loop.run_in_executor`](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor)
mentions `contextvars` nowhere. PEP 567's own example gives the explicit workaround —
"It is possible to run code in a separate OS thread using a copy of the current thread context:
`executor.submit(current_context.run, some_function)`".

A correlation identifier carried in a `ContextVar` therefore survives every `await` and every task,
and reaches a thread-pool call only if the caller copies the context by hand.

### 1.4 OpenTelemetry's advice to library authors

The [Libraries](https://opentelemetry.io/docs/concepts/instrumentation/libraries/) page carries four
statements a framework has to answer to. The API-only rule: "Libraries should only use the
OpenTelemetry API." The cost claim: "Unless your application imports the OpenTelemetry SDK, your
instrumentation does nothing and does not impact application performance." A negative rule: "Don't
instrument if all the following cases apply: Your library is a thin proxy on top of documented or
self-explanatory APIs. OpenTelemetry has instrumentation for underlying network calls. There are no
conventions your library should follow to enrich telemetry." And, decisively for the packaging
question, "While your instrumentation stabilizes, consider shipping it as a separate package, so
that it never causes issues for users who don't use it."

The API's own stability promise is strong:
[versioning and stability](https://opentelemetry.io/docs/specs/otel/versioning-and-stability/)
requires that "Backward-incompatible changes to API packages MUST NOT be made unless the major
version number is incremented", that "All existing API calls MUST continue to compile and function
against all future minor versions of the same major version", and that "Major versions of the API
MUST be supported for a minimum of three years after the release of the next major API version".

The dependency is small. `opentelemetry-api` 1.44.0 (released 2026-07-16) declares
`requires-python >=3.10` and exactly one runtime dependency, `typing-extensions>=4.5.0`
([PyPI JSON](https://pypi.org/pypi/opentelemetry-api/json),
[pyproject.toml](https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-api/pyproject.toml)).

### 1.5 Prometheus, OpenMetrics and W3C Trace Context

Naming rules from [Prometheus practices](https://prometheus.io/docs/practices/naming/): metrics
"SHOULD use base units (e.g. seconds, bytes, meters - not milliseconds, megabytes, kilometers)";
"an accumulating count has `total` as a suffix"; names "SHOULD have a suffix describing the unit,
in plural form"; and "Do not put the label names in the metric name, as this introduces
redundancy."

Cardinality guidance, with the only published numbers in this whole survey, from
[Prometheus instrumentation](https://prometheus.io/docs/practices/instrumentation/): "As a general
guideline, try to keep the cardinality of your metrics below 10, and for metrics that exceed that,
aim to limit them to a handful across your whole system"; "If you have a metric that has a
cardinality over 100 or the potential to grow that large, investigate alternate solutions." The
same page addresses library authors twice: "Libraries should provide instrumentation with no
additional configuration required by users", and, for calls to external resources, track "the
overall query count, errors (if errors are possible) and latency at a minimum".

[OpenMetrics](https://github.com/prometheus/OpenMetrics/blob/main/specification/OpenMetrics.md)
declines to add a limit — "This standard does not prescribe any particular limits on the number of
samples exposed by a single exposition, the number of labels that may be present…" — and its one
library-relevant rule is about namespacing: "The more public a library is the better namespaced its
metric names should be."

[W3C Trace Context](https://www.w3.org/TR/trace-context/) fixes `traceparent` as
`version "-" trace-id "-" parent-id "-" trace-flags` (2, 32, 16 and 2 lowercase hex digits, all-zero
ids forbidden) and `tracestate` as a list of at most 32 members. Its one normative privacy rule is
absolute: "Tracing vendors MUST NOT use `traceparent` and `tracestate` fields for any personally
identifiable or otherwise sensitive information", and the random-number generator "MUST NOT rely on
any information that can potentially be user-identifiable".

### 1.6 There is no mechanical cardinality rule anywhere

Across every source above, no published rule bounds label cardinality mechanically. Prometheus
publishes heuristics in prose; OpenMetrics explicitly refuses to prescribe; no PEP applies; the
OpenTelemetry conventions encode the intent *structurally* instead — metrics carry `url.template`
and never `url.full`, `http.request.method` collapses unknown verbs to `_OTHER`, and `error.type`
"SHOULD have low cardinality" ([`docs/research/17`](17-http-client-observability.md) §1, §6). Any
allow-list, ceiling or validation step a framework enforces is therefore its own policy layered on
top of the ecosystem, not compliance with it — a distinction worth stating wherever such a rule is
written down.

## 2 OpenTelemetry semantic conventions for an event-consuming bot

### 2.1 The messaging conventions are not stable

The messaging conventions carry the **Development** status badge — OpenTelemetry's current term for
the former "Experimental" tier — on both the index and the spans page, and the spans page still
frames its guidance around instrumentations emitting the pre-stabilisation v1.24.0 attributes and
migrating through the `OTEL_SEMCONV_STABILITY_OPT_IN` switch with the values `messaging` and
`messaging/dup` ([messaging](https://opentelemetry.io/docs/specs/semconv/messaging/),
[messaging-spans](https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/)). The
current specification release is v1.44.0
([releases](https://github.com/open-telemetry/semantic-conventions/releases)); a CHANGELOG entry
"Define a span per messaging operation type (create, send, receive, process, settle)" is attributed
to that release **[unverified]** at line-exact level. Stabilisation is open work:
[oteps#192](https://github.com/open-telemetry/oteps/pull/192) is unmerged, and a governance proposal
that would let instrumentation libraries stabilise while the underlying conventions stay in
Development is under discussion in
[semantic-conventions#3330](https://github.com/open-telemetry/semantic-conventions/issues/3330).

A framework that adopts these names inherits their status: the names may change, and a library's own
compatibility promise cannot cover them.

### 2.2 The consumer span shape

From [messaging-spans](https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/): the
span name is `{messaging.operation.name} {destination}`, where the destination is taken from
`messaging.destination.template`, else `messaging.destination.name`, else
`server.address:server.port` — in that preference order. The span kind is **CONSUMER** for `process`
(push-based delivery) and **CLIENT** for `receive` (pull-based) and `settle`. The five operation
types are `create`, `send`, `receive`, `process` and `settle`.

Requirement levels for a consumer span: `messaging.system` **Required**;
`messaging.operation.name` **Required**; `messaging.operation.type` **Conditionally Required** if
applicable; `messaging.destination.name` **Conditionally Required** when it describes a single
message or a batch-wide value; `messaging.message.id` **Recommended** for a single-message
operation.

The span-name rule is the trap for a chat platform. Read naively — with the channel as the
destination — it puts an unbounded platform identifier into the span name and into a metric
attribute, which is exactly what §1.5's cardinality guidance and the redaction rules of
[`docs/research/17`](17-http-client-observability.md) §7 forbid. The reading that avoids it is that
a bot consumes **one stream** — the WebSocket connection to one server — and the channel is a
property of the message, not of the destination, exactly as a Kafka topic is the destination and the
record key is not.

### 2.3 No registered value for a chat platform, and no WebSocket convention

The `messaging.system` enumeration is a closed list of named brokers — `activemq`, `aws.sns`,
`aws_sqs`, `eventgrid`, `eventhubs`, `gcp_pubsub`, `jms`, `kafka`, `pulsar`, `rabbitmq`, `rocketmq`,
`servicebus` — and the registry states the escape explicitly: "If one of them applies, then the
respective value MUST be used; otherwise, a custom value MAY be used"
([registry](https://opentelemetry.io/docs/specs/semconv/registry/attributes/messaging/)). A chat
platform therefore mints its own low-cardinality value with the conventions' permission, and has no
worked example to copy.

There is no separate WebSocket semantic convention. WebSocket transport telemetry falls under the
general network attributes (`network.protocol.name`) rather than a dedicated document. This is a
negative finding from non-discovery rather than a statement by a source that discusses it
**[unverified]**.

The HTTP client conventions, by contrast, are Stable, and their attribute set, metric names,
requirement levels and redaction rules are recorded in
[`docs/research/17`](17-http-client-observability.md) §1 and not repeated here.

## 3 What peer frameworks instrument on the dispatch path

### 3.1 FastStream

Core dependencies are `fast-depends[pydantic]`, `typing-extensions` and `anyio`; neither
`opentelemetry-api` nor `prometheus-client` is among them. `opentelemetry-sdk>=1.24.0,<2.0.0` ships
only under the `otel` extra and `prometheus-client>=0.20.0,<0.30.0` only under `prometheus`
([pyproject.toml](https://github.com/airtai/faststream/blob/main/pyproject.toml)). Note that the
extra pins the **SDK**, not the API, because its middleware helpers need it.

`PrometheusMiddleware.__init__` takes `registry: CollectorRegistry` as a **mandatory** keyword
argument, beside `app_name`, `metrics_prefix="faststream"`, `settings_provider_factory`,
`received_messages_size_buckets` and `custom_labels`; it never touches the global `REGISTRY`
([middleware.py](https://github.com/airtai/faststream/blob/main/faststream/prometheus/middleware.py)).
The metrics, all prefixed by `metrics_prefix`, are `received_messages_total`,
`received_messages_size_bytes`, `received_messages_in_process`,
`received_processed_messages_total` (with a `status` label),
`received_processed_messages_duration_seconds`,
`received_processed_messages_exceptions_total` (with `exception_type`),
`published_messages_total`, `published_messages_duration_seconds` and
`published_messages_exceptions_total`; the base labels on all of them are `app_name`, `broker` and
`handler`/`destination`, plus any `custom_labels`
([container.py](https://github.com/airtai/faststream/blob/main/faststream/prometheus/container.py)).

The OpenTelemetry middleware names spans `"{destination} create"` / `"{destination} publish"` as
PRODUCER and `"{destination} create"` / `"{destination} process"` as CONSUMER, sets
`messaging.system`, `messaging.destination.name`, `messaging.destination_publish.name`,
`messaging.operation`, `messaging.batch.message_count` and `error.type`, and emits the histograms
`messaging.publish.duration` and `messaging.process.duration` plus the optional counters
`messaging.publish.messages` and `messaging.process.messages` when
`include_messages_counters=True`
([middleware.py](https://github.com/airtai/faststream/blob/main/faststream/opentelemetry/middleware.py),
[consts.py](https://github.com/airtai/faststream/blob/main/faststream/opentelemetry/consts.py)).

Both are **middleware over the existing chain**, not a dedicated observation Protocol.

### 3.2 Litestar

Core dependencies are `anyio`, `msgspec`, `multidict`, `typing-extensions`, `multipart` and
`sniffio`; `opentelemetry-instrumentation-asgi` with `opentelemetry-sdk` sits in the
`opentelemetry` extra and `prometheus-client` in `prometheus`, both aggregated into `full`
([pyproject.toml](https://github.com/litestar-org/litestar/blob/main/pyproject.toml)).

`PrometheusConfig` exposes `app_name`, `prefix`, `labels`, `exemplars`, `buckets`,
`excluded_http_methods`, `exclude`, `exclude_opt_key`, `scopes`, `middleware_class` and
`group_path` — and **no `registry` field at all**, so `PrometheusMiddleware` constructs its
`Counter`/`Histogram`/`Gauge` objects without a `registry=` argument and they land in
`prometheus_client`'s global default registry
([config.py](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/prometheus/config.py),
[middleware.py](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/prometheus/middleware.py)).
The metrics are `{prefix}_requests_total`, `{prefix}_request_duration_seconds`,
`{prefix}_requests_in_progress` (with `multiprocess_mode="livesum"`) and
`{prefix}_requests_error_total`, labelled `method`, `path`, `status_code` and `app_name` merged
with `config.labels`. Its only cardinality mitigation is the `group_path` flag, whose docstring
reads "Whether to group paths in the metrics to avoid cardinality explosion"
([reference](https://docs.litestar.dev/latest/reference/plugins/prometheus.html)); the cardinality
of user-supplied `labels` is left to the user.

### 3.3 Celery

Metrics are absent from the core, and the documentation says so plainly: "While Prometheus
monitoring is not a native part of Celery, you can easily monitor your Celery workers using
Prometheus via Flower"
([monitoring.rst](https://github.com/celery/celery/blob/main/docs/userguide/monitoring.rst)).

The dispatch-path mechanism is signals: `task_received`, `task_prerun`, `task_postrun`,
`task_success`, `task_retry`, `task_failure`, `task_internal_error`, `task_revoked`,
`task_rejected` and `task_unknown`, each with a documented argument set
([signals.py](https://github.com/celery/celery/blob/main/celery/signals.py)), fired inline by
`build_tracer`/`trace_task` in the same call stack as the task
([trace.py](https://github.com/celery/celery/blob/main/celery/app/trace.py)). Celery's own
`Signal.send` is a blocking in-process loop over synchronous receivers, and `send_robust` is the
same function — there is no separate "safe" variant. Failure is isolated and logged, and the
remaining receivers still run: `except Exception as exc: logger.exception('Signal handler %r
raised: %r', receiver, exc)`
([signal.py](https://github.com/celery/celery/blob/main/celery/utils/dispatch/signal.py)).

`opentelemetry-instrumentation-celery` is a separate installable package that connects to
`task_prerun`, `task_postrun`, `task_failure` and `task_retry`
([contrib](https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation/opentelemetry-instrumentation-celery)).

### 3.4 taskiq, arq, Dramatiq

**taskiq** is a hybrid: `PrometheusMiddleware` and `OpenTelemetryMiddleware` live inside the core
package
([middlewares](https://github.com/taskiq-python/taskiq/blob/master/taskiq/middlewares/prometheus_middleware.py)),
while their real dependencies sit behind the `taskiq[metrics]` and `taskiq[opentelemetry]` extras
([pyproject.toml](https://github.com/taskiq-python/taskiq/blob/master/pyproject.toml)), so
importing them without the extra raises `ImportError`. The mechanism is the `TaskiqMiddleware`
abstract base with `pre_send`, `post_send`, `pre_execute`, `post_execute`, `post_save` and
`on_error` ([middleware.py](https://github.com/taskiq-python/taskiq/blob/master/taskiq/abc/middleware.py));
the hooks accept either colour, declared as `Union[T, Coroutine]` and called through
`await maybe_awaitable(...)`. Only `post_save` is wrapped in a try/except — a raising
`pre_execute`, `post_execute` or `on_error` propagates
([receiver.py](https://github.com/taskiq-python/taskiq/blob/master/taskiq/receiver/receiver.py)).
Its metric names were not retrieved **[unverified]**.

**arq** has no metrics in core or in the official organisation. Its dispatch-path surface is three
plain async callback slots — `on_job_start`, `on_job_end`, `after_job_end` — passed to `Worker(...)`
and fired around `run_job`
([worker.py](https://github.com/python-arq/arq/blob/main/arq/worker.py)). Whether a raising hook is
isolated was not confirmed **[unverified]**. What is confirmed is that arq logs every job
unconditionally through `logging.getLogger('arq.worker')` — start, success, retry and failure with
timing — with no optional dependency.

**Dramatiq** keeps `prometheus-client` in the `dramatiq[prometheus]` extra
([setup.py](https://github.com/Bogdanp/dramatiq/blob/main/setup.py)). Its mechanism is a
`Middleware` base class with `before_process_message`, `after_process_message`,
`after_skip_message`, the ack/nack and enqueue pairs and the worker/thread boot hooks, all plain
synchronous `def` with no-op defaults
([middleware.py](https://github.com/Bogdanp/dramatiq/blob/main/dramatiq/middleware/middleware.py)).
`Broker.emit_before`/`emit_after` catch generic `Exception`, call `logger.critical(...)` and swallow
it so processing continues; only `MiddlewareError` and `SkipMessage` propagate, and only from
`emit_before` ([broker.py](https://github.com/Bogdanp/dramatiq/blob/main/dramatiq/broker.py)). The
Prometheus middleware forks its own `http.server.HTTPServer` rather than calling
`start_http_server`, writes to a `PROMETHEUS_MULTIPROC_DIR` shared directory, uses its own
`CollectorRegistry` and never the global one, and registers `dramatiq_messages_total`,
`dramatiq_message_errors_total`, `dramatiq_message_retries_total`, `dramatiq_message_rejects_total`,
`dramatiq_messages_inprogress`, `dramatiq_delayed_messages_inprogress` and
`dramatiq_message_duration_milliseconds`, all labelled `queue_name` and `actor_name`
([prometheus.py](https://github.com/Bogdanp/dramatiq/blob/main/dramatiq/middleware/prometheus.py)).
Since 2.0 it is **not** in `default_middleware` and must be installed and added explicitly
([__init__.py](https://github.com/Bogdanp/dramatiq/blob/main/dramatiq/middleware/__init__.py),
[changelog](https://dramatiq.io/changelog.html)).

### 3.5 The chat and web frameworks

**discord.py** has no metrics or tracing and states no position on them. Dispatch runs
`Client.dispatch()` → `_schedule_event` → `_run_event`
([client.py](https://github.com/Rapptz/discord.py/blob/master/discord/client.py)), where
`_run_event` catches everything but `CancelledError` and routes it to `on_error`, whose default is
`logger.exception('Ignoring exception in %s', ...)`. `on_socket_raw_receive` exists but fires only
when `enable_debug_events` is switched on, which it is not by default.

**hikari** has none either, and the maintainers say so in an open issue: "We want to expose more
data that can be used for metrics... for an official future side package hikari-risa"
([#2783](https://github.com/hikari-py/hikari/issues/2783)). `EventManagerBase.dispatch()` fans out
through `asyncio.create_task(self._invoke_callback(...))` per matching event class;
`_invoke_callback` catches, logs at `debug` or `error` depending on whether an `ExceptionEvent`
listener exists, then
dispatches an `ExceptionEvent` instead of re-raising, and `ExceptionEvent` itself is
`@no_recursive_throw()`
([event_manager_base.py](https://github.com/hikari-py/hikari/blob/master/hikari/impl/event_manager_base.py)).

**aiogram** ships no observability: its extras are `fast`, `redis`, `mongo`, `proxy`, `i18n`, `cli`,
`signature` and `docs`
([pyproject.toml](https://github.com/aiogram/aiogram/blob/dev-3.x/pyproject.toml)), and the
organisation's only metrics repository instruments the Telegram Bot API server rather than the
framework. Its dispatch mechanism is the two-tier outer/inner middleware chain per
`TelegramEventObserver`; middleware must be `async def`, because `BaseMiddleware.__call__` is an
abstract coroutine
([base.py](https://github.com/aiogram/aiogram/blob/master/aiogram/dispatcher/middlewares/base.py)).
`ErrorsMiddleware`, registered as the first outer middleware on the root observer, converts an
exception into an `ErrorEvent`; if no error handler claims it, the exception re-raises out of
`feed_update`
([dispatcher.py](https://github.com/aiogram/aiogram/blob/master/aiogram/dispatcher/dispatcher.py)).

**Starlette and FastAPI** have no Prometheus support at all, and an `OpenTelemetryMiddleware` was
merged to Starlette's `main` on 2026-08-23 but is unreleased at tag 1.6.0, must be added explicitly
through `Middleware(OpenTelemetryMiddleware)`, and depends on `opentelemetry-api` only through the
`full` extra
([middleware](https://github.com/encode/starlette/tree/main/starlette/middleware)). The canonical
answers are third-party: `prometheus-fastapi-instrumentator` with `http_requests_total`,
`http_request_duration_seconds`, `http_request_size_bytes` and `http_response_size_bytes`
([repo](https://github.com/trallnag/prometheus-fastapi-instrumentator)), `starlette_exporter` with
`starlette_requests_total`, `starlette_request_duration_seconds` and
`starlette_requests_in_progress` ([repo](https://github.com/stephenhillier/starlette_exporter)), and
`opentelemetry-instrumentation-fastapi`, which rebuilds the middleware stack
([contrib](https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/instrumentation/opentelemetry-instrumentation-fastapi/src/opentelemetry/instrumentation/fastapi/__init__.py)).

**httpx and httpcore** depend on no OpenTelemetry package in core or in any extra
([httpx](https://github.com/encode/httpx/blob/master/pyproject.toml),
[httpcore](https://github.com/encode/httpcore/blob/master/pyproject.toml)). Their one built-in
observability surface is `event_hooks`, and its colour follows the face: `httpx.Client` hooks are
plain `def`, `httpx.AsyncClient` hooks must be `async def`
([event hooks](https://www.python-httpx.org/advanced/event-hooks/)). OpenTelemetry support for
httpx lives in the separate `opentelemetry-instrumentation-httpx`, built on those same hooks and on
transport wrapping.

### 3.6 The regularity

Not one of the eleven projects emits a metric or a span from its own core code with nothing
optional installed. Dramatiq's collector needs an extra and is no longer default; taskiq's classes
are in core but inert without an extra; Starlette's middleware is unreleased, opt-in and
extra-dependent; Celery, arq, discord.py, hikari and aiogram have no metric or span concept in core
at all. Every one of them keeps a *hook* in core — a signal, a middleware base, a callback slot —
that produces nothing until the application supplies a receiver or installs a package.

The one thing a framework does emit for free is a **log line**: arq writes an INFO record per job
through stdlib `logging` unconditionally, and every project in the survey logs an escaped handler
exception. That is the only observability an unconfigured install has, which is why the logging
convention carries more weight than the metrics one.

Two further regularities bear on a design. First, **no project introduces a dedicated observation
Protocol for dispatch**: those that instrument reuse the mechanism they already have for wrapping
work, and the two that do not instrument still point users at that same mechanism. Second, the
mechanism has to *wrap* the work rather than be told about it afterwards, because a span must be the
parent of whatever the handler itself records — which is why FastStream's OpenTelemetry integration
is a middleware and not a hook.

Failure isolation splits three ways and is worth tabulating on its own: Celery and Dramatiq catch
and log, discord.py and hikari catch and reroute, taskiq and aiogram let it propagate.

## 4 Shipping a Prometheus collector without owning global state

Every metric constructor in `prometheus_client` — `Counter`, `Gauge`, `Histogram`, `Summary`,
`Info`, `Enum` — accepts a `registry=` keyword that defaults to the module-global `REGISTRY`, so a
metric defined at module scope registers itself into process-global state at import time.
`CollectorRegistry.register` raises
`ValueError("Duplicated timeseries in CollectorRegistry: " + str(duplicates))` when a name is
already present
([registry.py](https://github.com/prometheus/client_python/blob/master/prometheus_client/registry.py)),
which is what a second composition in one process, or a module re-imported under pytest, produces.

The cross-language client specification requires the escape hatch and describes exactly the
ownership model a library should use: "There MUST be a default CollectorRegistry, the standard
metrics MUST by default implicitly register into it… There MUST be a way to have metrics not
register to the default CollectorRegistry, for use in batch jobs and unittests… CollectorRegistry
SHOULD offer register()/unregister() functions, and a Collector SHOULD be allowed to be registered
to multiple CollectorRegistrys"
([writing_clientlibs.md](https://github.com/prometheus/docs/blob/main/docs/instrumenting/writing_clientlibs.md)).

Practice divides on it. FastStream takes the registry as a mandatory constructor argument and never
touches the default (§3.1); Dramatiq constructs its own `CollectorRegistry` (§3.4); Litestar has no
registry parameter and writes to the default (§3.2). Note the tension with the Prometheus
instrumentation page's own advice that "Libraries should provide instrumentation with no additional
configuration required by users" (§1.5): that sentence is written for a library instrumenting
*itself*, and the three projects above are instrumentation, not instrumented libraries.

For gauges there is a second pattern that removes shared mutable state entirely: a custom collector
whose `collect()` is called at scrape time, and, on the OpenTelemetry side, an observable gauge with
a callback. Either reads a value when asked rather than tracking it on the hot path.

## 5 Cardinality in practice

What the surveyed projects actually put in a label is a short and consistent list: FastStream uses
`app_name`, `broker`, `handler`/`destination`, `status` and `exception_type`; Dramatiq uses
`queue_name` and `actor_name`; Litestar uses `method`, `path`, `status_code` and `app_name`, with
`group_path` offered against path explosion. Every one of these is drawn from a set the process
knows at start-up — a broker name, a handler name, an actor name, a status code, an exception class.

Not one of them labels by an end-user, account, message or entity identifier, which matches both the
Prometheus rule against "user IDs, email addresses, or other unbounded sets of values" and the
OpenTelemetry conventions' structural refusal to put `url.full` on a metric
([`docs/research/17`](17-http-client-observability.md) §6). Litestar's `path` is the one dimension
in the set that can grow without bound, and it is also the one the project added a flag to contain.

## 6 Comparison

| Project | Core, extra or absent | Mechanism | Colour | Hook raises | Registry / tracer owner | Names |
|---|---|---|---|---|---|---|
| FastStream | extra (`otel` pins the SDK, `prometheus`) | middleware over the existing chain | `async` | — | caller-supplied `CollectorRegistry`, mandatory | `received_*`, `published_*`; spans `{destination} process` |
| Litestar | extra (`opentelemetry`, `prometheus`, both in `full`) | ASGI middleware + a config object | `async` | — | global default `REGISTRY`, no parameter | `{prefix}_requests_total`, `{prefix}_request_duration_seconds` |
| Celery | absent (docs point at Flower) | `task_*` signals | sync only | caught, logged, isolated per receiver | n/a | none |
| taskiq | classes in core, dependencies in extras | `TaskiqMiddleware` hooks | either, via `maybe_awaitable` | propagates, except `post_save` | n/a | **[unverified]** |
| arq | absent | plain callback slots | `async` | **[unverified]** | n/a | none; one INFO log line per job |
| Dramatiq | extra, and not default since 2.0 | `Middleware` class hooks | sync only | caught, `critical`, swallowed | its own `CollectorRegistry` | `dramatiq_*`, labelled `queue_name`, `actor_name` |
| discord.py | absent | `dispatch` → `_run_event` → `on_error` | `async` | caught, logged, swallowed | n/a | none |
| hikari | absent (acknowledged gap) | `EventManagerBase.dispatch` | `async` | caught, logged, rerouted as `ExceptionEvent` | n/a | none |
| aiogram | absent | outer/inner middleware chain | `async` only | routed to `ErrorEvent`, else re-raised | n/a | none |
| Starlette / FastAPI | absent; OTel middleware merged, unreleased, opt-in | ASGI middleware | `async` | 500 built, then re-raised | third-party | third-party names |
| httpx / httpcore | absent | `event_hooks`, transport wrapping | sync on `Client`, `async` on `AsyncClient` | aborts the request | n/a | none |

## 7 Recommendation

**On the mechanism.** Reusing the existing middleware chain is the ecosystem's unanimous answer and
the only one that can parent a span, so a dedicated dispatch-observation Protocol would be both an
outlier and functionally weaker. The alternative worth stating is a push-record Protocol, which buys
a narrower contract for a consumer that only wants counters and pays for it by making tracing
impossible through that seam and by adding a substitution point no peer has. A third option —
signals, as Celery uses — fits a framework whose lifecycle notifications are already signals, but a
signal fires *at* a moment and cannot measure a duration without pairing two of them.

**On the dependency.** Every project surveyed keeps `prometheus-client` and the OpenTelemetry
packages out of its core dependencies, and OpenTelemetry itself advises shipping instrumentation as
a separate package (§1.4). Depending on `opentelemetry-api` in the core is cheap in packaging terms
— one transitive dependency, no-op without an SDK, a three-year compatibility promise — and would
make the framework the only one in the set to do it. The trade-off is that a first-party observer or
middleware behind an extra needs the application to add one line, while an API dependency in the
core needs nothing; the price of the second is the framework's names, in every install, for every
user who runs neither backend.

**On the names.** Where a convention is Stable, following it is free and diverging is the outlier
choice; the HTTP client set is Stable. Where it is in Development, as messaging is, following it
buys recognisable dashboards and inherits an unstable vocabulary that a library's own compatibility
promise cannot cover — so the honest options are to follow it and say so, or to take a namespaced
name under the library's own promise and accept that no ecosystem dashboard applies. Whichever is
chosen, the destination of a chat consumer is the stream and not the channel (§2.2), because the
alternative reading is what puts an unbounded identifier into a span name.

**On process-global state.** A caller-supplied registry is the pattern the Prometheus client
specification requires to be *possible* and the one that survives two compositions in a process and
a re-import under a test runner; writing to the default registry is the friendlier one-liner and is
what breaks in both cases. For gauges, a collector read at scrape time avoids the question entirely.

**On cardinality.** No mechanical rule exists to comply with (§1.6), so a framework that wants one
is writing policy. The materials for a checkable version are all present in a design where the
router is frozen and the event vocabulary registered before the first event: an allow-list of label
keys, each drawn from a set enumerable at start-up, is testable, and the product of those set sizes
is computable at start-up and can therefore be compared against a ceiling instead of discovered on a
monitoring invoice. Stating that this is the framework's policy rather than the specification's is
part of getting it right.

## Sources

Standards and specifications:
- https://peps.python.org/pep-0282/ · https://peps.python.org/pep-0391/ · https://peps.python.org/pep-0567/
- https://peps.python.org/pep-0831/ · https://peps.python.org/pep-0752/ · https://peps.python.org/pep-0799/
- https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
- https://docs.python.org/3/library/logging.html · https://docs.python.org/3/library/logging.html#logrecord-attributes
- https://docs.python.org/3/library/contextvars.html
- https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread
- https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor
- https://www.w3.org/TR/trace-context/

OpenTelemetry:
- https://opentelemetry.io/docs/concepts/instrumentation/libraries/
- https://opentelemetry.io/docs/specs/otel/versioning-and-stability/
- https://opentelemetry.io/docs/specs/semconv/messaging/ · https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/
- https://opentelemetry.io/docs/specs/semconv/registry/attributes/messaging/
- https://github.com/open-telemetry/semantic-conventions/releases · https://github.com/open-telemetry/semantic-conventions/blob/main/CHANGELOG.md
- https://github.com/open-telemetry/semantic-conventions/issues/3330 · https://github.com/open-telemetry/oteps/pull/192
- https://pypi.org/pypi/opentelemetry-api/json · https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-api/pyproject.toml
- https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation/opentelemetry-instrumentation-celery
- https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/instrumentation/opentelemetry-instrumentation-fastapi/src/opentelemetry/instrumentation/fastapi/__init__.py

Prometheus and OpenMetrics:
- https://prometheus.io/docs/practices/naming/ · https://prometheus.io/docs/practices/instrumentation/
- https://github.com/prometheus/client_python/blob/master/prometheus_client/registry.py
- https://github.com/prometheus/docs/blob/main/docs/instrumenting/writing_clientlibs.md
- https://github.com/prometheus/OpenMetrics/blob/main/specification/OpenMetrics.md

Peer frameworks:
- https://github.com/airtai/faststream/blob/main/pyproject.toml · https://github.com/airtai/faststream/blob/main/faststream/prometheus/middleware.py · https://github.com/airtai/faststream/blob/main/faststream/prometheus/container.py · https://github.com/airtai/faststream/blob/main/faststream/opentelemetry/middleware.py · https://github.com/airtai/faststream/blob/main/faststream/opentelemetry/consts.py
- https://github.com/litestar-org/litestar/blob/main/pyproject.toml · https://github.com/litestar-org/litestar/blob/main/litestar/plugins/prometheus/config.py · https://github.com/litestar-org/litestar/blob/main/litestar/plugins/prometheus/middleware.py · https://docs.litestar.dev/latest/reference/plugins/prometheus.html
- https://github.com/celery/celery/blob/main/celery/signals.py · https://github.com/celery/celery/blob/main/celery/utils/dispatch/signal.py · https://github.com/celery/celery/blob/main/celery/app/trace.py · https://github.com/celery/celery/blob/main/docs/userguide/monitoring.rst
- https://github.com/taskiq-python/taskiq/blob/master/taskiq/abc/middleware.py · https://github.com/taskiq-python/taskiq/blob/master/taskiq/middlewares/prometheus_middleware.py · https://github.com/taskiq-python/taskiq/blob/master/taskiq/receiver/receiver.py · https://github.com/taskiq-python/taskiq/blob/master/pyproject.toml
- https://github.com/python-arq/arq/blob/main/arq/worker.py · https://github.com/python-arq/arq/blob/main/pyproject.toml
- https://github.com/Bogdanp/dramatiq/blob/main/dramatiq/middleware/middleware.py · https://github.com/Bogdanp/dramatiq/blob/main/dramatiq/middleware/prometheus.py · https://github.com/Bogdanp/dramatiq/blob/main/dramatiq/middleware/__init__.py · https://github.com/Bogdanp/dramatiq/blob/main/dramatiq/broker.py · https://github.com/Bogdanp/dramatiq/blob/main/setup.py · https://dramatiq.io/changelog.html
- https://github.com/Rapptz/discord.py/blob/master/discord/client.py
- https://github.com/hikari-py/hikari/blob/master/hikari/impl/event_manager_base.py · https://github.com/hikari-py/hikari/issues/2783
- https://github.com/aiogram/aiogram/blob/dev-3.x/pyproject.toml · https://github.com/aiogram/aiogram/blob/master/aiogram/dispatcher/dispatcher.py · https://github.com/aiogram/aiogram/blob/master/aiogram/dispatcher/middlewares/base.py
- https://github.com/encode/starlette/tree/main/starlette/middleware · https://github.com/trallnag/prometheus-fastapi-instrumentator · https://github.com/stephenhillier/starlette_exporter
- https://github.com/encode/httpx/blob/master/pyproject.toml · https://github.com/encode/httpcore/blob/master/pyproject.toml · https://www.python-httpx.org/advanced/event-hooks/
