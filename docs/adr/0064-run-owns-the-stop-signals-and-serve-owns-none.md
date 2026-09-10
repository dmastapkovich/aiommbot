---
status: accepted
date: 2026-09-10
ticket: "#40"
amends: [ADR-0031]
---

# `run()` installs the SIGINT and SIGTERM handlers on the loop it owns, `serve()` installs none, and a second signal ends the stop at once

`asyncio.Runner` installs a handler for **SIGINT only**, and nothing in the standard library
installs one for SIGTERM, so an asyncio bot under a container orchestrator dies on the default
disposition and the Drain never starts
([`docs/research/29`](../research/29-kubernetes-fields-a-drain-depends-on.md) §4). A grace period is
worth nothing to a process that never learns the period has begun. We decided:

- **`run()` owns both signals**, through `loop.add_signal_handler`, which is the only registration
  documented as "allowed to interact with the event loop"; each begins the one bounded stop phase of
  [ADR-0063](0063-the-process-declares-its-shutdown-budget-and-the-bot-bounds-the-stop.md). `run()`
  is a process boundary rather than a Face
  ([ADR-0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md)), and owning the process's
  signals is what a process boundary is for. It takes SIGINT over from the `Runner` deliberately, so
  that Ctrl-C and a `kill` take the same path instead of two.
- **`serve()` installs nothing.** It exists to embed a Bot in a loop somebody else runs, and that
  somebody already has a shutdown path — uvicorn captures SIGINT and SIGTERM with `signal.signal` on
  every run (same note, §10). Two owners of one signal is how a Drain is cancelled halfway.
- **A second signal collapses `stop_timeout` to zero**: the remaining tasks are cancelled at once
  and `DrainTimedOut(count)` reports what was dropped. The platform gives the second signal no
  meaning of its own — Kubernetes sends one and then SIGKILL, and `asyncio.Runner`'s second-Ctrl-C
  escape hatch is SIGINT-only — so the meaning is ours to define, and an operator who signals twice
  has said "now". A third changes nothing.
- **The handler is idempotent**, because a kubelet restart "retries from the start including the
  full original grace period" (same note, §9) and the same signal can arrive twice for one
  termination.
- **Where `loop.add_signal_handler` is not implemented**, `run()` falls back to `signal.signal` with
  a handler that only schedules the stop through `loop.call_soon_threadsafe`; a Python signal
  handler runs between bytecodes and may not touch the loop directly (same note, §4). The fallback
  is documented, not silent.

## Considered options

- *Leaving both signals to the application* — rejected: every bot would write the same ten lines,
  and the one that forgets is killed at the end of the budget with nothing in its log to say why.
- *`signal.signal` always, as uvicorn does so it can restore the previous handlers* — rejected: the
  restore is what a server embedded in someone else's process needs, and `serve()` gets the same
  property by installing nothing at all.
- *Leaving SIGINT to `asyncio.Runner`* — rejected: the Runner cancels the main task and raises
  `KeyboardInterrupt`, which reaches the stop phase through `finally` rather than through the stop
  phase's own entry, so a development Ctrl-C would exercise a different path from a production stop.
- *A configurable signal set* — rejected: a knob for a value only a container image's `STOPSIGNAL`
  changes, and the deployment view says to leave that at SIGTERM instead.
- *Escalating only on SIGINT, as uvicorn does* — rejected: under an orchestrator SIGTERM is the only
  signal an operator can send, so tying the escape hatch to SIGINT leaves them nothing but an
  uncatchable kill, which writes nothing at all.

## Consequences

- The signal handlers, the fallback and the second-signal rule are parts of `bot.md`.
- A container whose entry point is the shell form never receives the signal — `/bin/sh -c` "does not
  pass signals" — so [§7](../design/07-deployment-view.md) makes the exec form a requirement on the
  host rather than a style preference.
