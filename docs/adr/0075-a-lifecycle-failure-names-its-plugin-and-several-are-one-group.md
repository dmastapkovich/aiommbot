---
status: accepted
date: 2026-09-14
ticket: "#103"
amends: [ADR-0031]
---

# A lifecycle failure names the Plugin it belongs to, and several failures are one group rooted at `AiommbotError`

[ADR-0074](0074-a-failed-start-enters-the-same-stop-phase-and-never-retries.md) fixed *when* the
stop phase runs and [ADR-0016](0016-three-phase-start-with-checks.md) fixed that problems are
reported together. What reaches the caller was still open, and sixty-four failure paths across
eighty-six projects say the field gets it wrong in one specific way: it names the unit on the way up
and names nothing on the way down — eight wrapper classes exist and **none of them is on a stop
phase** ([`docs/research/41`](../research/41-reporting-which-lifecycle-unit-failed.md)).

Each part of the decision below is taken from the project that already carries it.

- **The stop phase drives the Plugins itself, in a reversed loop, and does not use
  `contextlib.AsyncExitStack`.** The stack rebuilds `exc_details` inside its own unwind, so a unit
  is told about its neighbour's failure rather than about the cause of the shutdown, one suppression
  blinds every unit below it, and it never builds a group
  ([`docs/research/42`](../research/42-the-lifecycle-contract-of-a-context-manager-unit.md)). The
  loop is **aiohttp's** `_on_cleanup`: every unit's `__aexit__` is attempted in reverse whatever
  failed before it, and the failures are collected.
- **One failure is raised bare; several become one group.** Also aiohttp's, and it is what
  [ADR-0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md) already requires of us in
  the opposite direction.
- **Every collected failure is a `PluginLifecycleError` naming its Plugin and its phase**, with the
  Plugin's own exception as `__cause__`. The wrapper is **discord.py's** `ExtensionFailed(name=…,
  original=…)`, which is a start-phase class there and has no counterpart on any stop path anywhere
  — so moving it is ours, and the reason is measured: **pytest** puts the unit's name in the group's
  message and then splices the single-failure case straight through, so the name survives only when
  two units fail at once. With the identity on the member instead, collapsing an aggregate of one
  costs nothing. The phase marker is the defect discord.py has and we do not want: it raises the
  identical class for a module that failed to import and a `setup()` that raised.
- **The group is `StopPhaseError(ExceptionGroup[PluginLifecycleError], AiommbotError)`.** Rooting an
  aggregate at the library's own error base is **dishka's** `ExitError`, the only one in the corpus,
  and it is half-built: without `derive` any `except*` narrower than the base rebuilds it as a plain
  `ExceptionGroup` and loses the mixin, which CPython's own test suite demonstrates. **hypothesis**
  has the correct form, `derive` returning `type(self)(self.message, excs)`. Measured on 3.12 and
  3.14, `derive` alone suffices while the constructor keeps `(message, excs)`, so the price is one
  method (`docs/research/41` §5).
- **A Plugin's `__aexit__` receives the real cause**, so a Plugin can see why it is being torn down.
  **dishka** is the one host that does this and pays for it by making its units generators, which
  cannot suppress; ours are context managers and pay nothing. **A `True` return does not suppress**:
  the Bot discards it, which is what aiohttp does, and a Plugin vetoing what it was told about is
  already refused by [ADR-0073](0073-what-a-plugin-may-not-do.md).

## Considered options

- *`AsyncExitStack` as the whole mechanism* — rejected on the measurement above: it is the right
  primitive for unwinding and the wrong one for reporting, and litestar inherits both properties
  without restating either.
- *A raw group, dishka's shape, with the Plugin named only in a log record* — rejected: it is what
  eleven of the eleven aggregating paths do, and none of them lets a caller read the identity. The
  three that came closest each had it in hand at the catch site and discarded it at the raise site.
- *A typed outcome instead of an exception, as `ST-ERR-04` asks for reporting all of something* —
  rejected: the stop phase is also entered through `__aexit__`, which has no return value to carry
  one, so the failure would need two representations and `ST-ERR-05` forbids that.
- *`CleanupError`'s shape, a `RuntimeError` with an `exceptions` property* — rejected: aiohttp wrote
  it before PEP 654 and never migrated, so `except*`, `split()` and `subgroup()` do nothing with it.

## Consequences

- `ST-ERR-04` reports every failure through a typed outcome; an exception group is the third
  cardinality it did not name, and its limits now say so.
- The cases belong to the plugin-lifecycle conformance suite of
  [ADR-0047](0047-a-conformance-suite-per-core-seam.md): one Plugin failing, two failing, a failure
  during the unwind of a failed start, and a `True` return that changes nothing.
- The exception classes are parts of `bot.md`, beside the check-failure catalogue of
  [ADR-0072](0072-duplicate-names-are-refused-and-every-refusal-is-one-catalogue-row.md).
