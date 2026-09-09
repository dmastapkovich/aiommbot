---
status: accepted
date: 2026-09-09
ticket: "#30"
amends: [ADR-0002, ADR-0016, ADR-0024, ADR-0041, ADR-0053]
---

# The framework ships one command, `aiommbot`, as a console script behind the `click` extra; it starts no server and configures only the logging the operator names

A bot is started by a module the application writes, and `run()` and `serve()`
([ADR-0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md)) are all that needs. What a
module cannot conveniently be is the check-only entry point
[ADR-0016](0016-three-phase-start-with-checks.md) requires "for CI and for operators". We decided to
ship a command for it, and to keep it the smallest thing that can be called one — arq's whole CLI is
a hundred lines
([`docs/research/25`](../research/25-cli-entry-points-and-what-clis-configure.md) §2):

- **Two commands.** `aiommbot check <module>:<attr>` runs compose and check and exits non-zero on
  the full list of error-severity Checks; `aiommbot run <module>:<attr>` resolves the same import
  string and calls `run()`. Shared options are `--app-dir`, `--log-config` and `--version`. There is
  no third command and no plugin-contributed one.
- **`click`, in an extra of that name**, joining the table of
  [ADR-0041](0041-default-dependencies-and-one-extra-per-optional-library.md) under its rule.
  `click` 8.5.0 is one 125 KB wheel with **no runtime dependencies at all**, against seven wheels
  and 1.72 MiB for `typer`, of which 69% is `pygments` for colour a two-command tool does not need; and
  since typer vendored click, depending on click no longer conflicts with a consumer of typer
  ([`docs/research/25`](../research/25-cli-entry-points-and-what-clis-configure.md) §3).
- **The console script is always installed, so the guard is ours.** An extra cannot gate an entry
  point — pip's maintainers state that "entry points are not conditional", and the wrapper imports
  the named module before any code of ours runs (same note, §1).
  `aiommbot = "aiommbot.__main__:main"` therefore guards its own import and raises
  `MissingExtraError` (`ST-MOD-08`), which `main` prints to `stderr` and turns into exit 1 — an
  operator gets the install line, not a traceback. This is the one place `MissingExtraError` is
  raised outside a constructor.
- **It starts no server.** Nothing in the distribution runs HTTP
  ([ADR-0002](0002-core-scope-two-condition-test.md)); the Webhook's ASGI application and the Health
  Plugin's ([ADR-0061](0061-health-is-a-generic-plugin-over-application-supplied-checks.md)) are
  handed to a server the application runs. A `serve` command would mean uvicorn as a dependency.
- **It touches `sys.path` only when told to.** Eight of the nine surveyed CLIs mutate it on every
  run; uvicorn is the exception because its insert is guarded, and `--app-dir` is the same guard
  here.
- **It configures only the logging the operator names.** With no `--log-config` the command changes
  no logging state whatsoever, exactly as Litestar's does; with `--log-config <file>` it calls
  `logging.config.dictConfig` once, which is faststream's shape. The command writes its own output
  with `print`, creates no logger and appears in no record catalogue
  ([ADR-0053](0053-log-records-are-a-documented-contract.md)).

## Considered options

- *No command at all, as every peer bot framework does* — rejected: it leaves ADR-0016's
  check-only entry point as a two-line script every project writes for itself, and CI is where a
  composition error is cheapest to find.
- *`python -m aiommbot` with `argparse` and no console script* — rejected although it costs nothing:
  it hides the tool from `--help` discovery and from shell completion, and `argparse` has no
  completion of any kind (same note, §3.3).
- *`typer`* — rejected on the fourteen-fold download cost for a two-command tool, and because
  `typer` is classified Beta while `click` is Production/Stable.
- *`basicConfig` by default with an opt-out flag, as taskiq and dramatiq do* — rejected: it makes
  the framework take the prerogative ADR-0053 refuses. `--log-config` keeps the configuration with
  whoever starts the process.
- *A plugin-contributed command set, as Litestar's entry-point group allows* — rejected for 0.5.0:
  entry-point discovery is deliberately out
  ([ADR-0015](0015-plugin-contract-and-composition.md)), and two commands do not need an extension
  mechanism.

## Consequences

- `ST-LOG-10` gains its only limit: the shipped command may apply the configuration named on the
  command line, and nothing else. Its semgrep rule carries one path exception for the command's
  module, and the smoke import test is joined by one asserting that `aiommbot check` with no
  `--log-config` leaves every logger's level and handlers untouched.
- `ST-MOD-08` gains its only limit: the entry point of the console script raises `MissingExtraError`
  where a constructor would.
- The command's own behaviour — the import-string grammar, the exit codes, the `--version` output —
  is a part of `docs/design/components/bot.md`, beside `run()` and `serve()`.
