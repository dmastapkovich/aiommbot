# 41. How a host reports which lifecycle unit failed

**Question.** When a plugin, extension, listener, bootstep, cleanup context or finaliser fails to
start or fails to stop, how does the *caller* learn which unit it was — and when several fail at
once, what reaches the caller?

[`32`](32-plugin-lifecycle-failure.md) asked what a host *does* on a lifecycle failure: unwind,
retry, resting state. It did not ask what the failure *says*. This note answers the second half,
and adds the standard-library mechanics an aggregate failure has to obey: what subclassing
`ExceptionGroup` costs, and what `derive` is for.

The decisions this note is evidence for are
[ADR-0074](../adr/0074-a-failed-start-enters-the-same-stop-phase-and-never-retries.md) and
[ADR-0075](../adr/0075-a-lifecycle-failure-names-its-plugin-and-several-are-one-group.md).

Findings only, and no recommendation. Sources are primary — project source at the commit named
below, `docs.python.org`, CPython's own test suite — read on 2026-09-14. Anything a primary source
did not confirm is marked **[unverified]**.

Sixty-four failure paths were classified across eighty-six clones. The result is lopsided enough to
be the finding: **hosts name the unit on the way up and name nothing on the way down.**

## 1 The six answers a host can give, and how often it gives each

One row of the census is one distinct code site that handles — or fails to handle — a lifecycle
unit's failure.

| Class | What the caller can read | Paths | of which on **stop** |
|---|---|---|---|
| **X** nowhere | the unit's own exception, bare, with nothing naming it | 27 | 16 |
| **L** log only | a `logger.exception` / `call_exception_handler` names it; the caller is told nothing | 13 | 8 |
| **G** raw member of a group | every failure reaches the caller; none carries an identity | 11 | 7 |
| **W** wrapper naming the unit | a host-defined class with the unit's name as an attribute | 8 | **0** |
| **S** host-side state | a registry, enum or set the caller inspects afterwards | 5 | 0 |
| **N** identity in the group's message or nesting | a string, or a sub-group per unit | 4 | 2 |

**Zero class-W paths on the stop phase.** Every exception class in the corpus whose name contains
Cleanup, Teardown, Shutdown, Close, Exit, Unload, Stop, Dispose or Finaliz plus Error/Exception was
read — nineteen of them — and none is a wrapper naming a unit that failed to stop. `CleanupError`
and `ExitError` are aggregates carrying no identity; `sqlalchemy`'s `_CleanupError` is about
annotation parsing; `dmr`'s `StreamingCloseError` is a signal user code raises; the rest are
network or state guards.

discord.py holds both extremes inside one file: the best-typed start-up taxonomy in the survey,
`ExtensionFailed(name=…, original=…)` raised after a full rollback
([`bot.py`](https://github.com/Rapptz/discord.py/blob/65232c38702be5844cf2ce865a4777eb1928b5d0/discord/ext/commands/bot.py#L972-L978)),
and three silent swallows on the way down — `except Exception: pass` around `teardown` ([same
file](https://github.com/Rapptz/discord.py/blob/65232c38702be5844cf2ce865a4777eb1928b5d0/discord/ext/commands/bot.py#L938-L954))
and two more in `BotBase.close` ([same
file](https://github.com/Rapptz/discord.py/blob/65232c38702be5844cf2ce865a4777eb1928b5d0/discord/ext/commands/bot.py#L243-L256)),
which discard every `ExtensionError` the unload path produces, `.name` and all.

## 2 Naming and grouping are disjoint everywhere

Of the eleven paths that raise an aggregate, **none puts the identity where a caller can read it
programmatically**: two put it in the group's message (both pytest, both defeated by collapse — §4),
two put it in a parallel log line, and seven put it nowhere.

Three projects came within one line of doing both and each declined, for a different reason.

**websockets builds the wrappers and deliberately omits the identity.** It is the only
group-of-wrappers in the corpus, and the wrapper is assembled by hand with `__cause__` set
explicitly:

```python
        except Exception as write_exception:
            if raise_exceptions:
                exception = RuntimeError("failed to write message")
                exception.__cause__ = write_exception
                exceptions.append(exception)
            else:
                connection.logger.warning(
                    "skipped broadcast: failed to write message: %s", …)
```

([`asyncio/connection.py`](https://github.com/python-websockets/websockets/blob/ad8d970e7678f0c1d676f988d9e0072c7f3626a5/src/websockets/asyncio/connection.py#L1239-L1252),
shipped identically in the `sync`, `trio` and `legacy` backends.) The machinery is all present; the
connection identity goes only to the non-raising branch's log line.

**redis-py builds named wrappers, keeps the mapping, then folds it into a dictionary.**
`UnhealthyDatabaseException(message, database, original_exception)` carries `.database` as a real
attribute
([`multidb/exception.py`](https://github.com/redis/redis-py/blob/5b3c8719371fcde36eda16a8a2ef8408daee8d20/redis/multidb/exception.py#L5-L11)),
and a `task_to_db` map preserves the correspondence across `gather(..., return_exceptions=True)` —
and the result becomes `dict[Database, bool]` plus a debug log
([`asyncio/multidb/client.py`](https://github.com/redis/redis-py/blob/5b3c8719371fcde36eda16a8a2ef8408daee8d20/redis/asyncio/multidb/client.py#L359-L391)).
Class W plus class S; never a group.

**pytest puts the name in the group's message and then collapses it away.** §4 has the mechanism.

The pattern behind all three is one sentence: **the identity is in hand at the catch site and
discarded at the raise site.** `_mounts.values()`, `_servers.values()`, `nodes_cache.values()` and
`for result in results` each throw away a key the caller needs — httpx
([`_client.py`](https://github.com/encode/httpx/blob/b5addb64f0161ff6bfe94c124ef76f6a1fba5254/httpx/_client.py#L1263-L1273)),
pymongo
([`topology.py`](https://github.com/mongodb/mongo-python-driver/blob/93c7bdf36c3f1ef197bbf297f3f2e055950f79a2/pymongo/asynchronous/topology.py#L608-L618),
whose `Server` knows `self._description.address` one line earlier), redis-py
([`cluster.py`](https://github.com/redis/redis-py/blob/5b3c8719371fcde36eda16a8a2ef8408daee8d20/redis/asyncio/cluster.py#L2702-L2709))
and python-telegram-bot
([`_application.py`](https://github.com/python-telegram-bot/python-telegram-bot/blob/3d72ea2a5a7fc11116a23ee86307a3ab62f10f3e/src/telegram/ext/_application.py#L1782-L1790),
where the index is the only identity and the loop discards it).

## 3 What a class-W wrapper carries

```python
class ExtensionError(DiscordException):
    def __init__(self, message=None, *args, name: str) -> None:
        self.name: str = name                              # keyword-only, mandatory

class ExtensionFailed(ExtensionError):
    def __init__(self, name: str, original: Exception) -> None:
        self.original: Exception = original
        msg = f'Extension {name!r} raised an error: {original.__class__.__name__}: {original}'
        super().__init__(msg, name=name)
```

([`errors.py`](https://github.com/Rapptz/discord.py/blob/65232c38702be5844cf2ce865a4777eb1928b5d0/discord/ext/commands/errors.py#L1019-L1085).)

| Class | Identity carrier | Cause carrier | Phase marker |
|---|---|---|---|
| `discord.ExtensionFailed` | `.name: str` | `.original` and `__cause__` | none |
| `discord.NoEntryPointError` | `.name: str` | none — a plain `raise` | none |
| `pytest.ConftestImportFailure` | `.path: Path` | `.cause: Exception`, custom `__str__` | none |
| `pytest.PluginImportFailure` | `args[0]` only — no `__init__`, no attribute | `__cause__` | none |
| `pluggy.PluginValidationError` | `.plugin` — the object itself | none | n/a, a validation class |
| `redis.UnhealthyDatabaseException` | `.database: Database` | `.original_exception` | n/a, a health class |
| pymongo `_raise_connection_failure` | a message string, `f"{host}:{port}: "` | `from error` | none |

**Three of seven expose the identity as a typed attribute**; the rest bury it in a message string,
unreadable without parsing. **None carries a phase marker** — discord.py raises the identical
`ExtensionFailed` for a module that failed to import and for a `setup()` that raised, so a caller
cannot tell them apart; and `ExtensionNotFound`'s docstring promises an `original` attribute its
`__init__` never assigns, so reading it raises `AttributeError` rather than returning `None`.

## 4 Collapsing an aggregate of one, and what it destroys

| Aggregate | Collapses at `len == 1`? | Rooted at |
|---|---|---|
| dishka `ExitError` | no — always wraps | `ExceptionGroup[Exception]` **and** `DishkaError` |
| aiohttp `CleanupError` | **yes** → the bare exception | `RuntimeError` alone — not a group at all |
| pytest `FixtureDef.finish` | yes → bare, losing `argname` | stdlib `BaseExceptionGroup` |
| pytest `teardown_exact` | yes, at **both** nesting levels | stdlib |
| pytest `unittest.py` class cleanups | no | stdlib |
| litestar `DependencyCleanupGroup._throw` | no | stdlib |
| hypothesis `BuildContext.__exit__` | yes → `raise errors[0] from exc_value` | stdlib |
| trio `close_all` | yes | stdlib, and the message is `""` |
| trio nursery | only under `strict_exception_groups=False`, with a warning note attached | stdlib |
| CPython `TaskGroup` | no | stdlib |
| CPython `doModuleCleanups` | no | stdlib |
| CPython `create_connection` | **the caller's choice** — an `all_errors` parameter | stdlib |
| websockets `broadcast` | no, and a `raise_exceptions` parameter gates the whole thing | stdlib |
| celery `delayed_delivery` | no | stdlib |

Six collapse, eight always wrap, two make it a parameter of the call.

**Collapse is where identity dies.** pytest nests a sub-group whose message names the node —
`f"errors while tearing down {node!r}"` — and then splices the single-failure case straight through:

```python
        if len(these_exceptions) == 1:
            exceptions.extend(these_exceptions)
        elif these_exceptions:
            msg = f"errors while tearing down {node!r}"
            exceptions.append(BaseExceptionGroup(msg, these_exceptions[::-1]))
```

([`runner.py`](https://github.com/pytest-dev/pytest/blob/3fd8675d6d798507c06cf9c60753be6d9d7b0e17/src/_pytest/runner.py#L551-L583);
the same shape guards `argname` at
[`fixtures.py`](https://github.com/pytest-dev/pytest/blob/3fd8675d6d798507c06cf9c60753be6d9d7b0e17/src/_pytest/fixtures.py#L1207-L1230).)
So the identity survives only when **two or more units under one parent fail together** — the rare
case, not the common one.

Grouping has a second, documented price. celery must re-raise retryable exceptions *out* of the
group it builds, because Kombu's `retry_over_time` matches on exception type and cannot see inside
one
([`delayed_delivery.py`](https://github.com/celery/celery/blob/3e40f4332479ccd83527908dc9249c54531380de/celery/worker/consumer/delayed_delivery.py#L167-L199)).
An aggregate defeats every outer `except` that is not `except*`.

**aiohttp is the one host whose rule is stated in full, in five lines**, and it is the rule a stop
phase needs: run every unit regardless of earlier failures, in reverse, then collapse or aggregate.

```python
    async def _on_cleanup(self, app: Application) -> None:
        errors = []
        for it in reversed(self._exits):
            try:
                await it.__aexit__(None, None, None)
            except (Exception, asyncio.CancelledError) as exc:
                errors.append(exc)
        if errors:
            if len(errors) == 1:
                raise errors[0]
            else:
                raise CleanupError("Multiple errors on cleanup stage", errors)
```

([`web_app.py`](https://github.com/aio-libs/aiohttp/blob/9e08ba02abe573ce9e4cc541d4e3c3646adb43a7/aiohttp/web_app.py#L436-L449).)
Its one defect is the class: `CleanupError` is a `RuntimeError` whose `.exceptions` is a property
reading `self.args[1]` ([same
file](https://github.com/aio-libs/aiohttp/blob/9e08ba02abe573ce9e4cc541d4e3c3646adb43a7/aiohttp/web_app.py#L409-L412))
— an exception group in every respect except type, written before PEP 654 and never migrated, so
`except*`, `split()` and `subgroup()` do nothing with it.

## 5 What subclassing `ExceptionGroup` actually costs

Two projects in the corpus subclass it. One pays the price and one does not, and CPython's own test
suite proves what the difference buys.

**The constructor is `__new__`, and the message must be a `str`.** "Note that `BaseExceptionGroup`
defines `__new__`, so subclasses that need a different constructor signature need to override that
rather than `__init__`"
([`Doc/library/exceptions.rst`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Doc/library/exceptions.rst#L1082)).
The C slot parses `"UO"` and rejects an empty sequence, a non-sequence, or any item that is not an
exception instance
([`Objects/exceptions.c`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Objects/exceptions.c#L928-L933)).
A subclass of `ExceptionGroup` — hence of `Exception` — **cannot wrap a `BaseException`**:
`TypeError: Cannot nest BaseExceptions in 'MyEG'` ([same
file](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Objects/exceptions.c#L973-L981)).

**`derive` is what keeps the subclass alive through a split.** "A subclass needs to override it in
order to make `subgroup` and `split` return instances of the subclass rather than `ExceptionGroup`"
([`exceptions.rst`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Doc/library/exceptions.rst#L1038-L1048)).
The default implementation constructs `BaseExceptionGroup(self.msg, excs)` **by name, not by
`type(self)`** ([`exceptions.c`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Objects/exceptions.c#L1138-L1148)),
and CPython's own test asserts the consequence: every partial split of a bare subclass returns a
plain `ExceptionGroup`
([`test_exception_group.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/test/test_exception_group.py#L922-L962)).
Overriding `__new__` alone degrades identically ([same
file](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/test/test_exception_group.py#L964-L1003));
only overriding both preserves the class ([same
file](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/test/test_exception_group.py#L1006-L1053)).

**`except*` degrades only on a partial match.** `_PyEval_ExceptionGroupMatch` first tries
`PyErr_GivenExceptionMatches`; on a hit against a group it hands the object over whole and
unmodified, and only on a miss does it call `split`
([`Python/ceval.c`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Python/ceval.c#L2256-L2309)).
So a class rooted at a library's own error base survives `except* ThatBase` and is stripped by
`except* SomeLeafError`.

| Subclass | `derive`? | `__new__`? | in `__all__`? | documented? |
|---|---|---|---|---|
| `dishka.exceptions.ExitError` | no | no | no | no |
| `hypothesis.errors.FlakyFailure` | **yes** | **yes** | n/a — the module has none | **yes**, in two pages |

dishka's is `class ExitError(ExceptionGroup[Exception], DishkaError): pass`
([`exceptions.py`](https://github.com/reagento/dishka/blob/929560592f51becf02b2182d5287c3ab87d909bd/src/dishka/exceptions.py#L28-L32)).
It is the only class in the corpus rooted at its library's own error base, and because it overrides
neither method, any leaf-type filter rebuilds it as a plain `ExceptionGroup` and loses the
`DishkaError` mixin with it.

hypothesis pays in full and records why, in a comment citing the CPython issue: "defining `derive`
is required for `split` to return an instance of FlakyFailure instead of ExceptionGroup"
([`errors.py`](https://github.com/HypothesisWorks/hypothesis/blob/cd434f23be1a3598085cf096e28e6738c63b29b3/hypothesis-python/src/hypothesis/errors.py#L183-L201)).
Its `derive` is `return type(self)(self.message, excs)` — `type(self)`, so a further subclass
inherits it correctly — and its `__new__` exists to wrap stray `BaseException`s before construction,
precisely because the `Exception` mixin forbids them.

**`derive` alone is enough when the constructor signature is unchanged.** Both overriding sites in
the corpus also override `__new__`, and both do so because their signature differs — hypothesis's to
normalise stray `BaseException`s, CPython's documentation example's to take `(errors, exit_code)`.
Measured on CPython **3.12.14 and 3.14.7**, with identical results on both, a subclass that keeps
`(message, excs)` and overrides only `derive` survives every path that rebuilds a group, and a bare
`pass` subclass survives only a full-base `except*`:

| Subclass | `subgroup()` | `split()` | remainder of a partial `except*` | full-base `except*` |
|---|---|---|---|---|
| `derive` only | preserved | preserved | preserved | preserved |
| bare `pass` | `ExceptionGroup` | `ExceptionGroup` | `ExceptionGroup` | preserved |

So the price of rooting an aggregate at a library's own error base is **one method**, not two — and
dishka pays none of it while hypothesis pays both because it had to.

**CPython's own standard library subclasses nothing**: `asyncio.TaskGroup`, `base_events`,
`staggered` and `unittest` all raise the builtins directly. Fourteen projects in the corpus import
the `exceptiongroup` backport and none subclasses it. And **no project defines a group subclass
whose `__new__` takes only the failures and synthesises the message** — the only such construction
anywhere is CPython's documentation example
([`exceptions.rst`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Doc/library/exceptions.rst#L1087-L1096)),
which hardcodes its own class name in both methods where hypothesis's `type(self)` form does not.

## 6 What the evidence supports

- A host names a unit on the way up and names nothing on the way down. All eight wrapper classes
  are start-phase; the stop phase has none in sixty-four paths. The field's default on a failed stop
  is not "one exception" but "no exception at all" — five of the surveyed hosts return from `stop()`
  normally however many units failed.
- Naming the unit and reporting every failure are disjoint in every project measured. The three that
  came closest each had the identity in hand at the catch site and discarded it at the raise site,
  and each paid for it in a different way.
- Collapsing an aggregate of one destroys whatever identity the aggregate carried in its message.
  pytest demonstrates it twice in one file: the name survives only when two units fail together.
  Collapse is safe exactly when the member itself carries the identity.
- An aggregate defeats every outer `except` that is not `except*`, and celery documents the
  workaround it was forced into — re-raising retryable members out of the group so an outer retry
  loop can match on type.
- Rooting an aggregate at a library's own error base costs exactly one method, `derive`, as long as
  the constructor keeps the `(message, excs)` signature — measured on 3.12 and 3.14 alike. Without
  it the class is correct only under a full-base `except*` and is silently rebuilt as a plain
  `ExceptionGroup` by anything narrower. hypothesis pays; dishka does not.
- aiohttp states the whole stop-phase rule in five lines — every unit attempted in reverse, failures
  collected, one collapsed and several aggregated — and then spends the aggregate on a
  `RuntimeError` that `except*` cannot see.

## Sources

Every claim above carries its own link inline. This section names what was read.

CPython:

- <https://github.com/python/cpython> — `Doc/library/exceptions.rst`, `Lib/contextlib.py`,
  `Lib/test/test_exception_group.py`, `Lib/unittest/case.py`, `Lib/socket.py`,
  `Lib/asyncio/taskgroups.py`, `Objects/exceptions.c`, `Python/ceval.c`

Aggregates and wrappers:

- <https://github.com/aio-libs/aiohttp> — `aiohttp/web_app.py`
- <https://github.com/HypothesisWorks/hypothesis> — `hypothesis-python/src/hypothesis/errors.py`
- <https://github.com/Rapptz/discord.py> — `discord/client.py`, `discord/ext/commands/bot.py`,
  `discord/ext/commands/cog.py`, `discord/ext/commands/errors.py`
- <https://github.com/litestar-org/litestar> — `litestar/_kwargs/cleanup.py`
- <https://github.com/pytest-dev/pytest> — `src/_pytest/config/__init__.py`,
  `src/_pytest/fixtures.py`, `src/_pytest/runner.py`, `src/_pytest/unittest.py`
- <https://github.com/pytest-dev/pluggy> — `src/pluggy/_manager.py`
- <https://github.com/python-trio/trio> — `src/trio/_core/_run.py`,
  `src/trio/_highlevel_open_tcp_stream.py`
- <https://github.com/python-websockets/websockets> — `src/websockets/asyncio/connection.py`
- <https://github.com/reagento/dishka> — `src/dishka/async_container.py`, `src/dishka/container.py`,
  `src/dishka/exceptions.py`

Identity discarded at the raise site:

- <https://github.com/celery/celery> — `celery/bootsteps.py`,
  `celery/worker/consumer/delayed_delivery.py`
- <https://github.com/encode/httpx> — `httpx/_client.py`
- <https://github.com/getsentry/sentry-python> — `sentry_sdk/client.py`,
  `sentry_sdk/integrations/__init__.py`
- <https://github.com/mongodb/mongo-python-driver> — `pymongo/asynchronous/monitor.py`,
  `pymongo/asynchronous/topology.py`, `pymongo/pool_shared.py`
- <https://github.com/open-telemetry/opentelemetry-python> —
  `opentelemetry-sdk/src/opentelemetry/sdk/metrics/_internal/__init__.py`,
  `opentelemetry-sdk/src/opentelemetry/sdk/trace/__init__.py`
- <https://github.com/python-telegram-bot/python-telegram-bot> — `src/telegram/_bot.py`,
  `src/telegram/ext/_application.py`
- <https://github.com/redis/redis-py> — `redis/asyncio/cluster.py`,
  `redis/asyncio/multidb/client.py`, `redis/multidb/exception.py`
- <https://github.com/sqlalchemy/sqlalchemy> — `lib/sqlalchemy/event/attr.py`,
  `lib/sqlalchemy/pool/base.py`, `lib/sqlalchemy/pool/impl.py`

Hosts with no answer at all:

- <https://github.com/Bogdanp/dramatiq> — `dramatiq/broker.py`
- <https://github.com/agronholm/anyio> — `src/anyio/_core/_sockets.py`
- <https://github.com/django/django> — `django/apps/registry.py`
- <https://github.com/encode/starlette> — `starlette/routing.py`
- <https://github.com/hikari-py/hikari> — `hikari/impl/gateway_bot.py`, `hikari/impl/rest_bot.py`
- <https://github.com/pydantic/pydantic> — `pydantic/plugin/_loader.py`
- <https://github.com/python-arq/arq> — `arq/worker.py`
- <https://github.com/sanic-org/sanic> — `sanic/server/runners.py`, `sanic/signals.py`
- <https://github.com/taskiq-python/taskiq> — `taskiq/abc/broker.py`, `taskiq/cli/worker/run.py`
- <https://github.com/wemake-services/django-modern-rest> — `dmr/streaming/exceptions.py`
