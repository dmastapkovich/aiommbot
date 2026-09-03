# Unhandled-exception boundaries in event and web frameworks: who owns the decision, and what the default does

Research date: 2026-09-03. Input to the Core error-boundary question (ADR-0006 tenet 6, ADR-0013,
ADR-0014): when a user handler raises an *unexpected* exception, what does each framework do by
default, where does that decision live, and should the aiommbot Core own an outermost boundary at
all. Sources are primary (framework source on GitHub, official docs, language references). Claims I
could not confirm from a primary source are marked **[unverified]**.

## 0. The question and the constraint set by ADR-0006/0013/0014

ADR-0006 tenet 6 says handlers are thin and "unexpected exceptions propagate to middleware and
observability"; ADR-0014 says "expected outcomes are values, never exceptions"; ADR-0013 makes
dispatch return a typed `Handled | Unhandled` outcome and routes the `Unhandled` case through an
observability hook "carrying the event name and never its content". None of the three says what
happens *above* the middleware chain: is there a Core-owned outermost boundary that turns an
escaped exception into a third outcome, or does the exception keep going into the transport
loop and, eventually, the process? The maintainer's counter-question — "what if the process is
meant to fail?" — is legitimate, so the survey asks every framework three things: **is there a
boundary and where**, **what does its default do** (log / respond / re-raise / crash), and **who
may override it**.

The historical baseline matters too. In aiommbot ≤0.4.5 the built-in
`SafeErrorNotificationMiddleware.dispatch` logged `logger.exception(...)` with
`"event_details": request.event.model_dump(mode="json")` and returned on the error path (no
re-raise) — full payload in the log, exception swallowed before Sentry/metrics. Commit `2d61ff3`
(2026-06-30, shipped in 0.4.6–0.4.8) rewrote it to log only the exception class plus an
allow-listed identifier context and to `raise` unconditionally
(`aiommbot/middlewares/safe_error_notification.py` in the 0.4.x repository). The usage-mining note
(`09-usage-mining-0.4.x-bots.md` §9) found 8/11 bots register the default unmodified, so whichever
version they pin decides whether their logs contain message text. That is the design smell this
document evaluates against the field.

## 1. aiogram 3: error observer, then a swallowing dispatcher loop

aiogram has two layers. `ErrorsMiddleware` is installed as an outer middleware on the `update`
observer in `Dispatcher.__init__` and, on `Exception`, wraps it in `ErrorEvent(update, exception)`
and offers it to the `error` observer (`@dp.error()` / `@router.errors()`); if no error handler
matches (`response is UNHANDLED`) it **re-raises** (`aiogram/dispatcher/middlewares/error.py`
L16–38; `SkipHandler`/`CancelHandler` pass straight through). `feed_update` has only a `finally`
that logs `"Update id=%s is %s. Duration %d ms by bot id=%d"` at INFO, so the exception escapes
`feed_update`. The second layer is `_process_update` (`dispatcher.py` L304–336): it catches
`Exception` with an explicit `# noqa: BLE001`, logs
`loggers.event.exception("Cause exception while process update id=%d by bot id=%d\n%s: %s", update_id, bot.id, cls, e)`
— stdlib `logging`, logger `aiogram.event`, ERROR with traceback, **ids only, no payload** — and
returns `True` ("processed but unsuccessful"). The `_polling` loop (L395–412) never sees the
exception; polling continues. With `handle_as_tasks=True` (default) each update runs in
`asyncio.create_task(self._process_update(...))` whose only done-callback is `set.discard`; that is
safe only because `_process_update` swallows everything.

The webhook path is the inconsistent one. `_feed_webhook_update` (L421–435) logs the same
message and **re-raises**; `feed_webhook_update` calls `process_updates.result()` next to a
literal `# TODO: handle exceptions` (L484–486), so with `handle_in_background=False` aiohttp's
`RequestHandler` answers **HTTP 500** and logs `"Error handling request from %s"`
(`aiohttp/web_protocol.py` L722–724); Telegram will redeliver the update. With
`handle_in_background=True` (the default for `SimpleRequestHandler`) HTTP 200 `{}` is returned
first and `_background_feed_update` runs in a task with only a `discard` callback, so the re-raised
exception dies inside the task — logged once by aiogram, then asyncio's "Task exception was never
retrieved" at GC **[unverified by running; inferred from the code]**.

Stated rationale (`docs/dispatcher/errors.rst`): "Is recommended way that you should use errors
inside handlers using try-except block, but in common cases you can use global errors handler at
router or dispatcher level." Nothing in the docs justifies the swallow-and-continue default; it is
simply what `_process_update` does. Override points: `@router.error(ExceptionTypeFilter(...))`,
a custom outer middleware on `dp.update`, subclassing `BaseRequestHandler`. Owner: `Dispatcher`
(polling) and aiohttp (webhook).

## 2. FastStream 0.6: ack-policy middleware decides the broker action, `consume()` swallows the rest

Source: `ag2ai/faststream` `main` (0.6 line).

**Boundary.** There is no single boundary; three middlewares and the subscriber loop share it.
`SubscriberUsecase.process_message`
(https://github.com/ag2ai/faststream/blob/main/faststream/_internal/endpoint/subscriber/usecase.py)
has **no try/except around `h.call(...)`**; the exception unwinds through an `AsyncExitStack` of
middleware `__aexit__`s. `AcknowledgementMiddleware.__aexit__`
(https://github.com/ag2ai/faststream/blob/main/faststream/middlewares/acknowledgement/middleware.py)
treats `AckMessage` / `NackMessage` / `RejectMessage` as control flow (`await self.__ack(...)` etc.
and **return `True`**, suppressing them); for any other exception it acts per `AckPolicy` and
returns `False` — `ACK` → ack anyway, `REJECT_ON_ERROR` → reject, `NACK_ON_ERROR` → nack,
`ACK_FIRST` → already acked on consume, `MANUAL` → nothing
(https://github.com/ag2ai/faststream/blob/main/faststream/middlewares/acknowledgement/config.py:
`"Disable default FastStream Acknowledgement logic. User should confirm all actions manually."`).
`asyncio.CancelledError` passes through without ack. Ack/nack failures themselves are logged at
CRITICAL and not raised. `CriticalLogMiddleware.__aexit__`
(https://github.com/ag2ai/faststream/blob/main/faststream/middlewares/logging.py) logs
`f"{exc_type.__name__}: {exc_val}"` at ERROR with `exc_info` (only `str(exc)` for
`IgnoredException`), **no message body**, and returns `False`. The user-facing
`ExceptionMiddleware` (https://github.com/ag2ai/faststream/blob/main/faststream/middlewares/exception.py)
walks `type(exc).__mro__` against `add_handler(...)` (consume-scope, `after_processed` returns
`True` when handled) and `add_handler(..., publish=True)` (`consume_scope`, the handler's return
value is published as the response); with no match it returns `False`/lets the exception
propagate. `IgnoredException` is pre-registered with `ignore_handler`, which re-raises.

**Default when nothing handles.** `consume()` (same `usecase.py`) is
`except StopConsume: await self.stop()` / `except SystemExit: await self.stop(); app.exit()` /
`except Exception: pass` with the comment "All other exceptions were logged by
CriticalLogMiddleware". So: logged once without payload, message rejected (RabbitMQ default
`REJECT_ON_ERROR`; docs: "a message will be acknowledged (and rejected in case of an exception)",
https://faststream.ag2.ai/latest/rabbit/ack/), consumption continues; only `SystemExit` stops the
app. **Retry was deliberately removed.** The 0.6.0 release notes
(https://faststream.ag2.ai/latest/release/) call `retry=True` "a design mistake" that was "a
shortcut to `message.nack()` on error" and say "manual acknowledgement control would be more
idiomatic". Discussion #1161 (https://github.com/ag2ai/faststream/discussions/1161) is the
dead-letter thread where the maintainer explains why: "retry counter exists only in memory … can't
be scaled by processes. Each instance has its own counter" — retry belongs to the broker (DLX,
`x-dead-letter-exchange`), not the framework. Owner: policy on the subscriber (`ack_policy`), user
handlers via `ExceptionMiddleware`; the framework never decides retries and never dies.

## 3. Starlette / FastAPI: respond 500, then always re-raise

Sources: starlette 1.6.0 / fastapi 0.141.1 / uvicorn 0.52.4 (identical to GitHub `master`).

**Boundary.** `ServerErrorMiddleware.__call__`
(https://github.com/encode/starlette/blob/master/starlette/middleware/errors.py) is always the
**outermost** layer: `Starlette.build_middleware_stack`
(https://github.com/encode/starlette/blob/master/starlette/applications.py) pulls the `500` /
`Exception` handlers out of `exception_handlers` into it, and puts every other handler into
`ExceptionMiddleware` just before the router. On `Exception` it sends `PlainTextResponse("Internal
Server Error", 500)` (or the user's 500 handler, or an HTML traceback when `debug=True`) only `if
not response_started`, and then **always `raise exc`**. The in-code comment: "We always continue
to raise the exception. This allows servers to log the error, or allows test clients to optionally
raise the error within the test case." `wrap_app_handling_exceptions`
(https://github.com/encode/starlette/blob/master/starlette/_exception_handler.py) re-raises
anything without a registered handler, so unexpected errors reach `ServerErrorMiddleware`.

**Default log content.** Starlette logs nothing itself. uvicorn's `RequestResponseCycle.run_asgi`
(https://github.com/encode/uvicorn/blob/master/uvicorn/protocols/http/h11_impl.py) does
`self.logger.error("Exception in ASGI application\n", exc_info=exc)` and, if no response started,
`send_500_response()`; the log carries the traceback and **no request body, URL or headers**. The
process keeps serving. `TestClient(raise_server_exceptions=True)` is the default, so tests see the
exception, not a 500.

**Stated rationale** (https://www.starlette.io/exceptions/): "Handled exceptions do not represent
error cases. They are coerced into appropriate HTTP responses … Errors are any other exception that
occurs within the application. These cases should bubble through the entire middleware stack as
exceptions. Any error logging middleware should ensure that it re-raises the exception all the way
up to the server."

**FastAPI** duplicates the stack construction (`FastAPI.build_middleware_stack`, adds
`AsyncExitStackMiddleware` innermost) and registers default handlers only for `HTTPException` and
`RequestValidationError` (`fastapi/exception_handlers.py`); an unexpected exception follows the
Starlette path: 500, then re-raise. Owner of the decision: the framework fixes "respond, then
re-raise"; the server owns logging; the application owns the 500 body and `debug`.

## 4. Litestar: convert to a response and swallow; logging is opt-in

Source: litestar 2.14.0 (identical to `main`).

**Boundary.** `ExceptionHandlerMiddleware.__call__`
(https://github.com/litestar-org/litestar/blob/main/litestar/middleware/_internal/exceptions/middleware.py):
on `Exception`, if the response already started it raises `LitestarException("Exception caught
after response started")`; otherwise it (1) runs `handle_exception_logging` when a
`logging_config` exists, (2) awaits every `app.after_exception` hook, (3) drops into
`pdb.post_mortem()` when `LITESTAR_PDB=1`, (4) builds the response. It **does not re-raise**: the
ASGI server sees an ordinary 500.

**Default response.** `default_http_exception_handler`: `exc.status_code` for `HTTPException`,
else 500; JSON `{"status_code": 500, "detail": "Internal Server Error", "extra": {}}`, or an
HTML/plain traceback when `app.debug`. Handlers resolve per layer (app → router → controller →
route handler, later layer wins), status code before MRO, `500` as the catch-all
(`litestar/handlers/base.py`).

**Default log content.** `LoggingConfig.log_exceptions: Literal["always", "debug", "never"] =
"debug"` (https://github.com/litestar-org/litestar/blob/main/litestar/logging/config.py) — in
production (`debug=False`) uncaught exceptions are **not logged by default**. When logged:
`logger.exception("Uncaught exception (connection_type=%s, path=%s):", …)` — path only, no query
string, headers or body. `after_exception` hooks are "not meant to return a response — only to
process the exception (e.g. log it, send it to Sentry etc.)" (`config/app.py`).

**Docs** (https://docs.litestar.dev/latest/usage/exceptions.html): "Litestar handles all errors by
default by transforming them into JSON responses … Otherwise, the responses will default to
`500 - "Internal Server Error"`." Owner: the framework owns "convert, never propagate"; the
application owns logging policy, hooks and layered handlers. Process continues.

## 5. discord.py: one task per event, `on_error` logs and ignores

`Client.dispatch` (`discord/client.py` L528–566) schedules every event through `_schedule_event`
→ `loop.create_task(wrapped, name=f"discord.py: {event_name}")`; `_run_event` (L500–515) does
`except asyncio.CancelledError: pass` / `except Exception: await self.on_error(event_name, *args, **kwargs)`.
Because each event is its own task and `_run_event` never propagates, one failing event cannot
take the gateway loop down. The default `Client.on_error` (L568–582) is
`_log.exception("Ignoring exception in %s", event_method)` — ERROR with traceback, event name
only; the event args are passed to the hook but **not logged** (the 2.0 changelog note in the
docstring: "instead of writing to sys.stderr it logs instead"). `docs/api.rst` L423–445 states the
contract: "Usually when an event raises an uncaught exception, a traceback is logged to stderr and
the exception is ignored. If you want to change this behaviour and handle the exception for
whatever reason yourself, this event can be overridden. Which, when done, will suppress the
default action of printing the traceback."

`ext.commands` adds a wrapping layer: `hooked_wrapped_callback` (`core.py` L258–280) turns any
non-`CommandError` into `CommandInvokeError(exc) from exc`; `Bot.invoke` catches `CommandError`
and calls `dispatch_error` (L664–683), which tries the local `@command.error` handler, then
`cog_command_error`, and in a `finally` always dispatches the `command_error` event. The default
`Bot.on_command_error` (`bot.py` L339–365) steps aside if a `command_error` listener, a local
handler or a cog handler exists; otherwise
`_log.error("Ignoring exception in command %s", command, exc_info=exception)` — command name, no
message content. Owner: the `Client`/`Bot` object via overridable methods; default = log and
continue.

## 6. Slack Bolt (Python): listener runner catches, logs, never re-raises; the HTTP status depends on timing

**Boundary.** `ThreadListenerRunner.run`
(https://github.com/slackapi/bolt-python/blob/main/slack_bolt/listener/thread_runner.py) and
`AsyncioListenerRunner.run` (`asyncio_runner.py`) wrap `listener.run_ack_function` in
`try/except Exception` → `listener_error_handler.handle(error, request, response)`; the exception
is never re-raised. Comment in source: "The default response status code is 500 in this case. You
can customize this by passing your own error handler."

**What Slack receives.** With `process_before_response=True` (FaaS mode) the listener runs inside
the request cycle and the failure becomes **HTTP 500**. With the default
`process_before_response=False`, auto-acknowledged events are `ack()`ed first and the listener
runs in a thread pool (`max_workers=5`) or as a task, so Slack already holds a **200** when the
listener fails; a non-auto-ack listener that fails before calling `ack()` gets a 500. Middleware
or dispatch-level exceptions become `BoltResponse(status=500, body="")` plus the middleware error
handler (`app.py`).

**Default log content.** `DefaultListenerErrorHandler.handle`
(https://github.com/slackapi/bolt-python/blob/main/slack_bolt/listener/listener_error_handler.py):
`logger.exception(f"Failed to run listener function (error: {error})")` — traceback and
`str(error)`, **no request body** (the request is passed to the handler but not logged). Process
continues.

**Override.** `@app.error` registers a custom handler receiving `error`, `body`, `logger`,
`request`, `response` by name; returning a `BoltResponse` overwrites status and body. Docs
(https://docs.slack.dev/tools/bolt-python/concepts/errors): "By default, the global error handler
will log all non-handled exceptions to the console." — the docs' own example logs the request
body, which is the framework inviting PII into logs. Owner: the listener runner; default = log and
continue.

## 7. python-telegram-bot v20+: `process_error`, retrieved task exceptions

`Application.process_update` (`src/telegram/ext/_application.py` L1248–1335) runs handler groups
inside `except ApplicationHandlerStop: break` / `except Exception as exc: if await self.process_error(update, exc): break`.
`process_error` (L1854–1940) walks the registered error handlers; with none registered it logs
`_LOGGER.exception("No error handlers are registered, logging exception.", exc_info=error)` — ERROR
with traceback and **no update payload** (the update is logged only at DEBUG by `__update_fetcher`,
L1240). If an error handler itself raises: "An error was raised and an uncaught error was raised
while handling the error with an error_handler." (L1931–1936). `__update_fetcher` therefore loops
on; the process never dies from a handler exception.

Two details are instructive. First, `block=False` handlers run through `__create_task`, whose
callback calls `process_error` **and then re-raises** so the exception is still set on the task,
while `__create_task_done_callback` (L1156–1161) calls `task.exception()` specifically to silence
asyncio's "Task exception was never retrieved" — the framework retrieves the exception on purpose
rather than letting the loop's default handler print it. Second, `add_error_handler(callback,
block=True)` documents `block` as "whether the return value of the callback should be awaited
before processing the next error handler", and a blocking error handler can raise
`ApplicationHandlerStop` to stop further handler groups. Network errors during polling have their
own path: `run_polling` installs `error_callback → process_error(update=None)`, while
`Updater.start_polling`'s default is `_LOGGER.exception("Exception happened while polling for updates.")`
(`_updater.py` L370–371).

Stated rationale (wiki "Exceptions, Warnings and Logging"): "In case you don't have an error
handler registered, PTB will log any unhandled exception" and "exceptions that are handled by the
error handlers don't stop your python process - your bot will just keep running!" Owner:
`Application`; hooks: `add_error_handler` (ordered, `block`), `context.error`,
`ApplicationHandlerStop`.

## 8. Sanic: a replaceable `ErrorHandler` that logs the full URL

**Boundary.** `Sanic.handle_request` catches `Exception` (re-raising `CancelledError`) and calls
`handle_exception` (https://github.com/sanic-org/sanic/blob/main/sanic/app.py), which dispatches
the `server.exception.report` and `http.lifecycle.exception` signals, then
`self.error_handler.response(request, exception)`. If the response was already partially sent it
only logs; if the error handler itself raises, the fallback is `"An error occurred while handling
an error"` (500). No re-raise; the worker keeps serving.

**Default action.** `ErrorHandler.default()`
(https://github.com/sanic-org/sanic/blob/main/sanic/handlers/error.py) = `log()` +
`exception_response(...)`. `log()`: unless the exception is `quiet` and `NOISY_EXCEPTIONS` is
off, `error_logger.exception("Exception occurred while handling uri: %s", repr(request.url))` —
**the full URL including the query string** plus traceback; no headers or body. The response body
comes from `errorpages.py`: `"The application encountered an unexpected error and could not
continue."` in the negotiated format; the traceback is rendered only in `debug` ("meant to not show
any sensitive data … the default fallback for production").

**Override.** `@app.exception(...)`, `app.error_handler.add(...)`, a subclassed `ErrorHandler`
assigned to `app.error_handler`, `config.NOISY_EXCEPTIONS`, the `http.lifecycle.exception`
signal (https://sanic.dev/en/guide/best-practices/exceptions.html). Owner: the framework's
`ErrorHandler` owns log + respond; the application replaces it wholesale.

## 9. Task systems: Celery, taskiq, arq, Dramatiq — the failure is a recorded result, never a dead worker

None of the four lets a task exception reach the worker process; all four turn it into a stored
result plus a hook. They differ in what the default log line contains.

**Celery.** `celery/app/trace.py` (https://github.com/celery/celery/blob/main/celery/app/trace.py)
classifies the exception: `Reject` → WARNING `LOG_REJECTED`, `Ignore` → INFO `LOG_IGNORED`,
`Retry` → RETRY state, `isinstance(exc, task.throws)` → "raised expected" at INFO, everything else
→ "raised unexpected" at ERROR. `handle_failure` marks the backend FAILURE, calls
`task.on_failure`, sends `signals.task_failure(task_id, exception, args, kwargs, traceback,
einfo)`, then logs `LOG_FAILURE = "Task %(name)s[%(id)s] %(description)s: %(exc)s"`. The format
string **does not include `%(args)r`**; `args`/`kwargs` (`argsrepr` or `safe_repr(req.args)`) are
placed in the record's `extra` data dict, so a formatter or log shipper that dumps `extra` will
emit them **[structure of the extra dict inferred from the fetched source summary, not quoted]**.
An exception raised inside the tracer itself is `LOG_INTERNAL_ERROR` at CRITICAL plus a
`task_internal_error` signal; the worker keeps consuming.

**taskiq.** `Receiver.run_task` (https://github.com/taskiq-python/taskiq/blob/master/taskiq/receiver/receiver.py)
wraps the call in `except BaseException as exc: found_exception = exc;
logger.exception("Exception found while executing function.")` — traceback, no task name in the
message and **no arguments** — builds `TaskiqResult(is_err=True, error=found_exception, ...)`,
then calls `middleware.on_error(message, result, found_exception)` for every middleware that
overrides `TaskiqMiddleware.on_error`, and the `runner()` loop continues; ack timing is decided
by `ack_type` in `callback()`, not by the exception.

**arq.** `Worker.run_job` (https://github.com/python-arq/arq/blob/main/arq/worker.py): `Retry`
(a `RuntimeError` carrying `defer`) re-queues when `retry_jobs` is on; `CancelledError` for an
aborting job is abort; anything else is `logger.exception('%6.2fs ! %s failed, %s: %s', t, ref,
e.__class__.__name__, e)` — time, job ref, class, `str(e)`, **no args** — and the job is
finished with `serialize_result(..., success=False, result=exc)`. `max_tries` defaults to 5 and
is checked *before* execution (`job_try > max_tries` → failed result without running).
`on_job_end`/`after_job_end` hooks fire regardless of outcome.

**Dramatiq.** `_WorkerThread.process_message`
(https://github.com/Bogdanp/dramatiq/blob/master/dramatiq/worker.py) catches `BaseException`,
logs `"Failed to process message %s with unhandled exception."` with `exc_info=True`, emits
`after_process_message(message, exception=e)` and continues. The `Retries` middleware
(https://github.com/Bogdanp/dramatiq/blob/master/dramatiq/middleware/retries.py; `max_retries=20`,
backoff 15 s → 7 d) retries unless the exception matches the actor's `throws`, `retry_when`
returns False, or retries are exhausted, then `message.fail()`; its own log lines carry only the
`message_id`. But the worker's `%s` is `MessageProxy.__str__` → `str(self._message)`
(https://github.com/Bogdanp/dramatiq/blob/master/dramatiq/broker.py), and `Message.__str__`
(https://github.com/Bogdanp/dramatiq/blob/master/dramatiq/message.py) renders
`actor_name(arg1, arg2, kw=value)` — so **Dramatiq's default failure log contains the full task
arguments**. Of the four, it is the only one that does.

## 10. "Let it crash" versus in-process boundaries: Erlang/OTP, Go, Python asyncio

**Erlang/OTP** is the reference for "let it crash", and the point usually lost is that the crash
is *supervised*. The design principles (https://www.erlang.org/doc/system/design_principles.html)
define workers and supervisors: "Supervisors are processes that monitor workers. A supervisor can
restart a worker if something goes wrong … which makes it possible to design and program
fault-tolerant software." The supervisor behaviour (https://www.erlang.org/doc/system/sup_princ.html)
makes the policy explicit and bounded: restart strategies `one_for_one` / `one_for_all` /
`rest_for_one`, restart types `permanent` / `transient` / `temporary`, and a restart intensity —
"If more than MaxR number of restarts occur in the last MaxT seconds, the supervisor terminates all
the child processes and then itself." The worker does not catch; the supervisor decides, and the
decision escalates upward when a restart budget is exhausted. A Python bot has no equivalent
in-process supervisor; the nearest thing is the container orchestrator restarting the pod, which
is coarse (one message kills every in-flight message on the replica) and slow.

**Go `net/http`** draws the line per request. `conn.serve`
(https://github.com/golang/go/blob/master/src/net/http/server.go) has
`defer func() { if err := recover(); err != nil && err != ErrAbortHandler { … runtime.Stack …
c.server.logf("http: panic serving %v: %v\n%s", c.remoteAddr, err, buf) } }()`. The `Handler`
doc states the contract: "If ServeHTTP panics, the server (the caller of ServeHTTP) assumes that
the effect of the panic was isolated to the active request. It recovers the panic, logs a stack
trace to the server error log, and either closes the network connection or sends an HTTP/2
RST_STREAM." The log has the remote address and stack, no body. `ErrAbortHandler` is an explicit
opt-out from logging. Panics in goroutines the handler spawns are *not* recovered and do kill the
process — Go's answer to "what if the process should fail" is: it does, whenever you leave the
per-request scope.

**Python asyncio** has no supervisor and a weak default. `loop.set_exception_handler`
(https://docs.python.org/3/library/asyncio-eventloop.html#error-handling-api) receives a
`context` dict (`message`, `exception`, `task`, …) and the `default_exception_handler` only logs.
A task created with `create_task` and never awaited surfaces its exception solely as "Task
exception was never retrieved", logged **when the task object is garbage collected**
(https://docs.python.org/3/library/asyncio-task.html#creating-tasks) — which is why aiogram's and
discord.py's per-event tasks *must* swallow inside the task (§1, §5) and PTB retrieves
`task.exception()` on purpose (§7). `asyncio.TaskGroup` is the structured alternative: "The first
time any of the tasks belonging to the group fails with an exception other than
`asyncio.CancelledError`, the remaining tasks in the group are cancelled … exceptions are combined
in an `ExceptionGroup` … which is then raised"; `KeyboardInterrupt`/`SystemExit` are re-raised
as themselves (https://docs.python.org/3/library/asyncio-task.html#task-groups). `asyncio.run`
"returns the awaitable's result or raises an exception"
(https://docs.python.org/3/library/asyncio-runner.html) — a main task that lets an exception
escape ends the program, which is the Python "let it crash". The line, then: **the unit that may
crash must be the unit something restarts.** OTP restarts a process; Go restarts nothing but
scopes the recover to a request; asyncio gives you a TaskGroup that converts one failure into
cancellation of its siblings and an exception in the parent. A message-processing runtime that
"lets it crash" without a supervisor above it is not fault-tolerant, it is just fragile.

## 11. Observability at the boundary: Sentry and OpenTelemetry

Both instrument the *same* place every framework above already has, and both preserve the
framework's behaviour by re-raising.

**Sentry.** `SentryAsgiMiddleware._run_app`
(https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/asgi.py) wraps
`await self.app(scope, receive, send)` in `except Exception as exc: self._capture_request_exception(exc); raise exc from None`
with `mechanism={"type": ..., "handled": False}`; the Starlette integration
(https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/starlette.py)
additionally patches `ExceptionMiddleware` so 5xx `HTTPException`s are captured as `handled=True`.
The Celery integration
(https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/celery/__init__.py)
wraps the tracer/task call: `except Exception: exc_info = sys.exc_info(); _capture_exception(task, exc_info); reraise(*exc_info)`,
skipping `Retry`/`Ignore`/`Reject` and anything in `task.throws`; arq
(https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/arq.py) does the
same around the job coroutine, marking `Retry`/`RetryJob`/`JobExecutionFailed` as aborted spans
instead of errors. In every case the framework's own boundary still runs afterwards. **What is
attached:** method, URL, query string and filtered headers always; cookies, client IP, request
body (bounded by `max_request_body_size`, default `"medium"`) and Celery/arq `args`/`kwargs` only
when `should_send_default_pii()` or the newer `data_collection` options allow it — otherwise the
job arguments are replaced by `SENSITIVE_DATA_SUBSTITUTE`. `send_default_pii` defaults to
`None`/off (https://docs.sentry.io/platforms/python/configuration/options/); note
`include_local_variables` defaults to `True`, so a handler's locals — which may hold the message —
travel with the stack trace unless disabled. The SDK thus models exactly the split the Core
needs: the exception with full context goes to the observability channel under an explicit PII
policy; the log line and the framework behaviour are untouched.

**OpenTelemetry.** The Trace API (https://opentelemetry.io/docs/specs/otel/trace/api/) says
languages "SHOULD provide a `RecordException` method" that records the exception as an `Event`
named `exception` with `exception.type`, `exception.message` ("may contain sensitive
information"), `exception.stacktrace` and `exception.escaped`
(https://opentelemetry.io/docs/specs/semconv/exceptions/exceptions-spans/ — the span-event form
is now marked deprecated in favour of log-based exception records, with an opt-in env var for
migration). `Status` is `Unset | Ok | Error`, "Description MUST only be used with the `Error`
`StatusCode`", and `Ok` overrides `Error`. The Python `start_as_current_span(...,
record_exception=True, set_status_on_exception=True)`
(https://opentelemetry-python.readthedocs.io/en/latest/api/trace.html) records the event, sets
`StatusCode.ERROR` and re-raises. Recording never alters control flow; it is a side channel.

## 12. Comparison table

| Framework | Boundary (where) | Default action | Default log has payload? | Process continues | Surfaced via | Override points |
|---|---|---|---|---|---|---|
| aiogram 3 (polling) | `ErrorsMiddleware` → `_process_update` | error observer, else log + **swallow** | No (ids only) | Yes | `@dp.error`, `ErrorEvent` | error handlers, outer middleware |
| aiogram 3 (webhook) | `_feed_webhook_update` → aiohttp | log + **re-raise** → HTTP 500 (or lost in bg task) | No | Yes | HTTP 500 / redelivery | `BaseRequestHandler` subclass |
| FastStream 0.6 | ack / log / exception middlewares → `consume()` | ack-policy action, log, **swallow** in `consume()` | No (class + str) | Yes (`SystemExit` stops) | ack/nack/reject, `ExceptionMiddleware` | `ack_policy`, `add_handler`, `AckMessage` & co. |
| Starlette / FastAPI | `ServerErrorMiddleware` (outermost) | respond 500 then **re-raise** | No (uvicorn: traceback only) | Yes | HTTP 500 + server log | 500 handler, `debug`, `ExceptionMiddleware` |
| Litestar | `ExceptionHandlerMiddleware` | convert to response, **swallow** | No; not logged at all in prod by default | Yes | HTTP 500, `after_exception` | layered handlers, `log_exceptions` |
| discord.py | `_run_event` per task → `on_error` | log + **ignore** | No (event name) | Yes | `on_error`, `on_command_error` | override methods, `@command.error` |
| Slack Bolt | listener runner → `listener_error_handler` | log + **swallow** (500 only if before ack) | No (`str(error)`) | Yes | HTTP 200/500, `@app.error` | `@app.error`, custom runner |
| python-telegram-bot | `process_update` → `process_error` | error handlers, else log + continue | No | Yes | `add_error_handler`, `context.error` | handlers, `block`, `ApplicationHandlerStop` |
| Sanic | `handle_request` → `ErrorHandler` | log + respond 500, **swallow** | **Yes** (full URL incl. query) | Yes | HTTP 500, signals | `@app.exception`, replace `ErrorHandler` |
| Celery | `trace_task` → `handle_failure` | FAILURE state + signal + log | No in message; args in `extra` | Yes | `task_failure`, backend state | `throws`, `on_failure`, `Retry`/`Reject`/`Ignore` |
| taskiq | `Receiver.run_task` | `TaskiqResult(is_err)` + log | No | Yes | `on_error` middleware, result | middlewares, `ack_type` |
| arq | `Worker.run_job` | failed `JobResult` + log | No | Yes | result, `on_job_end` | `Retry`, `max_tries`, hooks |
| Dramatiq | `process_message` → `Retries` | retry ≤20 then `fail()` + log | **Yes** (`actor(args, kw=…)`) | Yes | `after_process_message`, retries | `throws`, `retry_when`, middleware |
| Go `net/http` | `conn.serve` recover | log stack, drop connection | No (remote addr) | Yes (in-handler only) | server error log | `ErrAbortHandler` |
| Erlang/OTP | supervisor | restart child per strategy | n/a | Process dies, supervisor restarts | crash report | strategy, intensity, restart type |

## 13. Recommendation for aiommbot

**Yes, the Core should own an outermost boundary — but as an outcome, not as a policy.** Thirteen
of the fourteen runtimes surveyed have exactly one place where an escaped handler exception is
turned into something else, and in every event/task runtime that place is framework-owned and the
process continues. The only "re-raise" default, Starlette's, still responds first and re-raises
*only because* a server sits above it that is contractually obliged to log and keep serving
(§3). Nobody re-raises into nothing. The maintainer's "what if the process should fail?" is
answered by §10: a crash is only a valid strategy when a supervisor exists, and the supervisor
must have a restart budget; in a Kubernetes pod the budget is CrashLoopBackOff and the blast
radius is every in-flight event on the replica. That is a legitimate *choice* for a bot whose
state is corrupt, never a sane *default* for one handler's `KeyError`.

**What the default must do**, following the consensus rather than any single framework:

1. **Log without payload.** Every well-behaved boundary logs class, message and traceback with
   identifiers only (aiogram, discord.py, PTB, Bolt, FastStream, Celery, taskiq, arq, uvicorn).
   The two that leak — Sanic's full URL and Dramatiq's `actor(args…)` — are the anti-examples.
   The Core log line: exception class, event name, correlation/event id, handler name. Never
   `model_dump()`, never `str(exc)` of an exception that might wrap a payload (log `type(exc)` and
   let the observability hook carry the rest).
2. **Emit the full exception to an observability hook.** Sentry and OTel (§11) show the shape:
   the hook receives the exception object and a typed context and decides its own PII policy
   (`send_default_pii`, `include_local_variables`). That is where ADR-0013's
   `Unhandled`-observer belongs; the third outcome reuses it.
3. **Return a typed `Failed(exception, event_ref)` outcome to the transport.** This is the
   FastStream/taskiq/arq model: dispatch never decides ack/nack/reject or an HTTP status; the
   transport does, per its own `AckPolicy`-like setting. Webhook transports respond 500 (or 200 if
   already acked, Bolt-style); a polling/websocket transport continues; a queue transport
   nacks/rejects. The Core never decides user-facing text — Litestar's "Internal Server Error"
   body and Bolt's docs example that logs `body` are both the framework overreaching.
4. **Never swallow silently.** aiogram's `except Exception: # noqa: BLE001` and FastStream's
   `except Exception: pass` are tolerable only because a logging layer ran first. In aiommbot the
   `Failed` outcome *is* the record; a dispatch that returns `Failed` with no log and no hook call
   is a bug by construction.

**"Fail the process" is an explicit policy, expressed once.** Model it the way FastStream models
`SystemExit` and Go models leaving the request scope: the boundary re-raises `BaseException`
subclasses that are not `Exception` (`SystemExit`, `KeyboardInterrupt`, `CancelledError`) and
converts everything else — unless the application sets an explicit boundary policy
(`on_unhandled = "fail"` at bot construction, or a check-phase setting the composition root
validates) or a handler raises a Core-defined `FatalError` that the boundary is documented to
re-raise. Both are opt-in and both are visible in one place, which is what OTP's restart types
(`permanent`/`transient`/`temporary`) give the reader.

**What stays with plugins and applications:** user-facing error replies (a middleware or plugin
observing `Failed` and answering "something went wrong" with the correlation id), retries and
DLQ (FastStream's #1161 lesson: in-memory retry counters do not scale across replicas; retry is a
transport/broker concern or an explicit plugin, never a Core default), and error classification
(`throws`-style "expected" exceptions that should not page anyone).

**What 0.4.x got wrong against this evidence.** `SafeErrorNotificationMiddleware` ≤0.4.5 (§0)
(a) logged `event.model_dump()` — no surveyed framework does that by default, and the two that
log any payload are the ones flagged here as leaks; (b) swallowed the exception *inside* the
middleware chain, so Sentry/OTel-style hooks that sit above it never saw an unhandled error — the
opposite of the Starlette and Sentry contract "re-raise all the way up"; (c) made the middleware,
not the transport, decide the outcome, so a webhook still returned 200 and a queue would have
acked a failed message; (d) was opt-out by registration rather than a Core guarantee, so 8/11
bots' behaviour depended on which patch version they pinned. The 0.4.6 fix (log class + ids,
always re-raise) repaired (a) and (b) and moved the problem to (c): re-raising into a transport
loop with no defined consumer is the aiogram-webhook `# TODO: handle exceptions` situation. The
0.5.0 design closes it by making the boundary produce a value the transport must handle.

## Sources

- aiogram: https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/dispatcher/middlewares/error.py ·
  https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/dispatcher/dispatcher.py ·
  https://github.com/aiogram/aiogram/blob/dev-3.x/docs/dispatcher/errors.rst ·
  https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web_protocol.py
- FastStream: https://github.com/ag2ai/faststream/blob/main/faststream/_internal/endpoint/subscriber/usecase.py ·
  https://github.com/ag2ai/faststream/blob/main/faststream/middlewares/acknowledgement/middleware.py ·
  https://github.com/ag2ai/faststream/blob/main/faststream/middlewares/acknowledgement/config.py ·
  https://github.com/ag2ai/faststream/blob/main/faststream/middlewares/logging.py ·
  https://github.com/ag2ai/faststream/blob/main/faststream/middlewares/exception.py ·
  https://faststream.ag2.ai/latest/release/ · https://faststream.ag2.ai/latest/rabbit/ack/ ·
  https://github.com/ag2ai/faststream/discussions/1161
- Starlette / FastAPI / uvicorn: https://github.com/encode/starlette/blob/master/starlette/middleware/errors.py ·
  https://github.com/encode/starlette/blob/master/starlette/applications.py ·
  https://github.com/encode/starlette/blob/master/starlette/_exception_handler.py ·
  https://www.starlette.io/exceptions/ ·
  https://github.com/encode/uvicorn/blob/master/uvicorn/protocols/http/h11_impl.py ·
  https://github.com/fastapi/fastapi/blob/master/fastapi/exception_handlers.py
- Litestar: https://github.com/litestar-org/litestar/blob/main/litestar/middleware/_internal/exceptions/middleware.py ·
  https://github.com/litestar-org/litestar/blob/main/litestar/logging/config.py ·
  https://github.com/litestar-org/litestar/blob/main/litestar/handlers/base.py ·
  https://github.com/litestar-org/litestar/blob/main/litestar/config/app.py ·
  https://docs.litestar.dev/latest/usage/exceptions.html
- discord.py: https://github.com/Rapptz/discord.py/blob/master/discord/client.py ·
  https://github.com/Rapptz/discord.py/blob/master/discord/ext/commands/core.py ·
  https://github.com/Rapptz/discord.py/blob/master/discord/ext/commands/bot.py ·
  https://github.com/Rapptz/discord.py/blob/master/docs/api.rst
- Slack Bolt: https://github.com/slackapi/bolt-python/blob/main/slack_bolt/listener/thread_runner.py ·
  https://github.com/slackapi/bolt-python/blob/main/slack_bolt/listener/asyncio_runner.py ·
  https://github.com/slackapi/bolt-python/blob/main/slack_bolt/listener/listener_error_handler.py ·
  https://github.com/slackapi/bolt-python/blob/main/slack_bolt/app/app.py ·
  https://docs.slack.dev/tools/bolt-python/concepts/errors
- python-telegram-bot: https://github.com/python-telegram-bot/python-telegram-bot/blob/master/src/telegram/ext/_application.py ·
  https://github.com/python-telegram-bot/python-telegram-bot/blob/master/src/telegram/ext/_updater.py ·
  https://github.com/python-telegram-bot/python-telegram-bot/wiki/Exceptions%2C-Warnings-and-Logging
- Sanic: https://github.com/sanic-org/sanic/blob/main/sanic/app.py ·
  https://github.com/sanic-org/sanic/blob/main/sanic/handlers/error.py ·
  https://github.com/sanic-org/sanic/blob/main/sanic/errorpages.py ·
  https://sanic.dev/en/guide/best-practices/exceptions.html
- Task systems: https://github.com/celery/celery/blob/main/celery/app/trace.py ·
  https://github.com/taskiq-python/taskiq/blob/master/taskiq/receiver/receiver.py ·
  https://github.com/python-arq/arq/blob/main/arq/worker.py ·
  https://github.com/Bogdanp/dramatiq/blob/master/dramatiq/worker.py ·
  https://github.com/Bogdanp/dramatiq/blob/master/dramatiq/middleware/retries.py ·
  https://github.com/Bogdanp/dramatiq/blob/master/dramatiq/message.py ·
  https://github.com/Bogdanp/dramatiq/blob/master/dramatiq/broker.py
- Let it crash: https://www.erlang.org/doc/system/design_principles.html ·
  https://www.erlang.org/doc/system/sup_princ.html ·
  https://github.com/golang/go/blob/master/src/net/http/server.go ·
  https://docs.python.org/3/library/asyncio-eventloop.html#error-handling-api ·
  https://docs.python.org/3/library/asyncio-task.html ·
  https://docs.python.org/3/library/asyncio-runner.html
- Observability: https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/asgi.py ·
  https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/starlette.py ·
  https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/celery/__init__.py ·
  https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/arq.py ·
  https://docs.sentry.io/platforms/python/configuration/options/ ·
  https://opentelemetry.io/docs/specs/otel/trace/api/ ·
  https://opentelemetry.io/docs/specs/semconv/exceptions/exceptions-spans/ ·
  https://opentelemetry-python.readthedocs.io/en/latest/api/trace.html
- aiommbot 0.4.x: `aiommbot/middlewares/safe_error_notification.py` (0.4.x repository, commit `2d61ff3`) ·
  `docs/research/09-usage-mining-0.4.x-bots.md` §9
