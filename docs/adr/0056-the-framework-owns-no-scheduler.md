---
status: accepted
date: 2026-09-09
ticket: "#30"
amends: [ADR-0015]
---

# The framework owns no scheduler: a periodic task is a Plugin's own lifecycle, and a calendar schedule is a process beside the bot

Scheduling fails both conditions of [ADR-0002](0002-core-scope-two-condition-test.md): most bots
never schedule anything, the ones that do want different things, and a schedule has nothing to do
with a chat protocol. Every peer agrees — discord.py alone keeps a scheduler in its base wheel and
it is interval and time-of-day only, while python-telegram-bot demoted `JobQueue` to an extra for
footprint, aiogram refused one outright, and hikari, FastStream and Litestar each pushed theirs into
a separate distribution
([`docs/research/26`](../research/26-schedule-reliability-and-probe-primitives.md) §4). We decided
that **the framework ships no scheduler, no cron parser, no extra and no Plugin for scheduling**,
because owning one means owning a cron dialect and a daylight-saving tail that a fifteen-year-old
project still ships fixes for, and because the two shapes a bot actually needs are already
expressible:

- **A periodic coroutine is an ordinary Plugin.** `HasLifecycle`
  ([ADR-0015](0015-plugin-contract-and-composition.md)) gives it a start and a stop inside the Bot's
  own `TaskGroup` ([ADR-0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md)), so it is
  cancelled by the same drain as everything else and needs nothing from us but the contract it
  already has.
- **A calendar schedule is a second process.** It publishes into whatever the application already
  runs, and the constraint that exactly one scheduler instance may run — "you'd end up with
  duplicate tasks" in Celery's words, "may execute one task N times" in taskiq's — stays with the
  scheduler that carries it. `ProcessProfile`
  ([ADR-0016](0016-three-phase-start-with-checks.md)) already distinguishes a process with no
  Transport, which is what such a process is.

**A documented recipe is a how-to page of the user documentation**, in the Diátaxis quadrant
[`documentation-style.md` §1](../documentation-style.md#1-document-types-and-where-they-live)
already names; it is not a new document type and it never lives under `docs/`. This decision owes
#26 two pages: *Run something periodically inside the bot* and *Run a scheduled job beside the bot*,
the second naming the single-instance hazard rather than hiding it.

## Considered options

- *A first-party interval-only Plugin, with a single-runner lease over `LockProvider`* — rejected:
  it is the cheapest honest version and still costs a component, a design document and a decision
  about missed fires, for something a fifteen-line Plugin already does; the lease matters only to
  the minority running more than one replica of a process that by
  [ADR-0005](0005-one-ingress-many-workers.md) already has exactly one WebSocket consumer.
- *A full scheduler behind a `croniter` extra* — rejected: the parser was declared abandoned by its
  own README at the end of 2024 and re-adopted only in March 2026, it carries open daylight-saving
  defects, and an unreleased change silently redefines existing expressions
  ([`docs/research/26`](../research/26-schedule-reliability-and-probe-primitives.md) §2). Shipping
  it makes its dialect our compatibility promise.
- *Our own field matcher, as arq wrote* — rejected: it trades a dependency for a class of bug we
  would then own, and arq needed three issues to get its timezone handling right.

## Consequences

- The examples of a generic Plugin in
  [ADR-0015](0015-plugin-contract-and-composition.md) are the plugins this project ships, and a
  scheduling bridge is not among them.
- Nothing in the distribution imports a cron parser, so the four default dependencies of
  [ADR-0041](0041-default-dependencies-and-one-extra-per-optional-library.md) are unchanged and no
  extra is added for scheduling.
