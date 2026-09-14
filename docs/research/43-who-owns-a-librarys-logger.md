# 43. Who owns a library's logger, and how it reaches the code that writes records

**Question.** Does a library create its own loggers or take them from the caller, what does it do
when the caller supplies nothing, and what does either answer cost an operator who wants to silence
one part of it?

[`24`](24-library-logging-design.md) measured how a zero-dependency library should *write* a record
— levels, `extra`, correlation, the reserved `LogRecord` names. This note measures the question one
step earlier: where the logger object comes from. It also settles what a third-party plugin author
is told, which [`35`](35-the-third-party-author-kit.md) found no host answering.

The decisions this note is evidence for are
[ADR-0078](../adr/0078-a-logger-is-a-capability-the-composition-supplies.md) and
[ADR-0079](../adr/0079-the-record-catalogue-survives-a-supplied-logger.md).

Findings only, and no recommendation. Sources are primary — project source at the commit named
below and each project's own documentation — read on 2026-09-14. Anything a primary source did not
confirm is marked **[unverified]**.

## 1 The corpus: twenty-two libraries, five answers

| Library | How the logger is obtained | Caller may substitute | Ships a Protocol | Distinct names |
|---|---|---|---|---|
| **faststream** | constructor parameter defaulting to a sentinel, else one internal factory | **yes** — an object, `None`, or omit | **yes**, `LoggerProto`, one member | 7 |
| **websockets** | constructor parameter defaulting to `None`, else a literal | **yes**, per connection | no — a union alias | 2 |
| litestar | constructor parameter plus one `__name__` | yes — object, factory or name | **yes**, `Logger`, nine members | 1 fixed |
| aiohttp | six literals, injected as constructor defaults | yes, for the application and access logs | only for the access-log formatter | 6 |
| dramatiq | a custom factory over module and class | private classes only | no | unbounded |
| sqlalchemy | a custom factory, plus `echo=` per instance | the level only, never the object | no — duck-typed | unbounded |
| celery | a custom factory, `get_task_logger` | by lookup, not by injection | no | ~40 |
| stamina | a hook backend; the logger is built lazily | **yes** — `set_on_retry_hooks()` | **yes**, `RetryHook`, one member | 1 |
| opentelemetry | `getLogger(__name__)` ×32, for self-diagnostics | no | an ABC for its own Logs API only | ~33 |
| discord.py | `getLogger(__name__)` ×18 | no — `setup_logging()` only configures | no | 18 |
| redis-py | `getLogger(__name__)` ×21 plus one literal | no | no | 22 |
| urllib3 | `getLogger(__name__)` ×9 | no — `add_stderr_logger()` only configures | no | 9 |
| taskiq | ten literals plus seven `__name__` | **no** — not one `logger=` parameter | no | 17 |
| hikari | twelve literals plus a per-shard name | no — `logs=` reconfigures globally | no | 13 |
| aiogram | five literals plus two `__name__` | no | no | 7 |
| trio | three literals, on error paths only | no | no | 3 |
| httpx | one literal, `"httpx"`, two call sites | no | no | 1 |
| dishka | `getLogger(__name__)` ×1 | no | no | 1 |
| anyio | one inline `getLogger(__name__)` | no | no | 1 |
| **structlog** | none of its own | n/a | **yes**, `BindableLogger`, five members | **0** |
| **pydantic** | none | n/a | no | **0** |
| **msgspec** | none | n/a | no | **0** |

**Counts.** The logger is a parameter in **four** of twenty-two; a custom factory in four;
module-level `getLogger(__name__)` in six; a module-level literal in six; and absent altogether in
three. A logger Protocol or ABC ships in four. **A `NullHandler` is installed by two of
twenty-two** — urllib3
([`__init__.py`](https://github.com/urllib3/urllib3/blob/9a97e7b9ba30be1e9b2fbe3f0bb06e3dbbbba2fa/src/urllib3/__init__.py#L71))
and discord.py — despite it being the documented advice for libraries.

So the mainstream is a module-level logger the caller cannot replace, and supplying one is a
minority position held by four projects, two of which — faststream and websockets — hold it
deliberately and document why.

## 2 FastStream: a three-state parameter and a state machine behind it

**One `getLogger` call in the whole package**
([`_internal/logger/logging.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/_internal/logger/logging.py#L61)).
Every broker takes the logger as a constructor parameter whose default is a sentinel object rather
than `None`:

```python
logger: Optional["LoggerProto"] = EMPTY,
log_level: int = logging.INFO,
```

([`rabbit/broker/broker.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/rabbit/broker/broker.py#L112),
repeated on every broker; `EMPTY` is an instance of `EmptyPlaceholder` whose `__bool__` is `False`,
[`_internal/constants.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/_internal/constants.py#L14-L25).)

The three states are dispatched in one function, and the sentinel exists exactly so that `None` can
mean *silence* rather than *default*:

```python
def make_logger_storage(logger, default_storage_cls) -> "LoggerParamsStorage":
    if logger is EMPTY:
        return default_storage_cls()
    return EmptyLoggerStorage() if logger is None else ManualLoggerStorage(logger)
```

([`_internal/logger/params_storage.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/_internal/logger/params_storage.py#L13-L20).)
The documentation states the intent in the same words: "If you want to completely disable the
default logging of FastStream, you can set `logger=None`"
([`observability/logging.md`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/docs/docs/en/getting-started/observability/logging.md#L43-L51)).

**Silence is an object, not a branch.** Three proxies implement the same call — one that raises if
anything logs before `connect()`, one whose `log` is `pass`, and one that forwards
([`_internal/logger/logger_proxy.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/_internal/logger/logger_proxy.py#L31-L106))
— so none of the twenty-seven emit sites carries an `if logger is not None`.

**The Protocol is one method wide**, which is what makes a foreign logger substitutable at all:

```python
class LoggerProto(Protocol):
    def log(self, level: int, msg: Any, /, *, exc_info: Any = None,
            extra: Mapping[str, Any] | None = None) -> None: ...
```

([`_internal/basic_types.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/_internal/basic_types.py#L89-L98).)
The framework calls `.log(...)` and never `.info`/`.warning`, and the documentation walks an author
through handing it a structlog logger
([`logging.md`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/docs/docs/en/getting-started/observability/logging.md#L204-L289)).

**Two costs FastStream pays and documents.** Context enrichment splits in two: a `logging.Filter`
reads a contextvar and stamps fields onto the record, but it is installed **only on loggers
FastStream built**
([`logging.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/_internal/logger/logging.py#L13-L56));
a supplied logger receives the same dictionary as `extra=` instead, and the docs concede "you will
lose information about the context of the current request"
([`logging.md`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/docs/docs/en/getting-started/observability/logging.md#L184)).
And silencing becomes per *broker* rather than per component: there is no `logger=` on
`subscriber()`, so `logger=None` silences a whole broker and `log_level=` raises a whole broker's
floor.

**FastStream configures logging, and that is the half not to copy.** `get_logger` sets the level,
sets `propagate = False` and attaches a colourising `StreamHandler`
([`logging.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/_internal/logger/logging.py#L60-L83));
there is no `NullHandler` anywhere in the package. Its position is that its own loggers are its own
end to end and detached from the root, while the caller's logger is untouched.

**No record catalogue, and none is possible.** Nothing in its observability documentation enumerates
the records, and several of the twenty-seven emit sites build the message by interpolating an
exception — `f"{exc_type.__name__}: {exc_val}"`
([`middlewares/logging.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/middlewares/logging.py#L85))
and the supervisor's retry text
([`supervisor.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/_internal/endpoint/subscriber/supervisor.py#L104-L130))
— so the record set is not finite even in principle.

## 3 websockets: a logger per unit of work

The parameter is on the sans-I/O base and re-exposed at every layer, defaulting to `None` in all of
them, with the default built per side:

```python
        if logger is None:
            logger = logging.getLogger(f"websockets.{side.name.lower()}")
```

([`protocol.py`](https://github.com/python-websockets/websockets/blob/ad8d970e7678f0c1d676f988d9e0072c7f3626a5/src/websockets/protocol.py#L88-L103).)
The type is a plain union alias, `LoggerLike = logging.Logger | logging.LoggerAdapter[Any]`
([`typing.py`](https://github.com/python-websockets/websockets/blob/ad8d970e7678f0c1d676f988d9e0072c7f3626a5/src/websockets/typing.py#L37)),
not a Protocol.

Per-connection identity is **not** a child logger — there is no `getChild` call in the package — but
a stock adapter injecting a weak reference:

```python
        self.protocol.logger = logging.LoggerAdapter(
            self.protocol.logger, {"websocket": weakref.proxy(self)},
        )
```

([`asyncio/connection.py`](https://github.com/python-websockets/websockets/blob/ad8d970e7678f0c1d676f988d9e0072c7f3626a5/src/websockets/asyncio/connection.py#L69-L72),
shipped identically in the `sync`, `trio` and `legacy` backends.) No `process()` override ships, so
the field is usable only by a formatter or adapter the caller writes — which the documentation makes
the expected pattern, with a worked example
([`docs/topics/logging.rst`](https://github.com/python-websockets/websockets/blob/ad8d970e7678f0c1d676f988d9e0072c7f3626a5/docs/topics/logging.rst#L104-L138)).

Its stated reason for shipping no configuration is one sentence: "websockets doesn't provide a
default logging configuration because requirements vary a lot" ([same
page](https://github.com/python-websockets/websockets/blob/ad8d970e7678f0c1d676f988d9e0072c7f3626a5/docs/topics/logging.rst#L62-L63)),
and it tells the caller to add the `NullHandler` themselves ([same
page](https://github.com/python-websockets/websockets/blob/ad8d970e7678f0c1d676f988d9e0072c7f3626a5/docs/topics/logging.rst#L193)).

**And it publishes a convention instead of a catalogue**: which level carries what, and a
single-character prefix alphabet — `>` `<` `=` `x` `%` `-` `!` — so a reader can scan a transcript
([same
page](https://github.com/python-websockets/websockets/blob/ad8d970e7678f0c1d676f988d9e0072c7f3626a5/docs/topics/logging.rst#L237-L255)).

## 4 django-modern-rest: an absence, not a position

`dmr/` holds 194 Python files and **zero** `getLogger` calls, zero `import logging`, and no file
that so much as contains the substring. The only occurrences in the repository are a test silencing
schemathesis and the Sphinx build tool, neither shipped.

What it does instead is raise typed exceptions and convert them to typed responses: a body-parse
failure becomes `RequestSerializationError`
([`parsers.py`](https://github.com/wemake-services/django-modern-rest/blob/218b65a3c75b103b6289b8db54ea426c1365e89d/dmr/parsers.py#L302)),
validation becomes `ValidationError(..., status_code=400)`
([`internal/context.py`](https://github.com/wemake-services/django-modern-rest/blob/218b65a3c75b103b6289b8db54ea426c1365e89d/dmr/internal/context.py#L196-L200)),
and everything funnels to `global_error_handler`, which either converts or re-raises bare
([`errors.py`](https://github.com/wemake-services/django-modern-rest/blob/218b65a3c75b103b6289b8db54ea426c1365e89d/dmr/errors.py#L246-L326)).
That handler is a response shaper: its documentation describes returning a response or re-raising,
and mentions no reporting, no tracker and no observation. It emits exactly one warning in the whole
package, `UnsafeCacheBackendWarning`, and no telemetry of any kind.

**The silence is emergent rather than chosen.** No README, changelog or document states it — the
closest statement is oblique and about a different feature, advising reliance on "application-level
logging or analytics instead"
([`docs/pages/auth/token.rst`](https://github.com/wemake-services/django-modern-rest/blob/218b65a3c75b103b6289b8db54ea426c1365e89d/docs/pages/auth/token.rst#L280-L284)).
Meanwhile its lint configuration **enables ruff's `G` and `LOG` rule sets**
([`pyproject.toml`](https://github.com/wemake-services/django-modern-rest/blob/218b65a3c75b103b6289b8db54ea426c1365e89d/pyproject.toml#L313)),
guardrails for logging that never happens. And two `except Exception: pass` sites around user error
handlers
([`endpoint.py`](https://github.com/wemake-services/django-modern-rest/blob/218b65a3c75b103b6289b8db54ea426c1365e89d/dmr/endpoint.py#L237-L239))
mean a handler that itself raises vanishes without trace.

Three of the four projects that emit nothing — structlog, pydantic, msgspec — are pure value layers
with no I/O, no background task and no lifecycle to report on. pydantic replaces records with a
purpose-built warning tree of seven categories
([`warnings.py`](https://github.com/pydantic/pydantic/blob/831893ed0411d45c20aacae88e067c9c33a89501/pydantic/warnings.py#L22-L121));
msgspec is the strictest case, with neither loggers nor warnings, only exceptions.

## 5 The type of the parameter: a Protocol, or `logging.Logger`

Four of the twenty-two ship a logger Protocol, and reading them settles what one buys.

**Litestar's is nine members and it calls one.** `Logger` declares `debug info warning warn error
fatal exception critical setLevel`
([`types/protocols.py`](https://github.com/litestar-org/litestar/blob/7cccc5e52ce92683a13436a4be8ac77c1ccd1c12/litestar/types/protocols.py#L13)),
and the only call sites are two `.info`s in one middleware. Its real requirement — that the logger
accept arbitrary keyword arguments — lives in a **boolean parameter**, not in the type:
`log_structured=True` "will expect a logger that accept arbitrary data as keyword arguments"
([`docs/usage/logging.rst`](https://github.com/litestar-org/litestar/blob/7cccc5e52ce92683a13436a4be8ac77c1ccd1c12/docs/usage/logging.rst#L67-L69)).
Measured: mypy `--strict` accepts both the `**kwargs` call site and a `logging.Logger` argument, and
the combination raises `TypeError: Logger._log() got an unexpected keyword argument` at runtime.
**Litestar 3.0 then deleted the whole layer** — `Litestar.logging_config`, `Litestar.logger`,
`litestar.logging` and `litestar.plugins.structlog` — recording that "Users that have previously
relied on Litestar to configure logging, can simply use the standard logging configuration provided
by their logging library of choice"
([`changelog.rst`](https://github.com/litestar-org/litestar/blob/7cccc5e52ce92683a13436a4be8ac77c1ccd1c12/docs/release-notes/changelog.rst#L309-L331)).

**FastStream's is one member, and its structlog compatibility is one character.** `LoggerProto.log`
marks `level, msg` positional-only with a `/`, which suppresses a type checker's parameter-name
check. tenacity's near-identical Protocol omits the `/` and its docstring claims compatibility with
"logging, structlog, loguru, etc."
([`_utils.py`](https://github.com/jd/tenacity/blob/3e58094d3bc414975aad9eadf343a32bdb3b89b3/tenacity/_utils.py#L51-L58));
measured, mypy rejects `structlog.stdlib.BoundLogger` against it because structlog's parameter is
named `event` rather than `msg`. FastStream also carries a `type: ignore[attr-defined]` exactly
where the Protocol is too narrow, for `setLevel`, under a configuration that sets
`warn_unused_ignores`.

**The compatibility a Protocol is reached for already exists without one.**
`structlog.get_logger()` is typed `Any` and its documentation says so, so mypy `--strict` and ty
both accept it where `logging.Logger` is required. The cost of the stdlib annotation lands only on
a user who writes the explicit `structlog.stdlib.BoundLogger` annotation.

**And the substitution a Protocol would enable breaks the record contract.** `extra=` passed *into*
a structlog logger never reaches a record: the default configuration renders it into the message
text, and `render_to_log_kwargs` re-nests it as `extra["extra"]`. structlog's own advice to a
library is the section headed **"Don't integrate"** — configure standard-library logging and attach
`ProcessorFormatter`, whose `ExtraAdder` lifts `extra` fields off a `LogRecord` into the event
dictionary
([`docs/standard-library.md`](https://github.com/hynek/structlog/blob/73393f34b40c15688b3fdd0982889b225f11b59b/docs/standard-library.md#L145)).

**loguru is the sharper case, because the failure is silent.** `loguru._logger.Logger` is a bare
class
([`_logger.py`](https://github.com/Delgan/loguru/blob/48acf77ac2b3296acc67069511b99cc3ca3d0c41/loguru/_logger.py#L243)),
and `capture=True` makes every keyword argument both a record field and a `str.format()` argument
([`:2168-2188`](https://github.com/Delgan/loguru/blob/48acf77ac2b3296acc67069511b99cc3ca3d0c41/loguru/_logger.py#L2168-L2188)).
Measured on loguru 0.7.3 under Python 3.14.7:

| Call | Observed |
|---|---|
| `logger.info("msg", extra={"a": 1})` | `record["extra"] == {"extra": {"a": 1}}` — nested one level deeper |
| `logger.warning("rejected {reason}", extra={"reason": "x"})` | `KeyError 'reason'` on 0.7.3; `ValueError` on master |
| `logger.info("failed", exc_info=True)` | `record["extra"] == {"exc_info": True, …}` — a data field, no traceback |

A type checker flags none of it, because the stub is `**kwargs: Any`. Against a `logging.Logger`
annotation the same object is refused up front: `Argument "logger" … has incompatible type
"loguru.Logger"; expected "logging.Logger | None"`.

**What a one-method Protocol loses.** `isEnabledFor`, guarded on by websockets, httpcore, aiohttp,
redis-py and sqlalchemy; `%`-lazy `*args`; `.exception()`; and `stacklevel`, whose loss is
observable — FastStream's proxy does not forward it, so every record it writes reports the proxy's
own line instead of the call site, the same defect structlog subclasses `logging.Logger` to fix.

**A logger Protocol has no conformance test anywhere.** A sweep of seventy-six Python-bearing
clones found none referencing `LoggerProto`, `LoggerProtocol` or `LoggerLike`; the only checks in
the corpus are two one-line `isinstance` assertions inside structlog itself, against a
`@runtime_checkable` Protocol, which verify member presence and no signature. CPython declines the
same thing explicitly, with the comment "do a protocol check, but we do not use
`typing.runtime_checkable()`".

## 6 What the evidence supports

- A library that lets the caller supply the logger is a minority of four in twenty-two, and only two
  of those four — faststream and websockets — hold the position deliberately and publish the reason.
  The mainstream is a module-level logger the caller cannot replace.
- The sentinel is the load-bearing part, not the parameter. Three states are needed — omitted,
  `None`, an object — and a plain `None` default cannot express them, which is why FastStream
  carries an `EmptyPlaceholder` class whose only purpose is to let `logger=None` mean silence.
- Silence is cheaper as an object than as a branch. FastStream's null proxy keeps twenty-seven emit
  sites free of a presence test; the cost is one class.
- A supplied logger costs per-name silencing. The unit an operator can quieten becomes the object
  the logger was handed to, so a per-component name only survives where the framework built the
  logger itself. This is the single real regression against a fixed `<package>.<component>` scheme.
- Context enrichment splits unless it is built to survive substitution. FastStream's filter works
  only on its own loggers and its documentation admits the loss; the layers that do survive are the
  call's own `extra` and anything the *application* attaches to its own handler.
- A record catalogue and a supplied logger are compatible only if every message is a constant string
  with variable data in `extra`. FastStream cannot have a catalogue because several of its messages
  interpolate an exception; websockets publishes a levels-and-prefixes convention instead. Keeping
  the catalogue rule and writing interpolated messages is the combination that does not work.
- An absence of logging is not evidence of a decision. django-modern-rest emits nothing, states
  nowhere that it means to, and ships enabled lint rules for the logging it never writes.
- A logger Protocol buys less than it appears to and costs more. It does not buy structlog, which is
  typed `Any` and passes a `logging.Logger` annotation already; it does not buy loguru, whose
  positional-only parameters reject the usual Protocol shape; and it admits objects whose `extra`
  handling silently differs. The standard-library annotation is the one that refuses the wrong
  object at the point a type checker can still say so.
- Two libraries in the corpus shipped a logger Protocol and then walked it back in the same release
  line — Litestar deleted its whole logging layer in 3.0, and FastStream carries a `type: ignore`
  where its own Protocol is too narrow.

## Sources

Every claim above carries its own link inline. This section names what was read.

Loggers supplied by the caller:

- <https://github.com/ag2ai/faststream> — `faststream/_internal/basic_types.py`,
  `faststream/_internal/constants.py`, `faststream/_internal/logger/logger_proxy.py`,
  `faststream/_internal/logger/logging.py`, `faststream/_internal/logger/params_storage.py`,
  `faststream/middlewares/logging.py`, `faststream/rabbit/broker/broker.py`,
  `docs/docs/en/getting-started/observability/logging.md`
- <https://github.com/python-websockets/websockets> — `src/websockets/asyncio/connection.py`,
  `src/websockets/protocol.py`, `src/websockets/typing.py`, `docs/topics/logging.rst`
- <https://github.com/aio-libs/aiohttp> · <https://github.com/litestar-org/litestar> ·
  <https://github.com/hynek/stamina>

Libraries that emit nothing:

- <https://github.com/wemake-services/django-modern-rest> — `dmr/endpoint.py`, `dmr/errors.py`,
  `dmr/internal/context.py`, `dmr/parsers.py`, `dmr/settings.py`, `pyproject.toml`,
  `docs/pages/auth/token.rst`
- <https://github.com/pydantic/pydantic> — `pydantic/warnings.py`
- <https://github.com/jcrist/msgspec> · <https://github.com/hynek/structlog>

Loggers the caller cannot replace:

- <https://github.com/urllib3/urllib3> — `src/urllib3/__init__.py`
- <https://github.com/Bogdanp/dramatiq> · <https://github.com/Rapptz/discord.py> ·
  <https://github.com/aiogram/aiogram> · <https://github.com/agronholm/anyio> ·
  <https://github.com/celery/celery> · <https://github.com/encode/httpx> ·
  <https://github.com/hikari-py/hikari> · <https://github.com/open-telemetry/opentelemetry-python> ·
  <https://github.com/python-trio/trio> · <https://github.com/reagento/dishka> ·
  <https://github.com/redis/redis-py> · <https://github.com/sqlalchemy/sqlalchemy> ·
  <https://github.com/taskiq-python/taskiq>
