---
status: accepted
date: 2026-09-09
ticket: "#29"
amended-by: [ADR-0058]
---

# The set of log records is a documented contract checked against the code in both directions, and the framework never configures logging, ships no handler beyond `NullHandler` and offers no helper

An operator builds alerts and dashboards on log lines, so a renamed message or a moved level breaks
their tooling — and no surveyed project treats its records as anything it promises
([`docs/research/24`](../research/24-library-logging-design.md) §7), which is why every upgrade in
this ecosystem is a small gamble on the log. We decided to promise them, and to promise nothing
about configuration:

- **Every component document lists every record it can emit** — level, the constant message, the
  `extra` fields, and the condition that produces it. The message is a short human phrase, constant
  and unique within its logger, so a line is readable under a bare `basicConfig` and groupable in a
  structured pipeline without either being privileged. Adding a record, moving it between levels,
  or removing a field is a change to that document and a change to the public surface on the same
  terms as a name ([ADR-0043](0043-explicit-re-export-with-a-reference-page-as-the-public-list.md)),
  and a test checks the catalogue against the code **both ways**: a record with no row and a row
  with no record both fail.
- **One logger per component that logs, named `aiommbot.<term>`** in the glossary's snake case, with
  a `NullHandler` on `aiommbot` and no logger anywhere else; a component that emits nothing has no
  logger, as the `Event` component already states. The names are hand-chosen and are **not** module
  paths: [ADR-0040](0040-one-package-directory-per-import-rank.md) says a module path is not a
  documented import path, so deriving logger names from `__name__` would make a module split
  (`ST-MOD-09`) a breaking change for every operator's configuration. A guard test asserts that the
  loggers the framework creates are exactly the loggers the documentation names.
- **The framework changes no logging state.** No `basicConfig`, no `dictConfig`, no
  `captureWarnings`, no `setLevel` on any logger including our own root, no environment variable
  that configures logging, and no `setup_logging()`-style helper. The one thing that is not the
  library is the shipped command, which applies exactly the configuration the operator names in
  `--log-config` and touches nothing when the option is absent
  ([ADR-0058](0058-the-command-is-a-console-script-behind-the-click-extra.md)) — the prerogative
  stays with whoever starts the process. "The configuration of handlers is
  the prerogative of the application developer who uses your library", and every mechanism in the
  survey's right-hand column is a library doing something to state it does not own — uvicorn calling
  `dictConfig`, Celery hijacking the root logger, openai reading `OPENAI_LOG`, and the helper that
  discord.py's `run()` ends up calling for you. httpx is the only project that has *removed* such a
  mechanism.
- **The `NullHandler` means silence, deliberately.** It suppresses `logging.lastResort`, so an
  unconfigured process prints nothing rather than WARNING and above to `sys.stderr`. That is safe
  here because every serious failure also arrives programmatically — `Degraded`, `Dropped`,
  `DrainTimedOut` and `HandlerAbandoned` are Signals and `FatalError` is an exception — so nothing
  depends on a line the operator did not ask for, and `ST-LOG-03`'s reasoning applies to stderr as
  much as to a file. The documentation states it as plainly as aiohttp does.
- **Blocking handlers are documented, not solved.** The Cookbook instructs a library author to "be
  sure to document this (together with a suggestion to attach only `QueueHandlers` to your
  loggers)", and that is exactly the boundary: the documentation names our loggers and recommends a
  `QueueHandler`, the `QueueListener` and its thread belong to the application, and one executable
  `dictConfig` example carries the whole recommended shape. It also warns that
  `QueueHandler.prepare()` discards `exc_info` and `args` while leaving `extra` intact — one more
  reason every variable lives in `extra`.

## Considered options

- *Promise the logger names and the meaning of each level, and leave the strings free* — the
  ecosystem's position, rejected: it makes every `grep`-based alert a hostage of the next patch,
  and the requirement was a convention built once.
- *Ship a `QueueListenerHandler` convenience, as Litestar does* — rejected: it is eight lines of
  standard library and not chat-specific, so it fails the admission test of
  [ADR-0002](0002-core-scope-two-condition-test.md), and owning the listener's thread is owning the
  configuration.
- *No `NullHandler`, letting `lastResort` print WARNING and above* — the behaviour the Logging
  HOWTO calls "the best default": rejected because a library writing uninvited to another process's
  `sys.stderr` is what `NullHandler` exists to prevent, and a script that imports only
  `SyncMattermostClient` would find its own output polluted.
- *An opt-in helper on the model of `boto3.set_stream_logger`* — rejected: a second way to
  configure logging beside the standard one, and discord.py shows where the slope ends.

## Consequences

- `ST-DOC-08` carries the obligation to name every logger and the executable `dictConfig` example,
  `ST-LOG-08` the catalogue and `ST-LOG-10` the configuration ban; all three are checked by tests
  rather than by review.
- The framework is silent until configured, so the getting-started documentation configures logging
  before it starts a bot, not after.
