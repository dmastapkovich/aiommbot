# Plugin systems worth learning from: extending a small async core safely

Research date: 2026-09-02. Sources are primary (official docs, framework/library source on GitHub).
Claims I could not confirm from a primary source are marked **[unverified]**.

## 1. Django: `INSTALLED_APPS` and `AppConfig` as the reference model

**Registration is convention with an explicit override, not pure discovery.** `INSTALLED_APPS` is an
explicit list of dotted paths, but each entry may name a plain package (implicit) or a specific
`AppConfig` subclass (explicit). If a package is named and its `apps.py` has exactly one `AppConfig`
subclass, that one is used; with several, Django looks for the one with `AppConfig.default = True`;
otherwise the base `AppConfig` is used
([docs.djangoproject.com/en/5.2/ref/applications](https://docs.djangoproject.com/en/5.2/ref/applications/)).
This gives the common case zero ceremony while still letting a reusable app disambiguate explicitly.

**`AppConfig` fields are metadata, not behavior.** `name` (import path, globally unique), `label`
(short name, used in migration dependency records — changing it later "will result in breaking
changes"), `verbose_name`, `path`, and `default_auto_field` are plain attributes read once at startup.

**`ready()` is the one sanctioned side-effect hook, and it is deliberately late.** "It is called as soon
as the registry is fully populated," and the docs immediately warn against DB access there, because
"your `ready()` method will run during startup of every management command" — even `manage.py test`
against production settings. This is the clearest argument for why import-side-effect registration is
discouraged: Django's boot is staged — stage 1 imports app configs (no models yet; `get_app_config()`
becomes usable), stage 2 imports each app's `models` module (`get_model()` becomes usable), stage 3 calls
every `ready()`; `apps.ready` flips only once all three finish. A plugin system with only "module import"
as its extension point collapses these phases and reopens the exact bug class (`AppRegistryNotReady`)
this staging exists to prevent.

**Signals are the low-friction seam, and are now async-aware.** `Signal.connect(receiver, sender=None,
weak=True, dispatch_uid=None)` stores receivers as weak references by default — a plugin connecting a
closure without keeping its own reference will have it silently collected unless it passes `weak=False`
([docs.djangoproject.com/en/5.2/topics/signals](https://docs.djangoproject.com/en/5.2/topics/signals/)).
Since 5.0, four senders exist (`send`/`send_robust`/`asend`/`asend_robust`) and receivers may be sync or
async in either case: "Synchronous receivers will be called using `sync_to_async()` when invoked via
`asend()`. Asynchronous receivers will be called using `async_to_sync()` when invoked via `send()`."
Receivers are grouped by sync/async before dispatch (cross-group order is not guaranteed); async
receivers within a group run concurrently via `asyncio.gather()`.

**The checks framework validates configuration without side effects.** `@register(Tags.compatibility,
deploy=True)` registers `(app_configs, **kwargs) -> list[CheckMessage]`; fields/models/backends can
instead define their own `check()` classmethod
([docs.djangoproject.com/en/5.2/topics/checks](https://docs.djangoproject.com/en/5.2/topics/checks/)).
Checks only run on explicit invocation or before commands like `runserver`/`migrate` — never at import
or `ready()` time.

**Management commands are directory convention, not an import-time registry.** Any non-underscore `.py`
file under `<app>/management/commands/` becomes a CLI subcommand exposing `Command(BaseCommand)` with
`handle(self, *args, **options)`/`add_arguments(self, parser)`
([docs.djangoproject.com/en/5.2/howto/custom-management-commands](https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/)).

**Settings: `getattr(settings, "X", default)` vs an `AppSettings` object.** Scattering `getattr` calls
means the default lives wherever first read and can't react to test overrides. DRF's
`rest_framework.settings.APISettings` is the fix: `__getattr__` checks a `DEFAULTS` dict (raising
`"Invalid API setting: '%s'"` for unknown keys), resolves `IMPORT_STRINGS` dotted paths lazily, and
caches the result (`self._cached_attrs.add(attr); setattr(self, attr, val)`); `reload()`, wired to
Django's `setting_changed` signal, clears the cache for tests. One singleton is exported:
`api_settings = APISettings(None, DEFAULTS, IMPORT_STRINGS)`
([rest_framework/settings.py](https://raw.githubusercontent.com/encode/django-rest-framework/master/rest_framework/settings.py)).
This — one typed object per app/plugin owning its own defaults and cache invalidation — is a direct
precedent for plugin configuration.

## 2. pytest/pluggy: hook specifications, implementations, entry-point discovery

Pluggy is "the crystallized core of plugin management and hook calling for pytest"; pytest itself "is
composed as a set of pluggy plugins which are invoked in sequence"
([pluggy.readthedocs.io](https://pluggy.readthedocs.io/en/stable/index.html)). `hookspec =
pluggy.HookspecMarker("myproject")` / `hookimpl = pluggy.HookimplMarker("myproject")` are markers scoped
to one project name, so decorated functions for one pluggy-based project are invisible to another's
`PluginManager`. A `@hookspec` analyzes only the function's name and argument names; a `@hookimpl` is
"just a (callback) function which has been appropriately marked," added via `register()`. Ordering:
`tryfirst`/`trylast` reposition an implementation; `wrapper=True` (new, `yield`-based) or
`hookwrapper=True` (legacy) wrap all other implementations. Collection: every non-`None` return is
appended to a list in **LIFO registered order**; `@hookspec(firstresult=True)` stops at the first
non-`None` result. `PluginManager.load_setuptools_entrypoints(group)` auto-registers entry points — the
mechanism behind pytest's own `pytest11` group.

pytest layers conventions on top: `conftest.py` files are local per-directory plugins with no packaging
step; `-p no:NAME` disables a plugin; `pytest_plugins` force-loads specific modules; startup order is
`-p no:name` → builtins → `-p name` → entry-point plugins → env-var plugins → conftests
([docs.pytest.org/writing_plugins](https://docs.pytest.org/en/stable/how-to/writing_plugins.html)).
pytest ships its own **contract test kit**: the `pytester` fixture builds temporary `conftest.py`/test
files and runs them as a real pytest invocation, so plugin behavior is asserted against real collection
rather than mocks.

**Pluggy has no async hooks; the ecosystem's fix is a runtime shim, not a fork.** Datasette (asyncio +
pluggy) documents the mismatch: pluggy hooks are "regular non-awaitable Python functions," so Datasette's
`await_me_maybe(value)` — call if callable, await if awaitable, else return — lets a hook be sync,
coroutine-returning, or `async def`
([docs.datasette.io/internals](https://docs.datasette.io/en/1.0a14/internals.html);
rationale: [simonwillison.net/await-me-maybe](https://simonwillison.net/2020/Sep/2/await-me-maybe/)).
This has a documented sharp edge: `firstresult=True` short-circuits on the first non-`None` value, but a
coroutine object is never `None` even if its eventual result would be, breaking the short-circuit — a
bug Datasette hit in production
([github.com/simonw/datasette/issues/1425](https://github.com/simonw/datasette/issues/1425)). Lesson for
an async-native framework: make the hook protocol `async def` from the start rather than retrofitting a
sync hook system with a shim.

## 3. Entry points (`importlib.metadata.entry_points`): best practice and pitfalls

`entry_points(group=...)` returns an `EntryPoints` collection; each `EntryPoint` exposes `.name`,
`.group`, `.value`, derived `.module`/`.attr`/`.extras`, `.dist`, and `.load()`, which performs the actual
import
([docs.python.org/importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html#entry-points)).
The two-phase split — cheap metadata-only discovery vs. expensive `.load()` — lets a host enumerate
available plugins without paying every plugin's import cost, and defer import until one is selected.

Two source-confirmed implementations show the disciplined pattern. **pydantic** uses a private
`PYDANTIC_ENTRY_POINT_GROUP: Final[str] = 'pydantic'`, iterates `importlib_metadata.distributions()`,
loads matching entry points individually via `.load()`, guards against **recursion** (a plugin package
that itself uses pydantic at import time) with a `_loading_plugins: bool` flag, caches results in
`_plugins`, and honors `PYDANTIC_DISABLE_PLUGINS` (`__all__`/`1`/`true`, or a comma-separated name list)
([pydantic/plugin/_loader.py](https://raw.githubusercontent.com/pydantic/pydantic/main/pydantic/plugin/_loader.py)).
**Hypothesis** uses a `"hypothesis"` entry-point group so a library can auto-register a strategy for its
own type: "nothing happens unless Hypothesis is already in use, and it's totally seamless for downstream
users" ([hypothesis.readthedocs.io/extensions](https://hypothesis.readthedocs.io/en/latest/extensions.html));
pydantic ships its own `_hypothesis_plugin.py` this way. The common shape: entry points are for
third-party discovery by name, gated behind an explicit disable switch, with import deferred and
recursion-guarded — never a bulk "import everything installed" step.

## 4. ASGI-era frameworks: explicit lists over magic, and where each draws the line

**FastStream** treats "plugin" as middleware plus broker-specific integration, not a generic hook
registry. `BaseMiddleware` exposes `on_receive()`, `consume_scope(call_next, msg)`,
`publish_scope(call_next, cmd)`, `after_processed(...)` — a chain-of-responsibility requiring
`call_next` — attached via an explicit `Broker(middlewares=[...])` list
([faststream.ag2.ai/middlewares](https://faststream.ag2.ai/latest/getting-started/middlewares/)).
Observability ships as extras plus **broker-specific** classes: `faststream[prometheus]` +
`NatsPrometheusMiddleware(registry=...)`, `faststream[otel]` + e.g. `RabbitOtelMiddleware`, because
instrumentation needs broker-specific command attributes
([faststream.ag2.ai/opentelemetry](https://faststream.ag2.ai/latest/getting-started/observability/opentelemetry/)).
No entry-point discovery anywhere — every plugin is explicitly imported and passed in.

**Litestar** has the richest plugin *type system* studied: `litestar/plugins/base.py` defines narrow
protocols rather than one fat interface — `InitPlugin` (`on_app_init(app_config) -> AppConfig`, rewrites
app construction), `ReceiveRoutePlugin` (`receive_route(route)`, observes route registration),
`SerializationPlugin` (`supports_type`/`create_dto_for_type`), `DIPlugin` (`has_typed_init`/
`get_typed_init`, extends DI to types like Pydantic models whose `__init__` isn't directly
introspectable), `OpenAPISchemaPlugin` (`to_openapi_schema`), and `CLIPlugin` (`on_cli_init(cli:
click.Group)` plus `server_lifespan`)
([docs.litestar.dev/plugins](https://docs.litestar.dev/latest/usage/plugins/index.html),
[litestar/plugins/base.py](https://raw.githubusercontent.com/litestar-org/litestar/main/litestar/plugins/base.py)).
Registration is uniformly explicit — `Litestar(plugins=[...])` — and multiple `InitPlugin`s run in list
order, each seeing the previous one's `AppConfig` output. Optional integrations are guarded by
`MissingDependencyException(package, install_package=None, extra=None)`, turning a bare
`ModuleNotFoundError` into "install `litestar[sqlalchemy]`".

**FastAPI/Starlette deliberately have no plugin system.** Extensibility is `APIRouter` +
`include_router()`, `Depends`-based DI as the cross-cutting seam, and `app.dependency_overrides` — a
dict swap that works "regardless of where the dependency is used ... a path operation function ..., a
`.include_router()` call, etc."
([fastapi.tiangolo.com/testing-dependencies](https://fastapi.tiangolo.com/advanced/testing-dependencies/)).
Lifespan is one `@asynccontextmanager` passed to `FastAPI(lifespan=...)`; the docs warn this "will only
be executed for the main application, not for Sub Applications (Mounts)" — no built-in composition of
multiple lifespans
([fastapi.tiangolo.com/events](https://fastapi.tiangolo.com/advanced/events/)).

**Sanic-Ext is the cautionary tale for implicit activation:** "If it is installed in the environment, it
is setup and ready to go" — no explicit registration call in current versions
([sanic.dev/sanic-ext](https://sanic.dev/en/plugins/sanic-ext/getting-started.html)). `pip install` alone
can change request-handling behavior with no application code marking the decision — the opposite of
Django's checks framework and pydantic's `PYDANTIC_DISABLE_PLUGINS`.

**aiogram** has no plugin system; its seams are `Router`/`include_router` composition (depth-first,
first non-`UNHANDLED` wins), `BaseMiddleware` (outer/inner around the single `update` observer), and
`Dispatcher`'s `workflow_data` dict injected by parameter name — confirmed in this repo's prior research
(`docs/research/03-bot-framework-architectures.md`, citing `dispatcher/dispatcher.py`,
`dispatcher/router.py`). Third-party DI (`dishka.integrations.aiogram`) bolts on as one more middleware,
evidence that "middleware + typed context dict" is a sufficient seam for a bot framework.

## 5. Declarative metadata done well: Home Assistant integrations

`manifest.json` is the strongest example of pure declarative metadata plus explicit ordering, with zero
code executed to determine it: required fields include `domain`, `name`, `codeowners`, `dependencies`,
`documentation`, `integration_type`, `iot_class`, `requirements`
([developers.home-assistant.io/manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/)).
`dependencies` are hard prerequisites ("necessary if you want to offer functionality from that other
integration, like webhooks or an MQTT connection"), guaranteed loaded first; `after_dependencies` are
soft — HA "will wait for" them but proceeds if they're absent. Runtime setup is `async_setup_entry(hass,
entry) -> bool` (after any `async_migrate_entry`), typically forwarding to platforms via
`hass.config_entries.async_forward_entry_setups(...)`; failure uses typed exceptions
(`ConfigEntryNotReady` → retry with backoff, `ConfigEntryAuthFailed` → re-auth) instead of a bare
exception
([developers.home-assistant.io/config_entries](https://developers.home-assistant.io/docs/config_entries_index/)).
The lesson: separate static ordering metadata (name, hard/soft dependency names) from the imperative
setup coroutine, and give failure a small closed taxonomy of typed outcomes.

## 6. A clean event-bus model: Sphinx extensions

Where Django and Litestar are "rich metadata + typed lifecycle," Sphinx is the cleanest small
*event bus*. "An extension is simply a Python module with a `setup()` function," called as `setup(app)`;
it returns metadata (`version`, `env_version`, `parallel_read_safe`/`parallel_write_safe`)
([sphinx-doc.org/extdev](https://www.sphinx-doc.org/en/master/extdev/index.html)). Everything else goes
through `app`: `app.add_config_value(...)` declares a config key; `app.connect(event, callback)`
subscribes to a build-lifecycle event — plain pub/sub, registration-order only, no inheritance to
implement. This is the right model for a lightweight, observe-only hook layer sitting beside a heavier
lifecycle-plugin layer.

## 7. Isolation and typing of optional extension points

**Import-boundary enforcement, confirmed in a real, strictly-typed project.**
`wemake-services/django-modern-rest` (20k LOC, checked with mypy/pyright/ty/pyrefly in strict mode)
ships a root `.importlinter` `forbidden` contract naming optional dependencies — `pydantic`, `msgspec`,
`jwt`, `allauth`, `openapi_spec_validator`, `polyfactory`, `yaml`, `attrs`/`attr`, `cattrs` — confined to
`dmr.plugins.msgspec.*`, `dmr.plugins.pydantic.*`, `dmr.security.jwt.*`, `dmr.security.allauth.*`, plus
narrower single-module confinements
([repo](https://github.com/wemake-services/django-modern-rest),
[.importlinter](https://github.com/wemake-services/django-modern-rest/blob/master/.importlinter)).
Separate `independence` contracts stop plugin/OpenAPI/object/view subsystems from cross-importing. This
is a CI-enforced, machine-checked version of Litestar's `MissingDependencyException` and pydantic's
guarded loader: unmet optional dependencies fail inside the plugin package alone, not at framework
import.

**`Protocol` vs `ABC`.** `typing.Protocol` gives structural subtyping — no explicit inheritance required
— versus an ABC's nominal subtyping
([docs.python.org/typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)).
`@runtime_checkable` enables `isinstance()` against a Protocol but "will check only the presence of the
required methods or attributes, not their type signatures or types" (the docs' own counter-example:
`ssl.SSLObject` passes an `issubclass()` check against `Callable` yet cannot be called), and is
documented as "surprisingly slow" versus a nominal check. Use Protocol for *static* checking that a
plugin implements the right shape; don't lean on `isinstance()` against it as a runtime correctness gate.

**PEP 695 generics for typed plugin config.** Since 3.12, `class PluginConfig[T]: ...` declares a generic
class without inheriting `Generic[T]`, with bounds/constraints/defaults inline (`T: SomeBase`, `T: (A,
B)`, `T = Default`), introspectable via `__type_params__`
([docs.python.org/generic-classes](https://docs.python.org/3/reference/compound_stmts.html#generic-classes)).
A `Plugin[ConfigT]` base lets `Webhook(WebhookConfig)` and `State(StateConfig)` each carry a strongly
typed config object instead of a shared untyped `dict[str, Any]`.

## 8. Synthesis: comparison table and a candidate model

| | Registration | Ordering | Lifecycle hooks | Settings | Event hooks | Isolation | Typing | Testing |
|---|---|---|---|---|---|---|---|---|
| **Django apps** | Explicit list + convention default | Import/model/ready stage order | `ready()` (post-registry) | `AppConfig` attrs + DRF-style `AppSettings` | `django.dispatch` signals (sync+async) | Staged boot bars import-time DB/model access | Loosely typed | `checks` framework, `django.test` |
| **pytest/pluggy** | Entry points (`pytest11`) + `conftest.py` + `-p` | `tryfirst`/`trylast`, LIFO default, wrappers | `hookimpl`s per hook | N/A | Hookspecs = the model | Per-project marker namespace | Name+arity only | `pytester` (core-shipped) |
| **Entry points (generic)** | Package metadata | None built-in | N/A | N/A | N/A | Consumer must add recursion/disable guards | N/A | N/A |
| **FastStream** | Explicit `middlewares=[...]` | List order | `on_receive`/`consume_scope`/`publish_scope`/`after_processed` | Broker kwargs | Middleware chain only | Extras + broker-specific classes | Typed `BaseMiddleware` | Not confirmed here |
| **Litestar** | Explicit `plugins=[...]` | List order per protocol | `on_app_init`, `receive_route`, `on_cli_init` | Via `on_app_init` mutating `AppConfig` | None generic; typed protocols instead | `MissingDependencyException` | ABCs + `@runtime_checkable` Protocols | Not confirmed here |
| **FastAPI/Starlette** | No plugin system | Router/dependency declaration order | Single `lifespan`, no composition | N/A | `Depends` graph doubles as the seam | None built-in | Signature-based | `dependency_overrides` |
| **Sanic-Ext** | Implicit (installed ⇒ active) | N/A | N/A | N/A | N/A | None | N/A | N/A |
| **aiogram** | Explicit routers + middleware list | Depth-first walk, chain order | `startup`/`shutdown` observers | `workflow_data` dict | Per-event `observers` | None built-in | Weak (`Callable[..., Any]`) | Community-only |
| **Home Assistant** | Declarative `manifest.json` | `dependencies` (hard) / `after_dependencies` (soft) | `async_setup_entry`/`async_unload_entry`/`async_migrate_entry` | Config entries, separate | None generic | Per-integration `requirements` | Typed `ConfigEntry` | Not confirmed here |
| **Sphinx** | Explicit `extensions` list | Registration/connect order | `setup(app)` only | `add_config_value` | `app.connect(event, cb)` pub/sub | None built-in | Not confirmed here |
| **pydantic plugins** | Entry points (`pydantic` group) | Unordered | Validate-event hooks only | N/A | Validation-event hooks | Recursion guard + `PYDANTIC_DISABLE_PLUGINS` | `PydanticPluginProtocol` | Not confirmed here |

**Candidate model, weighing the evidence:**

1. **Explicit `Bot(plugins=[Webhook(...), State(storage=...), Scheduler(...), Observability(...)])`
   list** (Litestar/FastStream-style), not Django/pytest-style discovery. With one platform adapter and a
   handful of optional features, this framework doesn't have pytest's "thousands of third-party
   packages" problem. Explicit lists are strictly more debuggable; Sanic-Ext's "installed ⇒ active" and
   Django's implicit-single-config selection both show why implicit activation is a hazard once more than
   one configuration could exist per install.
2. **A narrow `Plugin` Protocol, not an ABC**, with `configure(app)`, `startup()/shutdown()`, and
   `contribute_routers()/contribute_middlewares()/contribute_dependencies()` — mirroring Litestar's split
   into several narrow protocols rather than one fat base class. Per `typing`'s own warning, don't lean
   on `@runtime_checkable` `isinstance()` as a correctness gate; the explicit list already proves intent.
3. **Split "declare" from "act"** (Django/Home-Assistant style): static metadata (name, declared
   soft/hard dependencies on other plugins, `Final`-typed config via a PEP-695 `PluginConfig[T]`)
   separate from `configure`/`startup`/`shutdown` coroutines. Resolve ordering from declared dependencies
   (topological, Home-Assistant style) with list position as tie-breaker.
4. **One `AppSettings`-style config object per plugin**, DRF's `APISettings` pattern adapted: a `Final`
   `DEFAULTS` dict, typed attributes, resolved once, with an explicit reload path for tests — not
   `getattr(app.state, ...)` scattered through handlers.
5. **A thin, separate `async def`-only event bus** (Sphinx/Django-signals shaped) for cross-plugin
   notifications that don't need to alter app construction, so observers don't need the heavier
   `contribute_*` surface. Async-only sidesteps the sync/async duality pluggy and Datasette's
   `await_me_maybe` had to retrofit, and its documented `firstresult`-short-circuit bug class.
6. **Entry points reserved for one purpose: discovery of third-party plugins by name**, never silent
   auto-activation. If used, copy pydantic's guardrails: lazy `.load()` per entry, a recursion guard, an
   explicit env-var opt-out.
7. **Enforce the optional-features boundary with `import-linter`'s `forbidden` contract**, following
   `django-modern-rest`: name each optional plugin's third-party deps and confine imports to its own
   package, checked in CI, so the core installs and runs with zero optional extras.
8. **Ship a plugin contract test kit** in `aiommbot.testing`, mirroring pytest's `pytester`: a fixture
   that builds a bot with a given plugin list and asserts on registered routers/middlewares/state/jobs,
   removing the need for every plugin author to hand-roll fakes.

**Counter-argument:** a purely explicit, Protocol-based plugin list has no answer for FastAPI's simplest
case — an ad hoc `Depends`-style concern too small to deserve a `Plugin` object — so lightweight
middleware/dependency injection should stay directly available on the composition root too, not forced
through the plugin abstraction. Litestar's own restraint (six narrow protocols, not one) argues the same
`Plugin` Protocol here should stay narrow rather than accumulate every hook any future feature might need.

## Sources

- Django: [Applications](https://docs.djangoproject.com/en/5.2/ref/applications/), [Signals](https://docs.djangoproject.com/en/5.2/topics/signals/), [System check framework](https://docs.djangoproject.com/en/5.2/topics/checks/), [Custom management commands](https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/)
- Django REST Framework: [`rest_framework/settings.py`](https://raw.githubusercontent.com/encode/django-rest-framework/master/rest_framework/settings.py)
- pluggy: [docs](https://pluggy.readthedocs.io/en/stable/index.html)
- pytest: [Writing plugins](https://docs.pytest.org/en/stable/how-to/writing_plugins.html)
- Datasette: [Internals for plugins](https://docs.datasette.io/en/1.0a14/internals.html), ["Await me maybe"](https://simonwillison.net/2020/Sep/2/await-me-maybe/), [issue #1425](https://github.com/simonw/datasette/issues/1425)
- Python: [`importlib.metadata` entry points](https://docs.python.org/3/library/importlib.metadata.html#entry-points), [`typing.Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol), [PEP 695 generic classes](https://docs.python.org/3/reference/compound_stmts.html#generic-classes)
- pydantic: [`pydantic/plugin/_loader.py`](https://raw.githubusercontent.com/pydantic/pydantic/main/pydantic/plugin/_loader.py)
- Hypothesis: [Third-party extensions](https://hypothesis.readthedocs.io/en/latest/extensions.html)
- FastStream: [Middlewares](https://faststream.ag2.ai/latest/getting-started/middlewares/), [OpenTelemetry](https://faststream.ag2.ai/latest/getting-started/observability/opentelemetry/)
- Litestar: [Plugins](https://docs.litestar.dev/latest/usage/plugins/index.html), [`litestar/plugins/base.py`](https://raw.githubusercontent.com/litestar-org/litestar/main/litestar/plugins/base.py), [CLI](https://docs.litestar.dev/latest/usage/cli.html)
- FastAPI/Starlette: [Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/), [Events: startup - shutdown](https://fastapi.tiangolo.com/advanced/events/)
- Sanic: [sanic-ext getting started](https://sanic.dev/en/plugins/sanic-ext/getting-started.html)
- aiogram: prior primary-source research in this repo, `docs/research/03-bot-framework-architectures.md` (citing `dispatcher/dispatcher.py`, `dispatcher/router.py`)
- Home Assistant: [Integration manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/), [Config entries](https://developers.home-assistant.io/docs/config_entries_index/)
- Sphinx: [Extension API overview](https://www.sphinx-doc.org/en/master/extdev/index.html)
- django-modern-rest: [repo](https://github.com/wemake-services/django-modern-rest), [`.importlinter`](https://github.com/wemake-services/django-modern-rest/blob/master/.importlinter)

**Not independently verified in this pass:** the exact Hypothesis environment variable name that
disables all plugin auto-loading; Litestar's and Home Assistant's own plugin contract-test tooling;
Sphinx's own testing harness for extensions.
