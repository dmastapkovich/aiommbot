---
status: accepted
date: 2026-09-14
ticket: "#103"
amends: [ADR-0016, ADR-0023, ADR-0063]
---

# A Plugin that fails to start ends the start and enters the same bounded stop phase a stop signal enters, and no lifecycle failure is ever retried

[ADR-0071](0071-plugins-start-in-list-order-and-declare-no-dependency-on-each-other.md) fixed the
order lifecycles are entered in and reversed on the way out, and nothing said what happens when one
of them raises. The mechanism that answers half of it is in the standard library —
`contextlib.AsyncExitStack` unwinds a partial start and documents the promise
([`docs/research/32`](../research/32-plugin-lifecycle-failure.md)) — but the failure the field
actually ships is a *second* stop path that guarantees less than the first: arq's `run()` unwinds
while its `async_run()` never calls `close()` at all, and hikari's `run()` unwinds while its bare
`start()` coroutine leaves the bot wedged at `is_alive == True`. Two entry points with two answers
is how this goes wrong, and we have exactly two.

- **A Plugin raising from `__aenter__` ends the start.** Composition and the check phase have
  already passed ([ADR-0016](0016-three-phase-start-with-checks.md)), so the failure is a dependency
  that was reachable when it was asked and is not now.
- **The Bot then runs the stop phase — the same one a stop signal enters**, over whatever is
  started: the Transports that started, then the Plugins that entered, in the reverse of the order
  they entered, under the one `asyncio.timeout` of
  [ADR-0063](0063-the-process-declares-its-shutdown-budget-and-the-bot-bounds-the-stop.md)'s
  `stop_timeout`. There is no second unwind path and no second deadline. aiohttp is the one surveyed
  host that states this in the code rather than leaving it to the caller — `# If an exception occurs
  in startup, ensure cleanup contexts are completed`
  ([`web_app.py`](https://github.com/aio-libs/aiohttp/blob/9e08ba02abe573ce9e4cc541d4e3c3646adb43a7/aiohttp/web_app.py#L353-L362)).
- **`run()` and `serve()` give the identical guarantee.** The only difference between them stays the
  signal handlers of [ADR-0064](0064-run-owns-the-stop-signals-and-serve-owns-none.md).
- **The phase is entered from a `try` that opens before the first lifecycle does**, which is the
  one-line registration order that decides whether teardown runs at all: Litestar registers first
  and always runs it, aiogram emits start-up outside the guard and never does (`docs/research/32`).
- **No lifecycle failure is retried.** No backoff, no attempt counter, and no "not ready yet" member
  of any taxonomy. Of every host surveyed only Home Assistant retries a plugin start, only through
  the one member that means the dependency is merely absent, and a taxonomy without that member buys
  nothing but a name (`docs/research/32`). A Plugin that wants to survive an absent dependency
  retries inside its own lifecycle, where it knows what it is waiting for.

## Considered options

- *`AsyncExitStack` as the whole mechanism, Litestar's shape* — rejected: it gives the unwind and
  not the report ([ADR-0075](0075-a-lifecycle-failure-names-its-plugin-and-several-are-one-group.md)),
  and the stack's unwind is not the stop phase, so a failed start would take a path with a different
  order, a different deadline and different Signals from every other stop.
- *A typed start-up taxonomy whose members differ by host reaction, Home Assistant's shape* —
  rejected: its four members map to four reactions and we have one. What keeps such a set closed is
  that a new error joins by inheriting the member whose reaction it wants; with a single reaction
  there is nothing to inherit.
- *Leaving a partially started Bot standing so the application can decide* — rejected: it is
  Django's registry, whose `loading` flag is left `True` with no path back (`docs/research/32`), and
  [ADR-0076](0076-a-bot-runs-once.md) closes the same question from the other side.

## Consequences

- The stop phase runs over a Transport list that may be empty and publishes the stop Signal for a
  Bot that never published the started one, so it is written to tolerate both.
- [ADR-0016](0016-three-phase-start-with-checks.md)'s third phase and
  [ADR-0023](0023-websocket-gateway-resilience.md)'s Drain paragraph said plugins were ordered
  topologically, which ADR-0071 withdrew; both now state the list order this decision stops on.
- The cases belong to the plugin-lifecycle conformance suite, the fourteenth of
  [ADR-0047](0047-a-conformance-suite-per-core-seam.md), rather than to a new mechanism.
