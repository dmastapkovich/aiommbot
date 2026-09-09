# 25. Process entry points and the cost of a shipped CLI

**Question.** When a library ships a command-line entry point of its own: what does the packaging
machinery guarantee about a `[project.scripts]` console script whose imports live behind an optional
dependency, what do peer framework CLIs actually contain, what do they configure on the
application's behalf, and what does an argument-parsing dependency cost?

Gathered for GitHub issue #93. The question is forced by two decisions that already
exist: every optional library is an Extra
([ADR-0041](../adr/0041-default-dependencies-and-one-extra-per-optional-library.md)), and the
framework changes no logging state
([ADR-0053](../adr/0053-log-records-are-a-documented-contract.md)). A CLI collides with both.
[`docs/research/08`](08-peer-responsibility-boundaries.md) records *where* peers put a CLI;
[`docs/research/24`](24-library-logging-design.md) §7 records that taskiq, arq and Dramatiq push
logging configuration into their CLI rather than their import. Neither records what a CLI costs or
what else it does.

Findings only. Sources are primary — `packaging.python.org`, `peps.python.org`, `docs.python.org`,
PyPI JSON metadata, and project source read at a pinned tag on `raw.githubusercontent.com` — read on
2026-09-09. Anything a primary source did not confirm is marked **[unverified]**.

## 1 A console script cannot be hidden behind an Extra

### 1.1 What the specification promises

An entry point in the `console_scripts` group is a build-time declaration and an install-time
artefact. The
[entry points specification](https://packaging.python.org/en/latest/specifications/entry-points/)
states that `mycmd = mymod:main` "would create a command `mycmd` launching a script like this:
`import sys` / `from mymod import main` / `sys.exit(main())`". The declaration is recorded in
`entry_points.txt` inside the distribution's `*.dist-info` directory; the wrapper is a separate file
the installer writes into the scripts directory at install time. The referenced object "points to a
function which will be called with no arguments"; its return value becomes the process exit code and
`None` is equivalent to `0`. `console_scripts` and `gui_scripts` differ only on Windows, where the
first is attached to a console and may use the standard streams and the second may not.

[PEP 621](https://peps.python.org/pep-0621/) defines `[project.scripts]` as the `console_scripts`
group with an object reference as the value, and requires a build back-end to raise an error if
`[project.entry-points.console_scripts]` is also declared. The
[`pyproject.toml` specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
documents three tables — `[project.scripts]`, `[project.gui-scripts]`, `[project.entry-points]` —
each taking a plain object reference. **No table, key or syntax makes an entry point conditional.**

### 1.2 The extras suffix is a dead letter

The old `name = module:func [extra1,extra2]` form is still described by the specification, which
requires readers to parse the brackets — and then says: "Using extras for an entry point is no
longer recommended. Consumers should support parsing them from existing distributions, but may then
ignore them. New publishing tools need not support specifying extras." The stated reason is that
the mechanism "was tied to setuptools' model of managing 'egg' packages, but newer tools such as pip
and virtualenv use a different model".

The authoritative statement that this cannot work lives in
[pypa/pip#9726](https://github.com/pypa/pip/issues/9726), "Console_scripts entrypoints hidden behind
extras are always installed", opened 2021-03-22 by chrisburr and closed. pip maintainer pradyunsg:
"I don't believe console scripts can be specified this way, and the fact that setuptools does not
error out on such input is a bug in setuptools IMO. What Python packaging calls 'extras' is really
optional additional dependencies, and *not* extra functionality. … It is not possible to specify
conditional entry points, as you're trying to do here; because entry points are not conditional."
Maintainer uranusjr adds that the notation "was never standard, and never adopted by pip (or any
other tools except setuptools), so that `[bar,baz]` part currently has no semantic meaning".
`importlib.metadata.EntryPoint` still parses the suffix and exposes it as an `extras` list, and the
value has no effect on installation
([CPython source](https://raw.githubusercontent.com/python/cpython/main/Lib/importlib/metadata/__init__.py)).

[pypa/packaging.python.org#757](https://github.com/pypa/packaging.python.org/issues/757) is open and
asks exactly how to declare an entry point that should only load when a given extra is installed;
the specification was not changed to answer it. [PEP 771](https://peps.python.org/pep-0771/),
*Default Extras for Python Software Packages*, remains Draft as of September 2026 and governs which
extras install by default, not entry points.

Measured rather than quoted **[unverified]**: `uv_build` 0.11.24, `setuptools` 84.0.0 and
`hatchling` 1.32.0 each accept `epdemo = "epdemo.cli:main [cli]"` in `[project.scripts]` with no
error, no warning and no deprecation notice, and write the bracket suffix verbatim into
`entry_points.txt`. Installing the resulting wheel with pip 26.2.1 and with uv 0.11.24 *without* the
`cli` extra still creates the script; running it prints a `ModuleNotFoundError` traceback naming the
wrapper's own `from epdemo.cli import main` line and exits 1.

### 1.3 Which means the guard is the library's job

Because the wrapper imports the target module unconditionally, the guard has to live in the module
the entry point names. The templates confirm the timing: pip's `PipScriptMaker.script_template` and
[pypa/installer](https://raw.githubusercontent.com/pypa/installer/main/src/installer/scripts.py)
both place `from <module> import <func>` at module top level, so it runs on every invocation before
any function body does; only
[distlib on master](https://raw.githubusercontent.com/pypa/distlib/master/distlib/scripts.py) defers
the import into the `if __name__ == '__main__':` block, and released distlib 0.3.9 does not.

Four shapes are in use.

| Project | Entry point | Guard | What the user sees without the extra |
|---|---|---|---|
| httpx | `httpx = "httpx:main"` | `try: from ._main import main` / `except ImportError:` in `httpx/__init__.py` | a two-line hint naming `pip install 'httpx[cli]'`, exit 1 |
| FastAPI | `fastapi = "fastapi.cli:main"` | `try: from fastapi_cli.cli import main` / `except ImportError: cli_main = None` | a printed message *and* a `RuntimeError` naming `pip install "fastapi[standard]"` |
| Typer | `typer = "typer.cli:main"` | none | cannot happen — every dependency is unconditional |
| uvicorn | `uvicorn = "uvicorn.main:main"` | none | cannot happen — `click` and `h11` are core dependencies |

[httpx](https://raw.githubusercontent.com/encode/httpx/master/pyproject.toml) is the closest
precedent to a library gating its own command: one console script, a `cli` extra pinning
`click==8.*`, `pygments==2.*` and `rich>=10,<15`, and a fallback `main()` that prints "The httpx
command line client could not run because the required dependencies were not installed. Make sure
you've installed everything with: pip install 'httpx[cli]'" before `sys.exit(1)`. Note where the
guard sits: `httpx/_main.py` imports click, pygments and rich unguarded at module top level, and
[`httpx/__init__.py`](https://raw.githubusercontent.com/encode/httpx/master/httpx/__init__.py) —
the module the entry point actually names — carries the `try`/`except`.

[FastAPI](https://raw.githubusercontent.com/fastapi/fastapi/master/fastapi/cli.py) splits the CLI
into a separate distribution and keeps the console script in the base package: `fastapi-cli`
declares no `[project.scripts]` of its own, so the `fastapi` command always comes from `fastapi` and
delegates at run time.

Two adjacent patterns are worth recording because they degrade instead of failing.
[black](https://raw.githubusercontent.com/psf/black/main/src/black/handle_ipynb_magics.py) uses
`importlib.util.find_spec` and emits a warning — "Skipping .ipynb files as Jupyter dependencies are
not installed. You can fix this by running ``pip install "black[jupyter]"``" — because the missing
extra removes one capability rather than the whole command.
[pandas](https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/compat/_optional.py)
centralises the same idea in one helper, `import_optional_dependency`, which re-raises `ImportError`
with a formatted install instruction or returns `None`.

Build back-ends make no difference here.
[hatchling](https://hatch.pypa.io/latest/config/metadata/) documents the three tables as straight
PEP 621 pass-through with no conditional feature;
[`uv_build`](https://docs.astral.sh/uv/concepts/build-backend/) passes them through as well and its
only relevant limitation is that it "currently only supports pure Python code";
[setuptools](https://setuptools.pypa.io/en/latest/userguide/entry_point.html) documents only that
"installers like pip create wrapper scripts around the function(s) being invoked".

## 2 What nine peer CLIs actually contain

Versions are the latest on PyPI on 2026-09-09; every file was read at the matching tag. Line counts
are measured over the CLI implementation files named in the Sources and are arithmetic over the
files, not a figure any source publishes **[unverified]**.

| Project | Version | Parser | How the parser arrives | Commands | Lines |
|---|---|---|---|---|---|
| arq | 0.28.0 | click | core dependency | 1 | 100 |
| dramatiq | 2.2.1 | argparse | stdlib | 1 | 708 |
| fastapi-cli | 0.0.32 | typer | core dependency | 2 | 986 |
| litestar | 2.24.0 | click + rich-click | core dependencies | 4 + 2 groups | 1223 |
| faststream | 0.7.5 | typer | **`cli` extra** | 4 | 1392 |
| taskiq | 0.12.6 | argparse | stdlib | 2, from an entry-point group | 1677 |
| uvicorn | 0.52.4 | click | core dependency | 1 | 1923 |
| celery | 5.6.3 | click ×4 packages | core dependencies | 18 | 3818 |
| sanic | 25.12.1 | argparse | stdlib | 6 forms, no subparsers | 4075 |

Four use click, two typer, three the standard library. **faststream is the only one of the nine
whose CLI dependency is optional**: its PyPI metadata gates `typer` and `watchfiles` on
`extra == "cli"`, and
[`faststream/__main__.py`](https://raw.githubusercontent.com/ag2ai/faststream/0.7.5/faststream/__main__.py)
raises `ImportError` with an install instruction when the import fails.

### 2.1 What they configure on the application's behalf

This is the column that matters, because each entry is a decision a library-level API would never
take.

| Project | Logging | Event loop | `sys.path` | Signals | Other |
|---|---|---|---|---|---|
| uvicorn | 32-line `dictConfig` literal applied from `Config.__init__`, so also in library use; `--log-config`, `--log-level`; adds a `TRACE` level | `LOOP_FACTORIES` table returning `uvloop.new_event_loop`, no policy | only with `--app-dir` | `signal.signal` for SIGINT, SIGTERM, SIGBREAK | `--env-file` via python-dotenv; forks for `--reload` and `--workers` |
| faststream | none; `dictConfig` exactly once and only for `--log-config`; `--log-level` goes through the app object | `loop_factory` passed to `anyio.run`, no policy | `--app-dir`, defaulting to `.` | `add_signal_handler`, falling back to `signal.signal` | `warnings.filterwarnings` on `ImportWarning` |
| litestar | none at all in the CLI | none | `sys.path.append` | none | writes `LITESTAR_APP`, `LITESTAR_DEBUG`, `LITESTAR_PDB`; loads `.env`; re-execs uvicorn as a subprocess |
| taskiq | `basicConfig` in the parent and again in a spawned child; scheduler also `setLevel` on `taskiq` | `asyncio.set_event_loop` with uvloop from the `uv` extra | cwd and `--app-dir` | three, in two places | `set_start_method("spawn")` on macOS |
| arq | unconditional `dictConfig` with a 9-line default touching only the `arq` logger | none | unconditional `sys.path.append(os.getcwd())` | none in the CLI | `--custom-log-dict` |
| dramatiq | `basicConfig` in parent and every child unless `--skip-logging` | none | `--path`, default `.` | three | reassigns `sys.stdout` and `sys.stderr` unconditionally; silences `pika` |
| celery | hijacks the **root logger** by default; `captureWarnings(True)` | none | two places | six | exports `CELERY_LOG_*`; double fork for `--detach`; patches concurrency before importing the CLI |
| fastapi-cli | only its own named logger, with `propagate = False`; reimplements uvicorn's config as a 41-line literal when stdout is a tty | delegated to uvicorn | two places | delegated | five labelled discovery sources |
| sanic | `dictConfig` in the `Sanic` constructor, not the CLI | **the only one installing a global `asyncio` event-loop policy** | `sys.path.append` | forks and handles SIGHUP for daemon mode | no `--log-level` or `--log-config` at all |

Three counts follow. **Two of the nine call `logging.basicConfig` from the CLI** — taskiq and
dramatiq — and both expose an opt-out flag whose help text names the call: dramatiq's
`--skip-logging` is documented as "do not call logging.basicConfig()", taskiq's
`--no-configure-logging` as "Use this parameter if your application configures custom logging."
**Two more configure logging without `basicConfig`**: arq calls `dictConfig` unconditionally on a
default that touches only its own logger, and faststream calls it once and only when the operator
passes a file. **Litestar's CLI configures nothing**, leaving `dictConfig` to the `LoggingConfig`
object the application passes to its constructor; sanic does the same one level down, in the
application constructor. uvicorn is the outlier in the other direction: because `configure_logging`
runs from `Config.__init__`, constructing `uvicorn.Config` in library code reconfigures logging too.

**Eight of the nine mutate `sys.path` on every run.** Only uvicorn leaves it alone by default,
because its insert is guarded by `if app_dir is not None`; faststream's, dramatiq's and taskiq's
equivalents default to the working directory and therefore always fire.

No maintainer-written issue, pull request or discussion articulating *why* a CLI should call
`basicConfig` was found; the closest primary rationale is the help text quoted above
**[unverified]**.

### 2.2 How they find the application

Every one of the nine resolves an object from a string, and the shapes differ mainly in how much
guessing they do. uvicorn requires the exact `<module>:<attribute>` form and walks dotted attributes
after the colon; it accepts `--factory` and additionally auto-detects a factory, logging "ASGI app
factory detected. Using it, but please consider setting the --factory flag explicitly." faststream
raises `SetupError` when the colon is missing. arq imports a `WorkerSettings` class or dict and has
no factory concept at all. dramatiq accepts `module` or `module:broker`, calls the attribute if it
is callable, and falls back to a registry lookup. sanic splits on `:` or `.`, defaults the attribute
to `app`, and marks a factory with a trailing `()`. litestar resolves three ways — `--app`, the
`LITESTAR_APP` environment variable, or filesystem autodiscovery over `["app", "application"]` — and
treats a module exposing `create_app` as a factory. fastapi-cli has the most elaborate discovery of
the nine, with five labelled sources including a `pyproject.toml` entry point.

Two CLIs are extensible by third parties: litestar adds commands from the `litestar.commands` entry
point group and calls `plugin.on_cli_init(self)`, and taskiq builds its subparsers entirely from the
`taskiq_cli` entry-point group, registering only `worker` and `scheduler` itself.

## 3 What the dependency costs

### 3.1 typer no longer means click

The premise that typer and click are one stack is out of date. **typer stopped depending on click as
a third-party package in 0.26.0 (2026-05-26) and vendors its source instead** (PR #1774). The
maintainers' recorded rationale is threefold: "This simplifies the work done by both Click and Typer
teams", "It allows Typer to evolve independently, and enables several new planned features", and "It
will solve several dependency conflict situations for projects that use some packages that depend on
Click and some that depend on Typer." The recorded cost: "Click-specific functionality is no longer
supported, like extracting the Click app and adding Click-specific plug-ins, or customizing the
field types with Click-specific types."
([release notes](https://raw.githubusercontent.com/fastapi/typer/master/docs/release-notes.md))

The consequence for a framework author is the one the release note states from the other side: a
library that depends on `click` directly no longer conflicts with a downstream consumer of typer.

`typer-slim`, the historical way to get typer without `rich`, is gone. typer 0.22.0 made it "a
shallow wrapper around `typer`, always requiring `rich` and `shellingham`", 0.24.1 dropped support
entirely, and the final `typer-slim` 0.24.0 is a 3,394-byte shim depending on `typer>=0.24.0` whose
own PyPI page opens with "⚠️ Do not install this package. ⚠️". The only remaining way to suppress
rich is the runtime environment variable `TYPER_USE_RICH`; the wheel is installed either way.

### 3.2 The numbers

| Package | Version | Date | `requires_python` | Runtime dependencies | Wheel |
|---|---|---|---|---|---|
| `click` | 8.5.0 | 2026-08-26 | `>=3.10` | none (`requires_dist` is null) | 125,251 B |
| `typer` | 0.27.2 | 2026-08-28 | `>=3.10` | `shellingham>=1.3.0`, `rich>=13.8.0`, `annotated-doc>=0.0.2`, `colorama` (Windows) | 123,130 B |
| `rich` | 15.0.0 | 2026-04-12 | `>=3.9.0` | `markdown-it-py>=2.2.0`, `pygments>=2.13.0,<3.0.0` | 310,654 B |
| `pygments` | 2.21.0 | — | `>=3.9` | none by default | 1,250,147 B |
| `markdown-it-py` | 4.2.0 | — | `>=3.10` | `mdurl~=0.1` | 91,687 B |
| `shellingham` | 1.5.4 | 2023-10-24 | `>=3.7` | none | 9,755 B |
| `annotated-doc` | 0.0.5 | 2026-07-28 | `>=3.9` | none | 5,302 B |

Summing the verified per-wheel sizes **[unverified as a total — no source publishes it]**:
installing `typer` pulls **7 wheels totalling 1,800,654 bytes** on Linux and macOS, against **1
wheel of 125,251 bytes** for `click` alone — a factor of 14.4, of which `pygments` alone is 69.4%.
On Windows typer adds `colorama` for 8 wheels and 1,825,989 bytes. These are download sizes, not
installed-on-disk sizes.

Two further signals. `click` is classified "Development Status :: 5 - Production/Stable" and `typer`
"4 - Beta"; `shellingham`, an unconditional typer dependency, is "3 - Alpha" and has had no release
since 2023-10-24. `click` 8.5.0 also dropped its Windows `colorama` dependency — "Supported versions
of Windows enable ANSI terminal styles by default. Colorama is no longer a dependency and is not
used" — while typer acquired that same marker at vendoring time and kept it. The effective Python
floor of the typer closure is 3.10, set by typer and by `markdown-it-py` alike.

### 3.3 What the standard library does and does not do

[`argparse`](https://docs.python.org/3/library/argparse.html) provides subcommands through
`add_subparsers()`, documented as the equivalent of "svn checkout, svn update, and svn commit", with
`aliases` on `add_parser()`. It provides type coercion through `type` and restriction through
`choices`, with its own caution that "the type keyword is a convenience that should only be used for
simple conversions that can only raise one of the three supported exceptions".

It provides **no shell completion of any kind**: the string "completion" does not occur anywhere on
the `argparse` documentation page, and no completion API is documented — an argument from absence,
but a complete one for that page **[unverified as a positive statement]**. click, by contrast,
"provides tab completion support for Bash (version 4.4 and up), Zsh, Fish, and PowerShell", the last
added in 8.5.0.

Recent versions moved: 3.13 added the `deprecated` parameter to `add_argument()` and `add_parser()`;
3.14 added `suggest_on_error` (default `False`) and `color`, whose **default is `True`** — "By
default, the help message is printed in color using ANSI escape sequences" — with the documented
consequence that "Error messages will include color codes when redirecting stderr to a file" unless
`NO_COLOR` or `PYTHON_COLORS` is set. 3.14 also removed nested `add_argument_group()` and deprecated
`argparse.FileType` and `prefix_chars` on `add_argument_group()`.

## 4 What the evidence supports

- **An Extra cannot gate a command.** Any `[project.scripts]` entry is installed unconditionally, so
  a CLI behind an extra must guard the import in the module the entry point names and exit with an
  install instruction — the httpx shape. There is no proposal in flight that would change this.
- **The parser is the smaller half of the cost.** `click` is one wheel with no dependencies and a
  Production/Stable classifier; `typer` is 14× the download and drags `pygments` for colour a
  framework's command does not need. `argparse` covers subcommands and coercion and costs nothing,
  and its only material gap is shell completion.
- **Size is not what a CLI actually spends.** Every peer CLI mutates state the application owns —
  logging in six of nine, `sys.path` in eight of nine, the event-loop policy in one, the root logger
  in one. A CLI that configures nothing is a real option: litestar's does exactly that.
- **`--log-config` is the narrow form of the concession.** faststream calls `dictConfig` once and
  only when the operator names a file, which leaves the configuration in the hands of whoever starts
  the process rather than in the library's.

## Sources

Specifications and standard library:

- <https://packaging.python.org/en/latest/specifications/entry-points/>
- <https://packaging.python.org/en/latest/specifications/pyproject-toml/>
- <https://peps.python.org/pep-0621/> · <https://peps.python.org/pep-0771/>
- <https://github.com/pypa/pip/issues/9726> · <https://github.com/pypa/packaging.python.org/issues/757>
- <https://raw.githubusercontent.com/python/cpython/main/Lib/importlib/metadata/__init__.py>
- <https://raw.githubusercontent.com/pypa/installer/main/src/installer/scripts.py> · <https://raw.githubusercontent.com/pypa/distlib/master/distlib/scripts.py>
- <https://docs.python.org/3/library/argparse.html> · <https://docs.python.org/3/whatsnew/3.13.html> · <https://docs.python.org/3/whatsnew/3.14.html>

Build back-ends:

- <https://hatch.pypa.io/latest/config/metadata/> · <https://docs.astral.sh/uv/concepts/build-backend/> · <https://docs.astral.sh/uv/concepts/projects/init/> · <https://setuptools.pypa.io/en/latest/userguide/entry_point.html>

Guarding an optional CLI:

- <https://raw.githubusercontent.com/encode/httpx/master/pyproject.toml> · <https://raw.githubusercontent.com/encode/httpx/master/httpx/__init__.py> · <https://raw.githubusercontent.com/encode/httpx/master/httpx/_main.py>
- <https://raw.githubusercontent.com/fastapi/fastapi/master/pyproject.toml> · <https://raw.githubusercontent.com/fastapi/fastapi/master/fastapi/cli.py>
- <https://raw.githubusercontent.com/psf/black/main/src/black/handle_ipynb_magics.py> · <https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/compat/_optional.py>
- <https://raw.githubusercontent.com/sqlalchemy/sqlalchemy/main/pyproject.toml>

Peer CLIs, read at the tag named in the table:

- <https://raw.githubusercontent.com/encode/uvicorn/0.52.4/uvicorn/main.py> · <https://raw.githubusercontent.com/encode/uvicorn/0.52.4/uvicorn/config.py> · <https://raw.githubusercontent.com/encode/uvicorn/0.52.4/uvicorn/server.py> · <https://raw.githubusercontent.com/encode/uvicorn/0.52.4/uvicorn/importer.py>
- <https://raw.githubusercontent.com/ag2ai/faststream/0.7.5/faststream/__main__.py> · <https://raw.githubusercontent.com/ag2ai/faststream/0.7.5/faststream/_internal/cli/main.py> · <https://raw.githubusercontent.com/ag2ai/faststream/0.7.5/faststream/_internal/cli/utils/logs.py> · <https://pypi.org/pypi/faststream/0.7.5/json>
- <https://raw.githubusercontent.com/litestar-org/litestar/v2.24.0/litestar/cli/main.py> · <https://raw.githubusercontent.com/litestar-org/litestar/v2.24.0/litestar/cli/_utils.py> · <https://raw.githubusercontent.com/litestar-org/litestar/v2.24.0/litestar/cli/commands/core.py> · <https://raw.githubusercontent.com/litestar-org/litestar/v2.24.0/litestar/logging/config.py>
- <https://raw.githubusercontent.com/taskiq-python/taskiq/0.12.6/pyproject.toml> · <https://raw.githubusercontent.com/taskiq-python/taskiq/0.12.6/taskiq/cli/worker/run.py> · <https://raw.githubusercontent.com/taskiq-python/taskiq/0.12.6/taskiq/cli/scheduler/run.py> · <https://raw.githubusercontent.com/taskiq-python/taskiq/0.12.6/taskiq/cli/worker/args.py> · <https://raw.githubusercontent.com/taskiq-python/taskiq/0.12.6/taskiq/cli/utils.py>
- <https://raw.githubusercontent.com/python-arq/arq/v0.28.0/arq/cli.py> · <https://raw.githubusercontent.com/python-arq/arq/v0.28.0/arq/logs.py> · <https://raw.githubusercontent.com/python-arq/arq/v0.28.0/pyproject.toml>
- <https://raw.githubusercontent.com/Bogdanp/dramatiq/v2.2.1/dramatiq/cli.py> · <https://raw.githubusercontent.com/Bogdanp/dramatiq/v2.2.1/setup.py>
- <https://raw.githubusercontent.com/celery/celery/v5.6.3/celery/bin/celery.py> · <https://raw.githubusercontent.com/celery/celery/v5.6.3/celery/app/log.py> · <https://raw.githubusercontent.com/celery/celery/v5.6.3/celery/apps/worker.py> · <https://raw.githubusercontent.com/celery/celery/v5.6.3/celery/platforms.py> · <https://raw.githubusercontent.com/celery/celery/v5.6.3/requirements/default.txt>
- <https://raw.githubusercontent.com/fastapi/fastapi-cli/0.0.32/src/fastapi_cli/cli.py> · <https://raw.githubusercontent.com/fastapi/fastapi-cli/0.0.32/src/fastapi_cli/logging.py> · <https://raw.githubusercontent.com/fastapi/fastapi-cli/0.0.32/src/fastapi_cli/utils/cli.py> · <https://raw.githubusercontent.com/fastapi/fastapi-cli/0.0.32/src/fastapi_cli/discover.py> · <https://raw.githubusercontent.com/fastapi/fastapi-cli/0.0.32/pyproject.toml>
- <https://raw.githubusercontent.com/sanic-org/sanic/v25.12.1/sanic/cli/app.py> · <https://raw.githubusercontent.com/sanic-org/sanic/v25.12.1/sanic/cli/arguments.py> · <https://raw.githubusercontent.com/sanic-org/sanic/v25.12.1/sanic/app.py> · <https://raw.githubusercontent.com/sanic-org/sanic/v25.12.1/sanic/server/loop.py> · <https://raw.githubusercontent.com/sanic-org/sanic/v25.12.1/sanic/worker/loader.py> · <https://raw.githubusercontent.com/sanic-org/sanic/v25.12.1/setup.py>

Dependency metadata:

- <https://pypi.org/pypi/typer/json> · <https://pypi.org/pypi/typer-slim/json> · <https://pypi.org/pypi/click/json> · <https://pypi.org/pypi/rich/json> · <https://pypi.org/pypi/pygments/json> · <https://pypi.org/pypi/markdown-it-py/json> · <https://pypi.org/pypi/shellingham/json> · <https://pypi.org/pypi/annotated-doc/json>
- <https://raw.githubusercontent.com/fastapi/typer/master/pyproject.toml> · <https://raw.githubusercontent.com/fastapi/typer/master/docs/release-notes.md> · <https://raw.githubusercontent.com/pallets/click/main/pyproject.toml> · <https://raw.githubusercontent.com/pallets/click/main/CHANGES.md> · <https://click.palletsprojects.com/en/stable/shell-completion/>
