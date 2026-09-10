# 34. Which declarations a host refuses, and what it says a plugin may not do

**Question.** Which conflicting declarations does a plugin host refuse, with what message and at
what moment; can a plugin be disabled or unloaded; and what does a host state that a plugin may
**not** do?

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

Every host in this survey refuses something. What differs is *what* it treats as a conflict, *when*
it notices, and whether the answer is an exception, a warning or silence. This section collects the
exact strings and the moment each one fires.

## 1 1. Duplicate identity

Django checks two different identities in one pass and refuses both with `ImproperlyConfigured`.
Phase 1 of `Apps.populate()` builds each `AppConfig` and rejects a repeated label as soon as the
colliding config is created; the name check runs after the whole loop, over a `Counter`, so it
reports every duplicated name at once. The two strings, from
[`django/apps/registry.py`](https://github.com/django/django/blob/main/django/apps/registry.py#L92-L110):

```python
raise ImproperlyConfigured(
    "Application labels aren't unique, "
    "duplicates: %s" % app_config.label
)
```

```python
raise ImproperlyConfigured(
    "Application names aren't unique, "
    "duplicates: %s" % ", ".join(duplicates)
)
```

Adjacent literals concatenate before `%` applies, so the rendered messages are
`Application labels aren't unique, duplicates: <label>` and
`Application names aren't unique, duplicates: <name>, <name>`. Both fire at start-up, inside
`populate()`, before any `models` module is imported and long before `ready()`.

Home Assistant states the uniqueness rule in the manifest documentation: "The domain is a short name
consisting of characters and underscores. This domain has to be unique and cannot be changed. […]
The domain key has to match the directory this file is in."
([`docs/creating_integration_manifest.md`](https://github.com/home-assistant/developers.home-assistant/blob/master/docs/creating_integration_manifest.md))

Enforcement is split across three places, and none of them raises.

- The filesystem enforces it structurally. `_get_custom_components` builds `{integration.domain:
  integration}` from the directories under `custom_components`, so two custom integrations cannot
  share a domain without sharing a directory
  ([`homeassistant/loader.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/loader.py#L305-L331)).
- `hassfest` checks the domain against the directory name and warns on a collision with a built-in:
  `integration.add_error("manifest", "Domain does not match dir name")` and
  `integration.add_warning("manifest", "Domain collides with built-in core integration")`
  ([`script/hassfest/manifest.py`](https://github.com/home-assistant/core/blob/dev/script/hassfest/manifest.py#L355-L361)).
- At runtime a custom integration deliberately wins. `async_get_integrations` comments "`# First we
  look for custom components`" and only falls back to `_resolve_integrations_from_root` for domains
  the custom map did not claim
  ([`homeassistant/loader.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/loader.py#L1424-L1447)).
  The developer documentation confirms the intent: "You can override a built-in integration by
  having an integration with the same domain in your `<config directory>/custom_components` folder."
  ([`docs/creating_integration_file_structure.md`](https://github.com/home-assistant/developers.home-assistant/blob/master/docs/creating_integration_file_structure.md))

Shadowing a core domain is therefore a supported feature, not a refusal — though the same page
discourages it in the next paragraph: "Note that overriding built-in integrations is not recommended
as you will no longer get updates. It is recommended to pick a unique name." The only runtime cost
is a warning per custom integration:

```python
CUSTOM_WARNING = (
    "We found a custom integration %s which has not "
    "been tested by Home Assistant. This component might "
    "cause stability problems, be sure to disable it if you "
    "experience issues with Home Assistant"
)
```

([`homeassistant/loader.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/loader.py#L155-L160))

Pluggy, the host that most Python plugin systems inherit from, is the strict case: a duplicate name
*or* a duplicate object is a `ValueError` at registration
([`src/pluggy/_manager.py`](https://github.com/pytest-dev/pluggy/blob/main/src/pluggy/_manager.py#L125-L137)).

```python
raise ValueError(
    "Plugin name already registered: "
    f"{plugin_name}={plugin}\n{self._name2plugin}"
)
```

```python
raise ValueError(
    "Plugin already registered under a different name: "
    f"{plugin_name}={plugin}\n{self._name2plugin}"
)
```

Pydantic is the silent case. Its loader skips a repeated entry-point *value* without a word: `if
entry_point.value in _plugins: continue`
([`pydantic/plugin/_loader.py`](https://github.com/pydantic/pydantic/blob/main/pydantic/plugin/_loader.py#L43-L44)).
First wins; nothing is reported.

## 2 2. Two plugins claiming one thing

**Litestar.** A shared path is not itself an error. `Litestar._build_routes` groups HTTP handlers by
path into `http_path_groups` and builds one `HTTPRoute` per path, "since http routes can have
multiple handlers (the case when one path handles multiple methods […])"
([`litestar/app.py`](https://github.com/litestar-org/litestar/blob/main/litestar/app.py#L660-L683)).
The refusal lands one level down, per HTTP method, in
[`litestar/routes/http.py`](https://github.com/litestar-org/litestar/blob/main/litestar/routes/http.py#L58-L71):

```python
    def create_handler_map(self, route_handlers: Iterable[HTTPRouteHandler]) -> dict[HttpMethodName, HTTPRouteHandler]:
        """Parse the ``router_handlers`` of this route and return a mapping of
        http- methods and route handlers.
        """
        handler_map = {}
        for route_handler in route_handlers:
            for http_method in route_handler.http_methods:
                if http_method in handler_map:
                    raise ImproperlyConfiguredException(
                        f"Handler already registered for path {self.path!r} and http method {http_method}"
                    )
                handler_map[http_method] = route_handler
        return handler_map
```

`ImproperlyConfiguredException` is declared in
[`litestar/exceptions/http_exceptions.py`](https://github.com/litestar-org/litestar/blob/main/litestar/exceptions/http_exceptions.py#L90)
as `class ImproperlyConfiguredException(HTTPException, ValueError)` and re-exported from
`litestar.exceptions`. Two more collisions carry their own strings:

- A named handler may not be reused. `_store_handler_to_route_mapping` raises the following while
  the routing trie is built
  ([`litestar/_asgi/asgi_router.py`](https://github.com/litestar-org/litestar/blob/main/litestar/_asgi/asgi_router.py#L152-L155)):

  ```python
  raise ImproperlyConfiguredException(
      f"route handler names must be unique - {handler.name} is not unique."
  )
  ```

- An ASGI handler may not share its path with anything, and a mount may not carry path parameters
  ([`litestar/_asgi/routing_trie/validate.py`](https://github.com/litestar-org/litestar/blob/main/litestar/_asgi/routing_trie/validate.py#L26-L42)):

  ```python raise ImproperlyConfiguredException("ASGI handlers must have a unique path not shared by
  other route handlers.") ```

  ```python raise ImproperlyConfiguredException("Path parameters are not allowed under a static or
  mount route.") ```

There is a quieter Litestar collision with no message at all. `PluginRegistry.__init__` builds
`self._plugins_by_type = {type(p): p for p in plugins}`, so a second plugin of the same concrete
class silently replaces the first, and `PluginRegistry.get(type_)` returns only the survivor
([`litestar/plugins/base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py#L304-L334)).

**Sphinx.** The two extension points named in the brief behave differently from one another.

`Sphinx.add_config_value` delegates to `Config.add`, which raises unconditionally — there is no
`override` parameter to relax it
([`sphinx/config.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/config.py#L502-L503)):

```python
        if name in self._options:
            raise ExtensionError(__('Config value %r already present') % name)
```

`Sphinx.add_directive` only warns, and the warning is typed for suppression through
`suppress_warnings` as `app.add_directive`
([`sphinx/application.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/application.py#L1110-L1119)):

```python
        logger.debug('[app] adding directive: %r', (name, cls))
        if not override and docutils.is_directive_registered(name):
            logger.warning(
                __('directive %r is already registered and will not be overridden'),
                name,
                type='app',
                subtype='add_directive',
            )

        docutils.register_directive(name, cls)
```

The warning text and the code disagree: `docutils.register_directive(name, cls)` runs
unconditionally on the next line, and it is a thin wrapper over docutils' global
`directives.register_directive`
([`sphinx/util/docutils.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/util/docutils.py#L112-L118)).
The second registration wins despite the message promising it "will not be overridden". `add_role`
and `add_generic_role` share the same shape with `__('role %r is already registered and will not be
overridden')`
([`sphinx/application.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/application.py#L1136-L1173)).

Sphinx's own registry, by contrast, raises for every duplicate it owns, each gated on `override`:
`__('domain %s already registered')`, `__('The %r directive is already registered to domain %s')`,
`__('The %r role is already registered to domain %s')`, `__('The %r object_type is already
registered')`, `__('source_suffix %r is already registered')`, `__('source_parser for %r is already
registered')`, `__('Translator for %r already exists')`
([`sphinx/registry.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/registry.py#L201-L521)).
`__('math renderer %s is already registered') % name` at line 521 has no `override` escape hatch.

Loading the same extension twice is a silent no-op: `if extname in app.extensions: # already loaded`
then `return`
([`sphinx/registry.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/registry.py#L531-L534)).

**pytest.** Two plugins contributing a fixture of the same name is not reported at all. The
resolution rule is visibility, then registration order
([`src/_pytest/fixtures.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/fixtures.py#L2098-L2115)):

```python
        faclist = self._arg2fixturedefs.setdefault(name, [])
        # Insert the fixturedef into the list while maintaining a partial order
        # based on visibility: a fixturedef whose visibility is more specific
        # sorts after a more general one, so that it takes precedence in the
        # override chain (the last applicable fixturedef in the list is used
        # first, see getfixturedefs).
        # fixturedefs with the same visibility keep registration order, i.e. the
        # last registered wins.
```

Two global plugin fixtures have the same visibility: `is_visibility_more_specific` returns
`candidate.node is not other.node and other.node in candidate.node.iter_parents()`, which is false
when both are attached to the `Session`
([`src/_pytest/fixtures.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/fixtures.py#L139-L161)).
Selection then takes the tail of the list: `index = -1` walked back one step per level of
self-requesting override, and `fixturedef = fixturedefs[index]`
([`src/_pytest/fixtures.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/fixtures.py#L739-L749)).
So the **last-registered plugin wins**, and the loser stays reachable only to a fixture that
requests its own name.

The shadowing is not reported. `src/_pytest/warning_types.py` declares no warning class for fixture
override
([`src/_pytest/warning_types.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/warning_types.py)),
and of the warnings `src/_pytest/fixtures.py` does emit, all but two are `PytestRemovedIn10Warning`
deprecations; the exceptions are a plain `PytestWarning` for `usefixtures()` called without
arguments
([`src/_pytest/fixtures.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/fixtures.py#L1943-L1949))
and a second plain `PytestWarning` for a fixture hidden behind `@classmethod` or `@staticmethod`
([`src/_pytest/fixtures.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/fixtures.py#L2205-L2217)).
The closest thing to a report is `--fixtures`, whose `_showfixtures_main` de-duplicates on
`(fixturedef.argname, loc)` and so lists both definitions with their file locations, without saying
which one is live
([`src/_pytest/fixtures.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/fixtures.py#L2480-L2534)).

**Sentry.** Duplicate integrations collapse on `identifier` with no diagnostic: `integrations =
dict((integration.identifier, integration) for integration in integrations or ())`
([`sentry_sdk/integrations/__init__.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/__init__.py#L206-L208)).

## 3 3. Disabling and unloading

**pytest.** `-p no:NAME` blocks a plugin before command-line parsing. The documented position is
step 1 of "Plugin discovery order at tool startup"
([`doc/en/how-to/writing_plugins.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_plugins.rst#L30-L64)):

> `pytest` loads plugin modules at tool startup in the following way:
>
> 1. by scanning the command line for the `-p no:name` option and *blocking* that plugin from being
>    loaded (even builtin plugins can be blocked this way). This happens before normal command-line
>    parsing.
> 2. by loading all builtin plugins.
> 3. by scanning the command line for the `-p name` option and loading the specified plugin. This
>    happens before normal command-line parsing.
> 4. by loading all plugins registered through installed third-party package entry points, unless
>    the `PYTEST_DISABLE_PLUGIN_AUTOLOAD` environment variable is set.
> 5. by loading all plugins specified through the `PYTEST_PLUGINS` environment variable.
> 6. by loading all "initial" `conftest.py` files […]

The user-facing page is "Deactivating / unregistering a plugin by name": "This means that any
subsequent try to activate/load the named plugin will not work."
([`doc/en/how-to/plugins.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/plugins.rst#L113-L145)).
Two names cannot be blocked, each with its own `UsageError`
([`src/_pytest/config/__init__.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py#L865-L878)):

```python
            if name in essential_plugins:
                raise UsageError(f"plugin {name} cannot be disabled")

            if name.endswith("conftest.py"):
                raise UsageError(
                    f"Blocking conftest files using -p is not supported: -p no:{name}\n"
                    "conftest.py files are not plugins and cannot be disabled via -p.\n"
                )
```

The undisableable set is small and named:

```python
# Plugins that cannot be disabled via "-p no:X" currently.
essential_plugins = (
    "mark",
    "main",
    "runner",
    "fixtures",
    "helpconfig",  # Provides -p.
)
```

([`src/_pytest/config/__init__.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py#L336-L343))
Blocking `cacheprovider` transitively blocks `stepwise`, and every bare name is blocked twice, as
`NAME` and as `pytest_NAME`
([`src/_pytest/config/__init__.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py#L879-L885)).

**pydantic.** `PYDANTIC_DISABLE_PLUGINS` has two modes in one variable, and the accepted
whole-disable values are exactly three
([`pydantic/plugin/_loader.py`](https://github.com/pydantic/pydantic/blob/main/pydantic/plugin/_loader.py#L27-L46)):

```python
    disabled_plugins = os.getenv('PYDANTIC_DISABLE_PLUGINS')
```

```python
    elif disabled_plugins in ('__all__', '1', 'true'):
        return ()
```

```python
                    if disabled_plugins is not None and entry_point.name in disabled_plugins.split(','):
                        continue
```

So `__all__`, `1` and `true` disable every plugin; any other value is read as a comma-separated list
of entry-point *names* to skip. The comparison is exact and case-sensitive — `TRUE` and `yes` are
not accepted, and would be treated as a plugin name. There is no documentation page to check this
against: `pydantic/plugin/__init__.py` still points at
`[Build a Plugin](../concepts/plugins.md#build-a-plugin)`, but `docs/concepts/plugins.md` does not
exist in the repository and is absent from the `mkdocs.yml` nav
([`pydantic/plugin/__init__.py`](https://github.com/pydantic/pydantic/blob/main/pydantic/plugin/__init__.py#L1-L4)).
The loader is the only authority for these values. A plugin that fails to import is downgraded to a
warning rather than a refusal, and only for two exception types:

```python
                    except (ImportError, AttributeError) as e:
                        warnings.warn(
                            f'{e.__class__.__name__} while loading the `{entry_point.name}` Pydantic plugin, '
                            f'this plugin will not be installed.\n\n{e!r}',
                            stacklevel=2,
                        )
```

**Home Assistant.** Two disabling mechanisms are refusals at load time, both logged as errors, both
returning `None` so the integration simply never appears
([`homeassistant/loader.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/loader.py#L710-L762)):

```python
                    (
                        "The custom integration '%s' does not have a version key in the"
                        " manifest file and was blocked from loading. See"
                        " https://developers.home-assistant.io"
                        "/blog/2021/01/29/custom-integration-changes#versions"
                        " for more details"
                    ),
```

```python
                        (
                            "Version %s of custom integration '%s' %s and was blocked "
                            "from loading, please %s"
                        ),
```

The reasons are hard-coded per domain in `BLOCKED_CUSTOM_INTEGRATIONS`, e.g. `"spook":
BlockedIntegration(AwesomeVersion("4.0.0"), "breaks the template engine")`
([`homeassistant/loader.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/loader.py#L101-L140)).
A host maintaining a blocklist of specific third-party versions is unusual and worth noting.

Home Assistant's unload path unloads a *config entry*, never the module. `ConfigEntry.async_unload`
requires the setup lock and records the outcome as a state; a non-recoverable state only returns
`False` here, and the `OperationNotAllowed` that names it is raised one level up, by the manager's
`ConfigEntries.async_unload`
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py#L995-L1076),
[`#L2450-L2459`](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py#L2450-L2459)):

```python
        if domain_is_integration := self.domain == integration.domain:
            if not self.setup_lock.locked():
                raise OperationNotAllowed(
                    f"The config entry {self.title} ({self.domain}) with entry_id"
                    f" {self.entry_id} cannot be unloaded because it does not hold "
                    "the setup lock"
                )
```

```python
        supports_unload = hasattr(component, "async_unload_entry")

        if not supports_unload:
            if domain_is_integration:
                self._async_set_state(
                    hass, ConfigEntryState.FAILED_UNLOAD, "Unload not supported"
                )
            return False
```

Unloadability is a per-integration capability discovered by `hasattr`, and failure is a first-class
state rather than an exception. `ConfigEntryState` marks `FAILED_UNLOAD`, `MIGRATION_ERROR`,
`SETUP_IN_PROGRESS` and `UNLOAD_IN_PROGRESS` as `recoverable=False`, and
`ConfigEntryState.recoverable` is documented as "If the entry state is recoverable, unloads and
reloads are allowed."
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/config_entries.py#L151-L187))
Nothing in `homeassistant/loader.py` deletes from `sys.modules`; the three `sys.modules` references
are membership tests only. The imported code stays imported for the life of the process.

**Does any host support unloading a plugin from a running process?** Two do, in narrow senses, and
the rest say plainly that they cannot.

- Pluggy does, unconditionally: "You can unregister any *plugin*'s hooks using
  `PluginManager.unregister()` and check if a plugin is registered by passing its name to the
  `PluginManager.is_registered()` method."
  ([`docs/index.rst`](https://github.com/pytest-dev/pluggy/blob/main/docs/index.rst#L732-L735)).
  `unregister` removes the hook implementations from every `HookCaller` and deletes the name entry;
  `set_blocked(name)` is documented as "Block registrations of the given name, unregister if already
  registered."
  ([`src/pluggy/_manager.py`](https://github.com/pytest-dev/pluggy/blob/main/src/pluggy/_manager.py#L186-L221)).
  Pluggy states **no hazards at all** for this — the docstring promises only "Returns the
  unregistered plugin, or `None` if not found", and the Registration and Blocking sections of the
  documentation carry no caveat. That is a sourced negative: the canonical Python plugin manager
  offers unloading with no stated risk and no stated guarantee about the side effects a plugin has
  already caused.
- Home Assistant does, at config-entry granularity, and names the hazard as resource leakage: "In
  the `async_unload_entry` interface function, the integration should clean up any subscriptions and
  close any connections opened during the setup of the integration. […] we want to clean up to avoid
  memory leaks."
  ([`docs/core/integration-quality-scale/rules/config-entry-unloading.md`](https://github.com/home-assistant/developers.home-assistant/blob/master/docs/core/integration-quality-scale/rules/config-entry-unloading.md))
  The same page states the benefit precisely: "This allows Home Assistant to unload the integration
  on runtime, allowing the user to remove the integration or to reload it without having to restart
  Home Assistant." And it closes the loophole: "Note that integrations always need to implement
  `async_unload_entry` to support config entry unloading, just calling `entry.async_on_unload` is
  not enough."

Django says the opposite, twice, in comments that are the clearest statement of the hazard anywhere
in this survey. On the model registry
([`django/apps/registry.py`](https://github.com/django/django/blob/main/django/apps/registry.py#L27-L34)):

```python
        # Mapping of app labels => model names => model classes. Every time a
        # model is imported, ModelBase.__new__ calls apps.register_model which
        # creates an entry in all_models. All imported models are registered,
        # regardless of whether they're defined in an installed application
        # and whether the registry has been populated. Since it isn't possible
        # to reimport a module safely (it could reexecute initialization code)
        # all_models is never overridden or reset.
```

And on the closest thing Django has to swapping the plugin set, `Apps.set_installed_apps`
([`django/apps/registry.py`](https://github.com/django/django/blob/main/django/apps/registry.py#L339-L355)):

```python
        This method may trigger new imports, which may add new models to the
        registry of all imported models. They will stay in the registry even
        after unset_installed_apps(). Since it isn't possible to replay
        imports safely (e.g. that could lead to registering listeners twice),
        models are registered when they're imported and never removed.
```

`set_available_apps` is the safe sibling precisely because it does less: "This method is safe in the
sense that it doesn't trigger any imports." Both are documented as test-only — "Primarily used for
performance optimization in `TransactionTestCase`" and "Primarily used as a receiver of the
`setting_changed` signal in tests" — and `populate()` guards reentry with
`raise RuntimeError("populate() isn't reentrant")`.

The language documentation agrees. CPython's `importlib.reload` lists the caveats
([`Doc/library/importlib.rst`](https://github.com/python/cpython/blob/main/Doc/library/importlib.rst#L145-L205)):

> Other references to the old objects (such as names external to the module) are not rebound to
> refer to the new objects and must be updated in each namespace where they occur if that is
> desired.

> It is generally not very useful to reload built-in or dynamically loaded modules. Reloading
> `sys`, `__main__`, `builtins` and other key modules is not recommended. In many cases extension
> modules are not designed to be initialized more than once, and may fail in arbitrary ways when
> reloaded.

> If a module instantiates instances of a class, reloading the module that defines the class does
> not affect the method definitions of the instances --- they continue to use the old class
> definition. The same is true for derived classes.

Sphinx, Litestar, Sentry and pydantic have no unload path. Sphinx's registry has `load_extension`
and no counterpart. Litestar's `PluginRegistry` is built once from a `frozenset` in `__init__` with
no mutator
([`litestar/plugins/base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py#L291-L340)).
Sentry gates `setup_once` on a module-level set — "`# Set of all integration identifiers we have
attempted to install`" `_processed_integrations` — under `_installer_lock`, so a second
`sentry_sdk.init` never re-runs it and the monkeypatches it installed are never undone
([`sentry_sdk/integrations/__init__.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/__init__.py#L14-L22)).
Pydantic caches loaded plugins in a module-level `_plugins` dict with no eviction.

## 4 4. The negative space: explicit prohibitions

**Sphinx — parallel safety.** The contract is stated in the extension-metadata reference
([`doc/extdev/index.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/extdev/index.rst#L197-L227)):

> `'parallel_read_safe'`
>   A boolean that specifies if parallel reading of source files can be used when the extension is
>   loaded. It defaults to `False`, meaning that you have to explicitly specify your extension to be
>   safe for parallel reading after checking that it is.
>
>   .. important::
>
>      When *parallel-read-safe* is `True`, the extension must satisfy the following conditions:
>
>      * The core logic of the extension is parallelly executable during the reading phase.
>      * It has event handlers for `env-merge-info` and `env-purge-doc` events if it stores data to
>        the build environment object (`env`) during the reading phase.

> `'parallel_write_safe'`
>   A boolean that specifies if parallel writing of output files can be used when the extension is
>   loaded. Since extensions usually don't negatively influence the process, this defaults to
>   `True`.

The code defaults differ from the documented ones in a way that matters: `Extension.__init__` sets
`self.parallel_read_safe = kwargs.pop('parallel_read_safe', None)` with the comment "The default
value is `None`. It means the extension does not tell the status. It will be warned on parallel
reading", while write safety really does default to `True`
([`sphinx/extension.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/extension.py#L23-L38)).

What an unsafe extension causes is a downgrade, not a failure. `Sphinx.is_parallel_allowed` emits
two warnings — the diagnosis and `doing serial %s` — and returns `False` at the first offending
extension, and the builder then reads or writes serially
([`sphinx/application.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/application.py#L1805-L1837)):

```python
            message_not_declared = __(
                'the %s extension does not declare if it '
                'is safe for parallel reading, assuming '
                "it isn't - please ask the extension author "
                'to check and make it explicit'
            )
            message_not_safe = __('the %s extension is not safe for parallel reading')
```

```python
        for ext in self.extensions.values():
            allowed = getattr(ext, attrname, None)
            if allowed is None:
                logger.warning(message_not_declared, ext.name)
                logger.warning(__('doing serial %s'), typ)
                return False
            elif not allowed:
                logger.warning(message_not_safe, ext.name)
                logger.warning(__('doing serial %s'), typ)
                return False
```

One silent extension therefore serialises the whole build for everyone. The call sites are
`self.parallel_ok = self._app.is_parallel_allowed('write')` and `par_ok =
self._app.is_parallel_allowed('read')`
([`sphinx/builders/__init__.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/builders/__init__.py#L448-L518)).
The write variant of the messages is identical with "writing" substituted.

The same reference page carries the hardest prohibition in the Sphinx API:

> .. attention::
>    If `'env_version'` is not set, the extension **must not** store any data or state directly on
>    the environment object  (`env`).

And a discouragement in the source, on the global-state mutation behind `add_directive`
([`sphinx/util/docutils.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/util/docutils.py#L112-L118)):

```python
def register_directive(name: str, directive: type[Directive]) -> None:
    """Register a directive to docutils.

    This modifies global state of docutils.  So it is better to use this
    inside ``docutils_namespace()`` to prevent side-effects.
    """
```

`Sphinx.add_config_value` adds a naming discouragement: the `name` parameter "is recommended to be
prefixed with the extension name (ex. `html_logo`, `epub_title`)"
([`sphinx/application.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/application.py#L900-L901)).

**Django — side effects and database access in `ready()`.** Two prohibitions, one per stage. On
stage 1 of the registry
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt#L452-L472)):

> *At this stage, your code shouldn't import any models!*
>
> In other words, your applications' root packages and the modules that define your application
> configuration classes shouldn't import any models, even indirectly.
>
> Strictly speaking, Django allows importing models once their application configuration is loaded.
> However, in order to avoid needless constraints on the order of `INSTALLED_APPS`, it's strongly
> recommended not import any models at this stage.

On `ready()` itself
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt#L317-L328)):

> .. warning::
>
>     Although you can access model classes as described above, avoid interacting with the database
>     in your `ready()` implementation. This includes model methods that execute queries (`save()`,
>     `delete()`, manager methods etc.), and also raw SQL queries via `django.db.connection`. Your
>     `ready()` method will run during startup of every management command. For example, even though
>     the test database configuration is separate from the production settings, `manage.py test`
>     would still execute some queries against your **production** database!

This one is enforced at runtime, from the database layer rather than the app registry
([`django/db/backends/utils.py`](https://github.com/django/django/blob/main/django/db/backends/utils.py#L24-L28)):

```python
    APPS_NOT_READY_WARNING_MSG = (
        "Accessing the database during app initialization is discouraged. To fix this "
        "warning, avoid executing queries in AppConfig.ready() or when your app "
        "modules are imported."
    )
```

It is raised as a `RuntimeWarning` from three cursor paths — `_execute`, `_executemany` and
`callproc` — each guarded by `if not apps.ready and not apps.stored_app_configs:`
([`django/db/backends/utils.py`](https://github.com/django/django/blob/main/django/db/backends/utils.py#L64-L114)).
The reasons are spelled out in the troubleshooting section: "Such premature database queries are
discouraged because they will run during the startup of every management command, which will slow
down your project startup, potentially cache stale data, and can even fail if migrations are
pending."
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt#L530-L536))

**Litestar — registering routes after the application exists.** `Litestar.register` warns
unconditionally, before doing the work
([`litestar/app.py`](https://github.com/litestar-org/litestar/blob/main/litestar/app.py#L805-L822)):

```python
    def register(self, value: ControllerRouterHandler) -> None:
        warnings.warn(
            "Registering routes after the application instance has been "
            "created is discouraged, as it might lead to unexpected behaviour "
            "and is a costly operation. To register routes dynamically, a "
            "plugin should be used where routes can be added to the "
            "application via 'AppConfig' 'route_handlers' property",
            category=LitestarWarning,
            stacklevel=2,
        )
```

The message names the sanctioned alternative only in outline — "a plugin should be used where routes
can be added to the application via 'AppConfig' 'route_handlers' property"; the hook that does it is
`InitPlugin.on_app_init`, which takes and returns an `AppConfig`. The rebuild that follows is total:
line 815 sets `self.routes = []`, then `_build_routes` runs over an
`itertools.chain(self._reduce_handlers([value]), …)` whose second element is a generator expression
over `self.routes` — read after that reset — and finally
`self.asgi_router.construct_routing_trie()`, which is where the "costly" claim comes from.
`LitestarWarning` is `class LitestarWarning(UserWarning)`
([`litestar/exceptions/base_exceptions.py`](https://github.com/litestar-org/litestar/blob/main/litestar/exceptions/base_exceptions.py#L62-L63)),
so it is on by default and suppressible per category.

**Other explicit prohibitions found in plugin-API references.**

- Pluggy, on calling convention: "Note that you **must** call hooks using keyword *argument*
  syntax!"
  ([`docs/index.rst`](https://github.com/pytest-dev/pluggy/blob/main/docs/index.rst#L809)).
  A positional call is not merely discouraged.
- Sentry, on a legacy method: `install = None` carries the docstring `"""Legacy method, do not
  implement."""`, and `setup_once` is documented as "This function is only called once, ever.
  Configuration is not available at this point, so the only thing to do here is to hook into
  exception handlers, and perhaps do monkeypatches."
  ([`sentry_sdk/integrations/__init__.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/__init__.py#L326-L352))
- aiogram, on the router-attachment setter: "Internal property setter of parent router fot this
  router. Do not use this method in own code. All routers should be included via `include_router`
  method. Self- and circular- referencing are not allowed here"
  ([`aiogram/dispatcher/router.py`](https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/dispatcher/router.py#L223-L253)).
  It is enforced with three `RuntimeError`s: `f"Router is already attached to
  {self._parent_router!r}"`, `"Self-referencing routers is not allowed"` and `"Circular referencing
  of Router is not allowed"`. The root object refuses re-parenting outright:
  `Dispatcher.parent_router`'s setter raises `RuntimeError("Dispatcher can not be attached to
  another Router.")`
  ([`aiogram/dispatcher/dispatcher.py`](https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/dispatcher/dispatcher.py#L130-L139)).
- Home Assistant, on depending on always-loaded code: `hassfest` rejects `f"Dependency {dep} is a
  core integration and is unconditionally loaded"`, alongside `f"Dependency {dep} does not exist"`
  and `f"Dependency {dep} is both in dependencies and after_dependencies"`
  ([`script/hassfest/dependencies.py`](https://github.com/home-assistant/core/blob/dev/script/hassfest/dependencies.py#L321-L347)).
- vsce, on a dependency direction: `"You should not depend on 'vscode' in your 'dependencies'. Did
  you mean to add it to 'devDependencies'?"` and, for icons, `` `SVGs can't be used as icons:
  ${manifest.icon}` ``
  ([`src/package.ts`](https://github.com/microsoft/vscode-vsce/blob/main/src/package.ts#L1395-L1423)).

## 5 5. Order determinism

The resolved order is introspectable in most hosts; almost nowhere is it a compatibility promise.

| Host | Introspection at runtime | Order source | Promise? |
|---|---|---|---|
| pluggy / pytest | `PluginManager.list_name_plugin()`, `get_plugins()`, `HookCaller.get_hookimpls()`; `pytest --trace-config` | LIFO registration, then `tryfirst`/`trylast`, wrappers outermost | Behaviour documented, no stability clause found |
| Django | `apps.get_app_configs()`, `apps.app_configs` | `INSTALLED_APPS` order, all three stages | Order documented; relying on it is discouraged |
| Sphinx | `app.extensions` (`dict[str, Extension]`) | `extensions` config list order, depth-first through `setup_extension` | Not documented as ordered |
| Litestar | `app.plugins` (`PluginRegistry`) | typed tuples keep list order; `__iter__` walks a `frozenset` | No promise; `__iter__` order is not registration order |
| Home Assistant | `hass.config.components` (a set) | hard-coded bootstrap stages plus `dependencies`/`after_dependencies` | Membership only; no order exposed |

Pluggy documents the mechanism twice: "By default hooks are *called* in LIFO registered order,
however, a *hookimpl* can influence its call-time invocation position using special attributes",
with the note "`tryfirst` and `trylast` hooks are still invoked in LIFO order within each category"
([`docs/index.rst`](https://github.com/pytest-dev/pluggy/blob/main/docs/index.rst#L319-L370)), and
later "Hook implementations are called in LIFO registered order: *the last registered plugin's hooks
are called first*"
([`docs/index.rst`](https://github.com/pytest-dev/pluggy/blob/main/docs/index.rst#L811-L813)).
`get_hookimpls()` returns `self._hookimpls.copy()`
([`src/pluggy/_hooks.py`](https://github.com/pytest-dev/pluggy/blob/main/src/pluggy/_hooks.py#L477-L479))
— the resolved list, but in reverse call order: `_multicall` walks it as `for hook_impl in
reversed(hook_impls)`, so its last element runs first
([`src/pluggy/_callers.py`](https://github.com/pytest-dev/pluggy/blob/main/src/pluggy/_callers.py#L98)).
pytest documents a worked three-plugin ordering example under *Hook function ordering / call
example*
([`doc/en/how-to/writing_hook_functions.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_hook_functions.rst#L108-L160)).
Neither page declares the order stable across versions; searching pytest's how-to and reference
documentation for a guarantee or a disclaimer about plugin order returns nothing.

Django is the one host that documents order as a property of the whole start-up: "The application
registry is initialized in three stages. At each stage, Django processes all applications in the
order of `INSTALLED_APPS`."
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt#L452-L453)).
It then discourages depending on it, "in order to avoid needless constraints on the order of
`INSTALLED_APPS`". `apps.get_app_configs()` is documented only as "Returns an iterable of
`AppConfig` instances" — the ordering is a property of `populate()`, not of the accessor
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt#L377-L379)).

Litestar is the counter-example worth naming. `PluginRegistry.__iter__` returns
`iter(self._plugins)` over a `frozenset`, while the typed views (`registry.init`,
`registry.openapi`, `registry.serialization`, …) are tuples built in the order plugins were passed
([`litestar/plugins/base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py#L304-L337)).
Iterating the public registry therefore cannot report registration order at all: "Being an unordered
collection, sets do not record element position or order of insertion."
([`Doc/library/stdtypes.rst`](https://github.com/python/cpython/blob/main/Doc/library/stdtypes.rst#L5427-L5429))

Sphinx exposes `self.extensions: dict[str, Extension] = {}` on the application
([`sphinx/application.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/application.py#L208)),
which preserves insertion order as any Python dict does, and `is_parallel_allowed` iterates it. The
`extensions` configuration value is documented as "A list of strings that are module names of Sphinx
extensions" with no statement about order or ordering guarantees
([`doc/usage/configuration.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/usage/configuration.rst#L199-L224)).
Nothing found makes the resolved extension order part of a compatibility promise.

Home Assistant does not expose an order. `hass.config.components` is a `_ComponentSet` over two
`set[str]`, documented as "Set of loaded components. This set contains both top level components and
platforms."
([`homeassistant/core_config.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/core_config.py#L485-L513)).
The setup order itself is partly hard-coded, in named stages with comments explaining each ordering
constraint — "`# Load logging and http deps as soon as possible`", "`# Zeroconf is used for mdns
resolution in aiohttp client helper.`", "`# We need to make sure discovery integrations update their
deps before stage 2 integrations load them inadvertently before their deps have been updated […]`"
([`homeassistant/bootstrap.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/bootstrap.py#L183-L213)).
Ordering is a property of the host's own stage table, not of the plugin declarations.

## 6 6. Static validation before start-up

All three validators run against the declaration on disk, without executing the plugin.

**hassfest** dispatches 23 integration validators and 7 repository-wide ones, named in
`INTEGRATION_PLUGINS` and `HASS_PLUGINS`
([`script/hassfest/__main__.py`](https://github.com/home-assistant/core/blob/dev/script/hassfest/__main__.py#L43-L81)):
`application_credentials`, `bluetooth`, `codeowners`, `conditions`, `config_schema`, `dependencies`,
`dhcp`, `icons`, `integration_info`, `integration_type`, `json`, `labs`, `manifest`, `mqtt`,
`quality_scale`, `requirements`, `services`, `ssdp`, `translations`, `triggers`, `usb`, `zeroconf`,
then `config_flow` last with the comment "`# This needs to run last, after translations are
processed`". Concrete manifest checks, with their exact messages
([`script/hassfest/manifest.py`](https://github.com/home-assistant/core/blob/dev/script/hassfest/manifest.py#L205-L420)):

- the manifest matches a voluptuous schema with `vol.Required("domain")` and `vol.Required("name")`,
  a closed `integration_type` enum, and per-discovery-protocol sub-schemas with case rules —
  `verify_uppercase` for a MAC address, `verify_lowercase` for a zeroconf manufacturer or model, and
  `verify_wildcard` raising `f"'{value}' needs to contain a wildcard matcher"`;
- `"Domain does not match dir name"`;
- `"Domain collides with built-in core integration"` (a warning, for custom integrations only);
- `"Domain should not have an IoT Class"` / `"Domain is missing an IoT Class"`;
- `"Virtual integration points to non-existing supported_by integration"`;
- `f"{quality_scale} integration does not have a code owner"` at silver and above;
- `"No 'version' key in the manifest file."` for a custom integration;
- key ordering: `f"Manifest keys {text}: domain, name, then alphabetical order"`.

The dependency validator parses every `.py` file in the integration with `ast` — `ImportCollector`
is an `ast.NodeVisitor` — and compares the imports it finds against the declaration
([`script/hassfest/dependencies.py`](https://github.com/home-assistant/core/blob/dev/script/hassfest/dependencies.py#L19-L347)):
`f"Using component {domain} but it's not in 'dependencies' or 'after_dependencies'"`, `f"Dependency
{dep} does not exist"`, `f"Dependency {dep} is both in dependencies and after_dependencies"`,
`f"Dependency {dep} is a core integration and is unconditionally loaded"`, and cycle detection
reporting `f"Found a circular dependency with {integration.domain} ({', '.join(checking)})"` plus a
separate message for cycles through `after_dependencies`.

**vsce** validates the `package.json` declaration in `validateManifestForPackaging`, called from
`readManifest` before the archive is built
([`src/package.ts`](https://github.com/microsoft/vscode-vsce/blob/main/src/package.ts#L1338-L1465),
[`src/validation.ts`](https://github.com/microsoft/vscode-vsce/blob/main/src/validation.ts#L1-L131)):

- identity: `name` and `publisher` must match `/^[a-z0-9][a-z0-9\-]*$/i`, with the publisher message
  distinguishing the two failure modes — `Missing extension "publisher": "<ID>" in package.json` and
  `Invalid extension "publisher": "…" in package.json. Expected the identifier of a publisher, not
  its human-friendly name.`;
- `version` must be `semver.valid`;
- `engines.vscode` must match `/^\*$|^(\^|>=)?((\d+)|x)\.((\d+)|x)\.((\d+)|x)(\-.*)?$/`, and a
  missing `engines` object is `'Manifest missing field: engines'`;
- `@types/vscode` may not exceed `engines.vscode` at major or minor:
  `@types/vscode ${typeVersion} greater than engines.vscode ${engineVersion}. Either upgrade
  engines.vscode or use an older @types/vscode version`;
- entry-point coherence, in both directions:
  `"Manifest needs either a 'main' or 'browser' property, given it has a 'activationEvents'
  property."` and `"Manifest needs the 'activationEvents' property, given it has a 'main'
  property."` — the second reached only when the manifest declares no `activationEvents` and does
  not qualify for implicit ones, the condition being
  `engines.vscode === '*' || semver.satisfies(parsedEngineVersion, '>=1.74', …)` together with a
  `contributes` entry for languages, commands, authentication, custom editors or views;
- closed enums and URL policy: `pricing` restricted to `Free` or `Trial`, `extensionKind` checked
  against `ValidExtensionKinds`, `sponsor.url` required to be HTTP or HTTPS, badge URLs required to
  be HTTPS with `Badge SVGs are restricted. Please use other file image formats, such as PNG`, and
  `SVGs can't be used as icons`.

**Ansible sanity tests** are a suite of independent static checks. Three matter here.

`validate-modules` cross-checks the `DOCUMENTATION` block against the `argument_spec` without
invoking the module, reporting a named code per divergence
([`validate_modules/main.py`](https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_util/controller/sanity/validate-modules/validate_modules/main.py)):
`undocumented-parameter` — "is listed in the argument_spec, but not documented in the module
documentation" (line 2183); `nonexistent-parameter-documented` — "is listed in
DOCUMENTATION.options, but not accepted by the module argument_spec" (line 2193);
`doc-default-does-not-match-spec`, `doc-choices-do-not-match-spec`, `doc-required-mismatch` — "is
required, but is not documented as being required" and its inverse; `parameter-type-not-in-doc` and
`doc-missing-type`; `<name>-collision` — "has repeated terms" (line 1431) and `<name>-unknown` —
"contains terms which are not part of argument_spec: …" (line 1441) for `required_together`,
`mutually_exclusive` and friends; `parameter-alias-self`, `parameter-alias-repeated`,
`invalid-argument-name`, `no-log-needed`, `missing-gplv3-license`,
`missing-module-utils-basic-import`, `import-before-documentation`.

`action-plugin-docs` enforces a pairing rule across two directories with one line of output: `'%s:
action plugin has no matching module to provide documentation'`
([`code-smell/action-plugin-docs.py`](https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_util/controller/sanity/code-smell/action-plugin-docs.py)).

`runtime-metadata` validates `meta/runtime.yml` — the redirect and deprecation declarations — with a
voluptuous schema under `PREVENT_EXTRA`, keyed per plugin type (`action`, `become`, `cache`,
`callback`, `cliconf`, `connection`, …), with custom validators that reject a non-FQCR redirect
target ("Must be a string that is a FQCR"), a malformed date ("Expected ISO 8601 date string
(YYYY-MM-DD), or YAML date"), a non-major removal version ("removal_version (%r) must be a major
release, not a minor or patch release"), and a removal window pointing the wrong way ("The tombstone
removal_date (%s) must not be after today (%s)", "The deprecation removal_version (%r) must be after
the current version (%s)")
([`code-smell/runtime-metadata.py`](https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_util/controller/sanity/code-smell/runtime-metadata.py)).

Two further tests bound how much can be checked statically. `import` does execute the module's
import — "Import the given python module(s) and report error(s) encountered" — in an isolated
virtualenv with an empty `ansible._vendor` preloaded, but never runs the task
([`sanity/import/importer.py`](https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_util/target/sanity/import/importer.py)).
`ansible-doc` renders the documentation of every documentable plugin type, which requires importing
the plugin but not executing it
([`sanity/ansible_doc.py`](https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_internal/commands/sanity/ansible_doc.py)).

## 7 A table of refusals

| Host | What is refused | Moment | Kind | Exact message |
|---|---|---|---|---|
| Django | duplicate app label | start-up, `Apps.populate()` phase 1 | `ImproperlyConfigured` | `Application labels aren't unique, duplicates: %s` |
| Django | duplicate app name | start-up, `Apps.populate()` after phase 1 | `ImproperlyConfigured` | `Application names aren't unique, duplicates: %s` |
| Django | reentrant `populate()` | start-up | `RuntimeError` | `populate() isn't reentrant` |
| Django | `available_apps` not a subset | test set-up | `ValueError` | `Available apps isn't a subset of installed apps, extra apps: %s` |
| Django | query before apps ready | first cursor `execute`/`executemany`/`callproc` | `RuntimeWarning` | `Accessing the database during app initialization is discouraged. To fix this warning, avoid executing queries in AppConfig.ready() or when your app modules are imported.` |
| Litestar | same path and HTTP method twice | init, `HTTPRoute.create_handler_map` | `ImproperlyConfiguredException` | `Handler already registered for path {path!r} and http method {http_method}` |
| Litestar | duplicate route-handler `name` | init, `construct_routing_trie` | `ImproperlyConfiguredException` | `route handler names must be unique - {name} is not unique.` |
| Litestar | ASGI handler sharing a path | init, `validate_node` | `ImproperlyConfiguredException` | `ASGI handlers must have a unique path not shared by other route handlers.` |
| Litestar | path parameter under a mount | init, `validate_node` | `ImproperlyConfiguredException` | `Path parameters are not allowed under a static or mount route.` |
| Litestar | duplicate path parameter name | init, `BaseRoute` | `ImproperlyConfiguredException` | `Duplicate parameter '{param_name}' detected in '{path}'.` |
| Litestar | router registered on itself | registration | `ImproperlyConfiguredException` | `Cannot register a router on itself` |
| Litestar | undecorated callable registered | registration | `ImproperlyConfiguredException` | `Unsupported value passed to `Router.register`. If you passed in a function or method, make sure to decorate it first with one of the routing decorators` |
| Litestar | route registered after app init | post-init `register()` | `LitestarWarning` | `Registering routes after the application instance has been created is discouraged, as it might lead to unexpected behaviour and is a costly operation. To register routes dynamically, a plugin should be used where routes can be added to the application via 'AppConfig' 'route_handlers' property` |
| Litestar | second plugin of the same class | init, `PluginRegistry.__init__` | none — silent overwrite | — |
| Sphinx | duplicate config value name | extension `setup()`, `Config.add` | `ExtensionError` | `Config value %r already present` |
| Sphinx | duplicate directive name | extension `setup()`, `add_directive` | warning, subtype `app.add_directive`; registration proceeds | `directive %r is already registered and will not be overridden` |
| Sphinx | duplicate role name | extension `setup()`, `add_role` | warning, subtype `app.add_role`; registration proceeds | `role %r is already registered and will not be overridden` |
| Sphinx | duplicate domain | extension `setup()`, registry | `ExtensionError` | `domain %s already registered` |
| Sphinx | duplicate source suffix / parser | extension `setup()`, registry | `ExtensionError` | `source_suffix %r is already registered` / `source_parser for %r is already registered` |
| Sphinx | duplicate math renderer (no `override`) | extension `setup()`, registry | `ExtensionError` | `math renderer %s is already registered` |
| Sphinx | extension without `setup()` | import, `load_extension` | warning | `extension %r has no setup() function; is it really a Sphinx extension module?` |
| Sphinx | unimportable extension | import, `load_extension` | `ExtensionError` | `Could not import extension %s` |
| Sphinx | extension merged into Sphinx | import, `load_extension` | warning, then ignored | `the extension %r was already merged with Sphinx since version %s; this extension is ignored.` |
| Sphinx | extension too old for the project | extension `setup()` | `VersionRequirementError` | `The %s extension used by this project needs at least Sphinx v%s; it therefore cannot be built with this version.` |
| Sphinx | undeclared parallel-read safety | build, `is_parallel_allowed('read')` | warning, then serial build | `the %s extension does not declare if it is safe for parallel reading, assuming it isn't - please ask the extension author to check and make it explicit` + `doing serial read` |
| Sphinx | declared parallel-unsafe | build, `is_parallel_allowed` | warning, then serial build | `the %s extension is not safe for parallel reading` (or `writing`) |
| Sphinx | loading an already-loaded extension | import, `load_extension` | none — silent return | — |
| pluggy | duplicate plugin name | `register()` | `ValueError` | `Plugin name already registered: {name}={plugin}\n{name2plugin}` |
| pluggy | same object under a second name | `register()` | `ValueError` | `Plugin already registered under a different name: {name}={plugin}\n{name2plugin}` |
| pluggy | hookspec module with no hooks | `add_hookspecs()` | `ValueError` | `did not find any {project_name!r} hooks in {module_or_class!r}` |
| pytest | blocking an essential plugin | start-up, before option parsing | `UsageError` | `plugin {name} cannot be disabled` |
| pytest | blocking a `conftest.py` | start-up, before option parsing | `UsageError` | `Blocking conftest files using -p is not supported: -p no:{name}\nconftest.py files are not plugins and cannot be disabled via -p.\n` |
| pytest | two plugins, one fixture name | collection | none — last registered wins | — |
| pydantic | duplicate entry-point value | first validator construction | none — silently skipped, first wins | — |
| pydantic | plugin raising `ImportError`/`AttributeError` | first validator construction | `UserWarning` | `{ExcName} while loading the `{entry_point.name}` Pydantic plugin, this plugin will not be installed.\n\n{e!r}` |
| Home Assistant | custom integration with no `version` | import, `Integration.resolve_from_root` | `_LOGGER.error`, integration dropped | `The custom integration '%s' does not have a version key in the manifest file and was blocked from loading.` |
| Home Assistant | unparseable `version` | import | `_LOGGER.error`, integration dropped | `The custom integration '%s' does not have a valid version key (%s) in the manifest file and was blocked from loading.` |
| Home Assistant | blocklisted version | import | `_LOGGER.error`, integration dropped | `Version %s of custom integration '%s' %s and was blocked from loading, please %s` |
| Home Assistant | any custom integration | import | `_LOGGER.warning`, load proceeds | `We found a custom integration %s which has not been tested by Home Assistant. This component might cause stability problems, be sure to disable it if you experience issues with Home Assistant` |
| Home Assistant | unload without the setup lock | runtime unload | `OperationNotAllowed` | `The config entry {title} ({domain}) with entry_id {entry_id} cannot be unloaded because it does not hold the setup lock` |
| Home Assistant | unload of a non-recoverable entry | runtime unload | `OperationNotAllowed` | `The config entry '{title}' ({domain}) with entry_id '{entry_id}' cannot be unloaded because it is in the non recoverable state {state}` |
| Home Assistant | unload of an entry without `async_unload_entry` | runtime unload | state `FAILED_UNLOAD`, returns `False` | reason string `Unload not supported` |
| Home Assistant | custom domain shadowing a core one | `hassfest` validate | warning | `Domain collides with built-in core integration` |
| Home Assistant | domain ≠ directory name | `hassfest` validate | error | `Domain does not match dir name` |
| Home Assistant | dependency on a core integration | `hassfest` validate | error | `Dependency {dep} is a core integration and is unconditionally loaded` |
| Home Assistant | circular dependency | `hassfest` validate | error | `Found a circular dependency with {domain} ({chain})` |
| aiogram | router already attached | `include_router()` | `RuntimeError` | `Router is already attached to {parent!r}` |
| aiogram | self-reference | `include_router()` | `RuntimeError` | `Self-referencing routers is not allowed` |
| aiogram | cycle | `include_router()` | `RuntimeError` | `Circular referencing of Router is not allowed` |
| aiogram | attaching the root dispatcher | `include_router()` | `RuntimeError` | `Dispatcher can not be attached to another Router.` |
| vsce | missing or malformed identity | packaging, `validateManifestForPackaging` | `Error` | `Missing extension "publisher": "<ID>" in package.json` / `Invalid extension "name": "…"` / `Invalid extension "version": "…"` |
| vsce | `main` without `activationEvents` | packaging | `Error` | `Manifest needs the 'activationEvents' property, given it has a 'main' property.` |
| vsce | `activationEvents` without an entry point | packaging | `Error` | `Manifest needs either a 'main' or 'browser' property, given it has a 'activationEvents' property.` |
| vsce | `vscode` in `dependencies` | packaging | `Error` | `You should not depend on 'vscode' in your 'dependencies'. Did you mean to add it to 'devDependencies'?` |
| Ansible | argument in spec but not in docs | `validate-modules` sanity | error `undocumented-parameter` | `Argument '%s' is listed in the argument_spec, but not documented in the module documentation` |
| Ansible | documented argument not in spec | `validate-modules` sanity | error `nonexistent-parameter-documented` | `Argument '%s' is listed in DOCUMENTATION.options, but not accepted by the module argument_spec` |
| Ansible | action plugin without a module | `action-plugin-docs` sanity | reported line | `%s: action plugin has no matching module to provide documentation` |

## 8 What the evidence supports

- **A conflict is only refusable where the host owns a namespace.** Django, Litestar, Sphinx and
  pluggy all raise on duplicate identity because each keeps a dict keyed by the contested name.
  Where the key is derived instead of declared — a Litestar plugin's concrete class, a pydantic
  entry-point value, a Sentry integration identifier — the collision resolves silently. A host that
  wants duplicates refused must first name what it is keying on.
- **The moment of refusal follows the shape of the registry, not the severity of the error.** Django
  catches labels one at a time during construction and names at the end from a `Counter`. Litestar
  catches method collisions when it groups handlers by path, and name collisions later when it
  builds the trie. Both are start-up, but a design that defers registry construction defers every
  refusal with it.
- **A warning that still performs the action is worse than either alternative.** Sphinx's
  `add_directive` warns "will not be overridden" and then overrides. A host should either raise or
  override quietly with an accurate message; the third option leaves the operator's mental model
  wrong.
- **Silence on shadowing has a real cost.** pytest resolves same-name fixtures from two plugins by
  last-registration-wins, with no warning class for it and only a location listing under
  `--fixtures`. Since entry-point plugin order is not under an author's control, the effective
  fixture depends on installation order. Naming a winner is cheap; reporting the shadowing is the
  part hosts skip.
- **Unloading is either narrow or absent, and the narrow cases push cleanup onto the plugin.**
  Pluggy removes hook implementations and says nothing about what the plugin already did. Home
  Assistant unloads a config entry and requires the integration to "clean up any subscriptions and
  close any connections", tracking failure as `FAILED_UNLOAD`. Nobody unimports.
- **The stated reason nobody unimports is module-import irreversibility, not effort.** Django writes
  it twice: "it isn't possible to reimport a module safely (it could reexecute initialization code)"
  and "it isn't possible to replay imports safely (e.g. that could lead to registering listeners
  twice)". CPython's own documentation backs it: extension modules "may fail in arbitrary ways when
  reloaded", and existing instances "continue to use the old class definition". A design that
  promises hot plugin reload is promising against the language.
- **Two-phase declaration is what makes static validation possible.** hassfest, vsce and Ansible's
  sanity tests all read a manifest or a module-level constant and never call the plugin. Their
  strongest checks are cross-references — domain against directory name, imports against declared
  dependencies, documented options against `argument_spec`, `@types/vscode` against
  `engines.vscode`. Every one of those needs the declaration to be inert data separable from the
  code.
- **Parallel safety is a declaration, and the default punishes silence collectively.** Sphinx names
  the first offending extension in a warning and then serialises the entire build. One extension
  that omits `parallel_read_safe` costs every other extension its parallelism. A capability flag
  whose absence degrades the shared path needs a loud default.
- **Order is introspectable but promised nowhere.** Pluggy documents LIFO plus `tryfirst`/`trylast`
  and exposes the resolved list; Django documents `INSTALLED_APPS` order across all three stages and
  then discourages depending on it; Sphinx and Litestar make no ordering statement, and Litestar's
  public `PluginRegistry.__iter__` runs over a `frozenset`, so it is not even stable between
  processes. Exposing an order is easy; the surveyed hosts consistently decline to guarantee it.
- **The prohibitions cluster on three things: global state, start-up-time side effects, and
  internal setters.** Sphinx says an extension "**must not** store any data or state directly on the
  environment object" without `env_version`, and that `register_directive` "modifies global state of
  docutils". Django forbids model imports in stage 1 and database access in `ready()`, and enforces
  the latter from the cursor. aiogram says "Do not use this method in own code" on the setter behind
  `include_router`. Sentry marks `install` "Legacy method, do not implement". These are the
  categories a plugin API has to make hard to reach rather than merely document.

## Sources

Every claim above carries its own link inline. This section names what was read.

Home Assistant:

- <https://github.com/home-assistant/core> — `homeassistant/bootstrap.py`,
  `homeassistant/config_entries.py`, `homeassistant/core_config.py`, `homeassistant/loader.py`,
  `script/hassfest/__main__.py`, `script/hassfest/dependencies.py`, `script/hassfest/manifest.py`
- <https://github.com/home-assistant/developers.home-assistant> —
  `docs/core/integration-quality-scale/rules/config-entry-unloading.md`,
  `docs/creating_integration_file_structure.md`, `docs/creating_integration_manifest.md`
- <https://developers.home-assistant.io>

Sphinx:

- <https://github.com/sphinx-doc/sphinx> — `doc/extdev/index.rst`, `doc/usage/configuration.rst`,
  `sphinx/application.py`, `sphinx/builders/__init__.py`, `sphinx/config.py`, `sphinx/extension.py`,
  `sphinx/registry.py`, `sphinx/util/docutils.py`

pytest:

- <https://github.com/pytest-dev/pytest> — `doc/en/how-to/plugins.rst`,
  `doc/en/how-to/writing_hook_functions.rst`, `doc/en/how-to/writing_plugins.rst`,
  `src/_pytest/config/__init__.py`, `src/_pytest/fixtures.py`, `src/_pytest/warning_types.py`

Django:

- <https://github.com/django/django> — `django/apps/registry.py`, `django/db/backends/utils.py`,
  `docs/ref/applications.txt`

Litestar:

- <https://github.com/litestar-org/litestar> — `litestar/_asgi/asgi_router.py`,
  `litestar/_asgi/routing_trie/validate.py`, `litestar/app.py`,
  `litestar/exceptions/base_exceptions.py`, `litestar/exceptions/http_exceptions.py`,
  `litestar/plugins/base.py`, `litestar/routes/http.py`

pluggy:

- <https://github.com/pytest-dev/pluggy> — `docs/index.rst`, `src/pluggy/_callers.py`,
  `src/pluggy/_hooks.py`, `src/pluggy/_manager.py`

Ansible:

- <https://github.com/ansible/ansible> —
  `test/lib/ansible_test/_internal/commands/sanity/ansible_doc.py`,
  `test/lib/ansible_test/_util/controller/sanity/code-smell/action-plugin-docs.py`,
  `test/lib/ansible_test/_util/controller/sanity/code-smell/runtime-metadata.py`,
  `test/lib/ansible_test/_util/controller/sanity/validate-modules/validate_modules/main.py`,
  `test/lib/ansible_test/_util/target/sanity/import/importer.py`

Other Python hosts:

- <https://github.com/getsentry/sentry-python> — `sentry_sdk/integrations/__init__.py`

VS Code:

- <https://github.com/microsoft/vscode-vsce> — `src/package.ts`, `src/validation.ts`

pydantic:

- <https://github.com/pydantic/pydantic> — `pydantic/plugin/__init__.py`,
  `pydantic/plugin/_loader.py`

CPython:

- <https://github.com/python/cpython> — `Doc/library/importlib.rst`, `Doc/library/stdtypes.rst`

aiogram:

- <https://github.com/aiogram/aiogram> — `aiogram/dispatcher/dispatcher.py`,
  `aiogram/dispatcher/router.py`
