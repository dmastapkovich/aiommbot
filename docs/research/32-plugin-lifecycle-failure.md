# 32. What a host does when a plugin fails to start or stop

**Question.** When a plugin fails to start or fails to stop, what does the host do — is a partial
start unwound, what does the caller see when several stops fail at once, is there a retry, is the
failure typed, and what state is the host left in?

One of five notes gathered for GitHub issue #100, which asked what a plugin host specifies
beyond an explicit list and a set of narrow Protocols — the mechanics that
[ADR-0015](../adr/0015-plugin-contract-and-composition.md) states as words rather than as
mechanisms. The five are
[`30`](30-plugin-contract-versioning.md) the contract version,
[`32`](32-plugin-lifecycle-failure.md) lifecycle failure,
[`33`](33-the-plugin-to-plugin-channel.md) the plugin-to-plugin channel,
[`34`](34-plugin-conflicts-and-prohibitions.md) conflicts and prohibitions, and
[`35`](35-the-third-party-author-kit.md) the third-party author's kit.
[`docs/research/10`](10-plugin-systems.md) surveyed the same hosts for registration, ordering,
isolation and settings; it did not ask what a host specifies after those choices.

The load-bearing half is the standard library: the documented guarantees of
`contextlib.AsyncExitStack` and `asyncio.TaskGroup` decide what a host can promise at all.

The decision this note is evidence for is #103.

Findings only, and no recommendation. Sources are primary — project source at the default branch,
reference and developer documentation, PEPs, the Python packaging specifications,
`docs.python.org`, PyPI metadata and project issue trackers — read on 2026-09-10. Anything a
primary source did not confirm is marked **[unverified]**.

Two questions separate the hosts in this field. Does a start that fails halfway undo the part
that succeeded? And when the stopping half itself fails, what reaches the caller? The CPython
primitives that most async hosts build on answer the first question generously and the second
one badly, and almost every framework inherits both answers without restating them.

## 1 1. Home Assistant: a closed taxonomy, and a backoff schedule written as numbers

Home Assistant is the only host surveyed here whose start-up failures are a named, finite set with a
defined host reaction per name. The root of the set is `IntegrationError`, whose docstring reads
"Base class for platform and config entry exceptions"
([`homeassistant/exceptions.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/exceptions.py#L231-L255)).
It has four direct members in that file, each a one-line docstring:

- `PlatformNotReady` — "Error to indicate that platform is not ready."
- `ConfigEntryError` — "Error to indicate that config entry setup has failed."
- `ConfigEntryNotReady` — "Error to indicate that config entry is not ready."
- `ConfigEntryAuthFailed` — "Error to indicate that config entry could not authenticate."

The taxonomy is deliberately reusable by subclassing: the OAuth 2.0 errors inherit from a member in
order to acquire its host behaviour rather than to add a new one. `OAuth2TokenRequestError`
"Inherits ConfigEntryNotReady so setup retries without the integration having to map it. Catch it
explicitly to handle it differently", and `OAuth2TokenRequestReauthError` "Inherits
ConfigEntryAuthFailed so setup starts reauth without the integration having to map it"
([`homeassistant/exceptions.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/exceptions.py#L256-L378)).
Inheriting the behaviour instead of mapping it is what keeps the set closed: a new error joins the
taxonomy by picking a parent.

Dispatch happens in one `try` in `ConfigEntry.async_setup`, and the order of the `except` clauses is
what makes the multiple-inheritance trick work — `ConfigEntryAuthFailed` is tested before
`ConfigEntryNotReady`, so `OAuth2TokenRequestReauthError`, which inherits both, starts a reauth flow
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L800-L915)).

| Raised from `async_setup_entry` | Entry state after | Reason recorded | Retry | Side effect |
|---|---|---|---|---|
| `ConfigEntryError` | `SETUP_ERROR` | `str(exc) or "Unknown fatal config entry error"` | no | `logger.exception` |
| `ConfigEntryAuthFailed` | `SETUP_ERROR` | `str(exc) or "could not authenticate"` | no | `async_start_reauth_if_available` |
| `ConfigEntryNotReady` | `SETUP_RETRY` | `str(exc) or None` | yes, scheduled | `logger.info` once per attempt |
| `asyncio.CancelledError` with `task.cancelling() > 0` | `SETUP_ERROR` | `None` | no | re-raised |
| anything else (`except SystemExit, Exception`) | `SETUP_ERROR` | `None` | no | `logger.exception` |
| returned `False` | `SETUP_ERROR` | `None` | no | `_async_process_on_unload` runs |
| returned a non-`bool` | `SETUP_ERROR` | `None` | no | logs "did not return boolean" |

The `except SystemExit, Exception:` clause is unparenthesised because Home Assistant now requires
`>=3.14.2`
([`pyproject.toml`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/pyproject.toml#L24)),
and [PEP 758](https://peps.python.org/pep-0758/) — "Allow `except` and `except*` expressions without
parentheses", `Python-Version: 3.14`, `Status: Final` — made that syntax legal.

**Returning `False` is not the same as raising.** Raising `ConfigEntryNotReady` is the only path
that schedules another attempt; every other outcome, `False` included, lands in `SETUP_ERROR` and
stops. A `False` return also records no reason at all: `error_reason` stays `None`, so the entry
lands in `SETUP_ERROR` with `reason` unset — that the integrations page therefore shows the failure
without a cause is **[unverified]**; the source shows only the empty field. And the cleanup `False`
triggers is not exclusive to it: `finally: if not result and domain_is_integration: await
self._async_process_on_unload(hass)` runs on every exit where `result` is falsy, and the
`ConfigEntryNotReady` branch returns from inside the `try`, so the retry path runs it too
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L916-L918)).
A non-`bool` return is coerced: `logger.error("%s.async_setup_entry did not return boolean", ...)`
then `result = False`.

**The retry schedule.** One line computes it:

```python
wait_time = min(2**self._tries * 5, SETUP_RETRY_MAX_WAIT) + (
    randint(RANDOM_MICROSECOND_MIN, RANDOM_MICROSECOND_MAX) / 1000000
)
self._tries += 1
```

with `SETUP_RETRY_MAX_WAIT = 600 # 10 minutes`
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L145))
and `RANDOM_MICROSECOND_MIN = 50000`, `RANDOM_MICROSECOND_MAX = 500000`
([`homeassistant/helpers/event.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/helpers/event.py#L87-L88)).
`_tries` starts at `0`
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L564)),
so the waits in seconds are **5, 10, 20, 40, 80, 160, 320, 600, 600, …** plus 0.05–0.5 s of jitter.
The retry count is never capped. It is reset only by moving to a state outside
`NO_RESET_TRIES_STATES = {ConfigEntryState.SETUP_RETRY, ConfigEntryState.SETUP_IN_PROGRESS}`
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L222-L225)),
which is what lets the backoff keep growing across consecutive failures.

Scheduling depends on whether the host has finished booting. During boot the retry is not a
timer at all — the entry subscribes to `EVENT_HOMEASSISTANT_STARTED` instead, so a slow device
does not delay start-up. It still burns a retry: `self._tries += 1` runs before either branch,
so the boot-time attempt advances the backoff for the next one:

```python
if hass.state is CoreState.running:
    self._async_cancel_retry_setup = async_call_later(hass, wait_time, HassJob(...))
else:
    self._async_cancel_retry_setup = hass.bus.async_listen(
        EVENT_HOMEASSISTANT_STARTED, functools.partial(self._async_setup_again, hass)
    )
```

**The entity-platform path has its own, different schedule.** `PlatformNotReady` is handled in
`EntityPlatform._async_setup_platform` with `wait_time = min(tries, 6) *
PLATFORM_NOT_READY_BASE_WAIT_TIME`
([`homeassistant/helpers/entity_platform.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/helpers/entity_platform.py#L508-L541))
where the base is `30 # seconds`
([`entity_platform.py#L70`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/helpers/entity_platform.py#L70)):
**30, 60, 90, 120, 150, 180, 180, …** — linear, not exponential, capped at three minutes, no jitter,
and again uncapped in count. The constant `PLATFORM_NOT_READY_RETRIES = 10`
([`entity_platform.py#L62`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/helpers/entity_platform.py#L62))
appears nowhere else under `homeassistant/` — a retry cap that is defined and never applied. Two
neighbouring failures on the same platform get non-retryable treatment ([same file, lines
542-561](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/helpers/entity_platform.py#L542-L561)):
a `SLOW_SETUP_MAX_WAIT = 60` timeout logs "Setup of platform %s is taking longer than %s seconds.
Startup will proceed without waiting any longer." and returns `False`, and a forwarded platform that
raises a config-entry error is told off — "Instead raise %s before calling
async_forward_entry_setups" — and also returns `False`.

**A failing stop leaves the entry neither loaded nor unloaded.** `ConfigEntry.async_unload` has
three failure exits, all producing the same state
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L995-L1077)):
no `async_unload_entry` attribute at all gives `FAILED_UNLOAD` with reason `"Unload not supported"`;
a `False` return gives `FAILED_UNLOAD` with `"Unload failed"`; a raised exception is logged with
`logger.exception` and gives `FAILED_UNLOAD` with `str(exc) or "Unknown error"`. In all three
`async_unload` returns `False`. The consequences are structural, not cosmetic:

- The on-unload callbacks and `runtime_data` teardown sit inside `if result:`, so they do
  **not** run. The entry keeps its runtime object.
- `FAILED_UNLOAD = "failed_unload", False` marks the state non-recoverable, and the enum documents
  what that flag buys: "If the entry state is recoverable, unloads and reloads are allowed."
  ([`ConfigEntryState`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L151-L187))
  For the integration's own domain `async_unload` refuses before it reaches the component — `if not
  self.state.recoverable: return False`, inside the `if domain_is_integration:` branch — so a second
  unload or a reload can never be attempted. The entry is wedged until Home Assistant restarts.
- A non-`bool` return trips `assert isinstance(result, bool)`, which the surrounding `except
  Exception` converts into the same `FAILED_UNLOAD`.

The documentation is narrower than the code. "Handling setup failures"
([developers.home-assistant.io](https://developers.home-assistant.io/docs/integration_setup_failures))
documents `ConfigEntryNotReady` ("Home Assistant will automatically take care of retrying set up
later"), `PlatformNotReady`, and `ConfigEntryAuthFailed` ("Home Assistant will automatically put the
config entry in a failure state and start a reauth flow") — and never names `ConfigEntryError`,
never states a wait time, and never mentions returning `False`. It also says of a retry message
"Home Assistant will log at `debug` level", where the code logs the retry line at `logger.info` and
only the traceback at `debug`.

## 2 2. Django: `AppConfig.ready()` raising leaves the registry populated and unrecoverable

`Apps.populate()` runs in three phases and guards itself with a reentrancy flag rather than a
transaction
([`django/apps/registry.py`](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/django/apps/registry.py#L61-L127)):

```python
    def populate(self, installed_apps=None):
        """
        Load application configurations and models.
        ...
        It is thread-safe and idempotent, but not reentrant.
        """
        if self.ready:
            return

        with self._lock:
            if self.ready:
                return

            # An RLock prevents other threads from entering this section. The
            # compare and set operation below is atomic.
            if self.loading:
                # Prevent reentrant calls to avoid running AppConfig.ready()
                # methods twice.
                raise RuntimeError("populate() isn't reentrant")
            self.loading = True
```

Phase 3 is a bare loop with no error handling:

```python
            # Phase 3: run ready() methods of app configs.
            for app_config in self.get_app_configs():
                app_config.ready()

            self.ready = True
            self.ready_event.set()
```

So when one `AppConfig.ready()` raises:

- **Nothing is rolled back.** There is no `try`, no `finally`, no compensating loop. Every entry
  written into `self.app_configs` during phase 1 stays there, every model imported in phase 2
  stays imported, and every `ready()` that already returned keeps whatever it registered —
  signal receivers, system checks, monkeypatches. The apps after the failing one never get
  `ready()` called at all.
- **The flags are left inconsistent.** `self.apps_ready = True` was set at the end of phase 1
  and `self.models_ready = True` at the end of phase 2, both before phase 3 begins; `self.ready`
  is still `False` and `self.ready_event` is unset. `self.loading` is still `True`, because
  nothing clears it on the error path. The registry therefore answers `check_apps_ready()` and
  `check_models_ready()` affirmatively while `django.apps.apps.ready` is `False`.
- **A second `populate()` cannot recover.** `if self.ready: return` does not fire, the `RLock` is
  free (the exception unwound out of the `with`), and `if self.loading:` is `True` — so the second
  call raises `RuntimeError("populate() isn't reentrant")`, from any thread, forever. The one place
  that resets `self.loading` is `set_installed_apps`, which opens with `if not self.ready: raise
  AppRegistryNotReady("App registry isn't ready yet.")`
  ([`django/apps/registry.py`](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/django/apps/registry.py#L356-L362)),
  and `self.ready` is `False`. There is no path back.

`django.setup()` is a thin wrapper — `apps.populate(settings.INSTALLED_APPS)` with no error handling
([`django/__init__.py`](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/django/__init__.py#L8-L24))
— so a raising `ready()` propagates to whatever called `setup()`. Django has no typed failure for
this: `ImproperlyConfigured` and `AppRegistryNotReady`
([`django/core/exceptions.py`](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/django/core/exceptions.py))
cover duplicate labels and premature access, not a plugin whose own initialisation failed. There is
also no stop half to fail: the registry has no `unready()`.

## 3 3. Starlette and Litestar: one context manager versus an exit stack

The two frameworks answer the partial-start question differently, and the difference is in the
code rather than in the docs.

**Starlette holds exactly one lifespan context manager.** `Router.lifespan` is the whole of it
([`starlette/routing.py`](https://github.com/encode/starlette/blob/f03f65c2f98c592773d691b4d309c68b83e568ef/starlette/routing.py#L645-L670)):

```python
        started = False
        app: Any = scope.get("app")
        await receive()
        try:
            async with self.lifespan_context(app) as maybe_state:
                ...
                await send({"type": "lifespan.startup.complete"})
                started = True
                await receive()
        except BaseException:
            exc_text = traceback.format_exc()
            if started:
                await send({"type": "lifespan.shutdown.failed", "message": exc_text})
            else:
                await send({"type": "lifespan.startup.failed", "message": exc_text})
            raise
```

Starlette keeps no stack, so it has nothing to unwind. `started` is the entire state machine, and it
only decides which ASGI failure message to send. Whether the shutdown half runs after a partial
start is delegated wholly to the single user object: with the ordinary `@asynccontextmanager`
generator, a failure before `yield` means the code after `yield` never runs, because `__aenter__`
raised and the `async with` never entered its body — so `__aexit__` is never called. In this version
the legacy hook path is inert as well: `_DefaultLifespan.__aenter__` and `__aexit__` are both `pass`
([`starlette/routing.py`](https://github.com/encode/starlette/blob/f03f65c2f98c592773d691b4d309c68b83e568ef/starlette/routing.py#L565-L576)),
and `Router.__init__` accepts no `on_startup`/`on_shutdown` sequences at all — the version read is
`__version__ = "1.6.0"`
([`starlette/__init__.py`](https://github.com/encode/starlette/blob/f03f65c2f98c592773d691b4d309c68b83e568ef/starlette/__init__.py#L1)).

**Litestar builds the lifespan out of an `AsyncExitStack`, so a partial start is unwound.**
`Litestar.lifespan` is an `@asynccontextmanager` wrapping one stack
([`litestar/app.py`](https://github.com/litestar-org/litestar/blob/7cccc5e52ce92683a13436a4be8ac77c1ccd1c12/litestar/app.py#L589-L612)):

```python
        async with AsyncExitStack() as exit_stack:
            for hook in self.on_shutdown[::-1]:
                exit_stack.push_async_callback(partial(self._call_lifespan_hook, hook))

            await exit_stack.enter_async_context(self.event_emitter)

            for manager in self._lifespan_managers:
                if not isinstance(manager, AbstractAsyncContextManager):
                    manager = manager(self)
                await exit_stack.enter_async_context(manager)

            for hook in self.on_startup:
                await self._call_lifespan_hook(hook)

            yield
```

Three consequences follow from the registration order, all of them mechanical:

- If the *n*-th lifespan manager's `__aenter__` raises, the *n−1* already entered are exited,
  and so is `event_emitter`, because the stack's `__aexit__` runs as the enclosing `async with`
  unwinds. Litestar is the unwinding case; Starlette is not.
- Every `on_shutdown` hook is pushed onto the stack **before** anything is entered and before
  any `on_startup` hook runs. So an `on_startup` hook that raises still causes **all**
  `on_shutdown` hooks to run — teardown for a start-up that never completed. They were pushed in
  `on_shutdown[::-1]` order and pop LIFO, so they execute in declaration order.
- `push_async_callback` registers a callback that "Cannot suppress exceptions" and receives no
  exception details
  ([`Lib/contextlib.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/contextlib.py#L739-L750)),
  so an `on_shutdown` hook cannot see that start-up failed, nor swallow the failure.

Litestar's ASGI wrapper is otherwise the same shape as Starlette's — `started` flag, `try`,
`lifespan.startup.failed` versus `lifespan.shutdown.failed`, `raise e`
([`litestar/_asgi/asgi_router.py`](https://github.com/litestar-org/litestar/blob/7cccc5e52ce92683a13436a4be8ac77c1ccd1c12/litestar/_asgi/asgi_router.py#L189-L223)).
Neither framework types the failure: both catch `BaseException` and re-raise it unchanged. The
version read is `3.0.0b0`
([`pyproject.toml`](https://github.com/litestar-org/litestar/blob/7cccc5e52ce92683a13436a4be8ac77c1ccd1c12/pyproject.toml#L11)).

**The protocol behind both is a closed two-message taxonomy, and it is the server that decides.**
The ASGI lifespan spec defines `lifespan.startup.failed` — "Sent by the application when it has
failed to complete its startup. If a server sees this it should log/print the message provided and
then exit." — and `lifespan.shutdown.failed` — "Sent by the application when it has failed to
complete its cleanup. If a server sees this it should log/print the message provided and then
terminate."
([`specs/lifespan.rst`](https://github.com/django/asgiref/blob/cf94d8e0cff969d21462a8994b5c46c4eae6954d/specs/lifespan.rst#L106-L161)),
added in "2.0 (2019-03-04): Added startup.failed and shutdown.failed, clarified exception handling
during startup phase". Uvicorn implements exactly that: `startup()` logs "Application startup
failed. Exiting." and sets `should_exit`
([`uvicorn/lifespan/on.py`](https://github.com/encode/uvicorn/blob/fa324a415364563cf45908966435e2480a6b46bf/uvicorn/lifespan/on.py#L46-L75)),
and `Server.startup` then calls `sys.exit(STARTUP_FAILURE)` with `STARTUP_FAILURE = 3`
([`uvicorn/server.py`](https://github.com/encode/uvicorn/blob/fa324a415364563cf45908966435e2480a6b46bf/uvicorn/server.py#L115-L118),
[`uvicorn/config.py`](https://github.com/encode/uvicorn/blob/fa324a415364563cf45908966435e2480a6b46bf/uvicorn/config.py#L83)).
There is no retry anywhere on this path.

## 4 4. FastStream: the first broker that fails to connect ends start-up

Brokers are started sequentially with no error handling at all
([`faststream/_internal/application.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/_internal/application.py#L93-L96)):

```python
    async def _start_broker(self) -> None:
        assert self.brokers, "You should setup a broker"
        for b in self.brokers:
            await b.start()
```

So the answer is: **fail, not degrade and not retry.** The first broker whose `start()` raises
aborts the loop; the remaining brokers are never started; the brokers already started are never
stopped by this code path.

In the CLI application the failure travels through an anyio task group. `FastStream.run` puts
`_startup` in the group and then polls a flag
([`faststream/app.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/app.py#L77-L98)):

```python
        async with self.lifespan_context(**(run_extra_options or {})):
            try:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self._startup, log_level, run_extra_options)

                    while not self._should_exit:
                        await anyio.sleep(sleep_time)

                    await self._shutdown(log_level)
                    tg.cancel_scope.cancel()
            except ExceptionGroup as e:
                for ex in e.exceptions:
                    raise ex from None
```

A broker failure cancels the group before the loop can reach `await self._shutdown(log_level)`,
so `stop()` — and with it every `on_shutdown` and `after_shutdown` hook and every
`broker.stop()` — is skipped entirely. The `except ExceptionGroup` clause then flattens the
group by raising its first member `from None`, discarding the rest and suppressing the group as
context.

The ASGI variant behaves differently in two ways worth naming
([`faststream/asgi/app.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/asgi/app.py#L249-L322)).
`__start` signals readiness before the brokers connect —

```python
        async with (
            self._startup_logging(log_level=log_level),
            self._start_hooks_context(**run_extra_options),
        ):
            task_status.started()
            await self._start_broker()
```

— so `await tg.start(self.__start, ...)` returns once the `on_startup` hooks have run, the
`start_lifespan_context` body yields, and `lifespan.startup.complete` is sent to the server
*before* any broker connection is established. And unlike the CLI path,
`start_lifespan_context` wraps the body in `try: yield finally: await self._shutdown()`, so the
shutdown half does run.

FastStream types its start-up failures only shallowly. Its hierarchy is rooted at
`FastStreamException(Exception)` with `SetupError(FastStreamException, ValueError)` — "Exception to
raise at wrong method usage" — and `StartupValidationError(FastStreamException, ValueError)` for
mismatched CLI options
([`faststream/exceptions.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/exceptions.py)).
`StartupValidationError` is the one failure the ASGI lifespan handler special-cases: when Typer is
installed it is drawn with `draw_startup_errors` and `lifespan.startup.failed` is sent with an empty
message, and without Typer it falls through to the generic handler. There is no `BrokerNotReady`, no
not-ready-yet class, and no retry policy: a connection failure surfaces as whatever the underlying
driver raised.

## 5 5. CPython: `contextlib.AsyncExitStack` and `asyncio.TaskGroup`

#### 5a. `AsyncExitStack`: entered callbacks are unwound, simultaneous exit failures are lost

**The unwinding guarantee is documented, and it is the whole promise.** The class example says: "All
opened connections will automatically be released at the end of the async with statement, even if
attempts to open a connection later in the list raise an exception"
([docs.python.org](https://docs.python.org/3/library/contextlib.html#contextlib.AsyncExitStack)).
The `ExitStack` prose it refers back to says "Each instance maintains a stack of registered
callbacks that are called in reverse order when the instance is closed (either explicitly or
implicitly at the end of a `with` statement)" and "Since registered callbacks are invoked in the
reverse order of registration, this ends up behaving as if multiple nested `with` statements had
been used with the registered set of callbacks. This even extends to exception handling - if an
inner callback suppresses or replaces an exception, then outer callbacks will be passed arguments
based on that updated state"
([docs.python.org](https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack)). The
mechanism is that `enter_async_context` pushes the exit callback only after `await _enter()`
returns, so a failed `__aenter__` is never registered while everything before it is
([`Lib/contextlib.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/contextlib.py#L707-L725)).

**The documentation says nothing whatever about several `__aexit__` calls raising.** The
`contextlib` page never mentions `ExceptionGroup`, `BaseExceptionGroup` or `__context__` in
connection with either stack class; the only `BaseExceptionGroup` discussion on that page belongs to
`suppress()`. The behaviour has to be read from the source
([`Lib/contextlib.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/contextlib.py#L759-L815)):

```python
        # Callbacks are invoked in LIFO order to match the behaviour of
        # nested context managers
        suppressed_exc = False
        pending_raise = False
        while self._exit_callbacks:
            is_sync, cb = self._exit_callbacks.pop()
            try:
                ...
            except BaseException as new_exc:
                # simulate the stack of exceptions by setting the context
                _fix_exception_context(new_exc, exc)
                pending_raise = True
                exc = new_exc

        if pending_raise:
            try:
                # bare "raise exc" replaces our carefully
                # set-up context
                fixed_ctx = exc.__context__
                raise exc
            except BaseException:
                exc.__context__ = fixed_ctx
                raise
        return received_exc and suppressed_exc
```

Four findings, none of them in the documentation:

1. **No grouping ever happens.** `AsyncExitStack.__aexit__` raises a single exception. There is
   no `BaseExceptionGroup` construction anywhere in `Lib/contextlib.py` outside `suppress()`.
2. **Every registered callback still runs.** The `except BaseException` sits inside the `while`,
   so one failing `__aexit__` — `CancelledError` included — does not stop the unwind. The
   remaining callbacks are all invoked, each receiving the newest pending exception as its
   `exc_details`.
3. **The last-run callback's exception is the one that propagates.** `exc = new_exc` overwrites
   on each failure and the loop is LIFO, so the winner is the failure from the
   *earliest-registered* (outermost) callback.
4. **The earlier failures are chained only if an exception was already in flight; otherwise
   they are silently dropped.** `_fix_exception_context(new_exc, old_exc)` begins `exc_context =
   new_exc.__context__` and returns immediately `if exc_context is None or exc_context is
   old_exc`, and it only rewrites a link when it reaches `frame_exc = sys.exception()`. During a
   clean unwind `frame_exc` is `None`, and each callback raises while no exception is being
   handled, so `new_exc.__context__` is `None` and the helper returns without linking anything.
   Reproduced on CPython 3.14.7: three failing `__aexit__` callbacks in one stack, no body
   exception, yield exactly one `RuntimeError` whose `__context__` is `None` — the other two
   vanish. Add a body exception and the same three produce a full `exit-a ← exit-b ← exit-c ←
   body` chain, because the interpreter set each `__context__` to the in-flight exception and
   the helper could re-point it.

The practical reading: `AsyncExitStack` gives a strong unwind guarantee and a weak reporting
guarantee. A host that closes its plugins through one stack on a clean shutdown will hear about
at most one failing plugin, with no marker that others failed.

#### 5b. `asyncio.TaskGroup`: grouping is the documented contract, with three named escapes

Here the documentation is explicit where `contextlib`'s is silent. The class docstring states the
rule — "Any exceptions other than `asyncio.CancelledError` raised within a task will cancel all
remaining tasks and wait for them to exit. The exceptions are then combined and raised as an
`ExceptionGroup`"
([`Lib/asyncio/taskgroups.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/asyncio/taskgroups.py#L14-L28))
— and the library reference gives the full ordering
([`Doc/library/asyncio-task.rst`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Doc/library/asyncio-task.rst#L439-L466)):

> The first time this happens, the remaining tasks in the group are cancelled and then waited
> for, and no further tasks can be added to the group.

> Once all tasks have finished, the non-cancellation exceptions -- including the exception the
> body exited with, unless it is `asyncio.CancelledError` -- are combined in an `ExceptionGroup`
> or `BaseExceptionGroup` (as appropriate; see their documentation), which is then raised.

> Some exceptions are treated specially: if any task fails with `KeyboardInterrupt` or
> `SystemExit`, the task group still cancels the remaining tasks and waits for them, but then
> the initial `KeyboardInterrupt` or `SystemExit` is re-raised instead of `ExceptionGroup` or
> `BaseExceptionGroup`. Additionally, if the body of the `async with` statement raises
> `GeneratorExit` and none of the other tasks raise exceptions that would be reported, the
> `GeneratorExit` is re-raised.

The source supplies the details the prose leaves out
([`Lib/asyncio/taskgroups.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/asyncio/taskgroups.py#L86-L319)):

- **Failures during cancellation join the same group.** `_on_task_done` appends to
  `self._errors` whenever `task.exception()` is not `None`, and it is registered on every task,
  so an exception raised by a task's own cleanup while it is being cancelled is collected
  exactly like the original failure. Only `if task.cancelled(): return` — a task that ends
  genuinely cancelled contributes nothing.
- **The group's message is fixed:** `raise BaseExceptionGroup('unhandled errors in a TaskGroup',
  self._errors) from None`. The `from None` sets `__suppress_context__`, so the body's own
  exception is not shown as context — it is a *member* of the group instead, appended last by
  `if et is not None and not issubclass(et, exceptions.CancelledError):
  self._errors.append(exc)`.
- **Real errors outrank cancellation.** `if propagate_cancellation_error is not None and not
  self._errors:` — the comment reads "Propagate CancelledError if there is one, except if there
  are other errors -- those have priority." An external cancellation arriving at the same time
  as task failures is not lost, though: "In the case where a task group is cancelled externally
  and also must raise an `ExceptionGroup`, it will call the parent task's `cancel()` method"
  ([docs.python.org](https://docs.python.org/3/library/asyncio-task.html#task-groups)), which
  the source does as `self._parent_task.uncancel(); self._parent_task.cancel()`.
- **The `SystemExit`/`KeyboardInterrupt` escape used to lose the other errors, and now reports
  them.** On `main` the base-error branch first walks `self._errors` and hands each to
  `self._loop.call_exception_handler` with the message `'TaskGroup task exception was not
  propagated because the TaskGroup body is being closed with a BaseException'`, under a comment
  naming gh-135736: "self._base_error (SystemExit or KeyboardInterrupt) is about to propagate
  out of this method, which discards any other collected task errors silently. Report them
  instead of losing them." That block is absent from
  [`v3.14.0`](https://github.com/python/cpython/blob/v3.14.0/Lib/asyncio/taskgroups.py), where
  the branch is just `try: raise self._base_error finally: exc = None` — so on 3.14 those errors
  are discarded without a trace.
- **Nesting is well defined.** "when one task group is syntactically nested in another, and both
  experience an exception in one of their child tasks simultaneously, the inner task group will
  process its exceptions, and then the outer task group will receive another cancellation and
  process its own exceptions"
  ([docs.python.org](https://docs.python.org/3/library/asyncio-task.html#task-groups)).

The contrast with `AsyncExitStack` is the sharpest result in this section. Both primitives
handle "n things failed at once" and they choose opposite answers: `TaskGroup` grouped and
documented, `AsyncExitStack` single-exception, partially-chained and undocumented.

## 6 6. Elsewhere in the field: other closed start-up-failure taxonomies

Beyond Home Assistant, three of the four projects below give plugin start-up a named failure set
rather than a bare exception — pydantic does not — and only one of the three also undoes the
partial work.

**discord.py — a five-member extension taxonomy with rollback.** `ExtensionError(DiscordException)`
carries the extension `name`, and the members are `ExtensionAlreadyLoaded`, `ExtensionNotLoaded`,
`NoEntryPointError` ("An exception raised when an extension does not have a `setup` entry point
function"), `ExtensionFailed` ("raised when an extension failed to load during execution of the
module or `setup` entry point", exposing `original` and `__cause__`) and `ExtensionNotFound`
([`discord/ext/commands/errors.py`](https://github.com/Rapptz/discord.py/blob/65232c38702be5844cf2ce865a4777eb1928b5d0/discord/ext/commands/errors.py#L1019-L1105)).
The loader compensates a partially-run `setup` before raising
([`discord/ext/commands/bot.py`](https://github.com/Rapptz/discord.py/blob/65232c38702be5844cf2ce865a4777eb1928b5d0/discord/ext/commands/bot.py#L956-L980)):

```python
        try:
            await setup(self)
        except Exception as e:
            del sys.modules[key]
            await self._remove_module_references(lib.__name__)
            await self._call_module_finalizers(lib, key)
            raise errors.ExtensionFailed(key, e) from e
```

Every registration the half-run `setup` made — commands, cogs, listeners — is removed, the
module is un-imported, and the module's own finalisers run. This is the only host in this
section that both types the failure and rolls back the plugin's side effects.

**Sentry's Python SDK — one type whose meaning depends on how the plugin was asked for.**
`DidNotEnable(Exception)`: "The integration could not be enabled due to a trivial user error like
`flask` not being installed for the `FlaskIntegration`. This exception is silently swallowed for
default integrations, but reraised for explicitly enabled integrations."
([`sentry_sdk/integrations/__init__.py`](https://github.com/getsentry/sentry-python/blob/7e95b86bc31b0a1411f0e54c0397152b2201cb2f/sentry_sdk/integrations/__init__.py#L316-L323)).
The dispatch is exactly that: `except DidNotEnable as e: if identifier not in
used_as_default_integration: raise` and otherwise a `logger.debug` ([same file, lines
262-273](https://github.com/getsentry/sentry-python/blob/7e95b86bc31b0a1411f0e54c0397152b2201cb2f/sentry_sdk/integrations/__init__.py#L262-L273)).
One typed decline, two host policies, chosen by whether the user named the plugin.

**pytest — a three-way classification of import failure, with the reasoning in the docstring.**
`PluginManager.import_plugin` sorts failures into declined, user error and plugin defect
([`src/_pytest/config/__init__.py`](https://github.com/pytest-dev/pytest/blob/3fd8675d6d798507c06cf9c60753be6d9d7b0e17/src/_pytest/config/__init__.py#L939-L960)):

```python
        except Skipped as e:
            self.skipped_plugins.append((modname, e.msg or ""))
        except ModuleNotFoundError as e:
            if _is_missing_module(e, importspec):
                # The plugin itself is nowhere to be found - pytest was pointed
                # at something which does not exist, so this is a usage error.
                raise UsageError(f'Error importing plugin "{modname}": {e}') from e
            # Some *other* module the plugin imports is missing: the plugin was
            # found, so this is a defect in the plugin, not a usage error.
            raise PluginImportFailure(modname) from e
        except UsageError:
            raise
        except Exception as e:
            raise PluginImportFailure(modname) from e
```

`PluginImportFailure` states the distinction it exists to draw: "This is deliberately distinct from
a plugin which could not be found at all: not finding it means pytest was pointed at something that
isn't there, which is a `UsageError`, while a plugin blowing up on import is a defect in the plugin
and reported as an internal error." ([same file, lines
146-153](https://github.com/pytest-dev/pytest/blob/3fd8675d6d798507c06cf9c60753be6d9d7b0e17/src/_pytest/config/__init__.py#L146-L153)).
The declined branch is the degraded start: pytest continues and later emits
`PytestConfigWarning(f"skipped plugin {module_name!r}: {msg}")` ([same file, line
2264](https://github.com/pytest-dev/pytest/blob/3fd8675d6d798507c06cf9c60753be6d9d7b0e17/src/_pytest/config/__init__.py#L2264-L2269)).

**pydantic — narrow, untyped, degraded.** The entry-point loader catches only two exception
types and warns:

```python
                    try:
                        _plugins[entry_point.value] = entry_point.load()
                    except (ImportError, AttributeError) as e:
                        warnings.warn(
                            f'{e.__class__.__name__} while loading the `{entry_point.name}` Pydantic plugin, '
                            f'this plugin will not be installed.\n\n{e!r}',
                            stacklevel=2,
                        )
```

([`pydantic/plugin/_loader.py`](https://github.com/pydantic/pydantic/blob/831893ed0411d45c20aacae88e067c9c33a89501/pydantic/plugin/_loader.py#L46-L55)).
Anything else a plugin raises escapes and breaks the caller. There is no failure type of pydantic's
own.

**Two negatives worth recording, because they are the common case.** `pluggy` — "the canonical
Python plugin system" in this catalogue's own reference list — does `plugin = ep.load()` with no
`try` at all in `load_setuptools_entrypoints`
([`src/pluggy/_manager.py`](https://github.com/pytest-dev/pluggy/blob/6a7f8960eb4009b551f14030233cea7a64ccaf5d/src/pluggy/_manager.py#L380-L408)):
the raw exception propagates, plugins registered earlier in the same call stay registered, and the
returned count is lost. And the two closest bot-framework peers do no better:

- `python-telegram-bot`'s `Application.__aenter__` documents a rollback — "Raises: `Exception`: If
  an exception is raised during initialization, `shutdown` is called in this case" — and implements
  it as `try: await self.initialize() except Exception: await self.shutdown(); raise`
  ([`src/telegram/ext/_application.py`](https://github.com/python-telegram-bot/python-telegram-bot/blob/3d72ea2a5a7fc11116a23ee86307a3ab62f10f3e/src/telegram/ext/_application.py#L359-L374)).
  The rollback does nothing: `initialize()` sets `self._initialized = True` only after its last
  step, and `shutdown()`, after a running-state check, returns early — `if not self._initialized:
  _LOGGER.debug("This Application is already shut down. Returning."); return` ([same file, lines
  470-555](https://github.com/python-telegram-bot/python-telegram-bot/blob/3d72ea2a5a7fc11116a23ee86307a3ab62f10f3e/src/telegram/ext/_application.py#L470-L555)).
  So if `self.updater.initialize()` raises, the already-initialised `bot` and `_update_processor`
  are left initialised and never shut down. `__aenter__` also catches `Exception`, not
  `BaseException`, so a cancellation during init skips even the attempt.
- `aiogram` emits start-up hooks *outside* the `try` whose `finally` emits shutdown: `await
  self.emit_startup(bot=bots[-1], **workflow_data)` precedes `try: ... finally: ... await
  self.emit_shutdown(...)`
  ([`aiogram/dispatcher/dispatcher.py`](https://github.com/aiogram/aiogram/blob/97cfe79fa0ac9459d498bdb15cb7cb0530dbaac7/aiogram/dispatcher/dispatcher.py#L596-L631)).
  A raising startup callback therefore means no shutdown callback runs anywhere in the router tree,
  and `emit_startup` itself walks sub-routers with no error handling
  ([`aiogram/dispatcher/router.py`](https://github.com/aiogram/aiogram/blob/97cfe79fa0ac9459d498bdb15cb7cb0530dbaac7/aiogram/dispatcher/router.py#L281-L292)),
  so routers after the failing one never start at all.

## 7 Comparison

| Host | Partial start unwound? | A failing stop produces | Retry, and on what schedule | Failure typed? |
|---|---|---|---|---|
| Home Assistant config entry | Yes — `_async_process_on_unload` runs on a `False`/exception setup | `FAILED_UNLOAD`, non-recoverable; entry stuck, `runtime_data` kept, `async_unload` returns `False` | Yes, only for `ConfigEntryNotReady`: 5, 10, 20, 40, 80, 160, 320, 600, 600 s + 0.05–0.5 s jitter, uncapped in count; before boot completes, waits for `EVENT_HOMEASSISTANT_STARTED` | Yes — `IntegrationError` with four members plus OAuth subclasses |
| Home Assistant entity platform | No rollback; `_setup_complete` stays `False` | `async_reset` removes the entities, logging each failure with `logger.exception`, and finishes anyway | Yes, for `PlatformNotReady`: 30, 60, 90, 120, 150, 180, 180 s, no jitter, uncapped; `PLATFORM_NOT_READY_RETRIES = 10` unused | Yes — `PlatformNotReady` |
| Django app registry | No — configs, imports and completed `ready()` side effects all persist | n/a — no `unready()` | No | No — bare exception out of `populate()`; `loading` stuck `True`, second call raises `RuntimeError("populate() isn't reentrant")` |
| Starlette | No stack to unwind; delegated to the single lifespan CM, whose post-`yield` half never runs | `lifespan.shutdown.failed` + re-raise; uvicorn logs "Application shutdown failed. Exiting." and sets `should_exit` — exit code `3` is the startup path only | No | No — `except BaseException`, re-raised unchanged |
| Litestar | Yes — `AsyncExitStack` exits everything entered, and runs every `on_shutdown` hook even if `on_startup` failed | `lifespan.shutdown.failed` + re-raise; only one exit failure survives (see `AsyncExitStack`) | No | No — `except BaseException as e` … `raise e` |
| FastStream (CLI) | No — started brokers not stopped, `_shutdown` skipped entirely | `stop()` is not reached on a failed start; on a clean stop, exceptions flatten to the group's first member `from None` | No | Partly — `SetupError`, `StartupValidationError`; connection errors are the driver's own |
| FastStream (ASGI) | Shutdown does run (`try: yield finally: await self._shutdown()`) | `lifespan.shutdown.failed` | No | Same, plus a special case for `StartupValidationError` |
| `contextlib.AsyncExitStack` | Yes — the documented promise; a failed `__aenter__` is never registered | One exception: the earliest-registered failing callback. Others chained via `__context__` only if an exception was already in flight, else dropped. Never a `BaseExceptionGroup` | No | No |
| `asyncio.TaskGroup` | Cancels and awaits every remaining task | `BaseExceptionGroup('unhandled errors in a TaskGroup', …) from None`, cleanup failures included; `SystemExit`/`KeyboardInterrupt` and lone `GeneratorExit` escape the group | No | Grouped rather than typed |
| discord.py extensions | Yes — module dropped from `sys.modules`, references removed, finalisers called | `unload_extension` raises `ExtensionNotLoaded` / `ExtensionNotFound` only; a raising `teardown` is swallowed by `_call_module_finalizers` (`except Exception: pass`) | No | Yes — `ExtensionError` with five members |
| Sentry SDK integrations | n/a — `setup_once` failure is the unit | n/a — no teardown | No | Yes — `DidNotEnable`, swallowed for defaults, re-raised for explicit |
| pytest plugins | No — earlier plugins stay registered | n/a | No | Yes — `Skipped` / `UsageError` / `PluginImportFailure` |
| pydantic plugins | n/a — plugin simply absent | n/a | No | No — warns on `ImportError`/`AttributeError`, else propagates |
| pluggy | No — earlier plugins stay registered | n/a | No | No — `ep.load()` unguarded |
| python-telegram-bot | Documented, but ineffective: `shutdown()` early-returns because `_initialized` is still `False` | `shutdown()` raises `RuntimeError("This Application is still running!")` if still running | No | No |
| aiogram | No — `emit_startup` is outside the `try`, so no `emit_shutdown` runs | n/a on a failed start | No | No |

## 8 What the evidence supports

- A typed start-up taxonomy is a small, closed set whose members differ by *host reaction*, not
  by cause. Home Assistant's four `IntegrationError` members map to retry-with-backoff,
  start-reauth, give-up-fatally and give-up-with-a-platform-retry, and new errors join by
  inheriting the member whose reaction they want — the mechanism that keeps the set from growing.
- A typed taxonomy is worth little without the "not ready yet" member. That is the only Home
  Assistant class that produces a second attempt; everything else, including a plain `False`
  return, is terminal. Two of the surveyed hosts retry at all, and both are Home Assistant paths.
- Retry schedules in the field are short, uncapped in count, and jittered only where the host
  has many plugins: 5→600 s doubling with sub-second jitter for config entries, 30→180 s linear
  without jitter for platforms. That both were chosen so a device that is merely offline
  recovers without a restart is **[unverified]** — the only rationale in the source is the
  comment that the jitter bounds "have been determined experimentally in production testing".
- `False` and `raise` must not mean the same thing, and Home Assistant shows the cost when they
  nearly do: `False` records no reason, so the failure reaches the operator without a cause.
- `AsyncExitStack` is the right primitive for unwinding a partial start and the wrong one for
  reporting a failed stop. Its unwind promise is documented and total; its behaviour with
  several simultaneous exit failures is undocumented, single-exception, and silently lossy on a
  clean shutdown. A host that wants to report every plugin that failed to stop must collect the
  failures itself rather than rely on the stack.
- `asyncio.TaskGroup` already solves the n-simultaneous-failures problem in the standard
  library, and documents the solution: grouping into `BaseExceptionGroup`, cancellation
  subordinate to real errors, and two named escapes for `SystemExit`/`KeyboardInterrupt` and
  `GeneratorExit`. The pattern is available to any host that wants closed shutdown semantics.
- A failed stop needs a defined resting state. Home Assistant's `FAILED_UNLOAD` is explicitly
  non-recoverable, which makes the entry un-reloadable until restart — a decision, visible in
  the enum, that the host prefers a wedged plugin to an unknown one. Django's registry
  demonstrates the alternative: no defined state, `loading` left `True`, and
  `RuntimeError("populate() isn't reentrant")` on every subsequent attempt.
- Ordering a teardown hook's registration before the corresponding start-up work decides whether
  teardown runs after a failed start. Litestar registers `on_shutdown` first and therefore
  always runs it; aiogram emits startup outside the guarded block and therefore never runs
  shutdown; both are one-line consequences of where the registration sits.
- Signalling readiness before the last dependency is connected produces a genuinely degraded
  start. `AsgiFastStream` calls `task_status.started()` before `await self._start_broker()`, so
  the server is told start-up completed while brokers are still connecting.

## Sources

Every claim above carries its own link inline. This section names what was read.

Home Assistant:

- <https://github.com/home-assistant/core> — `homeassistant/config_entries.py`,
  `homeassistant/exceptions.py`, `homeassistant/helpers/entity_platform.py`,
  `homeassistant/helpers/event.py`, `pyproject.toml`
- <https://developers.home-assistant.io/docs/integration_setup_failures>

CPython:

- <https://github.com/python/cpython> — `Doc/library/asyncio-task.rst`, `Lib/asyncio/taskgroups.py`,
  `Lib/contextlib.py`
- <https://docs.python.org/3/library/asyncio-task.html#task-groups> ·
  <https://docs.python.org/3/library/contextlib.html#contextlib.AsyncExitStack> ·
  <https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack>

Other Python hosts:

- <https://github.com/Rapptz/discord.py> — `discord/ext/commands/bot.py`,
  `discord/ext/commands/errors.py`
- <https://github.com/django/asgiref> — `specs/lifespan.rst`
- <https://github.com/getsentry/sentry-python> — `sentry_sdk/integrations/__init__.py`
- <https://github.com/python-telegram-bot/python-telegram-bot> — `src/telegram/ext/_application.py`

Django:

- <https://github.com/django/django> — `django/__init__.py`, `django/apps/registry.py`,
  `django/core/exceptions.py`

FastStream:

- <https://github.com/ag2ai/faststream> — `faststream/_internal/application.py`,
  `faststream/app.py`, `faststream/asgi/app.py`, `faststream/exceptions.py`

Litestar:

- <https://github.com/litestar-org/litestar> — `litestar/_asgi/asgi_router.py`, `litestar/app.py`,
  `pyproject.toml`

Starlette:

- <https://github.com/encode/starlette> — `starlette/__init__.py`, `starlette/routing.py`

pytest:

- <https://github.com/pytest-dev/pytest> — `src/_pytest/config/__init__.py`

uvicorn:

- <https://github.com/encode/uvicorn> — `uvicorn/config.py`, `uvicorn/lifespan/on.py`,
  `uvicorn/server.py`

aiogram:

- <https://github.com/aiogram/aiogram> — `aiogram/dispatcher/dispatcher.py`,
  `aiogram/dispatcher/router.py`

Python packaging and PEPs:

- <https://peps.python.org/pep-0758/>

pluggy:

- <https://github.com/pytest-dev/pluggy> — `src/pluggy/_manager.py`

pydantic:

- <https://github.com/pydantic/pydantic> — `pydantic/plugin/_loader.py`
