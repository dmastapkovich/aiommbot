# 33. The sanctioned channel between two plugins

**Question.** Through which sanctioned channel does one plugin reach another plugin's capability, in
a host that forbids or discourages direct imports between plugins — what is the lookup keyed on,
what is returned, how is absence expressed, and is the channel typed?

One of five notes gathered for GitHub issue #100, which asked what a plugin host specifies
beyond an explicit list and a set of narrow Protocols — the mechanics that
[ADR-0015](../adr/0015-plugin-contract-and-composition.md) states as words rather than as
mechanisms. The five are
[`30`](30-plugin-contract-versioning.md) the contract version,
[`32`](32-plugin-lifecycle-failure.md) lifecycle failure,
[`33`](33-the-plugin-to-plugin-channel.md) the plugin-to-plugin channel,
[`34`](34-plugin-conflicts-and-prohibitions.md) conflicts and prohibitions, and
[`35`](35-the-third-party-author-kit.md) the third-party author's kit.
[`docs/research/10`](10-plugin-systems.md) surveyed the same hosts for registration, ordering,
isolation and settings; it did not ask what a host specifies after those choices.

The decision this note is evidence for is #102.

Findings only, and no recommendation. Sources are primary — project source at the default branch,
reference and developer documentation, PEPs, the Python packaging specifications,
`docs.python.org`, PyPI metadata and project issue trackers — read on 2026-09-10. Anything a
primary source did not confirm is marked **[unverified]**.

Six hosts sanction six different channels. Every one of them is a host-owned lookup — a registry
object, a domain-keyed dict, or an object the plugin handed the host at activation. None of the five
Python hosts examined documents type-keyed dependency injection as the channel between plugins.

## 1 Litestar `PluginRegistry`

`PluginRegistry` is defined in
[`litestar/plugins/base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py)
and re-exported from
[`litestar/plugins/__init__.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/__init__.py)
in an `__all__` of nine names: the registry, the six members of the `PluginProtocol` union, that
union itself and `InitPlugin`. The reference documentation renders the whole module with `..
automodule:: litestar.plugins` and `:members:`, so the registry is public API
([`docs/reference/plugins/index.rst`](https://github.com/litestar-org/litestar/blob/main/docs/reference/plugins/index.rst)).

The lookup is one method with two branches
([`base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py)):

```python
def get(self, type_: type[PluginT] | str) -> PluginT:
    """Return the registered plugin of ``type_``.

    This should be used with subclasses of the plugin protocols.
    """
```

The type branch reads `self._plugins_by_type`, built as `{type(p): p for p in plugins}` — keyed by
the exact runtime class, so a lookup by a base class or a protocol misses
([`base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py)). The
string branch scans `self._plugins` and matches `type_` against either `plugin.__class__.__name__`
or the qualified name `f"{_module}.{plugin.__class__.__qualname__}"`; qualified-name lookup arrived
with PR 3027, changelog entry "Allow discovering registered plugins by their fully qualified name"
([`2.x-changelog.rst`](https://github.com/litestar-org/litestar/blob/main/docs/release-notes/2.x-changelog.rst)).

Absence raises `KeyError`, with two different messages
([`base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py)):

- string lookup — `raise KeyError(f"No plugin of type {type_!r} registered")`
- type lookup — `raise KeyError(f"No plugin of type {type_.__name__!r} registered")`

The string branch returns `cast("PluginT", plugin)`, so nothing checks that the object matches the
caller's annotation
([`base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py)).

The registry partitions plugins into six public tuples, each named and described in `__slots__` and
each filled by an `isinstance` filter in `__init__`: `init` ("Plugins that implement InitPlugin"),
`openapi`, `receive_route`, `serialization`, `cli`, `di`
([`base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py)). Three
private slots accompany them: `_plugins_by_type`, `_plugins` (a `frozenset`), and
`_get_plugins_of_type` — the last is declared in `__slots__` and never assigned or read anywhere in
the tree. `__iter__` yields the frozenset and `__contains__` tests membership; there is no
`unregister`.

`app.plugins` is assigned once, in `Litestar.__init__`, *after* the entire init chain has run
([`litestar/app.py`](https://github.com/litestar-org/litestar/blob/main/litestar/app.py)):

```python
for handler in chain(
    on_app_init or [],
    (p.on_app_init for p in config.plugins if isinstance(p, InitPluginProtocol)),
    [self._patch_opentelemetry_middleware],
):
    config = handler(config)

self.plugins = PluginRegistry(config.plugins)
```

So no `InitPlugin` can call `app.plugins.get` from inside `on_app_init` — the registry does not
exist yet. What one `InitPlugin` *can* observe is another's effect on the shared `AppConfig`, and
the documentation states the order explicitly: "This method is invoked after any ``on_app_init``
hooks have been called, and each plugin is invoked in the order that they are provided in the
``plugins`` argument of the app. Because of this, plugin authors should make it clear in their
documentation if their plugin should be invoked before or after other plugins"
([`docs/usage/plugins/index.rst`](https://github.com/litestar-org/litestar/blob/main/docs/usage/plugins/index.rst)).
The coordination burden is pushed onto prose, not onto an API. The generator over `config.plugins`
in that `chain` is consumed lazily, so a plugin appended to `config.plugins` by an earlier
`on_app_init` appears to be visited later in the same pass — a reading of the source that no
document states and that this note did not execute, **[unverified]**
([`litestar/app.py`](https://github.com/litestar-org/litestar/blob/main/litestar/app.py));
`AppConfig.plugins` is a plain `list[PluginProtocol]` documented as "List of plugins"
([`litestar/config/app.py`](https://github.com/litestar-org/litestar/blob/main/litestar/config/app.py)).

Litestar itself uses both branches. Typed: `self.plugins.get(OpenAPIPlugin)` in
`update_openapi_schema`. Stringly, with absence as control flow
([`litestar/app.py`](https://github.com/litestar-org/litestar/blob/main/litestar/app.py)):

```python
try:
    otel_plugin: OpenTelemetryPlugin = self.plugins.get("OpenTelemetryPlugin")
    asgi_handler = otel_plugin.middleware(app=asgi_handler)
except KeyError:
    pass
```

The documented user-facing form of one component reaching another's capability is a handler pulling
a registry plugin out by type: `registry = request.app.plugins.get(FileSystemRegistry)`
([`docs/examples/file_systems/registry_access.py`](https://github.com/litestar-org/litestar/blob/main/docs/examples/file_systems/registry_access.py)).

## 2 Home Assistant `dependencies`, `after_dependencies`, and the runtime channel

The manifest keys promise different things, and the documentation is careful about the gap between
load order and presence of data
([integration-manifest](https://developers.home-assistant.io/docs/creating_integration_manifest)):

- `dependencies` — "Adding an integration to dependencies will ensure the depending integration is
  loaded before setup, but it does not guarantee all dependency configuration entries have been set
  up." So it buys import safety and setup order, not the existence of a configured entry.
- `after_dependencies` — "set up of an integration will wait for the integrations listed in
  `after_dependencies`, which are configured either via YAML or a config entry, to be set up first
  before the integration is set up. It will also make sure that the requirements of
  `after_dependencies` are installed so methods from the integration can be safely imported,
  regardless of whether the integrations listed in `after_dependencies` are configured or not." The
  worked example ends: "If `stream` is not configured, `camera` will still load."

Both keys are scoped: "Built-in integrations shall only specify other built-in integrations in
`dependencies`" (and the same sentence for `after_dependencies`)
([integration-manifest](https://developers.home-assistant.io/docs/creating_integration_manifest)).

The classic runtime channel is a single untyped dict on the core object, keyed by domain: "You can
share data with your platforms by leveraging `hass.data[DOMAIN]`"
([component-code-review](https://developers.home-assistant.io/docs/creating_component_code_review/)).

A typed alternative exists and is now a Bronze-tier quality-scale rule titled "Use
ConfigEntry.runtime_data to store runtime data", for "storing data that is not persisted to the
configuration file storage, but is needed during the lifetime of the configuration entry"
([runtime-data-rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data/)).
The rule states that "The type of a `ConfigEntry` can be extended with the type of the data put in
`runtime_data`" via an alias such as `type MyIntegrationConfigEntry = ConfigEntry[MyClient]`, and
that for integrations under the strict-typing rule "the use of a custom typed
`MyIntegrationConfigEntry` is required and must be used throughout". The core source backs this. The
class is declared `class ConfigEntry[_DataT = Any]`, and the attribute is annotated `runtime_data:
_DataT`
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py)).

The maintainers' own announcement gives the reason and the lifetime rule: "Previously, those were
all stored inside `hass.data`, which made tracking them difficult", and "The config entry is already
available when setting up platforms and gets cleaned up automatically. No more deleting the key from
`hass.data` after unloading", and "`ConfigEntry` is generic now, so passing the data type along is
possible"
([runtime-data-announcement](https://developers.home-assistant.io/blog/2024/04/30/store-runtime-data-inside-config-entry/)).

Where the entry is not the right home, the dict itself became typed: "To fix that, it's now possible
to use two new key types `HassKey` and `HassEntryKey`. With a little bit of magic, type checkers are
now able to infer the type and make sure it's correct." The same post recommends the entry first:
"Storing data in a dict by `entry.entry_id`? It's often better to just store it inside the
`ConfigEntry` directly."
([hass-data-typing-announcement](https://developers.home-assistant.io/blog/2024/05/01/improved-hass-data-typing/)).
Both keys are generic `str` subclasses — `class HassKey[_T](str)` with the docstring "Generic Hass
key type. At runtime this is a generic subclass of str", and `class HassEntryKey[_T](str)` "Key type
for integrations with config entries"
([`homeassistant/util/hass_dict.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/util/hass_dict.py)).

## 3 Django `apps.get_app_config`

The registry is explicit about its own surface: "The application registry provides the following
public API. Methods that aren't listed below are considered private and may change without notice."
`get_app_config` is on that list: "Returns an `AppConfig` for the application with the given
`app_label`. Raises `LookupError` if no such application exists."
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt)).
The source matches, calling `self.check_apps_ready()` first and, before raising `LookupError("No
installed app with label '%s'.")`, scanning the app configs for one whose `name` equals the label so
it can append a `" Did you mean '%s'?"` hint carrying that app's `label`
([`django/apps/registry.py`](https://github.com/django/django/blob/main/django/apps/registry.py)).
Calling too early raises `AppRegistryNotReady("Apps aren't loaded yet.")` from `check_apps_ready`
([`django/apps/registry.py`](https://github.com/django/django/blob/main/django/apps/registry.py)).

The staging language names the exact moment the channel opens
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt)):

> The application registry is initialized in three stages. At each stage, Django processes all
> applications in the order of `INSTALLED_APPS`.
>
> 1. First Django imports each item in `INSTALLED_APPS`. […] *At this stage, your code shouldn't
>    import any models!* […] Once this stage completes, APIs that operate on application
>    configurations such as `apps.get_app_config()` become usable.
> 2. Then Django attempts to import the `models` submodule of each application […] Once this stage
>    completes, APIs that operate on models such as `apps.get_model()` become usable.
> 3. Finally Django runs the `ready()` method of each application configuration.

The safe stage for cross-app work is therefore `ready()`: "Subclasses can override this method to
perform initialization tasks such as registering signals. It is called as soon as the registry is
fully populated." The same entry advises indirection over direct references even for models: "If
you're registering model signals, you can refer to the sender by its string label instead of using
the model class itself."
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt)).
The registry also exposes `apps.ready`, a "Boolean attribute that is set to `True` after the
registry is fully populated and all `AppConfig.ready()` methods are called", so a late caller can
test the stage rather than catch the exception
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt)).

## 4 Sphinx `setup_extension`, `app.extensions` and `needs_extensions`

`Sphinx.setup_extension` is the documented answer to needing another extension's features: "Import
and setup a Sphinx extension module. Load the extension given by the module *name*. Use this if your
extension needs the features provided by another extension. No-op if called twice."
([`extdev/appapi`](https://www.sphinx-doc.org/en/master/extdev/appapi.html)). Its body is two lines
— a debug log and `self.registry.load_extension(self, extname)`
([`sphinx/application.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/application.py)).

The mapping exists in source as `self.extensions: dict[str, Extension] = {}`
([`sphinx/application.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/application.py)),
where `Extension` carries `name`, `module`, `metadata`, `version` (defaulting to the string
`'unknown version'`), `parallel_read_safe` and `parallel_write_safe`
([`sphinx/extension.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/extension.py)). It
is **not** public API for extension authors: the application-API page documents `connect`,
`disconnect`, `setup_extension` and `require_sphinx` with `automethod`, and documents no
`extensions` attribute
([`doc/extdev/appapi.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/extdev/appapi.rst)).
The extension-developer overview likewise never describes one extension reading another's state
([`extdev/index`](https://www.sphinx-doc.org/en/master/extdev/index.html)).

`needs_extensions` compares declared version strings, nothing else: "If set, this value must be a
dictionary specifying version requirements for extensions in `extensions`. The version strings
should be in the `'major.minor'` form. Requirements do not have to be specified for all extensions,
only for those you want to check. […] This requires that the extension declares its version in the
`setup()` function." Its type is `dict[str, str]`, default `{}`, added in 1.3
([`usage/configuration`](https://www.sphinx-doc.org/en/master/usage/configuration.html)).

Absence is a warning; a stale version is fatal
([`sphinx/extension.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/extension.py)):

```python
extension = app.extensions.get(extname)
if extension is None:
    logger.warning(
        __(
            'The %s extension is required by needs_extensions settings, '
            'but it is not loaded.'
        ),
        extname,
    )
    continue
```

```python
raise VersionRequirementError(
    __(
        'This project needs the extension %s at least in '
        'version %s and therefore cannot be built with '
        'the loaded version (%s).'
    )
    % (extname, reqversion, extension.version)
)
```

An extension that returns no `version` from `setup()` fails the check too, because the sentinel is
tested before any version comparison is attempted: `if extension.version == 'unknown version'` sets
`fulfilled = False`
([`sphinx/extension.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/extension.py)).

## 5 pytest `get_plugin` / `getplugin`

Plugins are keyed by **name**, never by type. `register(plugin, name=None)` takes the name from the
caller or from `get_canonical_name(plugin)`, which returns `getattr(plugin, "__name__", None) or
str(id(plugin))`. The lookups are `get_plugin(name) -> Any | None` ("Return the plugin registered
under the given name, if any") and `has_plugin(name) -> bool`
([`src/pluggy/_manager.py`](https://github.com/pytest-dev/pluggy/blob/main/src/pluggy/_manager.py)).
The object registered can be a module, a class instance or any object with hook implementations —
`register` simply walks `dir(plugin)` for hookimpls, and pytest additionally runs `consider_module`
on it under `if isinstance(plugin, types.ModuleType)`
([`src/_pytest/config/__init__.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py)).

The documented channel is one sentence and one line of code
([`doc/en/how-to/writing_plugins.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_plugins.rst)):

> **Accessing another plugin by name.** If a plugin wants to collaborate with code from another
> plugin it can obtain a reference through the plugin manager like this:
> `plugin = config.pluginmanager.get_plugin("name_of_plugin")`
> If you want to look at the names of existing plugins, use the `--trace-config` option.

`Config.pluginmanager` is a documented attribute — "The plugin manager handles plugin registration
and hook invocation. :type: PytestPluginManager" — and `Config` registers itself as a plugin named
`"pytestconfig"`
([`src/_pytest/config/__init__.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py)).
`PytestPluginManager` adds two underscore-free aliases, the first carrying a source comment that
calls the spelling deprecated:

```python
def getplugin(self, name: str):
    # Support deprecated naming because plugins (xdist e.g.) use it.
    plugin: _PluggyPlugin | None = self.get_plugin(name)
    return plugin

def hasplugin(self, name: str) -> bool:
    """Return whether a plugin with the given name is registered."""
    return bool(self.get_plugin(name))
```

The channel is untyped, and pytest itself pays for that at every use site — it re-annotates the
result and asserts
([`src/_pytest/config/__init__.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py)):

```python
terminalreporter: TerminalReporter | None = self.pluginmanager.get_plugin(
    "terminalreporter"
)
assert terminalreporter is not None
```

pytest has two further cross-plugin channels that the registry lookup does not cover. Fixtures are
global by name once a plugin is installed: "They can also be provided by third-party plugins that
are installed, and this is how many pytest plugins operate. As long as those plugins are installed,
the fixtures they provide can be requested from anywhere in your test suite" — and the worked
example has one plugin's fixture (`b_fix`) requested by a fixture defined elsewhere
([`doc/en/reference/fixtures.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/reference/fixtures.rst)).
And `Config.stash` is "A place where plugins can store information on the config for their own use"
([`src/_pytest/config/__init__.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py)),
typed by key: "`Stash` is a type-safe heterogeneous mutable mapping that allows keys and value types
to be defined separately from where it (the `Stash`) is created", with `StashKey[T]` "associated
with the type `T` of the value of the key", added in 7.0
([`src/_pytest/stash.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/stash.py)).

## 6 VS Code `activate()` exports

The namespace exists for exactly this: "Namespace for dealing with installed extensions. Extensions
are represented by an Extension-interface which enables reflection on them. Extension writers can
provide APIs to other extensions by returning their API public surface from the `activate`-call."
The lookup is `getExtension<T>(extensionId: string): Extension<T> | undefined` — "Get an extension
by its full identifier in the form of: `publisher.name`", returning "An extension or `undefined`".
`Extension.exports` is "The public API exported by this extension (return value of `activate`)", and
"It is an invalid action to access this field before this extension has been activated" — its
declared type is a bare `T`, not `T | undefined`. `activate()` "Activates this extension and returns
its public API", handing back "A promise that will resolve when this extension has been activated"
([vscode-api](https://code.visualstudio.com/api/references/vscode-api)).

The type parameter `T` of `Extension<T>` is supplied by the *consumer* at the call site; nothing in
the signature ties it to what the provider actually returned
([vscode-api](https://code.visualstudio.com/api/references/vscode-api)).

`extensionDependencies` is described in the manifest reference only as "An array with the ids of
extensions that this extension depends on. The id of an extension is always `${publisher}.${name}`"
— that page states no activation-order guarantee
([extension-manifest](https://code.visualstudio.com/api/references/extension-manifest)), and the
activation-events reference does not mention the field at all
([activation-events](https://code.visualstudio.com/api/references/activation-events)). The ordering
promise is documented instead by the built-in Git extension, next to its API sample: "To ensure that
the `vscode.git` extension is activated before your extension, add `extensionDependencies`" with

```ts
const gitExtension = vscode.extensions.getExtension<GitExtension>('vscode.git').exports;
const git = gitExtension.getAPI(1);
```

([`extensions/git/README.md`](https://github.com/microsoft/vscode/blob/main/extensions/git/README.md)).

## 7 The documented hazard

Four hosts document a way for a held reference to be wrong. Litestar yields nothing to the searches
described below.

**VS Code — the reference may be unreachable by construction.** "An extension can export an API from
their `activate` function. This API will become available to all extensions running in the same
extension host." In a remote workspace "the extensions run on two different extension hosts, which
means that the API from the provider is not available to the consumer", and the documented remedy is
to abandon the channel: "It is therefore required that the providing extension give up entirely the
ability to export any APIs by using `"api": "none"` in their extension's `package.json`. The
extensions can still communicate using VS Code commands (which are asynchronous)."
([remote-extensions](https://code.visualstudio.com/api/advanced-topics/remote-extensions)). The same
host documents the lifetime hole directly — reading `exports` before activation is "an invalid
action" — and an event for the set changing: `onDidChange` "fires when `extensions.all` changes.
This can happen when extensions are installed, uninstalled, enabled or disabled"
([vscode-api](https://code.visualstudio.com/api/references/vscode-api)).

**Home Assistant — the object is destroyed on unload.** `ConfigEntry.async_unload` deletes the
attribute after a successful unload, guarding on `hasattr(self, "runtime_data")` and then calling
`object.__delattr__(self, "runtime_data")`
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py)).
Unload is a routine event, not an edge case: the Silver-tier quality-scale rule says supporting it
"allows Home Assistant to unload the integration on runtime, allowing the user to remove the
integration or to reload it without having to restart Home Assistant", and that in
`async_unload_entry` the integration "should clean up any subscriptions and close any connections
opened during the setup of the integration"
([config-entry-unloading-rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading/)).
A reload therefore replaces the object any other integration might be holding.

**Django — initialization can run twice.** "In the usual initialization process, the `ready` method
is only called once by Django. But in some corner cases, particularly in tests which are fiddling
with installed applications, `ready` might be called more than once. In that case, either write
idempotent methods […]"
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt)).
The registry also has `clear_cache()`, "Clear all internal caches, for methods that alter the app
registry. This is mostly used in tests"
([`django/apps/registry.py`](https://github.com/django/django/blob/main/django/apps/registry.py)).

**pytest / pluggy — unregistration is not propagated.** `unregister` "Unregister a plugin and all of
its hook implementations", calling `hookcaller._remove_plugin(plugin)` on each of the plugin's
hookcallers, and "Returns the unregistered plugin, or `None` if not found" — it hands the object
back to the caller and has no mechanism to invalidate references other plugins already took from
`get_plugin`
([`src/pluggy/_manager.py`](https://github.com/pytest-dev/pluggy/blob/main/src/pluggy/_manager.py)).

**Litestar — nothing.** `PluginRegistry` has no `unregister` and the `_plugins` frozenset is fixed
at construction
([`litestar/plugins/base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py));
searching the documentation tree for `plugins.get` and `PluginRegistry` returns only two changelog
entries and the one file-system example, with no warning about holding a plugin reference
([`2.x-changelog.rst`](https://github.com/litestar-org/litestar/blob/main/docs/release-notes/2.x-changelog.rst),
[`registry_access.py`](https://github.com/litestar-org/litestar/blob/main/docs/examples/file_systems/registry_access.py),
[`docs/usage/plugins/index.rst`](https://github.com/litestar-org/litestar/blob/main/docs/usage/plugins/index.rst)).

## 8 Dependency injection as the alternative channel

**No Python host in this set documents type-keyed DI as the plugin-to-plugin channel.** The two that
have a DI system document a *name*-keyed one, and the rest document a registry or a data dict.

Litestar comes closest and still does not get there. `AppConfig.dependencies` has the type
`dict[str, Provide | AnyCallable]`
([`litestar/config/app.py`](https://github.com/litestar-org/litestar/blob/main/litestar/config/app.py)),
and the canonical `InitPlugin` example writes into it with the line `app_config.dependencies["name"]
= Provide(get_name)`
([`litestar/plugins/base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py)).
The key is a string by design: "Because dependencies are declared at each level of the app using a
string keyed dictionary, overriding dependencies is very simple"
([`docs/usage/dependency-injection.rst`](https://github.com/litestar-org/litestar/blob/main/docs/usage/dependency-injection.rst)).
`DIPlugin` is not a provider registry — it is signature archaeology: "`DIPlugin` can be used to
extend Litestar's dependency injection by providing information about injectable types. Its main
purpose it to facilitate the injection of callables with unknown signatures, for example Pydantic's
`BaseModel` classes"
([`docs/usage/plugins/index.rst`](https://github.com/litestar-org/litestar/blob/main/docs/usage/plugins/index.rst)).
Its two abstract methods are `has_typed_init(type_)` and `get_typed_init(type_) -> tuple[Signature,
dict[str, Any]]`
([`litestar/plugins/base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py)),
and the only consumer is `Provide.finalize`, which takes the first plugin in `plugins.di` whose
`has_typed_init` accepts the dependency and reads a signature from it
([`litestar/di.py`](https://github.com/litestar-org/litestar/blob/main/litestar/di.py)).

pytest's fixture system is the one Python precedent for a documented DI channel between plugins, and
it is keyed by fixture name, not by type: an installed plugin's fixtures "can be requested from
anywhere in your test suite", and the documented search order puts them last — "pytest will search
for fixtures stepping out through scopes as explained previously, only reaching fixtures defined in
plugins *last*"
([`doc/en/reference/fixtures.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/reference/fixtures.rst)).

Home Assistant, Django and Sphinx have no DI container in the channel at all: the documented answers
are `hass.data[DOMAIN]` / `ConfigEntry.runtime_data`
([runtime-data-rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data/)),
`apps.get_app_config`
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt))
and `setup_extension` ([`extdev/appapi`](https://www.sphinx-doc.org/en/master/extdev/appapi.html)).

The non-Python precedents do document it. Spring Boot routes
auto-configuration-to-auto-configuration through the bean container by type, with conditions as the
presence test: "we recommend using only `@ConditionalOnBean` and `@ConditionalOnMissingBean`
annotations on auto-configuration classes (since these are guaranteed to load after any user-defined
bean definitions have been added)", ordering via "the `before`, `beforeName`, `after` and
`afterName` attributes on the `@AutoConfiguration` annotation", and an explicit warning that
ordering is not dependency: "the order in which auto-configuration classes are applied only affects
the order in which their beans are defined. The order in which those beans are subsequently created
is unaffected and is determined by each bean's dependencies and any `@DependsOn` relationships"
([developing-auto-configuration](https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html)).
NestJS makes the boundary explicit per module: "The module encapsulates providers by default,
meaning you can only inject providers that are either part of the current module or explicitly
exported from other imported modules", where `exports` is "the subset of `providers` that are
provided by this module and should be available in other modules which import this module", and the
stated payoff is identity — "the same instance of `CatsService` is reused across all modules that
import `CatsModule`" ([Modules](https://docs.nestjs.com/modules)).

## 9 Comparison

| Host | Lookup key | What is returned | Typed channel | Documented public API |
|---|---|---|---|---|
| Litestar `PluginRegistry.get` | exact `type(p)`, or class name / fully qualified name string | the plugin instance; `KeyError` if absent | yes for the type branch; the string branch is an unchecked `cast` | yes — `litestar.plugins.__all__` plus `automodule` in the reference |
| Home Assistant `hass.data[DOMAIN]` | domain string from the manifest | whatever the integration put there | only with `HassKey[_T]` / `HassEntryKey[_T]`; plain string keys are untyped | yes — the component code-review checklist |
| Home Assistant `ConfigEntry.runtime_data` | the `ConfigEntry` object | `_DataT`, the type the integration parameterises the entry with (`ConfigEntry[MyClient]` in the rule) | yes — `ConfigEntry[_DataT]` plus a `type` alias, required under strict-typing | yes — Bronze quality-scale rule |
| Django `apps.get_app_config` | `app_label` string | an `AppConfig` instance; `LookupError` if absent | class-typed return, string-keyed lookup, no type parameter | yes — "the following public API" |
| Sphinx `app.setup_extension` | module name string | `None`; the effect is that the extension is loaded | no | yes — documented on the application API page |
| Sphinx `app.extensions` | extension name string | `Extension` (`dict[str, Extension]` in source) | typed in source | no — absent from `doc/extdev/appapi.rst` |
| pytest `pluginmanager.get_plugin` | registration name string | `Any \| None` — module, instance or any object | no; callers re-annotate and assert | yes — "Accessing another plugin by name" |
| pytest `Config.stash` | `StashKey[T]` object | `T` | yes — "type-safe heterogeneous mutable mapping" | yes — documented attribute; `Stash`/`StashKey` added in 7.0 |
| pytest fixtures | fixture name string | whatever the fixture yields | only by the fixture's own annotations | yes — "Fixtures from third-party plugins" |
| VS Code `extensions.getExtension` | `publisher.name` id string | `Extension<T> \| undefined`; reading `.exports` before activation is "an invalid action" | `T` is asserted by the consumer, unverified | yes — the `extensions` namespace |
| Spring Boot auto-configuration | bean type | the bean, injected | yes — by type | yes — the auto-configuration reference |
| NestJS modules | provider token / type, scoped to `exports` | the provider instance, shared | yes — by type | yes — the modules guide |

## 10 What the evidence supports

- Every host sanctions a **host-owned lookup**, not a direct reference: a registry object (Litestar,
  pytest), a dict on the core object (Home Assistant), a label-keyed registry (Django), a loader
  call (Sphinx), or an object the plugin handed the host at activation (VS Code). No host documents
  plugins importing one another.
- **Type-keyed lookup is the exception, not the rule.** Litestar is the only host here whose primary
  key is a class, and even it keys on the exact `type(p)`, so a base class or protocol misses.
  Everything else keys on a string: a name, a domain, an id, a fixture name.
- **Absence is a normal outcome and every host encodes it differently**: `KeyError` (Litestar),
  `LookupError` (Django), `None` (pytest, VS Code `undefined`), a logged warning (Sphinx
  `needs_extensions`). Litestar's own OpenTelemetry path wraps `get` in `try/except KeyError: pass`,
  which is the shape a caller ends up writing when the lookup can fail.
- **Declared dependency buys order, not data.** Home Assistant says `dependencies` "does not
  guarantee all dependency configuration entries have been set up"; Spring Boot says
  auto-configuration ordering "only affects the order in which their beans are defined"; VS Code's
  ordering promise for `extensionDependencies` is documented in a built-in extension's README rather
  than in the manifest reference. A host that promises order still owes the caller a presence check.
- **The two channels that are actually type-safe are key-object channels, not type-lookup
  channels.** pytest's `StashKey[T]` and Home Assistant's `HassKey[_T]` / `ConfigEntry[_DataT]` give
  a checker something to verify. Home Assistant's pair was retrofitted onto the untyped `hass.data`
  dict that came first ("Previously, those were all stored inside `hass.data`"); the same
  retrofit reading of pytest's stash is **[unverified]** — the cited source says only that `Stash`
  and `StashKey` were "added in 7.0".
- **The registry cannot be consulted while the registry is being built.** Litestar assigns
  `app.plugins` only after every `on_app_init` has run, so init-time coordination happens through
  the shared `AppConfig` in registration order — and the documentation delegates that ordering to
  plugin authors' prose.
- **A held plugin reference goes stale in every host that can unload or reload.** Home Assistant
  deletes `runtime_data` on unload; VS Code documents reading `exports` before activation as "an
  invalid action" and the provider's API as unavailable across extension hosts, where the documented
  answer is to give up exports entirely and use commands; pluggy's `unregister` invalidates nothing
  that other plugins already hold.
- **Dependency injection as the plugin-to-plugin channel has no Python precedent in this set.** The
  sourced answer is no: Python hosts document a registry, a data dict or a name-keyed provider;
  type-keyed DI between extension units is documented only outside Python, by Spring Boot's bean
  container and NestJS's module `exports`.

## Sources

Every claim above carries its own link inline. This section names what was read.

Litestar:

- <https://github.com/litestar-org/litestar> — `docs/examples/file_systems/registry_access.py`,
  `docs/reference/plugins/index.rst`, `docs/release-notes/2.x-changelog.rst`,
  `docs/usage/dependency-injection.rst`, `docs/usage/plugins/index.rst`, `litestar/app.py`,
  `litestar/config/app.py`, `litestar/di.py`, `litestar/plugins/__init__.py`,
  `litestar/plugins/base.py`

Home Assistant:

- <https://github.com/home-assistant/core> — `homeassistant/config_entries.py`,
  `homeassistant/util/hass_dict.py`
- <https://developers.home-assistant.io/blog/2024/04/30/store-runtime-data-inside-config-entry/> ·
  <https://developers.home-assistant.io/blog/2024/05/01/improved-hass-data-typing/> ·
  <https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-entry-unloading/>
- <https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data/> ·
  <https://developers.home-assistant.io/docs/creating_component_code_review/> ·
  <https://developers.home-assistant.io/docs/creating_integration_manifest>

Sphinx:

- <https://github.com/sphinx-doc/sphinx> — `doc/extdev/appapi.rst`, `sphinx/application.py`,
  `sphinx/extension.py`
- <https://www.sphinx-doc.org/en/master/extdev/appapi.html> ·
  <https://www.sphinx-doc.org/en/master/extdev/index.html> ·
  <https://www.sphinx-doc.org/en/master/usage/configuration.html>

VS Code:

- <https://github.com/microsoft/vscode> — `extensions/git/README.md`
- <https://code.visualstudio.com/api/advanced-topics/remote-extensions> ·
  <https://code.visualstudio.com/api/references/activation-events> ·
  <https://code.visualstudio.com/api/references/extension-manifest>
- <https://code.visualstudio.com/api/references/vscode-api>

pytest:

- <https://github.com/pytest-dev/pytest> — `doc/en/how-to/writing_plugins.rst`,
  `doc/en/reference/fixtures.rst`, `src/_pytest/config/__init__.py`, `src/_pytest/stash.py`

Django:

- <https://github.com/django/django> — `django/apps/registry.py`, `docs/ref/applications.txt`

Outside Python:

- <https://docs.nestjs.com/modules> ·
  <https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html>

pluggy:

- <https://github.com/pytest-dev/pluggy> — `src/pluggy/_manager.py`
