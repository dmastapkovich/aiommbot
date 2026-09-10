---
status: accepted
date: 2026-09-09
ticket: "#29"
---

# A record's level is decided by how often the fact happens and who needs it: nothing per delivery above DEBUG, INFO for lifecycle transitions only, one ERROR per escaped exception, and neither CRITICAL nor a custom level ever

Thirty components choosing levels by taste is how a log becomes unreadable, and the empirical split
shows which side gets complained about: httpx logs one INFO line per request, aiogram one per
update — the subject of an open issue — while httpcore, urllib3, openai, botocore, SQLAlchemy,
discord.py and Litestar say nothing at INFO on a normal path
([`docs/research/24`](../research/24-library-logging-design.md) §7). We decided a rule with two
questions in it — how often, and for whom:

- **DEBUG** — everything that happens once per delivery or once per request: the dispatch of an
  event with its kind, outcome and duration; one line per HTTP attempt; a state transition; a
  routing decision. No exceptions: a per-delivery record above DEBUG is what makes a bot's log
  unusable at the volume `typing` and `status_change` events arrive in.
- **INFO** — only transitions whose frequency is bounded by the lifetime of the process or of a
  connection: the Bot started and stopping, connected, disconnected, resumed, resynced, Drain
  finished. Each sits **beside** the Signal for the same fact rather than replacing it, and this is
  the one place in the design where one fact travels two ways on purpose — a Signal is for a
  program, a line is for a person. One further record belongs here: a single start-up line carrying
  the composition — version, transports, plugins, `ProcessProfile` — because it is the first thing
  any incident asks for and it happens once in a process's life.
- **WARNING** — a degradation the operator can act on that the process survived: a retry scheduled,
  a drop under an `OverflowPolicy`, an observer that raised, a synchronous Handler abandoned at
  Drain, the loss window of a resync, a token refreshed after an authentication failure.
- **ERROR** — exactly once per escaped exception, from the ErrorBoundary
  ([ADR-0021](0021-core-error-boundary.md)), and that is also the only place in the framework
  allowed to pass `exc_info`: a traceback ends in `str(exc)`, so it is itself a content channel
  ([`docs/research/12`](../research/12-error-boundary-conventions.md)), and one failure that
  produced four tracebacks on its way up would be four leaks and three duplicates. Everywhere else
  records `error_type`.
- **CRITICAL is never used, and no custom level is ever added.** A process dying is the
  supervisor's to report ([ADR-0021](0021-core-error-boundary.md)). A custom level costs an
  application a `dictConfig` it cannot write portably and lands in a coarse bucket on both severity
  bridges — the OpenTelemetry SDK's `_STD_TO_OTEL` maps exactly the five standard levels
  ([`docs/research/24`](../research/24-library-logging-design.md) §5) — which is why httpx removed
  the one it had.

## Considered options

- *One INFO line per dispatched event and per API call, as httpx, Celery and aiogram do* —
  rejected: it is the practice with an open complaint against it, and a bot receives presence and
  typing events by the thousand.
- *Nothing below WARNING at all* — rejected: it leaves an operator with no trail to debug from,
  which is the opposite of the requirement.
- *INFO for transitions but no start-up composition line* — rejected: an incident is usually read
  from yesterday's log rather than from a live process, where `bot.routes()` and `bot.stats()`
  cannot be called.
- *Silence at INFO, with the application subscribing to Signals to print "connected"* — rejected:
  every application would write the same subscriber, and a Signal is not a substitute for a line
  when the reader is a person.

## Consequences

- Three mechanisms hold the rule instead of review: `semgrep` forbids `logger.critical` anywhere
  and `logger.exception` or `exc_info` outside the ErrorBoundary's module; a test feeds a
  `TestBot` a hundred events with the logger at INFO and asserts that no record is produced; and
  the record catalogue of [ADR-0053](0053-log-records-are-a-documented-contract.md) is checked
  against the code in both directions.
- A level meaning is part of what the documentation promises, so moving a record between levels is
  a documented change (ADR-0053) rather than a patch-level detail.
