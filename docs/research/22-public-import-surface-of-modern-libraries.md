# The public import surface of modern Python libraries: root, subpackages, and what a move costs

Research date: 2026-09-09, for ticket #24. One question: how do modern, strictly typed Python
libraries lay out their public import surface across the root namespace and their subpackages, and
which layouts stay extensible as the library grows? The concrete decision this note feeds is the
*documented import path* of a Core name in one distribution whose code is split into four import
ranks — `aiommbot/core/`, `aiommbot/mattermost/` (with its own `plugins/`), `aiommbot/plugins/`
and `aiommbot/testing/`. Three candidate layouts were weighed:

- **(A) two tiers** — about twelve headline names re-exported from the root, everything else from
  `aiommbot.core.<module>`, with exactly one documented path per name;
- **(B) one tier** — the whole Core public surface re-exported from the root (~35 names),
  `aiommbot.core` being merely where the files live;
- **(C) deep canonical** — the canonical path is always `aiommbot.core.<module>`, the root
  re-export being an acknowledged convenience, so headline names have two paths.

Every claim below names its source. Numbers state the method that produced them. Anything not
checked against a primary source is marked **[unverified]**. This note records findings only. The
decisions it feeds are [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md),
[ADR-0042](../adr/0042-a-public-name-is-documented-at-its-package-path.md),
[ADR-0043](../adr/0043-explicit-re-export-with-a-reference-page-as-the-public-list.md) and
[`engineering-style.md`](../design/engineering-style.md) §8 (`ST-MOD-01`…`ST-MOD-05`); where an ADR
decided, the ADR is the decision and this note is its evidence.

## 1. Measurement method

Four independent methods produced the facts, and each row of §2 says which one it used.

- **Source at a tag.** Each library's root `__init__.py` was fetched through the GitHub contents
  API at the tag of its latest release on the research date, with
  `Accept: application/vnd.github.raw`, and parsed with the standard-library `ast` module: the
  script counted `__all__` entries by `ast.literal_eval`, classified every `ImportFrom` alias as
  `X as X` / plain / star, and detected a module-level `__getattr__` or `__dir__`. Package
  directory listings came from the same API at the same tag. Tags and publication dates come from
  `GET /repos/{owner}/{repo}/releases/latest`.
- **Installed wheels.** The same versions were installed from PyPI into one throwaway virtual
  environment on CPython 3.14.7, and the runtime surface was read back
  (`len(module.__all__)`, `len([n for n in dir(module) if not n.startswith('_')])`). Where the
  runtime number differs from the source number, §2 says so.
- **Import cost.** Wall-clock cost of one import statement, measured as a subprocess delta:
  `python -c "<statement>"` run nine times after a warm-up run that fills `__pycache__`, minimum
  kept, minus the minimum of `python -c ""` measured in the same session. Reported to the nearest
  millisecond, with the spread across two independent sessions, on an Apple-silicon macOS 24.6.0
  host. These numbers are ordinal, not portable.
- **Checker behaviour.** Four checkers were run against purpose-built two-package fixtures
  (a `py.typed` library installed into site-packages, and a consumer module outside it):
  mypy 2.3.1, pyright 1.1.411, ty 0.0.79, pyrefly 1.2.0, plus ruff 0.16.6. The exact fixtures and
  outputs are in §5.

Versions measured, with the release date each tag carries:

| Library | Tag measured | Released |
|---|---|---|
| attrs | `26.1.0` | 2026-03-19 |
| httpx | `0.28.1` | 2024-12-06 |
| httpcore | `1.0.9` | 2025-04-24 |
| starlette | `1.6.0` | 2026-08-08 |
| litestar | `v2.24.0` | 2026-06-11 |
| faststream | `0.7.5` | 2026-08-27 |
| aiogram | `v3.31.0` | 2026-08-25 |
| pydantic | `v2.13.5` | 2026-08-28 |
| msgspec | `0.21.1` | 2026-04-12 |
| websockets | `17.1` | 2026-08-26 |
| anyio | `4.15.1` | 2026-09-05 |
| structlog | `26.1.0` | 2026-06-06 |
| SQLAlchemy | `rel_2_0_52` | 2026-08-11 |
| dishka | `1.10.1` | 2026-04-25 |
| django-modern-rest | `0.14.0` | 2026-08-14 |

The suggested witness list was measured unchanged, with two additions and one split. `attrs` is
measured twice, as the `attr` and the `attrs` import namespace, because the pair *is* the finding
(§4.1). `starlette` is kept although its root is empty, because an empty root is a fourth layout
and the note needs it named. Peer bot frameworks (`aiogram`, `faststream`) are read as evidence of
practice, never as authority.

## 2. Fifteen root namespaces, measured

"Root re-exports" is the number of public names the root `__init__` offers: the length of `__all__`
where one exists, otherwise the count of imported aliases. Where the two disagree the cell gives
both. "Documented paths" answers whether a name reachable from the root is *also* documented at a
deeper module path.

| Library (version) | Root re-exports | `__all__` | Re-export form | Public second-level packages users import from (named after…) | >1 documented path per name | Public `core`/`base`/`abc`/`protocols` | Private-module convention | Module `__getattr__` (PEP 562) |
|---|---|---|---|---|---|---|---|---|
| attrs `26.1.0` (`attrs` namespace) | 38 in `__all__` (9 of them dunders, 5 submodules); 29 plain imports | yes | plain `from attr import …` + `__all__` | none; five topic modules (`converters`, `validators`, `filters`, `setters`, `exceptions`) | **yes** — every name also at `attr.<name>` | no | `_name.py` inside `attr/` | yes, for packaging dunders only |
| attrs `26.1.0` (`attr` namespace) | 34 in `__all__`; 35 plain imports | yes | plain + `__all__` | same five topic modules | **yes** — the `attrs` namespace | no | `_name.py` | yes, for packaging dunders only |
| httpx `0.28.1` | 69 | yes | 11 × `from ._mod import *` + `__all__` | **none** — every module is `_`-prefixed | no | no | `_name.py`, `_transports/` | no |
| httpcore `1.0.9` | 49 | yes | plain + `__all__` | **none** — every module is `_`-prefixed | no | no | `_name.py`, `_async/`, `_sync/`, `_backends/` | no |
| starlette `1.6.0` | **0** (the file is one line, `__version__`) | no | none | ~20, topic (`applications`, `responses`, `routing`, `requests`, `middleware/`, `testclient`) | no | no | `_utils.py`, `_exception_handler.py` | no |
| litestar `v2.24.0` | 20 | yes | plain + `__all__` | ~20, topic (`dto`, `params`, `security`, `channels`, `openapi`, `middleware`, `handlers`, `stores`, `testing`) plus layer-ish `utils`, `typing` | **yes** — the reference is per module (`.. automodule:: litestar.handlers`), the prose uses the root | no | `_asgi/`, `_kwargs/`, `_layers/`, `_openapi/`, `_signature/` | no |
| faststream `0.7.5` | 20 | yes | plain + `__all__` | ~14, topic — the broker names (`rabbit`, `kafka`, `nats`, `redis`, `confluent`, `mqtt`) plus `asgi`, `params`, `middlewares`, `response`, `specification`, `opentelemetry`, `prometheus` | importable at a second path — 12 of the 20 come from public modules (`faststream.params.Depends`, `faststream.response.Response`, …); which path the documentation names is **[unverified]** | no | **`_internal/`** | no |
| aiogram `v3.31.0` | 14 | yes | plain + `__all__` | ~10, topic (`types`, `methods`, `filters`, `fsm`, `enums`, `client`, `dispatcher`, `handlers`, `utils`, `webhook`) | **yes** — one page carries both `from aiogram import Router` and `.. autoclass:: aiogram.dispatcher.router.Router` | no | **none** — no underscore module at any level | no |
| pydantic `v2.13.5` | 151 | yes | `__all__` + a `TYPE_CHECKING` block (5 star, 54 plain) + a 151-entry `_dynamic_imports` table read by `__getattr__` | ~13, topic (`dataclasses`, `json_schema`, `types`, `fields`, `networks`, `aliases`, `functional_validators`, `experimental`, `plugin`, `v1`, `deprecated`) | **yes** — the reference documents `pydantic.fields.Field` at the module path while `pydantic.BaseModel` is documented at the root | no | `_internal/` | **yes** — lazy table plus `_migration.getattr_migration` |
| msgspec `0.21.1` | 22 plain imports (runtime `dir()` shows 21 public names) | no in `.py`; none in `__init__.pyi` either | plain, with a hand-written `__init__.pyi` stub beside it | 6, topic (`json`, `msgpack`, `yaml`, `toml`, `structs`, `inspect`) | no | no (the C extension is `msgspec._core`) | `_name.py` | no |
| websockets `17.1` | 65 in `__all__`; 76 reachable (65 + 11 deprecated aliases) | yes | `__all__` + a `TYPE_CHECKING` eager block + PEP 562 `lazy_import()` at runtime | 5 named after the **I/O layer** (`asyncio`, `sync`, `trio`, `legacy`, `extensions`) plus topic modules (`frames`, `datastructures`, `exceptions`, `http11`, `protocol`, `typing`, `uri`) | **yes** — the reference documents `websockets.asyncio.client.connect` | `protocol` (the Sans-I/O module), not `core`/`base`/`abc` | **none** — privacy is by documentation, not by name | **yes** |
| anyio `4.15.1` | 104 `X as X` plus 9 submodule re-exports; runtime `dir()` shows 96 | no | `X as X` **inside `if TYPE_CHECKING`**, with the runtime map built by AST-parsing that same block | ~10: `abc` (**layer**), `streams/` (topic), `to_thread`, `from_thread`, `to_process`, `to_interpreter`, `lowlevel`, `functools`, `itertools`, `pytest_plugin` | no — `_core/` is private, so a root name has no second path | **`anyio.abc`** — the only layer-named public subpackage in the set | `_core/`, `_backends/`, `_lazyimport.py` | **yes** |
| structlog `26.1.0` | 31 | yes | plain + `__all__` | ~11, topic (`stdlib`, `processors`, `dev`, `contextvars`, `testing`, `tracebacks`, `twisted`, `threadlocal`, `exceptions`, `typing`, `types`) | no for root names; **yes** for the `types`/`typing` pair | no | `_name.py` | yes, for packaging dunders, with a `DeprecationWarning` |
| SQLAlchemy `rel_2_0_52` | 250 `X as X`; runtime `dir()` shows 264 | no | `X as X`, no `__all__` | ~15, mixed: topic (`orm`, `dialects/`, `pool`, `schema`, `types`, `exc`, `event`) and layer (`sql`, `engine`, `ext/`, `util`, `future`, `connectors`) | **yes** — `sqlalchemy.select` is also `sqlalchemy.sql.expression.select` | no — "Core" is a documentation word, not a package (the non-ORM half lives in `sql/` and `engine/`) | **none** at top level; `util/` and `cyextension/` are public-named internals | no |
| dishka `1.10.1` | 26 | yes | plain + `__all__` | `integrations/` (topic — framework names) and `plotter`; the rest are public-named but undocumented | importable at a second path — `dishka.Scope` is `dishka.entities.scope.Scope`; which path the documentation names is **[unverified]** | no | `_adaptix/` only; `entities/`, `registry.py`, `dependency_source/`, `graph_builder/`, `code_tools/`, `text_rendering/` carry public names | no |
| django-modern-rest `0.14.0` | 16, every one `X as X` | **no** — none anywhere in the repository | `X as X` | ~10, topic (`security`, `throttling`, `openapi`, `streaming`, `plugins`, `test`, `management`, `locale`, `static`, `templates`) | **yes** — all 119 reference directives use `dmr.<module>.<Name>`, while the README examples use `from dmr import …` | no | **`internal/`** and `_compiled/` — no leading underscore on `internal/` | no |

Cross-checks worth keeping:

- The suggested set contained no library with a public subpackage named `core`, `base` or
  `protocols`. One has a public subpackage named after a layer: `anyio.abc`. SQLAlchemy uses the
  word "Core" throughout its documentation for the non-ORM half of the library and ships no
  package by that name. This is a gap in the evidence, not a verdict: see §6.
- Two libraries put their internals behind a name with no leading underscore — django-modern-rest
  (`dmr/internal/`) and faststream (`faststream/_internal/`, which does carry one). Two more
  (aiogram, SQLAlchemy) have no private-module convention at all, and websockets deliberately
  replaces it with a documentation rule (§3.3).
- The counts in the "Root re-exports" column span two orders of magnitude, from 0 (starlette) to
  250 (SQLAlchemy), and they cluster: nine libraries sit between 14 and 38, four between 49 and
  104, and two above 150.

## 3. Which of the three layouts is practised

### 3.1 Layout (A) — small curated root, deeper topical paths, one documented path per name

Witnesses: **msgspec**, **anyio**, **httpx**, **httpcore**, **structlog**, **starlette** (as the
degenerate case), and **attrs** within one namespace.

The mechanism that makes (A) hold is not a documentation habit; it is the module names. In httpx,
httpcore, structlog, anyio and attrs *every module that defines a root name is
underscore-prefixed*, so there is no second path a user could write. attrs is the clearest
demonstration of the discipline: `src/attr/` holds seven private modules (`_make.py`,
`_next_gen.py`, `_funcs.py`, `_cmp.py`, `_compat.py`, `_config.py`, `_version_info.py`) that
define everything the root exports flat, and five public ones (`converters`, `validators`,
`filters`, `setters`, `exceptions`) that the root re-exports *as modules* — their names are in
`attrs.__all__`, their contents are not. structlog does the same with nine
(`contextvars`, `dev`, `processors`, `stdlib`, `testing`, `threadlocal`, `tracebacks`, `types`,
`typing`). So the shape is: flat names from private modules, plus topical public modules named in
the root's `__all__` and never flattened. httpx has fifteen underscore-prefixed modules, one
underscore-prefixed package (`_transports/`), `__version__.py`, and 69 names in `__all__`: the
root is not a curated tier over a public `core`, it is the *only* public module in the
distribution. anyio is the same shape with a topical exception: 104 names come out of
the private `_core/`, and the public subpackages (`anyio.abc`, `anyio.streams.*`,
`anyio.to_thread`) hold what does not belong in the root.

msgspec is the cleanest (A) in the suggested sense: 21 public names at the root (`Struct`, `Meta`,
`Raw`, `field`, `convert`, `to_builtins`, the exceptions), and six topical modules —
`msgspec.json`, `msgspec.msgpack`,
`msgspec.yaml`, `msgspec.toml`, `msgspec.structs`, `msgspec.inspect` — each holding names that
exist nowhere else. No name has two paths, and the split is by topic (format, introspection), not
by layer.

starlette is (A) with the root tier removed: `starlette/__init__.py` contains one line,
`__version__ = "1.6.0"`. Every name is imported from exactly one topical module
(`starlette.responses.JSONResponse`, `starlette.routing.Route`). It is proof that a framework with
a large public surface can carry no root namespace at all and stay usable — and that this costs
the user one longer import line per name.

### 3.2 Layout (B) — the whole public surface at the root

Witnesses: **SQLAlchemy** and **pydantic** at the large end, **httpx** and **httpcore** at the
small end, since for them the root *is* the whole surface.

SQLAlchemy re-exports 250 names from `lib/sqlalchemy/__init__.py`, every one in the `X as X` form
and with no `__all__` at all, while `sqlalchemy.orm`, `sqlalchemy.sql`, `sqlalchemy.engine`,
`sqlalchemy.pool`, `sqlalchemy.ext.*` and `sqlalchemy.dialects.*` remain public and documented.
So SQLAlchemy is (B) *and* keeps deep public paths — which makes it also the largest witness for
(C). `select` is documented at the module path in `doc/build/core/selectable.rst`, under
`.. currentmodule:: sqlalchemy.sql.expression` followed by `.. autofunction:: select`, and it is
also `sqlalchemy.select` in the root's 250 re-exports and `sqlalchemy.future.select` in the
legacy staging package (§4.5) — three live paths to one function.

pydantic's 151-name `__all__` is (B) taken to its conclusion, and it is the one library in the set
that pays for the root's size with machinery: the names are declared under `if TYPE_CHECKING`,
listed again in a 151-entry `_dynamic_imports` table, and served at runtime by a module
`__getattr__` that, on the first hit for a module, copies *every* name from that module into the
package globals at once (`pydantic/__init__.py`). A 151-name root that imported eagerly would be
the whole library.

### 3.3 Layout (C) — the deep path is canonical, the root re-export is a convenience

Witnesses whose own documentation shows both paths: **django-modern-rest**, **websockets**,
**pydantic**, **litestar**, **aiogram**, **SQLAlchemy**. **dishka** and **faststream** have the
second path in the package; which one their documentation names is **[unverified]**.

- **django-modern-rest** is the sharpest case, because
  [`docs/research/21`](21-measured-facts-behind-the-rules.md) measured its root at exactly 16
  names. Its reference page `docs/pages/deep-dive/public-api.rst`
  contains 119 `autoclass` / `autofunction` / `autoexception` / `autodecorator` directives, and
  **every one of them names a module path** — `dmr.controller.Controller`,
  `dmr.endpoint.modify`, `dmr.cookies.NewCookie` — while its README's runnable example writes
  `>>> from dmr import Body, Controller, Headers`. Method: `grep -oE "^\.\. auto[a-z]+:: …"` over
  the page, then counting dotted segments; 58 directives have three segments, 47 have four, 14
  have five, and none has two. So the library whose tiny root ADR-0007 cites documents the deep
  path and uses the root path in prose. The four public-API criteria it states in its CHANGELOG do
  not say which path is canonical.
- **websockets** documents the deep path in its reference (`websockets.asyncio.client.connect`,
  via `.. automodule:: websockets.asyncio.client` followed by `.. autofunction:: connect`) and
  keeps the root name as an alias it calls, in its own changelog, a "convenience import".
- **litestar** re-exports 20 names at the root and organises its whole reference by module —
  `docs/reference/` holds `app.rst`, `handlers.rst`, `connection.rst`, `controller.rst`,
  `router.rst`, `response.rst`, `enums.rst`, each a bare `.. automodule:: litestar.<module>` with
  `:members:`. So `get`, `Litestar` and `Request` are documented at the module path and imported
  from the root in every example.
- **aiogram** re-exports 14, and `Bot`, `Dispatcher`, `Router`, `BaseMiddleware` all come out of
  public modules (`aiogram.client.bot`, `aiogram.dispatcher.dispatcher`,
  `aiogram.dispatcher.router`, `aiogram.dispatcher.middlewares.base`). Its `Router` page shows
  both paths in one file: the usage block reads `from aiogram import Router` and the reference
  directive below it reads `.. autoclass:: aiogram.dispatcher.router.Router`
  (`docs/dispatcher/router.rst`). Two of the 14 — `F = MagicFilter()` and
  `flags = FlagGenerator()` — are *constructed* in `__init__.py` and so exist at the root only.
- **dishka** re-exports 26 from `dishka.entities.*`, `dishka.container`,
  `dishka.async_container` and `dishka.provider`, none of which is underscore-private, so the
  second path exists whether or not the documentation names it (**[unverified]** which it does).

### 3.4 The layout with no witness

No library in the set documents a *public* subpackage as the canonical home of its
platform-independent core while also re-exporting a curated subset of that subpackage at the root.
The libraries that curate a small root make the implementation modules private (§3.1); the
libraries with public deep modules name them after topics and let a name have two paths (§3.3).
Our situation — a public `aiommbot.core` that is neither `_internal` nor a topic — has no direct
witness in this set. **[unverified]** whether one exists outside it; the search covered the fifteen
libraries above and no more.

## 4. What changing a public surface actually cost

### 4.1 attrs: a root namespace that could not be fixed, so a second one was added

attrs documents the whole episode itself, in `docs/names.md` ("On The Core API Names"). The
library shipped in April 2015 with the package name as part of the API — `attr.s`, `attr.ib` —
and then:

> Unfortunately, the `attr` package name started creaking the moment we added `attr.Factory`,
> since it couldn't be morphed into something meaningful in any way. A problem that grew worse
> over time, as more APIs and even modules were added.

The fix was not a rename. New function names arrived in 20.1.0, and in **December 2021, release
21.3.0**, attrs added a *second import namespace*: `attrs`, whose `__init__.py` is 72 lines of
`from attr import …` plus a 38-entry `__all__`. Both namespaces are documented, both are shipped,
and the old one is promised forever:

> The traditional, or *OG*, APIs `attr.s` / `attr.ib`, their serious-business aliases
> `attr.attrs` / `attr.attrib`, and the never-documented, but popular `attr.dataclass` easter egg
> will stay **forever**.

Two facts to take from this. First, the cost of getting a root namespace wrong is not paid in a
deprecation cycle; it is paid by shipping both surfaces indefinitely. Second, the undocumented
name still had to be kept: `attr.dataclass` is absent from `attr.__all__` (34 entries) and from
the reference documentation, and attrs still promises it forever because people found it and used
it. A criterion that says "documented or it is not public" only holds if nothing importable is
attractive enough to be used undocumented.

### 4.2 pydantic: 151 names at the root, twelve shim modules, and a 226-entry migration table

pydantic v2.0 shipped on **2023-06-30**. At v2.13.5 (**2026-08-28**, three years and two months
later) the migration machinery is still in the wheel, and it is not small. Measured in the
installed 2.13.5 wheel:

- **twelve modules whose entire body is five lines** — `class_validators.py`, `datetime_parse.py`,
  `decorator.py`, `env_settings.py`, `error_wrappers.py`, `generics.py`, `json.py`, `parse.py`,
  `schema.py`, `tools.py`, `utils.py`, `validators.py`. Each is exactly:

  ```python
  """The `utils` module is a backport module from V1."""

  from ._migration import getattr_migration

  __getattr__ = getattr_migration(__name__)
  ```

- **a 226-entry migration table** in `pydantic/_migration.py`: `MOVED_IN_V2` (7 entries),
  `DEPRECATED_MOVED_IN_V2` (12), `REDIRECT_TO_V1` (11) and `REMOVED_IN_V2` (196). Counted by
  `ast.literal_eval` on the module and by reading the dict lengths back from the import.
- **twenty modules besides `_migration.py` itself** import `getattr_migration`, including
  `__init__.py`,
  `config.py`, `errors.py`, `main.py`, `networks.py`, `types.py` and `typing.py` — that is, the
  live modules carry the shim too, not only the dead ones.
- **a vendored `pydantic.v1` subpackage** and a `pydantic.deprecated` subpackage holding the real
  implementations the shims forward to.

The moved-name mechanism itself is worth copying: `getattr_migration` returns a PEP 562 `wrapper`
that warns and forwards for a moved name, warns and forwards to `pydantic.v1` for a redirected
one, and raises `PydanticImportError` for a removed one — including the special case whose message
is the whole lesson about splitting a distribution:

> `` `BaseSettings` has been moved to the `pydantic-settings` package. ``

A name that leaves the distribution cannot be forwarded at all; the best available outcome is a
typed error with a pointer.

### 4.3 websockets: five years of aliases, one silent repoint, and a lazy root that broke checkers

websockets states its policy in the changelog, and the policy is the cost:

> When possible with reasonable effort, we preserve backwards-compatibility for five years after
> the release that introduced the change.

> Only documented APIs are public. Undocumented, private APIs may change without notice.

The five years are literal. Version **9.0 (2021-05-01)** moved `Headers` and
`MultipleValuesError` out of `websockets.http` into `websockets.datastructures`, moved `client`,
`server`, `protocol` and `auth` into `websockets.legacy`, and deprecated five low-level modules
with this reason:

> These modules provided low-level APIs for reuse by other projects, but they didn't reach that
> goal. Keeping these APIs public makes it more difficult to improve websockets.

The aliases those moves needed were removed in **17.0 (2026-07-29)** — "Aliases for modules moved
or deprecated in 9.0 are removed" — five years and three months later. In between, **11.0
(2023-04-02)** moved the Sans-I/O implementation again (`connection` → `protocol`,
`Connection`/`ServerConnection`/`ClientConnection` → `Protocol`/`ServerProtocol`/`ClientProtocol`)
with another alias set, and **14.0 (2024-11-09)** did the thing a root re-export makes possible
and a deep path does not:

> The following aliases in the `websockets` package were switched to the new `asyncio`
> implementation::
>
>     from websockets import connect, unix_connext
>     from websockets import broadcast, serve, unix_serve
>
> If you're using any of them, then you must follow the upgrade guide immediately.

The same import line kept working and started returning a different implementation. Users who had
written the deep path — `from websockets.legacy.client import connect` — were unaffected by
construction. This is the sharpest available argument about *which* path should be the documented
one: a root alias is a level of indirection the library can silently repoint, and a module path is
not.

The mechanism cost is recorded too. Version 9.0 introduced the lazy root:

> **Convenience imports from `websockets` are performed lazily.** While Python supports this,
> tools relying on static code analysis don't. This breaks auto-completion in an IDE or type
> checking with mypy.

It took until **12.0 (2023-10-21)** to repair that — "Made convenience imports from `websockets`
compatible with static code analysis tools such as auto-completion in an IDE or type checking with
mypy" — and the repair is the shape everybody now uses: a literal `__all__`, a
`if TYPE_CHECKING:` block that imports every name eagerly for the checker, and an `else:` branch
that installs a PEP 562 `__getattr__` from an alias table
(`src/websockets/__init__.py`, `src/websockets/imports.py`). The table has two buckets, `aliases`
and `deprecated_aliases`; the second warns with `DeprecationWarning` and still forwards. At 17.1
that bucket holds **eleven names**, deprecated in 14.0 (2024-11-09) and still shipped, pointing at
a `legacy/` subpackage that is also still shipped.

### 4.4 litestar: sixty-six shim modules and 259 names, from moving names between public subpackages

litestar is the largest measured case of the specific failure our layout risks: names that were
public at `litestar.contrib.<topic>` and had to move to `litestar.plugins.<topic>`. Measured in
the installed 2.24.0 wheel by `grep -rl "^def __getattr__"`:

- **66 modules** in the package define a module-level `__getattr__`, and **all 66** call
  `warn_deprecation`. They cover **259 names** (`ast.literal_eval` over the `__all__` of the 54
  of them that declare one literally).
- The deprecations they carry name ten distinct versions in the `version=` keyword form — `2.1`,
  `2.3.2`, `2.4`, `2.9`, `2.9.0`, `2.12` (25 sites), `2.13`, `2.13.0`, `2.18.0`, `2.22.0` (13
  sites) — plus positional ones such as `2.3.0`, and **every shim is marked `removal_in="3.0"`**
  or `"3.0.0"` (52 and 19 sites). Nothing gets removed inside a major version, so each
  move adds a file that lives until the next major release.
- The shim shape is worth copying verbatim, because it satisfies the checkers and the runtime at
  once (`litestar/contrib/jinja.py`):

  ```python
  __all__ = ("JinjaTemplateEngine",)


  def __getattr__(attr_name: str) -> object:
      if attr_name in __all__:
          from litestar.plugins import jinja

          warn_deprecation(
              deprecated_name=f"litestar.contrib.jinja.{attr_name}",
              version="2.22.0",
              kind="import",
              removal_in="3.0.0",
              info=f"importing {attr_name} from 'litestar.contrib.jinja' is deprecated, please "
              f"import it from 'litestar.plugins.jinja' instead",
          )
          return getattr(jinja, attr_name)

      raise AttributeError(f"module {__name__!r} has no attribute {attr_name!r}")


  if TYPE_CHECKING:
      from litestar.plugins.jinja import JinjaTemplateEngine
  ```

  `warn_deprecation` builds the message from `version`, `kind` and `removal_in` and raises
  `LitestarDeprecationWarning`, with `kind="import"` producing "Import of deprecated import …"
  (`litestar/utils/deprecation.py`).
- One shim exists only because a module name was **misspelled**: `litestar/contrib/minijnja.py`
  forwards to `litestar/contrib/minijinja.py`, deprecated in 2.3.0, removal in 3.0.0 — and
  `minijinja.py` is itself a shim forwarding to `litestar.plugins.minijinja`. A typo in a public
  module name cost a file that has to be carried for a whole major version, and then a second file
  when the destination moved again.

### 4.5 The smaller cases

- **structlog** renamed `structlog.types` to `structlog.typing` in **22.2.0 (2022-11-19)**. The old
  module is still shipped at 26.1.0 (2026-06-06) — three years and seven months — as a plain
  re-export with a docstring that reads "Deprecated name for :mod:`structlog.typing`" and
  `.. deprecated:: 22.2.0`. There is no runtime warning: a name may sit on two module paths
  indefinitely with nothing telling the user which is canonical.
  `structlog.threadlocal`, deprecated in **22.1.0 (2022-07-20)**, is likewise still shipped and is
  still imported eagerly by `structlog/__init__.py`.
- **SQLAlchemy** kept `sqlalchemy.future` after the 2.0 migration finished. Its docstring says
  "2.0 API features. this module is legacy as 2.0 APIs are now standard.", and it re-exports
  `Connection`, `Engine`, `create_engine` and `select`. So `select`, documented at
  `sqlalchemy.sql.expression.select` (§3.2) and re-exported as `sqlalchemy.select`, gained a third
  live path. A subpackage created to stage a migration outlives the migration.
- **httpx** shows the opposite failure — removing something believed private. 0.27.2
  (2024-08-27) is a patch release whose single entry is "Reintroduced supposedly-private
  `URLTypes` shortcut", and by 0.28.1 the name is gone from the root again (measured: `URLTypes`
  is defined in `httpx/_types.py:33` and `import httpx; httpx.URLTypes` raises `AttributeError`).
  What made the removal safe the second time is the gate: `httpx/__init__.py` does
  `from ._types import *`, `httpx/_types.py` declares `__all__ = ["AsyncByteStream",
  "SyncByteStream"]`, and the root's own 69-entry `__all__` decides the rest. httpx also treats
  import cost as a release-note item: 0.28.0 records "Ensure `certifi` and `httpcore` are only
  imported if required."

### 4.6 anyio: a lazy root is itself a compatibility surface

anyio switched its root and `anyio.abc` to lazy imports in **4.15.0 (2026-09-02)**:

> Changed the `anyio` and `anyio.abc` modules to lazily (much like :pep:`810`) import the
> necessary submodules. This is done by parsing the AST of the module and building a lookup table
> from the `if TYPE_CHECKING:` block. A fallback mode has been provided for installations where
> the source code is unavailable (e.g. PyInstaller).

The author's own statement of intent, on the pull request: "It reads the re-exports from under the
`if TYPE_CHECKING:` block and turns it into a map it uses to process imports on demand via an
injected module-level `__getattr__()` function. This should keep both run-time tooling and static
type checkers happy."

**Three days later, 4.15.1 (2026-09-05)** shipped "a compatibility fix for supporting direct
access of `anyio.*` submodules from the main package even when those submodules were not directly
imported first", for issue #1311: *"After upgrading anyio to version 4.15.0, the application
started failing with the following error: `AttributeError: module 'anyio' has no attribute
'abc'`… The issue appears to be related to an incompatibility with one of the dependencies that
uses `anyio.abc`."* Downstream libraries had relied on `import anyio` making `anyio.abc` reachable
as an attribute — behaviour an eager `from . import abc as abc` provides and a lazy table did not.
The lazy root did not change one name, and it still broke users in a minor release.

### 4.7 What a large root costs at import time

Two controlled A/B measurements, both on the same host with the method of §1:

| Measurement | Eager | Lazy |
|---|---|---|
| `import anyio` — 4.14.0 (104 eager `X as X`) vs 4.15.1 (same names, lazy) | 86 ms, 92 ms | 22 ms, 32 ms |
| `import websockets` 17.1, then touch every name in `__all__`, vs the bare import | 123 ms, 143 ms | 46 ms, 59 ms |

Two numbers per cell are the minima from two independent sessions; the spread is the honest
precision of the method. Reading them: a 104-name eager root costs roughly **60–70 ms** that a
lazy root defers, and a 65-name eager root would cost roughly **65–95 ms**. Both are of the same
order as the interpreter's own startup (38–42 ms baseline in the same sessions).

The uncontrolled numbers, for scale only — these compare different libraries doing different work
at import time, so they do not isolate the root namespace:

| `import <library>` | Cost above bare interpreter startup |
|---|---|
| `starlette` (0 root names) | 3 ms |
| `msgspec` (21) | 40 ms |
| `attrs` (38) | 41 ms |
| `pydantic` (151, lazy) | 52 ms |
| `httpcore` (49) | 124 ms |
| `structlog` (31) | 196 ms |
| `httpx` (69) | 213 ms |
| `sqlalchemy` (250) | 279 ms |
| `dishka` (26) | 280 ms |
| `litestar` (20) | 282 ms |
| `faststream` (20) | 312 ms |
| `aiogram` (14) | 2,816 ms |

The pairs that matter are the ends: starlette, whose root is one line, costs 3 ms, and SQLAlchemy,
whose root is 250 eager re-exports, costs 279 ms. And the counter-example matters just as much:
aiogram's root re-exports 14 names and costs 2.8 s, because two of them are
`from . import methods, types` and those subpackages build hundreds of pydantic models. **Root
size is not the variable; what the root pulls in is.** For a Core with no third-party dependency
([ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md)) the whole effect is
likely to be single-digit milliseconds, and it is **[unverified]** for our package because there
is no package yet to measure.

PEP 810, *Explicit lazy imports*, is **Final** for **Python 3.15** (created 2025-10-02, resolved
2025-11-03), which makes the hand-rolled machinery of §4.3 and §4.6 a transitional cost rather
than a permanent design. Its own motivation quotes "This can reduce startup time by 50-70% in
practice" for command-line tools and "Memory savings of 30-40% have been observed in real
workloads" — figures for whole applications, not for one library's root, and cited here only to
show the direction the language is taking.

## 5. What the typing rules require

### 5.1 The specification

The typing specification's *Library interface* section is the rule everything else implements. In a
`py.typed` package:

> If a `py.typed` module is present, a type checker will treat all modules within that package
> (i.e. all files that end in `.py` or `.pyi`) as importable unless the file name begins with an
> underscore. These modules comprise the supported interface for the library.

> - Symbols whose names begin with an underscore (but are not dunder names) are considered private.
> - Imported symbols are considered private by default. A fixed set of import forms re-export
>   imported symbols.
> - A module can expose an `__all__` symbol at the module level that provides a list of names that
>   are considered part of the interface. This overrides all other rules above, allowing imported
>   symbols or symbols whose names begin with an underscore to be included in the interface.

The fixed set, from the *Import Conventions* section:

> The following import forms re-export symbols:
>
> - `import X as X` (a redundant module alias): re-exports `X`.
> - `from Y import X as X` (a redundant symbol alias): re-exports `X`.
> - `from Y import *`: if `Y` defines a module-level `__all__` list, re-exports all names in
>   `__all__`; otherwise, re-exports all public symbols in `Y`'s global scope.

Note what the specification does *not* contain: it says nothing about a module-level
`__getattr__` in a `.py` file. A search of the whole `docs/spec/` directory finds `__getattr__`
only in `concepts.rst`, and there it is about *instance* attribute access. PEP 562 module
`__getattr__` is therefore outside the specification, and any behaviour a checker shows for it is
that checker's own.

`warnings.deprecated` (PEP 702, specified in the typing specification's *Directives* chapter)
cannot mark an import path. The specification is explicit that it applies to an object: it "can be
used on a class, function or method to mark it as deprecated", and the diagnostics it mandates
cover "references through module, class, or instance attributes" and "`from` imports
(`from module import deprecated_object`)". Marking a re-exported alias would deprecate the object
everywhere, including at its new home. A *moved* name therefore needs a module-level shim, not
`@deprecated`.

### 5.2 pyright

`--verifytypes` measures type completeness of an installed `py.typed` package:

> Pyright will analyze the library, identify all symbols that comprise the interface to the
> library and emit errors for any symbols whose types are ambiguous or unknown. It also produces a
> "type completeness score" which is the percentage of symbols with known types.

> The `--verifytypes` feature can be integrated into a continuous integration (CI) system to
> verify that a library remains "type complete".

It measures *the interface it can see*, and it decides what that is by the rules above, with one
addition pyright documents beyond the specification:

> If a file `__init__.py` uses the form "from .A import X", symbol "A" is not private unless the
> name begins with an underscore (but "X" is still private).

So a root `__init__.py` that writes `from .core.event import Event as Event` makes `Event` public
*and* makes the submodule name `core` public, whether or not the reference documentation mentions
it. **[unverified]**: `pyright --verifytypes` could not be run against an installed library in this
environment — every invocation, including against `anyio`, reported `Package directory: ""` and
`error: No py.typed file found` with a score of 0 %, on both pyright 1.1.411 and 1.1.403, while an
ordinary `pyright` check of the same environment resolved `anyio.sleep` correctly. The two
quotations above are from the documentation, not from a local run.

Two pyright rules bear on the mechanism, with their documented defaults:

- `reportPrivateImportUsage` — "Generate or suppress diagnostics for use of a symbol from a
  'py.typed' module that is not meant to be exported from that module. The default value for this
  setting is `"error"`." It is `"error"` in basic, standard and strict alike.
- `reportUnsupportedDunderAll` — "Also reports names within the `__all__` list that are not
  present in the module namespace. The default value for this setting is `"warning"`" and
  `"error"` in strict.

### 5.3 mypy

`implicit_reexport` defaults to `True`, and `--no-implicit-reexport` turns it off:

> By default, imported values to a module are treated as exported and mypy allows other modules to
> import them. When false, mypy will not re-export unless the item is imported using from-as or is
> included in `__all__`. Note that mypy treats stub files as if this is always disabled.

`--strict` includes it. Measured, not quoted: `mypy 2.3.1 --help` lists `--no-implicit-reexport`
among the thirteen flags `--strict` enables.

### 5.4 ty and pyrefly

ty states its position in `docs/coming-from-mypy-or-pyright.md`, in the row that pairs mypy's
`attr-defined` "(extended by `--no-implicit-reexport`)" with pyright's `reportPrivateImportUsage`:
the ty column reads **"None yet (tracked in #200)"**, and issue **#200 is "Add `implicit-reexport`
rule for runtime files"**, open on the research date. For the `__all__` check
(`reportUnsupportedDunderAll`) ty's column points at **Ruff `F822`**, `PLE0604`, `PLE0605` and
`PYI056` rather than at a rule of its own.

pyrefly publishes no position on implicit re-export that this note could find. **[unverified]**:
the search covered its rule list as exercised below and the ty comparison table, not the pyrefly
documentation site.

### 5.5 Measured: what the four checkers actually do

Two fixtures, both `py.typed` packages installed into a virtual environment's `site-packages`,
consumed from a module outside it.

**Fixture 1 — implicit re-export.** `implicitpkg/__init__.py` is one line,
`from ._impl import Declared` (no `as`, no `__all__`); the consumer writes
`from implicitpkg import Declared`.

| Checker | Result |
|---|---|
| mypy 2.3.1 `--strict` | `error: Module "implicitpkg" does not explicitly export attribute "Declared" [attr-defined]` |
| mypy 2.3.1 default | no error |
| pyright 1.1.411 | `error: "Declared" is not exported from module "implicitpkg" — Import from "implicitpkg._impl" instead (reportPrivateImportUsage)` |
| ty 0.0.79 | no diagnostic (confirmed to resolve the package: it reports `invalid-assignment` for `x: int = Declared`) |
| pyrefly 1.2.0, `preset = "strict"` | no diagnostic (same confirmation, `bad-assignment`) |

**Fixture 2 — a name provided only by a module `__getattr__`.** `lazypkg/__init__.py` declares
`__all__ = ["Declared", "InAllOnly", "Undeclared"]`, imports only `Declared` under
`if TYPE_CHECKING`, and defines `def __getattr__(name: str) -> Any`. The consumer imports
`Declared`, `InAllOnly`, `Undeclared` and a fourth name, `Missing`, that appears nowhere.

| Checker | `Declared` (declared under `TYPE_CHECKING`) | `InAllOnly` (in `__all__` only) | `Undeclared` | `Missing` |
|---|---|---|---|---|
| mypy 2.3.1 `--strict` | `def () -> lazypkg._impl.Declared` | `Any` | `Any` | no error |
| pyright 1.1.411 | `type[Declared]` | `Any` | `Any` | no error |
| ty 0.0.79 | `<class 'Declared'>` | `Any` | `Any` | no error |
| pyrefly 1.2.0 strict | `type[Declared]` (errors on `x: int = Declared`) | silent | silent | no error |

All four agree, and the agreement is the finding: **a module-level `__getattr__` makes the whole
module's namespace unbounded and untyped.** Every name it can serve becomes `Any`, `__all__` does
not rescue it, and a name that does not exist at all imports without complaint. The only names
that keep their types are the ones written out under `if TYPE_CHECKING` — which is exactly why
websockets 12.0 and anyio 4.15.0 both write them out (§4.3, §4.6). A checker cannot see a PEP 562
name unless it is declared, and nothing in the specification obliges it to try.

**Fixture 3 — a name in `__all__` that is not in the module.** `eagerpkg/__init__.py` is
`from ._impl import Declared as Declared` plus `__all__ = ["Declared", "Ghost"]`.

| Tool | Result |
|---|---|
| pyright 1.1.411 | `warning: "Ghost" is specified in __all__ but is not present in module (reportUnsupportedDunderAll)` |
| pyrefly 1.2.0 strict | `ERROR Name 'Ghost' is listed in '__all__' but is not defined in the module [bad-dunder-all]` |
| mypy 2.3.1 `--strict` | no diagnostic |
| ty 0.0.79 | no diagnostic |
| ruff 0.16.6, `F822`, default | no diagnostic — **the rule is skipped in `__init__.py`** |
| ruff 0.16.6, `F822`, `--preview` | `undefined-export: Undefined name 'Ghost' in '__all__'` |

ruff documents the exemption in the rule itself: "In [preview], this rule will flag undefined names
in `__init__.py` file, even if those names implicitly refer to other modules in the package. Users
that rely on implicit exports should disable this rule in `__init__.py` files via
`lint.per-file-ignores`."

**Fixture 5 — litestar's shim shape.** The exact form of §4.4 was reproduced: `__all__ =
("Declared",)`, a module-level `__getattr__` that forwards only names in `__all__` and otherwise
raises `AttributeError`, and a trailing `if TYPE_CHECKING: from ._impl import Declared` (a *plain*
import, made explicit by `__all__`). All four checkers type the name correctly — each reports
`type[Declared]` is not assignable to `int` for `x: int = Declared`: mypy 2.3.1 `--strict`
(`[assignment]`), pyright 1.1.411 (`reportAssignmentType`), ty 0.0.79 (`invalid-assignment`),
pyrefly 1.2.0 strict (`bad-assignment`). So the shim shape §6.4 recommends is measured, not
inferred.

**Fixture 4 — the `X as X` form and ruff.** `PLC0414` (`useless-import-alias`) fires on
`from os import path as path` in an ordinary module and stays silent in `__init__.py`; the rule's
own documentation says so in its second line: "This rule does not apply in `__init__.py` files."
So the explicit re-export form of `ST-MOD-03` needs no lint relaxation in a package `__init__.py`,
and does need one in any other module that re-exports.

## 6. Recommendation

This section is the input ticket #24 asked for, and #24 has since taken its decisions:
[ADR-0042](../adr/0042-a-public-name-is-documented-at-its-package-path.md) fixes the documented
path and [ADR-0043](../adr/0043-explicit-re-export-with-a-reference-page-as-the-public-list.md)
fixes the mechanism. Where an ADR went further than the evidence below, or the other way, the ADR
is the decision and this section is only its evidence.

### 6.1 What was already decided, and what was left

[ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md) has already fixed the root at
"on the order of ten to fifteen names", put the adapter in `aiommbot.mattermost`, each Plugin in
its own subpackage and the toolkit in `aiommbot.testing`, and made a name public only when all
four criteria hold. That decides against **(B)**: a 35-name root is outside the decided band, and
the measured witnesses for a root that large — pydantic at 151, SQLAlchemy at 250 — pay for it
with machinery (§3.2) that a Core with no third-party dependency has no reason to build.

Criterion 3 also settles more than it looks. "It is re-exported from the subpackage that owns it,
explicitly" means `aiommbot/core/__init__.py` re-exports every public Core name, and the typing
specification then treats `aiommbot.core.Event` as part of the interface (§5.1). The root's own
`from .core import Event as Event` adds a second interface path. So **two paths are mechanically
available for every headline name whatever we choose**, and the only lever left is criterion 4:
which path the reference documentation names. That is the whole of the (A)-versus-(C) question.

### 6.2 The recommendation: (A), with the package path — never the module path

Taken as
[ADR-0042](../adr/0042-a-public-name-is-documented-at-its-package-path.md).

**Choose (A).** Document each public name at exactly one path, and let the path be one of two
forms only:

```text
aiommbot.<Name>                 the headline Core names (ADR-0007's ten to fifteen)
aiommbot.core.<Name>            every other public Core name
aiommbot.mattermost.<Name>      the Adapter
aiommbot.plugins.<name>.<Name>  a generic Plugin
aiommbot.testing.<Name>         the toolkit
```

And **never** document `aiommbot.core.<module>.<Name>`. This is the part the evidence argues
hardest for, and it is why (A) is preferable to (C) rather than merely different.

Every measured case where a public surface change hurt was a **module-level move inside a stable
package**:

| The move | Announced | Shim still shipped at | Cost |
|---|---|---|---|
| `websockets.http` → `websockets.datastructures`; four modules → `websockets.legacy` | 9.0, 2021-05-01 | removed in 17.0, 2026-07-29 | 5 y 3 m of aliases |
| `websockets.connection` → `websockets.protocol` (+ three class renames) | 11.0, 2023-04-02 | 17.1 | still carried |
| `structlog.types` → `structlog.typing` | 22.2.0, 2022-11-19 | 26.1.0, 2026-06-06 | 3 y 7 m, no warning |
| `litestar.contrib.<topic>` → `litestar.plugins.<topic>`, plus module moves under `utils/`, `repository/`, `middleware/`, `template/`, `types/` | 2.1 … 2.22.0 | 2.24.0 | 66 shim modules, 259 names |
| `pydantic.utils`, `pydantic.parse`, ten more → elsewhere | 2.0, 2023-06-30 | 2.13.5, 2026-08-28 | 12 shim modules + a 226-entry table |

None of them was a *package* move. Packages are stable because they are named after the
architecture; modules are unstable because they are named after files, and
[`engineering-style.md`](../design/engineering-style.md) `ST-MOD-09` *requires* that a module be
split the moment it holds more than one component or part. A documented module path therefore
promises the one thing our own rules guarantee will change. Documenting the package path instead
makes every future split a non-event, and it costs the user nothing: `from aiommbot.core import
StateSpec` is no longer than `from aiommbot.core.state import StateSpec`.

The corollary for the root tier: a root name is an alias the library can silently repoint, which is
precisely what websockets 14.0 did to `from websockets import connect` (§4.3). So the root should
carry only names whose *meaning* cannot be reassigned — the envelope, the router, the bot, the
Protocol seams — and never a name that selects an implementation. Put another way, the argument for
(C) is real and this is its residue: keep out of the root anything a future version might want to
point somewhere else.

### 6.3 The rule for adding a public name, so no ticket renegotiates it

Three lines, each mechanical enough that a reviewer does not have to have taste:

1. **Which path.** A name is documented at the root if and only if a user writing their first bot
   must name it in the first file they write. Everything else is documented at its rank's package
   path. The root list is **closed**: adding to it amends
   [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md); adding a name at a rank
   path is an ordinary pull request. The observed band for a framework's closed root is 14–20
   names (aiogram 14, django-modern-rest 16, litestar 20, faststream 20), so ADR-0007's ten to
   fifteen is at the low end of practice, not below it.
2. **Which form.** The two candidate mechanisms are checked by different tools and neither is
   sufficient alone. `X as X` is what the specification's *Import Conventions* recognise (§5.1) and
   nothing checks that the set of aliases matches the documentation. `__all__` is the only form any
   tool can check for *completeness* — pyright's `reportUnsupportedDunderAll`, pyrefly's
   `bad-dunder-all` and ruff's `F822` under `preview` all report a name in `__all__` that the
   module does not have (§5.5) — and it brings a drift with a direction: because `__all__`
   "overrides all other rules" (§5.1), a name re-exported `X as X` but forgotten in the list is
   silently private for consumers, and no tool reports that.
   [ADR-0043](../adr/0043-explicit-re-export-with-a-reference-page-as-the-public-list.md) decided
   this: the alias form alone, no `__all__`, and a bidirectional guard test against a hand-written
   reference page in place of the tooling `__all__` would buy.
3. **Which rank.** Unchanged from `ST-MOD-05`: the layer table decides, and a name that would need
   an import in the wrong direction is a missing seam, not a new root export.

Note the finding behind line 2's insistence on the *package* re-export: an import rank is an
architecture boundary and does not have to be a public import path at all. httpx (fifteen private
modules and one private package), httpcore, structlog, anyio (`_core/`, `_backends/`) and attrs
all keep their entire internal structure behind underscore-prefixed modules and expose one
namespace. Our four ranks are import-linter contracts and directories; only the names ADR-0007's
criteria admit are paths.

### 6.4 The mechanism that keeps a moved name from breaking users

Adopted in the consequences of
[ADR-0042](../adr/0042-a-public-name-is-documented-at-its-package-path.md); the removal window over
it is #28's.

Copy litestar's shim shape (§4.4) — measured in §5.5, fixture 5, to satisfy the runtime and all
four checkers at once — and give it one project-owned warning type:

- the old path stays as a module (or package) whose body is a literal `__all__`, a module-level
  `__getattr__` that warns and forwards, and an `if TYPE_CHECKING:` block importing the name from
  its new home. Without that block the name is `Any` in every checker and a typo imports cleanly
  (§5.5, fixture 2);
- the warning is a project subclass of `DeprecationWarning` and carries three facts: the version
  that deprecated the path, the version that removes it, and the new path. litestar's
  `warn_deprecation(version=…, kind="import", removal_in=…, alternative=…)` is the reference
  signature;
- removal only at a major version, as litestar does with `removal_in="3.0"` on all 66 shims;
- **not** `warnings.deprecated`: §5.1 shows PEP 702 deprecates an object, so marking a re-export
  would warn at the new path too;
- when a name leaves the distribution entirely, forwarding is impossible and the best available
  outcome is a typed import error naming the new package — pydantic's `BaseSettings` message is the
  model.

If the surface goes lazy later, the shape to adopt is anyio's (`if TYPE_CHECKING:` as the single
source of truth, parsed into the runtime table) rather than a hand-written second table like
pydantic's — but §4.6 is the warning attached: anyio's lazy root broke `anyio.abc` for downstream
libraries in a minor release and needed a patch three days later. PEP 810 being Final for Python
3.15 (§4.7) means this whole mechanism has a scheduled replacement, and nothing here should be
built as if it were permanent.

### 6.5 Where the evidence is thin

- **No witness for our shape.** Not one of the fifteen libraries documents a public, non-topical
  subpackage as the home of its platform-independent core (§3.4). The libraries with a small
  curated root got it by making implementation modules private; the libraries with public deep
  packages named them after topics. So §6.2's "`aiommbot.core.<Name>`" is an extrapolation from
  the *failure* modes of module paths, not an imitation of a working example.
- **`pyright --verifytypes` is unmeasured here.** §5.2's claims about it are documentation, not a
  local run; the tool would not resolve an installed package in this environment.
- **Import cost for our package is unmeasured**, and the aiogram result (14 root names, 2.8 s)
  shows the number depends on what the root pulls in, not on how many names it has.
- **pyrefly's documented position** on implicit re-export was not found (§5.4).
- **The counterfactual is unobserved.** No library in the set documents package paths only, so
  there is no measured case of a library that *avoided* the module-move cost by that rule. The
  argument in §6.2 is that the cost cannot arise, not that somebody has demonstrated it does not.

## 7. Sources

### Library source and metadata (GitHub contents API at the tag named, plus `releases/latest`)

- attrs 26.1.0 — https://github.com/python-attrs/attrs — `src/attrs/__init__.py`,
  `src/attr/__init__.py`, `docs/names.md`
- httpx 0.28.1 — https://github.com/encode/httpx — `httpx/__init__.py`, `httpx/_types.py`,
  `CHANGELOG.md`
- httpcore 1.0.9 — https://github.com/encode/httpcore — `httpcore/__init__.py`
- starlette 1.6.0 — https://github.com/encode/starlette — `starlette/__init__.py`
- litestar 2.24.0 — https://github.com/litestar-org/litestar — `litestar/__init__.py`,
  `litestar/contrib/jinja.py`, `litestar/contrib/minijnja.py`, `litestar/utils/deprecation.py`,
  `docs/reference/` (`handlers.rst` and its siblings)
- faststream 0.7.5 — https://github.com/ag2ai/faststream — `faststream/__init__.py`
- aiogram 3.31.0 — https://github.com/aiogram/aiogram — `aiogram/__init__.py`,
  `docs/dispatcher/router.rst`
- pydantic 2.13.5 — https://github.com/pydantic/pydantic — `pydantic/__init__.py`,
  `pydantic/_migration.py`, `pydantic/utils.py`, `pydantic/error_wrappers.py`,
  `docs/api/base_model.md`, `docs/api/fields.md`
- msgspec 0.21.1 — https://github.com/jcrist/msgspec — `src/msgspec/__init__.py`,
  `src/msgspec/__init__.pyi`
- websockets 17.1 — https://github.com/python-websockets/websockets —
  `src/websockets/__init__.py`, `src/websockets/imports.py`, `docs/project/changelog.rst`,
  `docs/reference/index.rst`, `docs/reference/asyncio/client.rst`
- anyio 4.15.1 — https://github.com/agronholm/anyio — `src/anyio/__init__.py`,
  `src/anyio/_lazyimport.py`, `docs/versionhistory.rst`, pull request
  https://github.com/agronholm/anyio/pull/1169, issue
  https://github.com/agronholm/anyio/issues/1311
- structlog 26.1.0 — https://github.com/hynek/structlog — `src/structlog/__init__.py`,
  `src/structlog/types.py`, `src/structlog/typing.py`, `src/structlog/threadlocal.py`,
  `docs/api.rst`
- SQLAlchemy 2.0.52 — https://github.com/sqlalchemy/sqlalchemy — `lib/sqlalchemy/__init__.py`,
  `lib/sqlalchemy/future/__init__.py`, `doc/build/core/selectable.rst`
- dishka 1.10.1 — https://github.com/reagento/dishka — `src/dishka/__init__.py`
- django-modern-rest 0.14.0 — https://github.com/wemake-services/django-modern-rest —
  `dmr/__init__.py`, `README.md`, `docs/pages/deep-dive/public-api.rst`; further facts in
  [`docs/research/21`](21-measured-facts-behind-the-rules.md)

### Specifications

- Typing specification, *Distributing type information* —
  https://typing.python.org/en/latest/spec/distributing.html
  (sections *Library interface (public and private symbols)* and *Import Conventions*); source
  `docs/spec/distributing.rst` in https://github.com/python/typing
- Typing specification, *Directives* — `@deprecated` (PEP 702) —
  https://typing.python.org/en/latest/spec/directives.html
- PEP 562, *Module `__getattr__` and `__dir__`* — https://peps.python.org/pep-0562/
- PEP 702, *Marking deprecations using the type system* — https://peps.python.org/pep-0702/
- PEP 810, *Explicit lazy imports* — https://peps.python.org/pep-0810/ (Status Final,
  Python-Version 3.15, resolved 2025-11-03); source `peps/pep-0810.rst` in
  https://github.com/python/peps

### Type checkers and linters

- pyright — *Typed libraries* — https://microsoft.github.io/pyright/#/typed-libraries
  (*Type Completeness*, *Verifying Type Completeness*); *Configuration* —
  https://microsoft.github.io/pyright/#/configuration (`reportPrivateImportUsage`,
  `reportUnsupportedDunderAll`, and the per-mode defaults table)
- mypy — https://mypy.readthedocs.io/en/stable/config_file.html#confval-implicit_reexport and
  https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-no-implicit-reexport
- ty — *Coming from mypy or pyright* — https://github.com/astral-sh/ty
  (`docs/coming-from-mypy-or-pyright.md`); issue https://github.com/astral-sh/ty/issues/200
- pyrefly — https://pyrefly.org
- ruff — `F822` (`undefined-export`) and `PLC0414` (`useless-import-alias`) rule documentation —
  https://docs.astral.sh/ruff/rules/undefined-export/ and
  https://docs.astral.sh/ruff/rules/useless-import-alias/; source
  `crates/ruff_linter/src/rules/pyflakes/rules/undefined_export.rs` and
  `crates/ruff_linter/src/rules/pylint/rules/useless_import_alias.rs` in
  https://github.com/astral-sh/ruff

### Local measurements

Tool versions used for §4.7 and §5.5: CPython 3.14.7, mypy 2.3.1, pyright 1.1.411 (and 1.1.403),
ty 0.0.79, pyrefly 1.2.0, ruff 0.16.6, pip-installed from PyPI on 2026-09-09.
