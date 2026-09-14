---
status: accepted
date: 2026-09-14
ticket: "#103"
---

# A Bot runs once: the resting state after any stop is the same one, and a second `run()` is refused

A stop that fails leaves the Bot holding Plugins whose `__aexit__` did not finish, and the question
is what the object is afterwards. The field answers it badly and in two ways, both recorded in
[`docs/research/32`](../research/32-plugin-lifecycle-failure.md) and measured again in the clones:
Home Assistant defines the state and wedges the entry — `FAILED_UNLOAD` is marked non-recoverable,
so the config entry cannot be reloaded until a restart — while Django, celery, sanic and arq define
nothing, and each leaves a different kind of wreckage. celery's `TERMINATE` is identical after a
clean stop and a broken one; sanic never sets `is_started` back to `False`; arq's `_pool = None` is
the last statement of `close()`, so a raising `on_shutdown` leaves a live pool the worker believes
it owns; Django's `loading` stays `True` and every later `populate()` raises
`RuntimeError("populate() isn't reentrant")` for the life of the process.

We decided that **a Bot is composed, run once, and discarded**. `run()` and `serve()` may each be
entered exactly once per Bot object and a second entry raises, whatever the first one ended in — a
clean stop, a failed stop, a failed start. There is no recoverable/non-recoverable distinction to
draw because there is no second run to permit. Ten of the twenty-two application objects measured
refuse reuse this way; eleven leave it undefined, and one — dramatiq — silently doubles its thread
pool on a second `start()`
([`docs/research/42`](../research/42-the-lifecycle-contract-of-a-context-manager-unit.md) §3).

**The refusal takes httpx's shape**: one state field, and a different message for a Bot entered
twice and for a Bot entered after it has stopped, so the reader learns the lifecycle rule rather
than that one call failed
([`_client.py`](https://github.com/encode/httpx/blob/b5addb64f0161ff6bfe94c124ef76f6a1fba5254/httpx/_client.py#L1276-L1285)).
"Once it has been closed" is the half that teaches; anyio's `Each CancelScope may only be used for a
single 'with' block` is the runner-up, and teaches the correct shape instead of naming the broken
one.

**The resting state is reached before the failure is raised**, which is pytest's discipline and the
one thing in this area the field does well: `FixtureDef.finish` clears `cached_result` and
`_finalizers` and only then raises its group
([`fixtures.py`](https://github.com/pytest-dev/pytest/blob/3fd8675d6d798507c06cf9c60753be6d9d7b0e17/src/_pytest/fixtures.py#L1207-L1230)).
Every Plugin's `__aexit__` is attempted, the Bot drops its references, and the failure of
[ADR-0075](0075-a-lifecycle-failure-names-its-plugin-and-several-are-one-group.md) is raised last,
so nothing observes a half-torn-down Bot.

## Considered options

- *A public state enum with a `recoverable` flag, Home Assistant's shape* — rejected: it buys a
  second run nobody asked for, in exchange for a public enum, a branch in every caller and two paths
  through every test. A process that failed to stop is a process the host is about to replace.
- *Allowing a second run after a clean stop and refusing it after a failed one* — rejected as the
  same cost with a worse property: the rule an application has to remember then depends on how the
  previous run ended.
- *Leaving it undefined* — rejected on the measurement above; every host that did is the reason this
  decision exists.

## Consequences

- A test that needs a restart composes a second Bot; `TestBot`
  ([ADR-0046](0046-testbot-wraps-the-composed-bot.md)) wraps a composed Bot and never composes one,
  so this costs it a factory call and no API.
- The refusal is an exception rather than a Check: the check phase is side-effect-free and runs
  before anything has been entered ([ADR-0016](0016-three-phase-start-with-checks.md)), and a second
  entry is a broken contract, which is `ST-ERR-02`'s mechanism.
- A Plugin is therefore never asked to be re-enterable, which is what keeps `HasLifecycle` a bare
  asynchronous context manager with nothing bolted onto it
  ([ADR-0015](0015-plugin-contract-and-composition.md)).
