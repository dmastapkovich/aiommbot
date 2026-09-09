---
status: accepted
date: 2026-09-09
ticket: "#25"
---

# A bot is tested by wrapping the composed `Bot`, and the toolkit offers no second way to compose one

[ADR-0019](0019-handler-parameter-resolution-rules.md) put the only override API in
`aiommbot.testing` as `TestBot(bot).override(...)` without saying where that `bot` comes from. We
decided that **it comes from the application's own composition, unchanged**: `TestBot` takes a
composed `Bot` and adds four things to it — typed overrides by key applied before the start,
an asynchronous context manager that runs the check and start phases
([ADR-0016](0016-three-phase-start-with-checks.md)) with no Transport in the list, `feed`, which
hands one Event to the Dispatcher and returns the typed `Outcome`
([ADR-0013](0013-type-driven-routing-with-a-typed-dispatch-outcome.md)), and typed records of what
the run produced — outcomes, replies sent through the recording `ReplyChannel`
([ADR-0036](0036-reply-slot-as-a-second-type-parameter-over-a-core-owned-reply-channel.md)) and
Signals raised ([ADR-0017](0017-typed-async-lifecycle-signals.md)). A convenience constructor that
built a `Bot` from an adapter and a plugin list would be a second composition path to hold in
parity with the real one, and the composition is exactly what a bot's test exists to exercise.

## Considered options

- *`TestBot(adapter=…, plugins=[…])`* — rejected above: it spares the test three lines and
  introduces a shape whose divergence from the real composition is invisible until production.
- *Both constructors* — rejected: it is the same second path with the first one also available, so
  the divergence becomes a matter of which the reader happened to use.
- *A test double of the `Bot` itself* — rejected: the Bot is the composition root
  ([ADR-0015](0015-plugin-contract-and-composition.md)), so doubling it removes from the test the
  ordering, the checks and the resolution plans that are the most common thing to get wrong.

## Consequences

- The check phase runs in every bot test, so an unresolvable handler parameter, an unreachable
  handler or a missing plugin dependency fails the suite rather than the deployment
  ([ADR-0016](0016-three-phase-start-with-checks.md),
  [ADR-0013](0013-type-driven-routing-with-a-typed-dispatch-outcome.md)).
- `feed` is where the Transport would be, so a bot test needs no Transport and a Transport test
  needs no `TestBot`: `FakeMattermost`'s socket port drives the real WebSocketTransport
  ([ADR-0045](0045-one-stateful-fake-mattermost-is-the-only-platform-double.md)) when what is under
  test is the transport itself.
- Overrides are applied before the start and never after, which keeps
  [ADR-0019](0019-handler-parameter-resolution-rules.md)'s rule that a resolution plan compiled at
  check time is the one that runs.
- A question about routing that needs no run — whether an Event reaches a Handler through arbitrary
  filters — is answered by `assert_matches(event, handler)` instead, which start-up cannot decide
  ([ADR-0013](0013-type-driven-routing-with-a-typed-dispatch-outcome.md)).
