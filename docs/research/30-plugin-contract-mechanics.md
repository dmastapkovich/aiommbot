# 30. What a plugin host specifies beyond the list and the Protocols

**Question.** A plugin host that publishes only an explicit list and a set of narrow Protocols has
stated the *shape* of its contract and none of its *mechanics*. What do mature hosts specify beyond
that — how the contract is versioned, what happens when a plugin's lifecycle fails, through which
sanctioned channel one plugin reaches another, which conflicting declarations are refused, and what
a third-party author is handed — and by which mechanism is each of those answers enforced?

Gathered for GitHub issue #100. [`docs/research/10`](10-plugin-systems.md) surveyed the same hosts
for registration, ordering, isolation and settings, and its synthesis argued for the explicit list,
the narrow Protocols, the declare/act split and the per-plugin typed settings object. It did not ask
what a host specifies *after* those choices, which is this note: the five mechanics that
[ADR-0015](../adr/0015-plugin-contract-and-composition.md) states as words rather than as
mechanisms. It also closes two of the three items that note could not verify: Litestar's and Home
Assistant's plugin contract-test tooling, and Sphinx's own testing harness for extensions, all in
§5. The third, the Hypothesis environment variable, is untouched and remains open.

Findings only, and no recommendation: the decisions this note is evidence for are #102 and #103.
Sources are primary — project source at the default branch, reference and developer documentation,
PEPs, the Python packaging specifications, `docs.python.org`, PyPI metadata and project issue
trackers — read on 2026-09-10. Anything a primary source did not confirm is marked **[unverified]**.

## 1 Versioning the plugin contract

Eight hosts were read for a number that names the contract offered to plugins, separately from the
host's own release version. One has it. Five version the host release or the plugin release instead,
and two have no number at all.

### Sphinx: three numbers, none of them the API

`setup()` returns a metadata dictionary. Sphinx recognises exactly four keys, documented at
[Extension metadata](https://www.sphinx-doc.org/en/master/extdev/index.html#ext-metadata):

- `'version'` — "A string that identifies the extension version. It is used for extension version
  requirement checking (see `needs_extensions`) and informational purposes. If no version string is
  returned, `'unknown version'` is used by default."
- `'env_version'` — "A non-zero positive integer integer that records the version of data stored in
  the environment by the extension." The doc adds: "If `'env_version'` is not set, the extension
  **must not** store any data or state directly on the environment object (`env`)", and "The version
  number must be incremented whenever the type, structure, or meaning of the stored data change, to
  ensure Sphinx does not try and load invalid data from a cached environment."
- `'parallel_read_safe'` — "It defaults to `False`, meaning that you have to explicitly specify your
  extension to be safe for parallel reading after checking that it is."
- `'parallel_write_safe'` — "Since extensions usually don't negatively influence the process, this
  defaults to `True`."

The code disagrees with the docs on one default. `Extension.__init__` in
[`sphinx/extension.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/extension.py) sets
`self.parallel_read_safe = kwargs.pop('parallel_read_safe', None)`, with the comment "The default
value is ``None``.  It means the extension does not tell the status.  It will be warned on parallel
reading." So an undeclared extension gets `None`, not `False`, and the difference is a distinct
warning. `Sphinx.is_parallel_allowed` in
[`sphinx/application.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/application.py)
emits "the %s extension does not declare if it is safe for parallel reading, assuming it isn't -
please ask the extension author to check and make it explicit" for `None`, "the %s extension is not
safe for parallel reading" for `False`, and then "doing serial %s" in both cases. Any single
undeclared extension downgrades the whole build to serial.

`registry.load_extension` handles a non-dict return by warning "extension %r returned an unsupported
object from its setup() function; it should return None or a metadata dictionary" and substituting
an empty dict, and warns "extension %r has no setup() function; is it really a Sphinx extension
module?" when `setup` is absent
([`sphinx/registry.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/registry.py)).
Neither is fatal.

**`env_version` discards the environment; it does not warn and does not fail.**
[`sphinx/environment/__init__.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/environment/__init__.py)
holds `ENV_VERSION = 66` with the comment "This is increased every time an environment attribute is
added or changed to properly invalidate pickle files". `_get_env_version` builds a mapping of every
loaded extension's `env_version` plus `env_version['sphinx'] = ENV_VERSION`, and
`BuildEnvironment.setup` compares the whole mapping for equality:

```python
if self.version and self.version != _get_env_version(app.extensions):
    raise BuildEnvironmentError(__('build environment version not current'))
```

`Sphinx._load_existing_env` catches that with a bare `except Exception as err`, logs
`logger.info(__('failed: %s'), err)` under the progress message "loading pickled environment", and
calls `self._create_fresh_env()`. The cache is thrown away and the whole project is re-read. Because
the comparison is dict equality rather than per-key ordering, *adding or removing* an extension that
declares `env_version` invalidates the cache too — and a *decrease* invalidates it just as a rise
does. Sphinx core moves `ENV_VERSION`; the extension author moves their own `env_version`.

**`app.require_sphinx()` compares a two-element prefix.** From `sphinx/application.py`:

```python
if isinstance(version, tuple):
    major, minor = version
else:
    major, minor = map(int, version.split('.')[:2])
if (major, minor) > sphinx.version_info[:2]:
    req = f'{major}.{minor}'
    raise VersionRequirementError(req)
```

The docstring reads "Compare *version* with the version of the running Sphinx, and abort the build
when it is too old", and the parameter is "The required version in the form of ``major.minor`` or
``(major, minor)``". A patch-level requirement is impossible: `'7.1.2'` is truncated to `(7, 1)`.
The exception message is the bare required version. When `require_sphinx()` is called from inside
`setup()`, `registry.load_extension` catches it and re-raises with the extension named: "The %s
extension used by this project needs at least Sphinx v%s; it therefore cannot be built with this
version." Called anywhere else, the user sees only the number.

**`needs_sphinx` compares strings, not versions.** The confval is documented as "Set a minimum
supported version of Sphinx required to build the project. The format should be a `'major.minor'`
version string like `'1.1'` Sphinx will compare it with its version and refuse to build the project
if the running version of Sphinx is too old", default `''` ([configuration
reference](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-needs_sphinx)). The
implementation in `sphinx/application.py` is a lexicographic string comparison against
`sphinx.__display_version__`, assigned from `__version__` (`'9.1.1'` on master) and given a
`+/<short sha>` suffix in a development checkout
([`sphinx/__init__.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/__init__.py)):

```python
if (
    self.config.needs_sphinx
    and self.config.needs_sphinx > sphinx.__display_version__
):
    raise VersionRequirementError(
        __(
            'This project needs at least Sphinx v%s and therefore cannot '
            'be built with this version.'
        )
        % self.config.needs_sphinx
    )
```

String ordering is not version ordering. Verified with `python3`: `'10.0' > '8.3.0'` is `False`, so
a project needing Sphinx 10 builds silently on Sphinx 8; `'9' > '10.0.0'` is `True`, so a project
needing Sphinx 9 would be refused by Sphinx 10. The gate is set by the *documentation project
author* in `conf.py` — neither the host nor the plugin.

`needs_extensions` is the mirror image and does use real version comparison.
[`verify_needs_extensions`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/extension.py)
compares with `packaging.version.Version`, falls back to string comparison on `InvalidVersion`,
treats the sentinel `'unknown version'` as unfulfilled, and raises "This project needs the extension
%s at least in version %s and therefore cannot be built with the loaded version (%s)." A missing
extension is only a warning: "The %s extension is required by needs_extensions settings, but it is
not loaded." The confval doc says "The version strings should be in the `'major.minor'` form" and
"This requires that the extension declares its version in the `setup()` function" ([configuration
reference](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-needs_extensions)).

What Sphinx offers instead of an API version is a written deprecation policy: "If a feature is
deprecated in a release A.x, it will continue to work in all A.x.x versions (for all versions of x).
It will continue to work in all B.x.x versions but raise deprecation warnings. Deprecated features
will be removed at the C.0.0. It means the deprecated feature will work during 2 MAJOR releases at
least" ([Deprecation
policy](https://www.sphinx-doc.org/en/master/internals/release-process.html#deprecation-policy)).
The [Deprecated APIs table](https://www.sphinx-doc.org/en/master/extdev/deprecated.html) records
each target with its "Deprecated" and "Removed" version — for example `sphinx.io` (entire module),
deprecated 9.0, removed 11.0.

### Home Assistant: the plugin's version, and a host-maintained blocklist

No `manifest.json` field carries a minimum Home Assistant version. The hassfest schemas in
[`script/hassfest/manifest.py`](https://github.com/home-assistant/core/blob/dev/script/hassfest/manifest.py)
enumerate every accepted key — `INTEGRATION_MANIFEST_SCHEMA = vol.Schema({...})`, extended into
`CUSTOM_INTEGRATION_MANIFEST_SCHEMA` — and there is no `homeassistant`, `min_ha_version` or
equivalent in either the core or the custom-integration schema. The [manifest
reference](https://developers.home-assistant.io/docs/creating_integration_manifest) documents no
such key either. That is the answer to "how does Home Assistant version the contract": it does not.

Two fields carry a version constraint, and neither constrains the host:

| Field | What it constrains | Text |
|---|---|---|
| `version` | the integration itself | "The version of the integration is required for custom integrations. The version needs to be a valid version recognized by AwesomeVersion like CalVer or SemVer." For core integrations, "this should be omitted." ([docs](https://developers.home-assistant.io/docs/creating_integration_manifest#version)) |
| `requirements` | third-party Python packages | "Requirements is an array of strings. Each entry is a `pip` compatible string." ([docs](https://developers.home-assistant.io/docs/creating_integration_manifest#requirements)) |

`dependencies` and `after_dependencies` name other integrations by domain with **no version at
all**: "Dependencies are other Home Assistant integrations you want Home Assistant to set up
successfully before the integration is loaded"
([docs](https://developers.home-assistant.io/docs/creating_integration_manifest#dependencies)).

**What hassfest validates before release.** `verify_version` runs the string through
`AwesomeVersion(..., ensure_strategy=[CALVER, SEMVER, SIMPLEVER, BUILDVER, PEP440])` and raises
`vol.Invalid(f"'{value}' is not a valid version.")` on failure. `validate_version` adds the error
"No 'version' key in the manifest file." for any non-core integration, under a docstring that reads
"Will be removed when the version key is no longer optional for custom integrations." Requirements
are checked for format in
[`script/hassfest/requirements.py`](https://github.com/home-assistant/core/blob/dev/script/hassfest/requirements.py),
where core integrations must pin exactly:

```python
f'Requirement {req} need to be pinned "<pkg name>==<version>".'
```

**What the loader does at runtime.**
[`homeassistant/loader.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/loader.py)
runs three gates on every custom integration and returns `None` — refusing to load it — on each
failure:

1. No version key: "The custom integration '%s' does not have a version key in the manifest file and
   was blocked from loading. See
   https://developers.home-assistant.io/blog/2021/01/29/custom-integration-changes#versions for more
   details"
2. Unparsable version, same strategy list as hassfest: "The custom integration '%s' does not have a
   valid version key (%s) in the manifest file and was blocked from loading."
3. A host-maintained blocklist: "Version %s of custom integration '%s' %s and was blocked from
   loading, please %s"

The third gate is the interesting one. `BLOCKED_CUSTOM_INTEGRATIONS: dict[str, BlockedIntegration]`
maps an integration *domain* to a `lowest_good_version` and a `reason`, and `_version_blocked`
returns `True` for anything below it (or for everything, when `lowest_good_version is None`). The
entries are hand-written by Home Assistant maintainers with the release and the incident inline:

```python
# Added in 2024.3.0 because of https://github.com/home-assistant/core/issues/112464
"start_time": BlockedIntegration(AwesomeVersion("1.1.7"), "breaks Home Assistant"),
```

with siblings reading `"crashes Home Assistant"` and `"prevents recorder from working"`. Every
custom integration also draws an unconditional `CUSTOM_WARNING` on load.

So the number is moved by two parties, both after the fact: the integration author bumps `version`,
and Home Assistant core adds a floor to the blocklist once a specific version has already broken
something. The stated purpose matches: [Custom integration
changes](https://developers.home-assistant.io/blog/2021/01/29/custom-integration-changes) introduces
the key so users can report issues against a specific version and so Home Assistant can block
insecure versions, with "The `version` key is required from Home Assistant version 2021.6" and a
warning-then-error rollout through the hassfest action.

### VS Code, Ansible, Obsidian: the host release as a range

All three point the constraint at the host's release number, and all three put the field in the
plugin's own manifest.

**VS Code — `engines.vscode`.** Mandatory. The [extension manifest
reference](https://code.visualstudio.com/api/references/extension-manifest) describes it as "An
object containing at least the `vscode` key matching the versions of VS Code that the extension is
compatible with. Cannot be `*`. For example: `^0.10.5` indicates compatibility with a minimum VS
Code version of `0.10.5`." The syntax is not npm semver: `extensionValidator.ts` matches the value
against its own `VERSION_REGEXP = /^(\^|>=)?((\d+)|x)\.((\d+)|x)\.((\d+)|x)(\-.*)?$/`, so a single
`^` or `>=` prefix over three components with `x` wildcards is all that parses, and the `semver`
module is reserved for the extension's own `version`. [Publishing
extensions](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
distinguishes `"1.8.0"` — "your extension is compatible only with VS Code 1.8.0" — from `"^1.8.0"` —
"your extension is compatible with VS Code 1.8.0 and onwards, including 1.8.1, 1.9.0, etc." — and
notes Insiders date tags such as `^1.56.0-20210428`.

The check lives in
[`extensionValidator.ts`](https://github.com/microsoft/vscode/blob/main/src/vs/platform/extensions/common/extensionValidator.ts).
`isValidExtensionVersion` short-circuits first:

```typescript
if (extensionIsBuiltin || (typeof extensionManifest.main === 'undefined' && typeof extensionManifest.browser === 'undefined')) {
    // No version check for builtin or declarative extensions
    return true;
}
```

Only extensions that run code are gated. `isVersionValid` then *rejects imprecise ranges* under the
comment "enforce that a breaking API version is specified", with "Version specified in
`engines.vscode` ({0}) is not specific enough. For vscode versions after 1.0.0, please define at a
minimum the major desired version. E.g. ^1.10.0, 1.10.x, 1.x.x, 2.x.x, etc." An unparsable value
gives "Could not parse `engines.vscode` value {0}. Please use, for example: ^1.22.0, ^1.22.x, etc."
and the mismatch itself gives:

> Extension is not compatible with Code {0}. Extension requires: {1}.

The missing-field messages are separate: "property `{0}` is mandatory and must be of type `object`"
for `engines`, the same sentence with `string` for `engines.vscode`, and "Extension version is not
semver compatible." for the extension's own `version`. The same field also decides which published
version a client is offered — "your new extension version will only be available on VS Code
`>=1.9.0`" — so an older client is served an older compatible build rather than a failure. The
extension author moves it.

**Ansible — `requires_ansible`.** Declared in `meta/runtime.yml`. The [collection structure
guide](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections_structure.html)
gives the example `requires_ansible: ">=2.10,<2.11"`, names the syntax as a PEP 440 version
specifier, and records the deviation: "Ansible deviates from PEP440 behavior by truncating
prerelease segments from the Ansible version. This means that Ansible 2.11.0b1 is compatible with
something that `requires_ansible: ">=2.11"`."
[`lib/ansible/plugins/loader.py`](https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/loader.py)
implements exactly that:

```python
ss = SpecifierSet(requirement_string)

# ignore prerelease/postrelease/beta/dev flags for simplicity
base_ansible_version = Version(ansible_version).base_version

return ss.contains(base_ansible_version)
```

An empty string means "compatible"; a missing `packaging` module also means "compatible", with the
warning "packaging Python module unavailable; unable to validate collection Ansible version
requirements". On a genuine mismatch the behaviour is configurable:

```python
mismatch_behavior = C.config.get_config_value('COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH')
message = 'Collection {0} does not support Ansible version {1}'.format(collection_name, ansible_version)
if mismatch_behavior == 'warning':
    display.warning(message)
elif mismatch_behavior == 'error':
    raise AnsibleCollectionUnsupportedVersionError(message)
```

`COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH` has `default: warning`
([`lib/ansible/config/base.yml`](https://github.com/ansible/ansible/blob/devel/lib/ansible/config/base.yml)),
so out of the box a collection that declares itself incompatible still loads. A malformed specifier
degrades to another warning: "Error parsing collection metadata requires_ansible value from
collection {0}: {1}". Pre-release validation is thinner than runtime: the `runtime-metadata` sanity
test accepts `('requires_ansible'): str` with the standing comment "requires_ansible: In the future
we should validate this with SpecifierSet" ([sanity
test](https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/_util/controller/sanity/code-smell/runtime-metadata.py)).
The collection author moves it; the operator chooses whether it bites.

**Obsidian — `minAppVersion`.** A required string in `manifest.json`, "The minimum required Obsidian
version" ([manifest reference](https://docs.obsidian.md/Reference/Manifest)). It is a floor, not a
range; the manifest's own `version` must be "Semantic Versioning in the format `x.y.z`". Instead of
failing on a mismatch, Obsidian downgrades the plugin. From the [versions
reference](https://docs.obsidian.md/Reference/Versions): "`versions.json` contains a JSON object,
where the key is the plugin version, and the value is the corresponding `minAppVersion`. If a user
attempts to install a plugin where the Obsidian app version is lower than the `minAppVersion` in
Manifest, then Obsidian looks for a `versions.json` file at the root of the plugin repository." The
worked example has the user on Obsidian 1.1.0 and a manifest `minAppVersion` of 1.2.0, and concludes
"In this case, the most recent plugin version for 1.1.0 is 0.12.0." The plugin author maintains both
files: "You only need to update `versions.json` if you change the `minAppVersion` for your plugin."
The exact user-visible string when no fallback exists is **[unverified]** — Obsidian's application
code is not public and the developer documentation does not state it.

### Terraform: the only real protocol number

Terraform is the one host in this set with a contract version that is not a release version. The
[plugin protocol page](https://developer.hashicorp.com/terraform/plugin/terraform-plugin-protocol)
defines it as "a versioned interface between Terraform CLI and Terraform Plugins", implemented over
Protocol Buffers and gRPC. Protocol 6 works with Terraform CLI 1.0 and later and adds nested
attributes via a `NestedType` field, with per-attribute sensitivity; protocol 5 works with Terraform
CLI 0.12 and later and is what SDKv2 speaks. Protocol 6 "includes all version 5 functionality for
providers".

The number is per plugin *type*, not per RPC. Terraform's client-side map in
[`internal/plugin/plugin.go`](https://github.com/hashicorp/terraform/blob/main/internal/plugin/plugin.go)
shows protocol 6 never covered provisioners:

```go
var VersionedPlugins = map[int]plugin.PluginSet{
	5: {
		"provider":    &GRPCProviderPlugin{},
		"provisioner": &GRPCProvisionerPlugin{},
	},
	6: {
		"provider": &plugin6.GRPCProviderPlugin{},
	},
}
```

Negotiation runs in `hashicorp/go-plugin`. The client exports its whole supported set into the child
process environment as `PLUGIN_PROTOCOL_VERSIONS`, a comma-joined list. The server sorts both its
own versions and the client's in reverse "to ensure we match the newest compatible plugin version"
([`server.go`](https://github.com/hashicorp/go-plugin/blob/main/server.go)). The server announces
one chosen integer in its handshake line, and the client re-checks it for *exact equality* against
its own keys ([`client.go`](https://github.com/hashicorp/go-plugin/blob/main/client.go)):

```go
return 0, nil, fmt.Errorf("incompatible API version with plugin. "+
    "Plugin version: %d, Client versions: %d", serverVersion, clientVersions)
```

A separate, coarser gate runs first on the handshake's core protocol field:

```go
if coreProtocol != CoreProtocolVersion {
    err = fmt.Errorf("incompatible core API version with plugin. "+
        "Plugin version: %s, Core version: %d\n\n"+
        "To fix this, the plugin usually only needs to be recompiled.\n"+
        "Please report this to the plugin author", parts[0], CoreProtocolVersion)
    return
}
```

Terraform's `HandshakeConfig` still carries `DefaultProtocolVersion = 4`, documented as "the
protocol version assumed for legacy clients that don't specify a particular version during their
handshake … and must stay unchanged at 4 until we intentionally build plugins that are not
compatible with 0.10 and 0.11"
([`internal/plugin/serve.go`](https://github.com/hashicorp/terraform/blob/main/internal/plugin/serve.go)),
alongside a fixed magic cookie ("The magic cookie values should NEVER be changed"). After a
successful handshake the CLI branches on `client.NegotiatedVersion()` and panics with `"unsupported
protocol version"` on anything but 5 or 6
([`internal/command/meta_providers.go`](https://github.com/hashicorp/terraform/blob/main/internal/command/meta_providers.go)).
HashiCorp moves the number, on both sides at once; provider authors adopt it by switching SDK.

### pytest: no plugin API version, by design

pytest has no API version field, no protocol number, and no per-hook version. A grep of
`src/_pytest/` for `api_version`, `API_VERSION` and `apiversion` returns nothing ([source
tree](https://github.com/pytest-dev/pytest/tree/main/src/_pytest)). The entry-point group is the
fixed literal `pytest11` — "pytest looks up the `pytest11` entrypoint to discover its plugins"
([Writing plugins](https://docs.pytest.org/en/stable/how-to/writing_plugins.html)) — introduced by
the changelog line "introduce automatic plugin registration via 'pytest11'". The digits are
historical, not a contract generation: there is no `pytest12`. Its hook engine, pluggy, has no
notion either; a grep of `pluggy`'s `src/` and `docs/` for `specversion`, `api_version`, "API
version" and "hookspec version" returns nothing ([pluggy](https://github.com/pytest-dev/pluggy)).

What pytest has instead:

**A written compatibility policy.** [Backwards Compatibility
Policy](https://docs.pytest.org/en/stable/backwards-compatibility.html) splits changes into trivial,
transitional and true breakage. For transitional: "We will only start the removal of deprecated
functionality in major releases … and keep it around for at least two minor releases", using
`PytestRemovedInXWarning`, and "When the deprecation expires (e.g., 4.0 is released), we won't
remove the deprecated functionality immediately but will use the standard warning filters to turn
`PytestRemovedInXWarning` … into **errors** by default." True breakage "should only be considered
when a normal transition is unreasonably unsustainable", "should be limited to APIs where the number
of actual users is very small (for example, only impacting some plugins)", and must be announced in
an issue with a "Detailed description of the change", "Rationale" and "Expected impact on users and
plugin authors".

**Two user-set version gates, neither of them a plugin declaration.** `minversion` "Specifies a
minimal pytest version required for running tests"
([reference](https://docs.pytest.org/en/stable/reference/reference.html#confval-minversion)),
checked in `Config._checkversion` with `packaging.version.Version` and raising a `UsageError` whose
shipped format string ends in a stray apostrophe:

```python
f"{self.inipath}: 'minversion' requires pytest-{minver}, actual pytest-{pytest.__version__}'"
```

[`required_plugins`](https://docs.pytest.org/en/stable/reference/reference.html#confval-required_plugins)
takes PEP 508 requirement strings, resolves them against `list_plugin_distinfo()` and raises
`UsageError("Missing required plugins: {}")`
([`src/_pytest/config/__init__.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py)).
Both live in the *user's* ini file. A plugin cannot state its own requirement anywhere pytest reads.

**`PYTEST_DONT_REWRITE` is an opt-out from assertion rewriting, not from an API version.** "Disable
rewriting for a specific module by adding the string `PYTEST_DONT_REWRITE` to its docstring"
([assert how-to](https://docs.pytest.org/en/stable/how-to/assert.html)); the implementation is a
substring test against the module docstring, `return "PYTEST_DONT_REWRITE" in docstring`
([`src/_pytest/assertion/rewrite.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/assertion/rewrite.py)).
It protects modules that manipulate the import machinery; it says nothing about which pytest a
plugin targets. The changelog records it was extended to plugins: "`PYTEST_DONT_REWRITE` is now
checked for plugins too rather than only for test modules"
([changelog](https://docs.pytest.org/en/stable/changelog.html)).

**Plugins pin the pytest distribution instead.** Three first-party plugins, all with a lower bound
on the *release*, one with a ceiling — and pytest's own bound on pluggy alongside them:

| Plugin | Declared dependency |
|---|---|
| [`pytest-xdist`](https://github.com/pytest-dev/pytest-xdist/blob/master/pyproject.toml) | `pytest>=7.0.0` |
| [`pytest-cov`](https://github.com/pytest-dev/pytest-cov/blob/master/pyproject.toml) | `pytest>=7`, `pluggy>=1.2` |
| [`pytest-asyncio`](https://github.com/pytest-dev/pytest-asyncio/blob/main/pyproject.toml) | `pytest>=8.4,<10` |
| [`pytest` itself, on pluggy](https://github.com/pytest-dev/pytest/blob/main/pyproject.toml) | `pluggy>=1.5,<2` |

pytest bounds its own hook engine (`pluggy>=1.5,<2`) more tightly than three of its plugins bound
pytest. Resolution happens at install time, so a mismatch surfaces as a pip resolver failure, never
as a host-side diagnostic at plugin load.

### Python packaging: nothing, having looked

There is no convention. Three places were checked.

**Core metadata.** The
[specification](https://packaging.python.org/en/latest/specifications/core-metadata/) lists every
field: Metadata-Version, Name, Version, Dynamic, Platform, Supported-Platform, Summary, Description,
Description-Content-Type, Keywords, Author, Author-email, Maintainer, Maintainer-email, License,
License-Expression, License-File, Classifier, Requires-Dist, Requires-Python, Requires-External,
Project-URL, Provides-Extra, Import-Name, Import-Namespace, Provides-Dist, Obsoletes-Dist,
Home-page, Download-URL, Requires, Provides, Obsoletes. None of them names an API version.
`Requires-Python` constrains the interpreter and nothing else; a host *library* version can only be
expressed through `Requires-Dist`, which is the distribution version.

The closest thing is `Provides-Dist`, and it comes with a disclaimer. It sits under the heading
**"Rarely Used Fields"**, introduced as: "The fields in this section are currently rarely used, as
their design was inspired by comparable mechanisms in Linux package management systems, and it isn't
at all clear how tools should interpret them in the context of an open index server such as PyPI."
Its own text does describe the shape of a capability declaration: "A distribution may also provide a
'virtual' project name, which does not correspond to any separately-distributed project: such a name
might be used to indicate an abstract capability which could be supplied by one of multiple
projects. E.g., multiple projects might supply RDBMS bindings for use by a given ORM: each project
might declare that it provides `ORM-bindings`, allowing other projects to depend only on having at
most one of them installed." A version may ride along: "A version declaration may be supplied and
must follow the rules described in Version specifiers. The distribution's version number will be
implied if none is specified." So a virtual name plus a version is expressible — and unused,
uninterpreted, and by the spec's own admission unclear.

**Entry-point group names.** The [entry points
specification](https://packaging.python.org/en/latest/specifications/entry-points/) constrains the
syntax — "Group names must be one or more groups of letters, numbers and underscores, separated by
dots (regex `^\w+(\.\w+)*$`)" — and gives exactly one naming convention, about ownership, not
versions: "To avoid clashes, consumers defining a new group should use names starting with a PyPI
name owned by the consumer project, followed by `.`" No version convention is documented, and the
two Python hosts read here follow the flat pattern: pytest's group is `pytest11`, and pydantic's is
the bare string `PYDANTIC_ENTRY_POINT_GROUP: Final[str] = 'pydantic'`
([`pydantic/plugin/_loader.py`](https://github.com/pydantic/pydantic/blob/main/pydantic/plugin/_loader.py)).

**PEPs.** The one place the Python ecosystem does version an extension contract in packaging
metadata is the C ABI, not the plugin API. [PEP 425](https://peps.python.org/pep-0425/) states "The
ABI tag indicates which Python ABI is required by any included extension modules" and "The CPython
stable ABI is `abi3` as in the shared library suffix", giving wheel names like
`cp33-abi3-linux_x86_64`. The matching source-side declaration is `Py_LIMITED_API` from [PEP
384](https://peps.python.org/pep-0384/) — "During the compilation of applications, the preprocessor
macro Py_LIMITED_API must be defined. Doing so will hide all definitions that are not part of the
ABI." CPython documents the value as a version: "Define `Py_LIMITED_API` to the value of
`PY_VERSION_HEX` corresponding to the lowest Python version your extension supports", advising that
rather than using the macro directly you "hardcode a minimum minor version (e.g. `0x030A0000` for
Python 3.10) for stability when compiling with future Python versions", with the historical note
"You can also define `Py_LIMITED_API` to `3`. This works the same as `0x03020000` (Python 3.2, the
version that introduced Limited API)" ([C API
Stability](https://docs.python.org/3/c-api/stable.html#c.Py_LIMITED_API)). This is a real contract
version, declared by the plugin, checked by the compiler and encoded in the filename — and it exists
only for C extensions.

### The incident: pytest 8.1.0, yanked for breaking plugins

pytest 8.1.0 removed deprecated APIs whose warnings had not been firing, broke plugins that were
still using them, and was pulled from PyPI. The changelog entry is unambiguous ([pytest
changelog](https://docs.pytest.org/en/stable/changelog.html)):

> pytest 8.1.0 (YANKED)
>
> This release has been **yanked**: it broke some plugins without the proper warning period, due
> to some warnings not showing up as expected.

The 8.1.1 entry names what was reverted and why:

> Delayed the deprecation of the following features to `9.0.0`: … It was discovered after `8.1.0`
> was released that the warnings about the impeding removal were not being displayed, so the team
> decided to revert the removal.
>
> This is the reason for `8.1.0` being yanked.

The reporting issue, [pytest #12069](https://github.com/pytest-dev/pytest/issues/12069) — titled
"[YANKED] pytest 8.1.0 removes many deprecations, but not mentioned in changelog" — states the
failure in one sentence:

> https://github.com/pytest-dev/pytest/pull/11757 is not mentioned as a breaking change for the
> Pytest 8.1.0 Release in https://docs.pytest.org/en/stable/changelog.html ; it breaks plugins who
> were still supporting the older signature.

Two properties of this incident matter. First, the guard that failed was a *warning*, not a version
check: the policy's whole transitional mechanism depends on `PytestRemovedInXWarning` reaching
plugin authors, and when the warnings silently stopped firing there was no second line of defence.
Second, recovery required a distribution-level action — a PyPI yank plus a revert — because no
plugin declared which API generation it was written against, so the host had no way to keep serving
the old behaviour to old plugins.

Home Assistant's blocklist records the same class of failure from the other direction. Each entry is
a plugin that broke the host after a host upgrade, with the release that added the block and the
incident linked in a comment: `"start_time"` blocked at `lowest_good_version` 1.1.7 "because of
[home-assistant/core#112464](https://github.com/home-assistant/core/issues/112464)" with reason
"breaks Home Assistant" — that issue is titled "HassOS 2024.03.0b6 upgrade fails to start (
RuntimeError: Event loop is closed )". Siblings carry the reasons "crashes Home Assistant" and
"prevents recorder from working"
([`homeassistant/loader.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/loader.py)).
Without a contract number the host cannot express "plugins built for the old API stay on the old
path", so it hard-codes a per-plugin floor after each incident.

### Comparison across hosts

| Host | What carries the number | Granularity | Comparison rule | When checked | Failure looks like | Who moves it |
|---|---|---|---|---|---|---|
| Sphinx `needs_sphinx` | `conf.py` confval (project author's) | whole host release | lexicographic **string** `>` against `__display_version__` | app init, before extensions load | `VersionRequirementError`: "This project needs at least Sphinx v%s and therefore cannot be built with this version." | the documentation project author |
| Sphinx `require_sphinx()` | call inside the extension's `setup()` | whole host release, `(major, minor)` prefix only | tuple `>` against `sphinx.version_info[:2]` | during `load_extension` | `VersionRequirementError`, re-wrapped as "The %s extension used by this project needs at least Sphinx v%s; it therefore cannot be built with this version." | the extension author |
| Sphinx `needs_extensions` | `conf.py` confval, against `setup()`'s `'version'` | per extension release | `packaging.version.Version` `>`, string fallback, `'unknown version'` fails | `config-inited`, priority 800 | `VersionRequirementError`: "This project needs the extension %s at least in version %s and therefore cannot be built with the loaded version (%s)." | project author sets it; extension author supplies `'version'` |
| Sphinx `env_version` | `setup()` metadata int, plus core `ENV_VERSION = 66` | per extension's stored data | dict equality of the whole `{ext: int}` mapping | unpickling the cached environment | silent rebuild: info log "failed: build environment version not current", fresh env | Sphinx core for `ENV_VERSION`; extension author for its own |
| Home Assistant | `manifest.json` `version` (custom only) + core `BLOCKED_CUSTOM_INTEGRATIONS` | per integration release | `AwesomeVersion` `>=` against a hand-written `lowest_good_version` | hassfest pre-release; loader at import | integration refused (`return None`) with "was blocked from loading" | integration author bumps `version`; HA core adds the floor after an incident |
| VS Code | `package.json` `engines.vscode` (mandatory) | whole host release | its own regexp — `^`/`>=` prefix over `major.minor.patch` with `x` wildcards, not npm semver; major must be pinned | extension scan, before activation; the same field also filters which published version a client is offered | "Extension is not compatible with Code {0}. Extension requires: {1}." — skipped for built-in and declarative extensions | the extension author |
| Ansible | `meta/runtime.yml` `requires_ansible` | whole host release | PEP 440 `SpecifierSet.contains`, prereleases truncated | collection load | **warning by default** ("Collection {0} does not support Ansible version {1}"); `AnsibleCollectionUnsupportedVersionError` only if the operator sets `error` | the collection author; the operator picks the severity |
| Obsidian | `manifest.json` `minAppVersion` + repo `versions.json` | whole host release | minimum floor; `versions.json` maps plugin version to its floor | install and update | no failure — an older compatible plugin version is installed instead | the plugin author, in both files |
| Terraform | protocol integer, independent of both release versions | per plugin type (`provider`, `provisioner`) | highest mutually supported wins, then **exact integer equality** | process handshake | "incompatible API version with plugin. Plugin version: %d, Client versions: %d"; core-level: "incompatible core API version with plugin … the plugin usually only needs to be recompiled" | HashiCorp, on both sides simultaneously |
| pytest | nothing | — | — | — | plugin breaks at runtime; recovery is a PyPI yank | nobody |
| Python packaging | nothing (`Provides-Dist` under "Rarely Used Fields" is the nearest shape) | — | — | install-time resolution of `Requires-Dist` only | pip resolver conflict | nobody |

### mypy: the host hands the plugin its version, then hashes the plugin behind its back

mypy is an in-process, pip-installed Python host, and it has a load-time gate. The gate is not a
version comparison. It is a six-step refusal ladder over the *shape* of the entry point, plus a
content hash of the plugin module used only to throw away the host's own cache.

**Discovery is the config file, not entry points.** The `plugins` confval is documented as ":type:
comma-separated list of strings — A comma-separated list of mypy plugins"
([`docs/source/config_file.rst`](https://github.com/python/mypy/blob/master/docs/source/config_file.rst)),
and `load_plugins_from_config` returns `[], {}` immediately when `not options.config_file`
([`mypy/build.py`](https://github.com/python/mypy/blob/master/mypy/build.py)). A plugin that is
merely installed is never found. Two spellings are accepted, "relative or absolute path to the
plugin file, or a module name (if the plugin is installed using `pip install` in the same virtual
environment where mypy is running)", and the entry-point function name is overridable after a colon:
`plugins = custom_plugin:custom_entry_point`
([`docs/source/extending_mypy.rst`](https://github.com/python/mypy/blob/master/docs/source/extending_mypy.rst)).

**The contract is a module docstring, in six bullets.** From
[`mypy/plugin.py`](https://github.com/python/mypy/blob/master/mypy/plugin.py), verbatim on the two
that bind the entry point:

> * Every module should get an entry point function (called 'plugin' by default, but may be
>   overridden in the config file) that should accept a single string argument that is a full mypy
>   version (includes git commit hash for dev versions) and return a subclass of
>   mypy.plugins.Plugin.
>
> * All plugin class constructors should match the signature of mypy.plugin.Plugin (i.e. should
>   accept an mypy.options.Options object), and *must* call super().__init__().

The other four bullets fix discovery, the `get_xxx` dispatch on a fully qualified name, first-non-
`None`-wins ordering ("The plugins are called in the order they are passed in the config option"),
and the API a plugin may use to decide (`mypy.plugin.CommonPluginApi`).

**The call, and what is in the string.** One line does it
([`mypy/build.py`](https://github.com/python/mypy/blob/master/mypy/build.py)):

```python
plugin_type = getattr(module, func_name)(__version__)
```

`__version__` is mypy's own release string, and the docstring's "includes git commit hash for dev
versions" is literal.
[`mypy/version.py`](https://github.com/python/mypy/blob/master/mypy/version.py) documents the three
shapes in a comment — "Release versions have the form "1.2.3"", "Dev versions have the form
"1.2.3+dev" (PLUS sign to conform to PEP 440)", "Before 1.0 we had the form "0.NNN"" — and then
appends the revision:

```python
__version__ = "2.4.0+dev"
base_version = __version__

mypy_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if __version__.endswith("+dev") and git.is_git_repo(mypy_dir):
    revision = git.git_revision_no_subprocess(mypy_dir)
```

So the plugin is handed a string it cannot compare with `packaging` without stripping a suffix. The
host performs no comparison of its own and defines no minimum: the argument is data, and the
documented licence to ignore it is in the example itself
([`docs/source/extending_mypy.rst`](https://github.com/python/mypy/blob/master/docs/source/extending_mypy.rst)):

```python
def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return CustomPlugin
```

**The refusal ladder: six messages, every one a `CompileError`.** `plugin_error` is typed `NoReturn`
and does `errors.report(line, 0, message)` then `errors.raise_error(use_stdout=False)`, which raises
`CompileError` ([`mypy/errors.py`](https://github.com/python/mypy/blob/master/mypy/errors.py)). The
first failure ends the run; nothing is skipped or downgraded.

| Order | Condition | Exact message |
|---|---|---|
| 1 | `.py` path not on disk | `Can't find plugin "{plugin_path}"` |
| 2 | a path without a `.py` suffix | `Plugin "{fnam}" does not have a .py extension` |
| 3 | import raised | `Error importing plugin "{plugin_path}": {exc}` |
| 4 | `not hasattr(module, func_name)` | `Plugin "{}" does not define entry point function "{}"` |
| 5 | `not isinstance(plugin_type, type)` | `Type object expected as the return value of "plugin"; got {!r} (in {})` |
| 6 | `not issubclass(plugin_type, Plugin)` | `Return value of "plugin" must be a subclass of "mypy.plugin.Plugin" (in {})` |

The last two are the answer to "what happens when the return value is not a `Plugin` subclass", and
both are pinned by test data. `test-data/unit/plugins/badreturn.py` is the whole of

```python
def plugin(version: str) -> None:
    pass
```

and `badreturn2.py` returns a bare `class MyPlugin` that does not inherit `Plugin`. The asserted
output is
([`test-data/unit/check-custom-plugin.test`](https://github.com/python/mypy/blob/master/test-data/unit/check-custom-plugin.test)):

```
tmp/mypy.ini:3: error: Type object expected as the return value of "plugin"; got None (in <ROOT>/test-data/unit/plugins/badreturn.py)
tmp/mypy.ini:2: error: Return value of "plugin" must be a subclass of "mypy.plugin.Plugin" (in <ROOT>/test-data/unit/plugins/badreturn2.py)
```

Note the ordering: mypy checks `isinstance(plugin_type, type)` *before* `issubclass`, so returning
an *instance* of a correct `Plugin` subclass fails with message 5 ("Type object expected"), not
message 6. The contract is a class, not an object.

**The error is attributed to the config file, at the line the `plugins` key sits on.**
`errors.set_file(options.config_file, None, options)` precedes the loop, and the line comes from
`find_config_file_line_number(options.config_file, "mypy", "plugins")`, with the fallback commented
`line = 1  # We need to pick some line number that doesn't look too confusing`. The test
`testMultipleSectionsDefinePlugin` puts `plugins=` in three sections and asserts the `[mypy]` one:
`tmp/mypy.ini:4: error: Can't find plugin "tmp/missing.py"`. Reading the helper, the section name is
matched as the literal `mypy` between brackets and the setting as `^plugins\s*=`, so a
`pyproject.toml` whose section is `[tool.mypy]` never matches and every plugin error there is
reported at line 1. No test asserts that case.

**Two failures deliberately bypass the ladder and show the user a traceback.** If the entry point
itself raises, or if the constructor raises, mypy prints a line to `stdout` and re-raises with the
comment `# Propagate to display traceback`:

```python
print(f"Error calling the plugin(version) entry point of {plugin_path}\n", file=stdout)
print(f"Error constructing plugin instance of {plugin_type.__name__}\n", file=stdout)
```

So a plugin that *does* decide to refuse a mypy version — the one thing the handed string is
for — surfaces as an unhandled Python traceback, not as a mypy diagnostic.

**`take_module_snapshot`: what is recorded.** The function is nine lines and its docstring states
the motive ([`mypy/build.py`](https://github.com/python/mypy/blob/master/mypy/build.py)):

> Take plugin module snapshot by recording its version and hash.
>
> We record _both_ hash and the version to detect more possible changes (e.g. if there is a change
> in modules imported by a plugin).

```python
if hasattr(module, "__file__"):
    assert module.__file__ is not None
    with open(module.__file__, "rb") as f:
        digest = hash_digest(f.read())
else:
    digest = "unknown"
ver = getattr(module, "__version__", "none")
return f"{ver}:{digest}"
```

`hash_digest` is `hashlib.sha1(data).hexdigest()`, chosen "because we want a low probability of
accidental collision, but we don't really care about any of the cryptographic properties"
([`mypy/util.py`](https://github.com/python/mypy/blob/master/mypy/util.py)). The absent-version
fallback is the literal string `"none"`, and the absent-file fallback the literal `"unknown"`. Only
the entry-point module's own file is hashed — nothing it imports — which is precisely why the
optional `__version__` exists.

**What it invalidates.** The snapshot is a `dict[str, str]` keyed by module name, written to
`PLUGIN_SNAPSHOT_FILE: Final = "@plugins_snapshot.json"` after a successful graph pass, and read
back into `manager.old_plugins_snapshot` at `BuildManager` construction. `validate_meta` compares
the whole mapping:

```python
if manager.old_plugins_snapshot and manager.plugins_snapshot:
    # Check if plugins are still the same.
    if manager.plugins_snapshot != manager.old_plugins_snapshot:
        manager.log(f"Metadata abandoned for {id}: plugins differ")
        return None
```

Four properties follow from that code. It is dict inequality, so one plugin changing invalidates
*every* module's cache — the same all-or-nothing shape as Sphinx's `_get_env_version` mapping above.
There is no per-plugin or per-module granularity. The guard is truthiness of both dicts, so going
from some plugins to none, or from none to some, skips the check entirely. And unlike the host's own
version, which is checked two blocks earlier as `if m.version_id != manager.version_id and not
manager.options.skip_version_check`, the plugin snapshot has **no escape flag**:
`--skip-version-check` is documented as "By default, mypy will ignore cache data generated by a
different version of mypy. This flag disables that behavior"
([`docs/source/command_line.rst`](https://github.com/python/mypy/blob/master/docs/source/command_line.rst))
and does not reach the plugin comparison. Failing to write the snapshot is a blocker error, `"Error
writing plugins snapshot"`, unless the cache directory is `os.devnull`.

**In the daemon the same hash forces a full restart.** `cmd_run` re-loads the plugins on every run
and returns one of three restart reasons, in this order
([`mypy/dmypy_server.py`](https://github.com/python/mypy/blob/master/mypy/dmypy_server.py)):
`{"restart": "configuration changed"}`, `{"restart": "mypy version changed"}`, then

```python
if current_plugins_snapshot != start_plugins_snapshot:
    return {"restart": "plugins changed"}
```

The client prints `f"Restarting: {response['restart']}"`
([`mypy/dmypy/client.py`](https://github.com/python/mypy/blob/master/mypy/dmypy/client.py)). The
end-to-end test `testDaemonRunRestartPluginVersion` appends a single space to `plug.py` and asserts
the transcript
([`test-data/unit/daemon.test`](https://github.com/python/mypy/blob/master/test-data/unit/daemon.test)):

```
$ {python} -c "print(' ')" >> plug.py
$ dmypy run -- foo.py --no-error-summary
Restarting: plugins changed
Daemon stopped
Daemon started
```

**And the whole surface is disclaimed.** The docs put the warning above the mechanism
([`docs/source/extending_mypy.rst`](https://github.com/python/mypy/blob/master/docs/source/extending_mypy.rst)):

> The plugin system is experimental and prone to change. If you want to write a mypy plugin, we
> recommend you start by contacting the mypy core developers on gitter. In particular, there are no
> guarantees about backwards compatibility.
>
> Backwards incompatible changes may be made without a deprecation period, but we will announce them
> in the plugin API changes announcement issue.

The announcement channel is a single GitHub issue, `python/mypy#6617`. Its contents are
**[unverified]** — `api.github.com` and `github.com` both failed from this environment ("net/http:
TLS handshake timeout" from `gh api`, and "Unable to verify if domain github.com is safe to fetch"
from the fetch tool) — but the docs' own description of it, "the plugin API changes announcement
issue", is primary. There is no deprecation-period promise, no `PytestRemovedInXWarning` analogue,
and no timeline. mypy is the one host in this section whose written policy is the *absence* of a
policy.

The only compatibility mechanism actually offered to a plugin author, beyond the handed string, is
`Plugin.report_config_data`, whose docstring reads: "The data must be encodable as JSON and will be
stored in the cache metadata for the module. A mismatch between the cached values and the returned
will result in that module's cache being invalidated and the module being rechecked […] This can be
used to incorporate external configuration information that might require changes to typechecking"
([`mypy/plugin.py`](https://github.com/python/mypy/blob/master/mypy/plugin.py)). That is per-module
invalidation the plugin drives, checked in `validate_meta` right after the snapshot with the log
line `Metadata abandoned for {id}: plugin configuration differs`.

### The worked example: pydantic's mypy plugin declares a cache generation, not a compatibility range

pydantic is the reference third-party consumer of that contract, and what it does with each half is
the finding.

**It ignores the argument it is handed.** The entry point takes `version` and never reads it
([`pydantic/mypy.py`](https://github.com/pydantic/pydantic/blob/main/pydantic/mypy.py)):

```python
def plugin(version: str) -> type[Plugin]:
    """`version` is the mypy version string.

    We might want to use this to print a warning if the mypy version being used is
    newer, or especially older, than we expect (or need).
```

"We might want to" is still the state of it in the tree read (pydantic `VERSION = '2.14.0b1'`,
[`pydantic/version.py`](https://github.com/pydantic/pydantic/blob/main/pydantic/version.py)). The
module instead *imports* the number — `from mypy.version import __version__ as mypy_version` —
and normalises it itself, because the handed string is not comparable as-is:
`parse_mypy_version` "parses normal version like `1.11.0` and extra info followed by a `+` sign like
`1.11.0+dev.d6d9d8cd4f27c52edac1f537e236ec48a01e54cb.dirty`", returning "A triple of ints".

**In the current plugin the parsed number is dead.** `MYPY_VERSION_TUPLE = parse_mypy_version(
mypy_version)` is assigned at module scope in `pydantic/mypy.py` and referenced nowhere else in it.
The legacy `pydantic/v1/mypy.py` is where the mechanism was live, at five sites:

| Site | Guard | What it switches |
|---|---|---|
| `BUILTINS_NAME` | `>= (0, 930)` | `'builtins'` versus `'__builtins__'` |
| `get_class_decorator_hook` | `< (1, 1)` | supplies a dataclass callback; comment "Mypy version 1.1.1 added support for `@dataclass_transform` decorator" |
| default-factory handling | `> (0, 910)` | `Overloaded.items[0]` versus the older function form |
| `construct` self-typevar | `>= (1, 4)` | builds a `TypeVarType` at all |
| the same, inner | `>= (1, 11)` | `TypeVarId(-1, namespace=…)` versus `TypeVarId(-1)` |

([`pydantic/v1/mypy.py`](https://github.com/pydantic/pydantic/blob/main/pydantic/v1/mypy.py)). So
the handed-version mechanism is used for behavioural branching in practice — but by importing the
number, not by reading the argument, and the v2 rewrite dropped every branch.

**What pydantic does declare is the cache generation.** Two lines above the entry point, in both the
current and the legacy plugin, identical:

```python
# Increment version if plugin changes and mypy caches should be invalidated
__version__ = 2
```

This is the author declaration `take_module_snapshot` reads, so pydantic's snapshot entry is
`"2:<sha1 of pydantic/mypy.py>"`. The integer is not pydantic's release version — it is `2` while
the distribution is at `2.14.0b1` — and it is not a compatibility range. It is an opaque monotonic
counter over "the shape of the data I put in the host's cache", which is exactly the job of Sphinx's
`env_version`. pydantic also implements the per-module half: `report_config_data` returns
`self._plugin_data`, built as `{key: getattr(self, key) for key in self.__slots__}` over the
`pydantic-mypy` config section, under the docstring "Used by mypy to determine if cache needs to be
discarded."

This corrects the note's framing. mypy does not do the `env_version` job "without any author
declaration": it does it *twice*, once without one (the SHA-1 of the file, which no author touches)
and once with one (an optional module `__version__`, which pydantic supplies and whose stated
purpose is cache invalidation). The file hash is the floor; the declared integer covers the changes
the hash cannot see.

### The load-time gate that is structural rather than numeric: pluggy

The other in-process Python host with a real gate at registration is pluggy, and it checks argument
names against the hookspec rather than any number. `_verify_hook` runs inside `register()`
([`src/pluggy/_manager.py`](https://github.com/pytest-dev/pluggy/blob/main/src/pluggy/_manager.py)):

```python
notinspec = set(hookimpl.argnames) - set(hook.spec.argnames)
if notinspec:
    raise PluginValidationError(
        hookimpl.plugin,
        f"Plugin {hookimpl.plugin_name!r} for hook {hook.name!r}\n"
        f"hookimpl definition: {_formatdef(hookimpl.function)}\n"
        f"Argument(s) {notinspec} are declared in the hookimpl but "
        "can not be found in the hookspec",
    )
```

Three sibling refusals in the same method raise the same exception: `historic incompatible with
yield/wrapper/hookwrapper`, `Declared as wrapper=True or hookwrapper=True but function is not a
generator function`, and `The wrapper=True and hookwrapper=True options are mutually exclusive`. The
last two repeat the argument check's two-line preamble naming the plugin, the hook and
`_formatdef(hookimpl.function)`; the historic one names only the plugin and the hook. The argument
check is the failure a host upgrade actually produces when it renames or drops a hook parameter —
the skew is detected by name, per hook, with the offending signature printed, and it needs no
declaration from either side.

A hookimpl for a hook the host does not specify at all is *not* refused at registration. It is
deferred to `check_pending`, whose docstring is "Verify that all hooks which have not been verified
against a hook specification are optional, otherwise raise `PluginValidationError`", with the
message `unknown hook {name!r} in plugin {hookimpl.plugin!r}`. The plugin's opt-out is per
implementation: "Normally each *hookimpl* should be validated against a corresponding hook
specification. If you want to make an exception then the *hookimpl* should be marked with the
`"optionalhook"` option"
([`docs/index.rst`](https://github.com/pytest-dev/pluggy/blob/main/docs/index.rst)) — which is how a
plugin supports two host generations without a version number. pytest calls `check_pending()` once,
in `Session.perform_collect`, *after* collection has run
([`src/_pytest/main.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/main.py)), not
at plugin load.

pluggy's transitional channel is also per-argument and carries no version. `warn_on_impl` and
`warn_on_impl_args` are declared on the *hookspec* and fired by the host at registration: "As
projects evolve new hooks may be introduced and/or deprecated. If a hookspec specifies a
`warn_on_impl`, pluggy will trigger it for any plugin implementing the hook", and
`warn_on_impl_args` is "a dict mapping parameter names to warnings. The warnings will trigger
whenever any plugin implements the hook requesting one of the specified parameters", added in pluggy
1.5 ([`docs/index.rst`](https://github.com/pytest-dev/pluggy/blob/main/docs/index.rst)). A grep of
pytest's tree for `warn_on_impl` returns nothing — pytest specifies no deprecated hook or argument
through the mechanism its own engine provides.

### The Protocol-shaped hosts: no version member anywhere

Three hosts not tested above carry no contract number at all, and in two of them the
plugin contract is a `Protocol`.

**Litestar.** `litestar/plugins/base.py` defines `InitPluginProtocol`, `InitPlugin`,
`ReceiveRoutePlugin`, `CLIPlugin`, `SerializationPlugin`, `DIPlugin`, `OpenAPISchemaPlugin`, the
`PluginProtocol` union of six of them, and `PluginRegistry`. Not one declares a version attribute, a
`supported_versions`, or a minimum. `InitPluginProtocol` has `__slots__ = ()` and exactly one
member, `on_app_init(self, app_config: AppConfig) -> AppConfig`; the only versioned thing on it is a
directive about the protocol's own name, `.. deprecated:: 2.15 Use 'InitPlugin' instead`
([`litestar/plugins/base.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py)).
A grep for `version` across `litestar/plugins/` finds two kinds of hit and neither is a host gate:
the substring inside the local name `conversion_fn` in `problem_details.py`, and Litestar's own
bundled pydantic plugin sniffing the *wrapped library* — `if
int(pydantic.version.version_short().split(".")[1]) >= 10:` in
[`litestar/plugins/pydantic/plugins/schema.py`](https://github.com/litestar-org/litestar/blob/main/litestar/plugins/pydantic/plugins/schema.py).
The whole documented contract for the constructor parameter is one line: `plugins: Sequence of
plugins.` ([`litestar/app.py`](https://github.com/litestar-org/litestar/blob/main/litestar/app.py),
tree at `version = "3.0.0b0"`). Litestar's only load-time gate is `isinstance` against the six
`@runtime_checkable` protocols in `PluginRegistry.__init__`; an object satisfying none of them is
accepted into `_plugins` in silence and simply never called.

**pydantic.** `PydanticPluginProtocol` is a bare `Protocol` with one method,
`new_schema_validator(...)`, and `__all__` lists eight names — the protocol, four handler protocols,
`NewSchemaReturns`, `SchemaTypePath`, `SchemaKind`. No version member
([`pydantic/plugin/__init__.py`](https://github.com/pydantic/pydantic/blob/main/pydantic/plugin/__init__.py)).
The protocol is not decorated `@runtime_checkable`, so the host cannot even test conformance by
`isinstance`, and the loader does not try: `get_plugins` iterates
`importlib_metadata.distributions()` for the group `PYDANTIC_ENTRY_POINT_GROUP: Final[str] =
'pydantic'`, calls `entry_point.load()`, and stores whatever comes back. The single guard is a
warning on two exception types
([`pydantic/plugin/_loader.py`](https://github.com/pydantic/pydantic/blob/main/pydantic/plugin/_loader.py)):

```python
except (ImportError, AttributeError) as e:
    warnings.warn(
        f'{e.__class__.__name__} while loading the `{entry_point.name}` Pydantic plugin, '
        f'this plugin will not be installed.\n\n{e!r}',
        stacklevel=2,
    )
```

Anything else propagates. pydantic — the host whose own mypy plugin declares a cache-generation
integer to *another* host — asks its own plugins for no number, no type check and no conformance
proof.

**Django.** The app registry has no version field on either side. A grep of `django/apps/*.py` for
`version` returns nothing at all, and `docs/ref/applications.txt` documents exactly eight
`AppConfig` attributes — `name`, `label`, `verbose_name`, `path`, `default`, `default_auto_field`,
`module`, `models_module` — plus `get_models`, `get_model` and `ready`
([`docs/ref/applications.txt`](https://github.com/django/django/blob/main/docs/ref/applications.txt),
tree at `VERSION = VersionTuple(6, 2, 0, "alpha", 0)`). What Django offers instead is the promise,
and it is the strongest in this set
([`docs/misc/api-stability.txt`](https://github.com/django/django/blob/main/docs/misc/api-stability.txt)):

> Django is committed to API stability and forwards-compatibility. In a nutshell, this means that
> code you develop against a version of Django will continue to work with future releases.

with "stable" defined as four bullets, of which two bind: "All the public APIs (everything in this
documentation) will not be moved or renamed without providing backwards-compatible aliases", and
"If, for some reason, an API declared stable must be removed or replaced, it will be declared
deprecated but will remain in the API for at least two feature releases. Warnings will be issued
when the deprecated method is called." Scope is drawn by documentation membership — "In general,
everything covered in the documentation -- with the exception of anything in the internals area is
considered stable" — with three exceptions named: security fixes ("security trumps the compatibility
guarantee"), anything the docs call internal, and "Functions, methods, and other objects prefixed by
a leading underscore (`_`). This is the standard Python way of indicating that something is
private".

Django and mypy are the two ends of the axis. Neither has a number; Django promises that code
written against one release keeps working, and mypy promises the opposite in as many words.

### The four in-process Python hosts, compared

| Host | Load-time gate | What the plugin declares | Comparison | Failure | Compatibility promise |
|---|---|---|---|---|---|
| mypy | six shape checks on the entry point, then a SHA-1 of the module file | nothing required; an optional module `__version__` for cache invalidation only | none on any version; dict inequality of `{module: "ver:sha1"}` for the cache | `CompileError` at the config-file line; a raising entry point becomes a traceback | "there are no guarantees about backwards compatibility […] Backwards incompatible changes may be made without a deprecation period" |
| pluggy / pytest | `_verify_hook` at `register()`; `check_pending()` later | hook argument names; `optionalhook=True` to opt out; `specname` to rename | set difference of argument names against the hookspec | `PluginValidationError`, e.g. `Argument(s) {notinspec} are declared in the hookimpl but can not be found in the hookspec` | pytest's written policy, "at least two minor releases" |
| Litestar | `isinstance` against six `@runtime_checkable` protocols | which protocols it satisfies, structurally | none | no failure — a plugin matching nothing is stored and never called | `.. deprecated:: 2.15` markers on the protocols themselves |
| pydantic | none | nothing; `PydanticPluginProtocol` is not `@runtime_checkable` | none | `warnings.warn` on `ImportError`/`AttributeError` only; anything else propagates | none stated in the plugin module |
| Django (apps) | app label validity and uniqueness only | nothing; eight documented `AppConfig` attributes, none a version | none | — | "code you develop against a version of Django will continue to work with future releases"; deprecation kept "at least two feature releases" |

### What the in-process Python hosts change

The conclusion that "only Terraform versions the interface independently" holds for *versioning*,
but the survey of mechanism shapes above was incomplete: mypy is a fourth shape, and it inverts the
direction every manifest host uses. Instead of the plugin declaring a range and the host testing it,
the host hands over its full version string — git hash included — and delegates the whole decision,
while gating the plugin only on shape (a class, a `Plugin` subclass, a constructor taking `Options`)
and hashing the plugin module to protect its own cache. That splits the two jobs the comparison
above treats as one: the compatibility decision moves entirely to the plugin author and is
unenforced, and the cache-generation number stays with the host, computed from a file hash with an
optional author declaration on top — which is where pydantic's `__version__ = 2` sits. The corollary
is that "the number usually lives in the plugin's manifest and points at the host's release" does
not generalise to in-process Python hosts: of the five read here, four ask for no number at all, and
the one that does reads it for cache invalidation rather than compatibility. The load-time gate that
actually catches host-plugin skew in this ecosystem is structural — pluggy's per-argument set
difference against the hookspec, and Litestar's `isinstance` — and where no structural gate exists
(pydantic, Django's registry) the host relies wholly on a written promise, which Django states as
strongly as mypy disclaims it.

### What §1 establishes

- **A separate contract number is rare.** Of the six hosts with any gate, only Terraform versions
  the interface independently of both the host release and the plugin release. Sphinx, Home
  Assistant, VS Code, Ansible and Obsidian all reuse a release number; pytest and Python packaging
  have nothing, and of the five in-process Python
  hosts read below, four ask for no number at all.

- **Where a number exists at all, it usually lives in the plugin's manifest and points at the
  host's release** — a shape that does not generalise to in-process Python hosts.
  `engines.vscode`, `requires_ansible`, `minAppVersion` and `require_sphinx()` are all the same
  shape: the plugin declares which host releases it accepts. That makes the plugin author
  responsible for predicting the host's future, which is why Ansible defaults to a warning and
  Obsidian silently downgrades rather than refuse.

- **The one host with a real protocol number runs its plugins out of process.** Terraform's
  handshake picks the highest mutually supported integer and then demands equality; go-plugin's
  error even tells the user the fix ("the plugin usually only needs to be recompiled"). None of the
  other hosts read here — Sphinx, Home Assistant, VS Code, Obsidian, Ansible, pytest — negotiates
  anything at load time; each one tests a declaration and then proceeds or refuses. VS Code is not
  an in-process host either — extensions run in a Node.js or web-worker [extension
  host](https://code.visualstudio.com/api/advanced-topics/extension-host) — and it still negotiates
  nothing.

- **A version gate is not the same as a compatibility policy, and the policy is what actually
  carries the weight.** Sphinx ("2 MAJOR releases at least") and pytest ("at least two minor
  releases", `PytestRemovedInXWarning` turned into errors) both stake plugin compatibility on
  warnings plus a written timeline rather than on a number.

- **Staking it on warnings alone has a documented failure mode.** pytest 8.1.0 was yanked because
  "it broke some plugins without the proper warning period, due to some warnings not showing up as
  expected". With no contract number, the only recovery available was a release-level one.

- **Python packaging offers no field to borrow.** No core metadata field, no entry-point group
  convention, and no PEP covers "the plugin API version I offer" or "the plugin API version I need"
  for pure Python. `Provides-Dist` has the right shape and lives under "Rarely Used Fields" with the
  spec conceding "it isn't at all clear how tools should interpret them". The only versioned
  extension contract in Python packaging metadata is the C ABI tag `abi3` paired with
  `Py_LIMITED_API`.

- **A host that omits the gate ends up maintaining a per-plugin blocklist.** Home Assistant
  version-gates nothing about its own API and instead ships `BLOCKED_CUSTOM_INTEGRATIONS`, a
  hand-written map from integration domain to a floor version, each entry added after a specific
  plugin broke a specific release.

- **Granularity is always coarse.** No host in this set versions individual hooks. Terraform is
  per-plugin-type, Sphinx's `env_version` is per-extension-stored-data, and everything else is a
  single number for the whole surface.

- **When the comparison rule is written by hand, it goes wrong quietly.** Sphinx's `needs_sphinx`
  compares version strings lexicographically, so `'10.0' > '8.3.0'` is `False` and the gate does not
  fire; `require_sphinx()` truncates to `(major, minor)`, so a patch-level requirement cannot be
  expressed. Hosts that delegate to `packaging` (`needs_extensions`, `requires_ansible`,
  `required_plugins`, `minversion`) or to `AwesomeVersion` (Home Assistant) do not have this class
  of bug.

## 2 Lifecycle-failure semantics: what a host does when a plugin fails to start or stop

Two questions separate the hosts in this field. Does a start that fails halfway undo the part
that succeeded? And when the stopping half itself fails, what reaches the caller? The CPython
primitives that most async hosts build on answer the first question generously and the second
one badly, and almost every framework inherits both answers without restating them.

### 1. Home Assistant: a closed taxonomy, and a backoff schedule written as numbers

Home Assistant is the only host surveyed here whose start-up failures are a named, finite set with a
defined host reaction per name. The root of the set is `IntegrationError`, whose docstring reads
"Base class for platform and config entry exceptions"
([`homeassistant/exceptions.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/exceptions.py#L231-L255)).
It has four direct members in that file, each a one-line docstring:

- `PlatformNotReady` — "Error to indicate that platform is not ready."
- `ConfigEntryError` — "Error to indicate that config entry setup has failed."
- `ConfigEntryNotReady` — "Error to indicate that config entry is not ready."
- `ConfigEntryAuthFailed` — "Error to indicate that config entry could not authenticate."

The taxonomy is deliberately reusable by subclassing: the OAuth 2.0 errors inherit from a member in
order to acquire its host behaviour rather than to add a new one. `OAuth2TokenRequestError`
"Inherits ConfigEntryNotReady so setup retries without the integration having to map it. Catch it
explicitly to handle it differently", and `OAuth2TokenRequestReauthError` "Inherits
ConfigEntryAuthFailed so setup starts reauth without the integration having to map it"
([`homeassistant/exceptions.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/exceptions.py#L256-L378)).
Inheriting the behaviour instead of mapping it is what keeps the set closed: a new error joins the
taxonomy by picking a parent.

Dispatch happens in one `try` in `ConfigEntry.async_setup`, and the order of the `except` clauses is
what makes the multiple-inheritance trick work — `ConfigEntryAuthFailed` is tested before
`ConfigEntryNotReady`, so `OAuth2TokenRequestReauthError`, which inherits both, starts a reauth flow
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L800-L915)).

| Raised from `async_setup_entry` | Entry state after | Reason recorded | Retry | Side effect |
|---|---|---|---|---|
| `ConfigEntryError` | `SETUP_ERROR` | `str(exc) or "Unknown fatal config entry error"` | no | `logger.exception` |
| `ConfigEntryAuthFailed` | `SETUP_ERROR` | `str(exc) or "could not authenticate"` | no | `async_start_reauth_if_available` |
| `ConfigEntryNotReady` | `SETUP_RETRY` | `str(exc) or None` | yes, scheduled | `logger.info` once per attempt |
| `asyncio.CancelledError` with `task.cancelling() > 0` | `SETUP_ERROR` | `None` | no | re-raised |
| anything else (`except SystemExit, Exception`) | `SETUP_ERROR` | `None` | no | `logger.exception` |
| returned `False` | `SETUP_ERROR` | `None` | no | `_async_process_on_unload` runs |
| returned a non-`bool` | `SETUP_ERROR` | `None` | no | logs "did not return boolean" |

The `except SystemExit, Exception:` clause is unparenthesised because Home Assistant now requires
`>=3.14.2`
([`pyproject.toml`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/pyproject.toml#L24)),
and [PEP 758](https://peps.python.org/pep-0758/) — "Allow `except` and `except*` expressions without
parentheses", `Python-Version: 3.14`, `Status: Final` — made that syntax legal.

**Returning `False` is not the same as raising.** Raising `ConfigEntryNotReady` is the only path
that schedules another attempt; every other outcome, `False` included, lands in `SETUP_ERROR` and
stops. A `False` return also records no reason at all: `error_reason` stays `None`, so the entry
lands in `SETUP_ERROR` with `reason` unset — that the integrations page therefore shows the failure
without a cause is **[unverified]**; the source shows only the empty field. And the cleanup `False`
triggers is not exclusive to it: `finally: if not result and domain_is_integration: await
self._async_process_on_unload(hass)` runs on every exit where `result` is falsy, and the
`ConfigEntryNotReady` branch returns from inside the `try`, so the retry path runs it too
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L916-L918)).
A non-`bool` return is coerced: `logger.error("%s.async_setup_entry did not return boolean", ...)`
then `result = False`.

**The retry schedule.** One line computes it:

```python
wait_time = min(2**self._tries * 5, SETUP_RETRY_MAX_WAIT) + (
    randint(RANDOM_MICROSECOND_MIN, RANDOM_MICROSECOND_MAX) / 1000000
)
self._tries += 1
```

with `SETUP_RETRY_MAX_WAIT = 600 # 10 minutes`
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L145))
and `RANDOM_MICROSECOND_MIN = 50000`, `RANDOM_MICROSECOND_MAX = 500000`
([`homeassistant/helpers/event.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/helpers/event.py#L87-L88)).
`_tries` starts at `0`
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L564)),
so the waits in seconds are **5, 10, 20, 40, 80, 160, 320, 600, 600, …** plus 0.05–0.5 s of jitter.
The retry count is never capped. It is reset only by moving to a state outside
`NO_RESET_TRIES_STATES = {ConfigEntryState.SETUP_RETRY, ConfigEntryState.SETUP_IN_PROGRESS}`
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L222-L225)),
which is what lets the backoff keep growing across consecutive failures.

Scheduling depends on whether the host has finished booting. During boot the retry is not a
timer at all — the entry subscribes to `EVENT_HOMEASSISTANT_STARTED` instead, so a slow device
does not delay start-up. It still burns a retry: `self._tries += 1` runs before either branch,
so the boot-time attempt advances the backoff for the next one:

```python
if hass.state is CoreState.running:
    self._async_cancel_retry_setup = async_call_later(hass, wait_time, HassJob(...))
else:
    self._async_cancel_retry_setup = hass.bus.async_listen(
        EVENT_HOMEASSISTANT_STARTED, functools.partial(self._async_setup_again, hass)
    )
```

**The entity-platform path has its own, different schedule.** `PlatformNotReady` is handled in
`EntityPlatform._async_setup_platform` with `wait_time = min(tries, 6) *
PLATFORM_NOT_READY_BASE_WAIT_TIME`
([`homeassistant/helpers/entity_platform.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/helpers/entity_platform.py#L508-L541))
where the base is `30 # seconds`
([`entity_platform.py#L70`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/helpers/entity_platform.py#L70)):
**30, 60, 90, 120, 150, 180, 180, …** — linear, not exponential, capped at three minutes, no jitter,
and again uncapped in count. The constant `PLATFORM_NOT_READY_RETRIES = 10`
([`entity_platform.py#L62`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/helpers/entity_platform.py#L62))
appears nowhere else under `homeassistant/` — a retry cap that is defined and never applied. Two
neighbouring failures on the same platform get non-retryable treatment ([same file, lines
542-561](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/helpers/entity_platform.py#L542-L561)):
a `SLOW_SETUP_MAX_WAIT = 60` timeout logs "Setup of platform %s is taking longer than %s seconds.
Startup will proceed without waiting any longer." and returns `False`, and a forwarded platform that
raises a config-entry error is told off — "Instead raise %s before calling
async_forward_entry_setups" — and also returns `False`.

**A failing stop leaves the entry neither loaded nor unloaded.** `ConfigEntry.async_unload` has
three failure exits, all producing the same state
([`homeassistant/config_entries.py`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L995-L1077)):
no `async_unload_entry` attribute at all gives `FAILED_UNLOAD` with reason `"Unload not supported"`;
a `False` return gives `FAILED_UNLOAD` with `"Unload failed"`; a raised exception is logged with
`logger.exception` and gives `FAILED_UNLOAD` with `str(exc) or "Unknown error"`. In all three
`async_unload` returns `False`. The consequences are structural, not cosmetic:

- The on-unload callbacks and `runtime_data` teardown sit inside `if result:`, so they do
  **not** run. The entry keeps its runtime object.
- `FAILED_UNLOAD = "failed_unload", False` marks the state non-recoverable, and the enum documents
  what that flag buys: "If the entry state is recoverable, unloads and reloads are allowed."
  ([`ConfigEntryState`](https://github.com/home-assistant/core/blob/9c4c2f27e6bc239128ba8a786cfa469e46c786be/homeassistant/config_entries.py#L151-L187))
  For the integration's own domain `async_unload` refuses before it reaches the component — `if not
  self.state.recoverable: return False`, inside the `if domain_is_integration:` branch — so a second
  unload or a reload can never be attempted. The entry is wedged until Home Assistant restarts.
- A non-`bool` return trips `assert isinstance(result, bool)`, which the surrounding `except
  Exception` converts into the same `FAILED_UNLOAD`.

The documentation is narrower than the code. "Handling setup failures"
([developers.home-assistant.io](https://developers.home-assistant.io/docs/integration_setup_failures))
documents `ConfigEntryNotReady` ("Home Assistant will automatically take care of retrying set up
later"), `PlatformNotReady`, and `ConfigEntryAuthFailed` ("Home Assistant will automatically put the
config entry in a failure state and start a reauth flow") — and never names `ConfigEntryError`,
never states a wait time, and never mentions returning `False`. It also says of a retry message
"Home Assistant will log at `debug` level", where the code logs the retry line at `logger.info` and
only the traceback at `debug`.

### 2. Django: `AppConfig.ready()` raising leaves the registry populated and unrecoverable

`Apps.populate()` runs in three phases and guards itself with a reentrancy flag rather than a
transaction
([`django/apps/registry.py`](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/django/apps/registry.py#L61-L127)):

```python
    def populate(self, installed_apps=None):
        """
        Load application configurations and models.
        ...
        It is thread-safe and idempotent, but not reentrant.
        """
        if self.ready:
            return

        with self._lock:
            if self.ready:
                return

            # An RLock prevents other threads from entering this section. The
            # compare and set operation below is atomic.
            if self.loading:
                # Prevent reentrant calls to avoid running AppConfig.ready()
                # methods twice.
                raise RuntimeError("populate() isn't reentrant")
            self.loading = True
```

Phase 3 is a bare loop with no error handling:

```python
            # Phase 3: run ready() methods of app configs.
            for app_config in self.get_app_configs():
                app_config.ready()

            self.ready = True
            self.ready_event.set()
```

So when one `AppConfig.ready()` raises:

- **Nothing is rolled back.** There is no `try`, no `finally`, no compensating loop. Every entry
  written into `self.app_configs` during phase 1 stays there, every model imported in phase 2
  stays imported, and every `ready()` that already returned keeps whatever it registered —
  signal receivers, system checks, monkeypatches. The apps after the failing one never get
  `ready()` called at all.
- **The flags are left inconsistent.** `self.apps_ready = True` was set at the end of phase 1
  and `self.models_ready = True` at the end of phase 2, both before phase 3 begins; `self.ready`
  is still `False` and `self.ready_event` is unset. `self.loading` is still `True`, because
  nothing clears it on the error path. The registry therefore answers `check_apps_ready()` and
  `check_models_ready()` affirmatively while `django.apps.apps.ready` is `False`.
- **A second `populate()` cannot recover.** `if self.ready: return` does not fire, the `RLock` is
  free (the exception unwound out of the `with`), and `if self.loading:` is `True` — so the second
  call raises `RuntimeError("populate() isn't reentrant")`, from any thread, forever. The one place
  that resets `self.loading` is `set_installed_apps`, which opens with `if not self.ready: raise
  AppRegistryNotReady("App registry isn't ready yet.")`
  ([`django/apps/registry.py`](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/django/apps/registry.py#L356-L362)),
  and `self.ready` is `False`. There is no path back.

`django.setup()` is a thin wrapper — `apps.populate(settings.INSTALLED_APPS)` with no error handling
([`django/__init__.py`](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/django/__init__.py#L8-L24))
— so a raising `ready()` propagates to whatever called `setup()`. Django has no typed failure for
this: `ImproperlyConfigured` and `AppRegistryNotReady`
([`django/core/exceptions.py`](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/django/core/exceptions.py))
cover duplicate labels and premature access, not a plugin whose own initialisation failed. There is
also no stop half to fail: the registry has no `unready()`.

### 3. Starlette and Litestar: one context manager versus an exit stack

The two frameworks answer the partial-start question differently, and the difference is in the
code rather than in the docs.

**Starlette holds exactly one lifespan context manager.** `Router.lifespan` is the whole of it
([`starlette/routing.py`](https://github.com/encode/starlette/blob/f03f65c2f98c592773d691b4d309c68b83e568ef/starlette/routing.py#L645-L670)):

```python
        started = False
        app: Any = scope.get("app")
        await receive()
        try:
            async with self.lifespan_context(app) as maybe_state:
                ...
                await send({"type": "lifespan.startup.complete"})
                started = True
                await receive()
        except BaseException:
            exc_text = traceback.format_exc()
            if started:
                await send({"type": "lifespan.shutdown.failed", "message": exc_text})
            else:
                await send({"type": "lifespan.startup.failed", "message": exc_text})
            raise
```

Starlette keeps no stack, so it has nothing to unwind. `started` is the entire state machine, and it
only decides which ASGI failure message to send. Whether the shutdown half runs after a partial
start is delegated wholly to the single user object: with the ordinary `@asynccontextmanager`
generator, a failure before `yield` means the code after `yield` never runs, because `__aenter__`
raised and the `async with` never entered its body — so `__aexit__` is never called. In this version
the legacy hook path is inert as well: `_DefaultLifespan.__aenter__` and `__aexit__` are both `pass`
([`starlette/routing.py`](https://github.com/encode/starlette/blob/f03f65c2f98c592773d691b4d309c68b83e568ef/starlette/routing.py#L565-L576)),
and `Router.__init__` accepts no `on_startup`/`on_shutdown` sequences at all — the version read is
`__version__ = "1.6.0"`
([`starlette/__init__.py`](https://github.com/encode/starlette/blob/f03f65c2f98c592773d691b4d309c68b83e568ef/starlette/__init__.py#L1)).

**Litestar builds the lifespan out of an `AsyncExitStack`, so a partial start is unwound.**
`Litestar.lifespan` is an `@asynccontextmanager` wrapping one stack
([`litestar/app.py`](https://github.com/litestar-org/litestar/blob/7cccc5e52ce92683a13436a4be8ac77c1ccd1c12/litestar/app.py#L589-L612)):

```python
        async with AsyncExitStack() as exit_stack:
            for hook in self.on_shutdown[::-1]:
                exit_stack.push_async_callback(partial(self._call_lifespan_hook, hook))

            await exit_stack.enter_async_context(self.event_emitter)

            for manager in self._lifespan_managers:
                if not isinstance(manager, AbstractAsyncContextManager):
                    manager = manager(self)
                await exit_stack.enter_async_context(manager)

            for hook in self.on_startup:
                await self._call_lifespan_hook(hook)

            yield
```

Three consequences follow from the registration order, all of them mechanical:

- If the *n*-th lifespan manager's `__aenter__` raises, the *n−1* already entered are exited,
  and so is `event_emitter`, because the stack's `__aexit__` runs as the enclosing `async with`
  unwinds. Litestar is the unwinding case; Starlette is not.
- Every `on_shutdown` hook is pushed onto the stack **before** anything is entered and before
  any `on_startup` hook runs. So an `on_startup` hook that raises still causes **all**
  `on_shutdown` hooks to run — teardown for a start-up that never completed. They were pushed in
  `on_shutdown[::-1]` order and pop LIFO, so they execute in declaration order.
- `push_async_callback` registers a callback that "Cannot suppress exceptions" and receives no
  exception details
  ([`Lib/contextlib.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/contextlib.py#L739-L750)),
  so an `on_shutdown` hook cannot see that start-up failed, nor swallow the failure.

Litestar's ASGI wrapper is otherwise the same shape as Starlette's — `started` flag, `try`,
`lifespan.startup.failed` versus `lifespan.shutdown.failed`, `raise e`
([`litestar/_asgi/asgi_router.py`](https://github.com/litestar-org/litestar/blob/7cccc5e52ce92683a13436a4be8ac77c1ccd1c12/litestar/_asgi/asgi_router.py#L189-L223)).
Neither framework types the failure: both catch `BaseException` and re-raise it unchanged. The
version read is `3.0.0b0`
([`pyproject.toml`](https://github.com/litestar-org/litestar/blob/7cccc5e52ce92683a13436a4be8ac77c1ccd1c12/pyproject.toml#L11)).

**The protocol behind both is a closed two-message taxonomy, and it is the server that decides.**
The ASGI lifespan spec defines `lifespan.startup.failed` — "Sent by the application when it has
failed to complete its startup. If a server sees this it should log/print the message provided and
then exit." — and `lifespan.shutdown.failed` — "Sent by the application when it has failed to
complete its cleanup. If a server sees this it should log/print the message provided and then
terminate."
([`specs/lifespan.rst`](https://github.com/django/asgiref/blob/cf94d8e0cff969d21462a8994b5c46c4eae6954d/specs/lifespan.rst#L106-L161)),
added in "2.0 (2019-03-04): Added startup.failed and shutdown.failed, clarified exception handling
during startup phase". Uvicorn implements exactly that: `startup()` logs "Application startup
failed. Exiting." and sets `should_exit`
([`uvicorn/lifespan/on.py`](https://github.com/encode/uvicorn/blob/fa324a415364563cf45908966435e2480a6b46bf/uvicorn/lifespan/on.py#L46-L75)),
and `Server.startup` then calls `sys.exit(STARTUP_FAILURE)` with `STARTUP_FAILURE = 3`
([`uvicorn/server.py`](https://github.com/encode/uvicorn/blob/fa324a415364563cf45908966435e2480a6b46bf/uvicorn/server.py#L115-L118),
[`uvicorn/config.py`](https://github.com/encode/uvicorn/blob/fa324a415364563cf45908966435e2480a6b46bf/uvicorn/config.py#L83)).
There is no retry anywhere on this path.

### 4. FastStream: the first broker that fails to connect ends start-up

Brokers are started sequentially with no error handling at all
([`faststream/_internal/application.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/_internal/application.py#L93-L96)):

```python
    async def _start_broker(self) -> None:
        assert self.brokers, "You should setup a broker"
        for b in self.brokers:
            await b.start()
```

So the answer is: **fail, not degrade and not retry.** The first broker whose `start()` raises
aborts the loop; the remaining brokers are never started; the brokers already started are never
stopped by this code path.

In the CLI application the failure travels through an anyio task group. `FastStream.run` puts
`_startup` in the group and then polls a flag
([`faststream/app.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/app.py#L77-L98)):

```python
        async with self.lifespan_context(**(run_extra_options or {})):
            try:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self._startup, log_level, run_extra_options)

                    while not self._should_exit:
                        await anyio.sleep(sleep_time)

                    await self._shutdown(log_level)
                    tg.cancel_scope.cancel()
            except ExceptionGroup as e:
                for ex in e.exceptions:
                    raise ex from None
```

A broker failure cancels the group before the loop can reach `await self._shutdown(log_level)`,
so `stop()` — and with it every `on_shutdown` and `after_shutdown` hook and every
`broker.stop()` — is skipped entirely. The `except ExceptionGroup` clause then flattens the
group by raising its first member `from None`, discarding the rest and suppressing the group as
context.

The ASGI variant behaves differently in two ways worth naming
([`faststream/asgi/app.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/asgi/app.py#L249-L322)).
`__start` signals readiness before the brokers connect —

```python
        async with (
            self._startup_logging(log_level=log_level),
            self._start_hooks_context(**run_extra_options),
        ):
            task_status.started()
            await self._start_broker()
```

— so `await tg.start(self.__start, ...)` returns once the `on_startup` hooks have run, the
`start_lifespan_context` body yields, and `lifespan.startup.complete` is sent to the server
*before* any broker connection is established. And unlike the CLI path,
`start_lifespan_context` wraps the body in `try: yield finally: await self._shutdown()`, so the
shutdown half does run.

FastStream types its start-up failures only shallowly. Its hierarchy is rooted at
`FastStreamException(Exception)` with `SetupError(FastStreamException, ValueError)` — "Exception to
raise at wrong method usage" — and `StartupValidationError(FastStreamException, ValueError)` for
mismatched CLI options
([`faststream/exceptions.py`](https://github.com/ag2ai/faststream/blob/2c9df8aaec6fca6c11685667dc5ced762fc98154/faststream/exceptions.py)).
`StartupValidationError` is the one failure the ASGI lifespan handler special-cases: when Typer is
installed it is drawn with `draw_startup_errors` and `lifespan.startup.failed` is sent with an empty
message, and without Typer it falls through to the generic handler. There is no `BrokerNotReady`, no
not-ready-yet class, and no retry policy: a connection failure surfaces as whatever the underlying
driver raised.

### 5. CPython: `contextlib.AsyncExitStack` and `asyncio.TaskGroup`

#### 5a. `AsyncExitStack`: entered callbacks are unwound, simultaneous exit failures are lost

**The unwinding guarantee is documented, and it is the whole promise.** The class example says: "All
opened connections will automatically be released at the end of the async with statement, even if
attempts to open a connection later in the list raise an exception"
([docs.python.org](https://docs.python.org/3/library/contextlib.html#contextlib.AsyncExitStack)).
The `ExitStack` prose it refers back to says "Each instance maintains a stack of registered
callbacks that are called in reverse order when the instance is closed (either explicitly or
implicitly at the end of a `with` statement)" and "Since registered callbacks are invoked in the
reverse order of registration, this ends up behaving as if multiple nested `with` statements had
been used with the registered set of callbacks. This even extends to exception handling - if an
inner callback suppresses or replaces an exception, then outer callbacks will be passed arguments
based on that updated state"
([docs.python.org](https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack)). The
mechanism is that `enter_async_context` pushes the exit callback only after `await _enter()`
returns, so a failed `__aenter__` is never registered while everything before it is
([`Lib/contextlib.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/contextlib.py#L707-L725)).

**The documentation says nothing whatever about several `__aexit__` calls raising.** The
`contextlib` page never mentions `ExceptionGroup`, `BaseExceptionGroup` or `__context__` in
connection with either stack class; the only `BaseExceptionGroup` discussion on that page belongs to
`suppress()`. The behaviour has to be read from the source
([`Lib/contextlib.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/contextlib.py#L759-L815)):

```python
        # Callbacks are invoked in LIFO order to match the behaviour of
        # nested context managers
        suppressed_exc = False
        pending_raise = False
        while self._exit_callbacks:
            is_sync, cb = self._exit_callbacks.pop()
            try:
                ...
            except BaseException as new_exc:
                # simulate the stack of exceptions by setting the context
                _fix_exception_context(new_exc, exc)
                pending_raise = True
                exc = new_exc

        if pending_raise:
            try:
                # bare "raise exc" replaces our carefully
                # set-up context
                fixed_ctx = exc.__context__
                raise exc
            except BaseException:
                exc.__context__ = fixed_ctx
                raise
        return received_exc and suppressed_exc
```

Four findings, none of them in the documentation:

1. **No grouping ever happens.** `AsyncExitStack.__aexit__` raises a single exception. There is
   no `BaseExceptionGroup` construction anywhere in `Lib/contextlib.py` outside `suppress()`.
2. **Every registered callback still runs.** The `except BaseException` sits inside the `while`,
   so one failing `__aexit__` — `CancelledError` included — does not stop the unwind. The
   remaining callbacks are all invoked, each receiving the newest pending exception as its
   `exc_details`.
3. **The last-run callback's exception is the one that propagates.** `exc = new_exc` overwrites
   on each failure and the loop is LIFO, so the winner is the failure from the
   *earliest-registered* (outermost) callback.
4. **The earlier failures are chained only if an exception was already in flight; otherwise
   they are silently dropped.** `_fix_exception_context(new_exc, old_exc)` begins `exc_context =
   new_exc.__context__` and returns immediately `if exc_context is None or exc_context is
   old_exc`, and it only rewrites a link when it reaches `frame_exc = sys.exception()`. During a
   clean unwind `frame_exc` is `None`, and each callback raises while no exception is being
   handled, so `new_exc.__context__` is `None` and the helper returns without linking anything.
   Reproduced on CPython 3.14.7: three failing `__aexit__` callbacks in one stack, no body
   exception, yield exactly one `RuntimeError` whose `__context__` is `None` — the other two
   vanish. Add a body exception and the same three produce a full `exit-a ← exit-b ← exit-c ←
   body` chain, because the interpreter set each `__context__` to the in-flight exception and
   the helper could re-point it.

The practical reading: `AsyncExitStack` gives a strong unwind guarantee and a weak reporting
guarantee. A host that closes its plugins through one stack on a clean shutdown will hear about
at most one failing plugin, with no marker that others failed.

#### 5b. `asyncio.TaskGroup`: grouping is the documented contract, with three named escapes

Here the documentation is explicit where `contextlib`'s is silent. The class docstring states the
rule — "Any exceptions other than `asyncio.CancelledError` raised within a task will cancel all
remaining tasks and wait for them to exit. The exceptions are then combined and raised as an
`ExceptionGroup`"
([`Lib/asyncio/taskgroups.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/asyncio/taskgroups.py#L14-L28))
— and the library reference gives the full ordering
([`Doc/library/asyncio-task.rst`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Doc/library/asyncio-task.rst#L439-L466)):

> The first time this happens, the remaining tasks in the group are cancelled and then waited
> for, and no further tasks can be added to the group.

> Once all tasks have finished, the non-cancellation exceptions -- including the exception the
> body exited with, unless it is `asyncio.CancelledError` -- are combined in an `ExceptionGroup`
> or `BaseExceptionGroup` (as appropriate; see their documentation), which is then raised.

> Some exceptions are treated specially: if any task fails with `KeyboardInterrupt` or
> `SystemExit`, the task group still cancels the remaining tasks and waits for them, but then
> the initial `KeyboardInterrupt` or `SystemExit` is re-raised instead of `ExceptionGroup` or
> `BaseExceptionGroup`. Additionally, if the body of the `async with` statement raises
> `GeneratorExit` and none of the other tasks raise exceptions that would be reported, the
> `GeneratorExit` is re-raised.

The source supplies the details the prose leaves out
([`Lib/asyncio/taskgroups.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Lib/asyncio/taskgroups.py#L86-L319)):

- **Failures during cancellation join the same group.** `_on_task_done` appends to
  `self._errors` whenever `task.exception()` is not `None`, and it is registered on every task,
  so an exception raised by a task's own cleanup while it is being cancelled is collected
  exactly like the original failure. Only `if task.cancelled(): return` — a task that ends
  genuinely cancelled contributes nothing.
- **The group's message is fixed:** `raise BaseExceptionGroup('unhandled errors in a TaskGroup',
  self._errors) from None`. The `from None` sets `__suppress_context__`, so the body's own
  exception is not shown as context — it is a *member* of the group instead, appended last by
  `if et is not None and not issubclass(et, exceptions.CancelledError):
  self._errors.append(exc)`.
- **Real errors outrank cancellation.** `if propagate_cancellation_error is not None and not
  self._errors:` — the comment reads "Propagate CancelledError if there is one, except if there
  are other errors -- those have priority." An external cancellation arriving at the same time
  as task failures is not lost, though: "In the case where a task group is cancelled externally
  and also must raise an `ExceptionGroup`, it will call the parent task's `cancel()` method"
  ([docs.python.org](https://docs.python.org/3/library/asyncio-task.html#task-groups)), which
  the source does as `self._parent_task.uncancel(); self._parent_task.cancel()`.
- **The `SystemExit`/`KeyboardInterrupt` escape used to lose the other errors, and now reports
  them.** On `main` the base-error branch first walks `self._errors` and hands each to
  `self._loop.call_exception_handler` with the message `'TaskGroup task exception was not
  propagated because the TaskGroup body is being closed with a BaseException'`, under a comment
  naming gh-135736: "self._base_error (SystemExit or KeyboardInterrupt) is about to propagate
  out of this method, which discards any other collected task errors silently. Report them
  instead of losing them." That block is absent from
  [`v3.14.0`](https://github.com/python/cpython/blob/v3.14.0/Lib/asyncio/taskgroups.py), where
  the branch is just `try: raise self._base_error finally: exc = None` — so on 3.14 those errors
  are discarded without a trace.
- **Nesting is well defined.** "when one task group is syntactically nested in another, and both
  experience an exception in one of their child tasks simultaneously, the inner task group will
  process its exceptions, and then the outer task group will receive another cancellation and
  process its own exceptions"
  ([docs.python.org](https://docs.python.org/3/library/asyncio-task.html#task-groups)).

The contrast with `AsyncExitStack` is the sharpest result in this section. Both primitives
handle "n things failed at once" and they choose opposite answers: `TaskGroup` grouped and
documented, `AsyncExitStack` single-exception, partially-chained and undocumented.

### 6. Elsewhere in the field: other closed start-up-failure taxonomies

Beyond Home Assistant, three of the four projects below give plugin start-up a named failure set
rather than a bare exception — pydantic does not — and only one of the three also undoes the
partial work.

**discord.py — a five-member extension taxonomy with rollback.** `ExtensionError(DiscordException)`
carries the extension `name`, and the members are `ExtensionAlreadyLoaded`, `ExtensionNotLoaded`,
`NoEntryPointError` ("An exception raised when an extension does not have a `setup` entry point
function"), `ExtensionFailed` ("raised when an extension failed to load during execution of the
module or `setup` entry point", exposing `original` and `__cause__`) and `ExtensionNotFound`
([`discord/ext/commands/errors.py`](https://github.com/Rapptz/discord.py/blob/65232c38702be5844cf2ce865a4777eb1928b5d0/discord/ext/commands/errors.py#L1019-L1105)).
The loader compensates a partially-run `setup` before raising
([`discord/ext/commands/bot.py`](https://github.com/Rapptz/discord.py/blob/65232c38702be5844cf2ce865a4777eb1928b5d0/discord/ext/commands/bot.py#L956-L980)):

```python
        try:
            await setup(self)
        except Exception as e:
            del sys.modules[key]
            await self._remove_module_references(lib.__name__)
            await self._call_module_finalizers(lib, key)
            raise errors.ExtensionFailed(key, e) from e
```

Every registration the half-run `setup` made — commands, cogs, listeners — is removed, the
module is un-imported, and the module's own finalisers run. This is the only host in this
section that both types the failure and rolls back the plugin's side effects.

**Sentry's Python SDK — one type whose meaning depends on how the plugin was asked for.**
`DidNotEnable(Exception)`: "The integration could not be enabled due to a trivial user error like
`flask` not being installed for the `FlaskIntegration`. This exception is silently swallowed for
default integrations, but reraised for explicitly enabled integrations."
([`sentry_sdk/integrations/__init__.py`](https://github.com/getsentry/sentry-python/blob/7e95b86bc31b0a1411f0e54c0397152b2201cb2f/sentry_sdk/integrations/__init__.py#L316-L323)).
The dispatch is exactly that: `except DidNotEnable as e: if identifier not in
used_as_default_integration: raise` and otherwise a `logger.debug` ([same file, lines
262-273](https://github.com/getsentry/sentry-python/blob/7e95b86bc31b0a1411f0e54c0397152b2201cb2f/sentry_sdk/integrations/__init__.py#L262-L273)).
One typed decline, two host policies, chosen by whether the user named the plugin.

**pytest — a three-way classification of import failure, with the reasoning in the docstring.**
`PluginManager.import_plugin` sorts failures into declined, user error and plugin defect
([`src/_pytest/config/__init__.py`](https://github.com/pytest-dev/pytest/blob/3fd8675d6d798507c06cf9c60753be6d9d7b0e17/src/_pytest/config/__init__.py#L939-L960)):

```python
        except Skipped as e:
            self.skipped_plugins.append((modname, e.msg or ""))
        except ModuleNotFoundError as e:
            if _is_missing_module(e, importspec):
                # The plugin itself is nowhere to be found - pytest was pointed
                # at something which does not exist, so this is a usage error.
                raise UsageError(f'Error importing plugin "{modname}": {e}') from e
            # Some *other* module the plugin imports is missing: the plugin was
            # found, so this is a defect in the plugin, not a usage error.
            raise PluginImportFailure(modname) from e
        except UsageError:
            raise
        except Exception as e:
            raise PluginImportFailure(modname) from e
```

`PluginImportFailure` states the distinction it exists to draw: "This is deliberately distinct from
a plugin which could not be found at all: not finding it means pytest was pointed at something that
isn't there, which is a `UsageError`, while a plugin blowing up on import is a defect in the plugin
and reported as an internal error." ([same file, lines
146-153](https://github.com/pytest-dev/pytest/blob/3fd8675d6d798507c06cf9c60753be6d9d7b0e17/src/_pytest/config/__init__.py#L146-L153)).
The declined branch is the degraded start: pytest continues and later emits
`PytestConfigWarning(f"skipped plugin {module_name!r}: {msg}")` ([same file, line
2264](https://github.com/pytest-dev/pytest/blob/3fd8675d6d798507c06cf9c60753be6d9d7b0e17/src/_pytest/config/__init__.py#L2264-L2269)).

**pydantic — narrow, untyped, degraded.** The entry-point loader catches only two exception
types and warns:

```python
                    try:
                        _plugins[entry_point.value] = entry_point.load()
                    except (ImportError, AttributeError) as e:
                        warnings.warn(
                            f'{e.__class__.__name__} while loading the `{entry_point.name}` Pydantic plugin, '
                            f'this plugin will not be installed.\n\n{e!r}',
                            stacklevel=2,
                        )
```

([`pydantic/plugin/_loader.py`](https://github.com/pydantic/pydantic/blob/831893ed0411d45c20aacae88e067c9c33a89501/pydantic/plugin/_loader.py#L46-L55)).
Anything else a plugin raises escapes and breaks the caller. There is no failure type of pydantic's
own.

**Two negatives worth recording, because they are the common case.** `pluggy` — "the canonical
Python plugin system" in this catalogue's own reference list — does `plugin = ep.load()` with no
`try` at all in `load_setuptools_entrypoints`
([`src/pluggy/_manager.py`](https://github.com/pytest-dev/pluggy/blob/6a7f8960eb4009b551f14030233cea7a64ccaf5d/src/pluggy/_manager.py#L380-L408)):
the raw exception propagates, plugins registered earlier in the same call stay registered, and the
returned count is lost. And the two closest bot-framework peers do no better:

- `python-telegram-bot`'s `Application.__aenter__` documents a rollback — "Raises: `Exception`: If
  an exception is raised during initialization, `shutdown` is called in this case" — and implements
  it as `try: await self.initialize() except Exception: await self.shutdown(); raise`
  ([`src/telegram/ext/_application.py`](https://github.com/python-telegram-bot/python-telegram-bot/blob/3d72ea2a5a7fc11116a23ee86307a3ab62f10f3e/src/telegram/ext/_application.py#L359-L374)).
  The rollback does nothing: `initialize()` sets `self._initialized = True` only after its last
  step, and `shutdown()`, after a running-state check, returns early — `if not self._initialized:
  _LOGGER.debug("This Application is already shut down. Returning."); return` ([same file, lines
  470-555](https://github.com/python-telegram-bot/python-telegram-bot/blob/3d72ea2a5a7fc11116a23ee86307a3ab62f10f3e/src/telegram/ext/_application.py#L470-L555)).
  So if `self.updater.initialize()` raises, the already-initialised `bot` and `_update_processor`
  are left initialised and never shut down. `__aenter__` also catches `Exception`, not
  `BaseException`, so a cancellation during init skips even the attempt.
- `aiogram` emits start-up hooks *outside* the `try` whose `finally` emits shutdown: `await
  self.emit_startup(bot=bots[-1], **workflow_data)` precedes `try: ... finally: ... await
  self.emit_shutdown(...)`
  ([`aiogram/dispatcher/dispatcher.py`](https://github.com/aiogram/aiogram/blob/97cfe79fa0ac9459d498bdb15cb7cb0530dbaac7/aiogram/dispatcher/dispatcher.py#L596-L631)).
  A raising startup callback therefore means no shutdown callback runs anywhere in the router tree,
  and `emit_startup` itself walks sub-routers with no error handling
  ([`aiogram/dispatcher/router.py`](https://github.com/aiogram/aiogram/blob/97cfe79fa0ac9459d498bdb15cb7cb0530dbaac7/aiogram/dispatcher/router.py#L281-L292)),
  so routers after the failing one never start at all.

### Comparison

| Host | Partial start unwound? | A failing stop produces | Retry, and on what schedule | Failure typed? |
|---|---|---|---|---|
| Home Assistant config entry | Yes — `_async_process_on_unload` runs on a `False`/exception setup | `FAILED_UNLOAD`, non-recoverable; entry stuck, `runtime_data` kept, `async_unload` returns `False` | Yes, only for `ConfigEntryNotReady`: 5, 10, 20, 40, 80, 160, 320, 600, 600 s + 0.05–0.5 s jitter, uncapped in count; before boot completes, waits for `EVENT_HOMEASSISTANT_STARTED` | Yes — `IntegrationError` with four members plus OAuth subclasses |
| Home Assistant entity platform | No rollback; `_setup_complete` stays `False` | `async_reset` removes the entities, logging each failure with `logger.exception`, and finishes anyway | Yes, for `PlatformNotReady`: 30, 60, 90, 120, 150, 180, 180 s, no jitter, uncapped; `PLATFORM_NOT_READY_RETRIES = 10` unused | Yes — `PlatformNotReady` |
| Django app registry | No — configs, imports and completed `ready()` side effects all persist | n/a — no `unready()` | No | No — bare exception out of `populate()`; `loading` stuck `True`, second call raises `RuntimeError("populate() isn't reentrant")` |
| Starlette | No stack to unwind; delegated to the single lifespan CM, whose post-`yield` half never runs | `lifespan.shutdown.failed` + re-raise; uvicorn logs "Application shutdown failed. Exiting." and sets `should_exit` — exit code `3` is the startup path only | No | No — `except BaseException`, re-raised unchanged |
| Litestar | Yes — `AsyncExitStack` exits everything entered, and runs every `on_shutdown` hook even if `on_startup` failed | `lifespan.shutdown.failed` + re-raise; only one exit failure survives (see `AsyncExitStack`) | No | No — `except BaseException as e` … `raise e` |
| FastStream (CLI) | No — started brokers not stopped, `_shutdown` skipped entirely | `stop()` is not reached on a failed start; on a clean stop, exceptions flatten to the group's first member `from None` | No | Partly — `SetupError`, `StartupValidationError`; connection errors are the driver's own |
| FastStream (ASGI) | Shutdown does run (`try: yield finally: await self._shutdown()`) | `lifespan.shutdown.failed` | No | Same, plus a special case for `StartupValidationError` |
| `contextlib.AsyncExitStack` | Yes — the documented promise; a failed `__aenter__` is never registered | One exception: the earliest-registered failing callback. Others chained via `__context__` only if an exception was already in flight, else dropped. Never a `BaseExceptionGroup` | No | No |
| `asyncio.TaskGroup` | Cancels and awaits every remaining task | `BaseExceptionGroup('unhandled errors in a TaskGroup', …) from None`, cleanup failures included; `SystemExit`/`KeyboardInterrupt` and lone `GeneratorExit` escape the group | No | Grouped rather than typed |
| discord.py extensions | Yes — module dropped from `sys.modules`, references removed, finalisers called | `unload_extension` raises `ExtensionNotLoaded` / `ExtensionNotFound` only; a raising `teardown` is swallowed by `_call_module_finalizers` (`except Exception: pass`) | No | Yes — `ExtensionError` with five members |
| Sentry SDK integrations | n/a — `setup_once` failure is the unit | n/a — no teardown | No | Yes — `DidNotEnable`, swallowed for defaults, re-raised for explicit |
| pytest plugins | No — earlier plugins stay registered | n/a | No | Yes — `Skipped` / `UsageError` / `PluginImportFailure` |
| pydantic plugins | n/a — plugin simply absent | n/a | No | No — warns on `ImportError`/`AttributeError`, else propagates |
| pluggy | No — earlier plugins stay registered | n/a | No | No — `ep.load()` unguarded |
| python-telegram-bot | Documented, but ineffective: `shutdown()` early-returns because `_initialized` is still `False` | `shutdown()` raises `RuntimeError("This Application is still running!")` if still running | No | No |
| aiogram | No — `emit_startup` is outside the `try`, so no `emit_shutdown` runs | n/a on a failed start | No | No |

### What §2 establishes

- A typed start-up taxonomy is a small, closed set whose members differ by *host reaction*, not
  by cause. Home Assistant's four `IntegrationError` members map to retry-with-backoff,
  start-reauth, give-up-fatally and give-up-with-a-platform-retry, and new errors join by
  inheriting the member whose reaction they want — the mechanism that keeps the set from growing.
- A typed taxonomy is worth little without the "not ready yet" member. That is the only Home
  Assistant class that produces a second attempt; everything else, including a plain `False`
  return, is terminal. Two of the surveyed hosts retry at all, and both are Home Assistant paths.
- Retry schedules in the field are short, uncapped in count, and jittered only where the host
  has many plugins: 5→600 s doubling with sub-second jitter for config entries, 30→180 s linear
  without jitter for platforms. That both were chosen so a device that is merely offline
  recovers without a restart is **[unverified]** — the only rationale in the source is the
  comment that the jitter bounds "have been determined experimentally in production testing".
- `False` and `raise` must not mean the same thing, and Home Assistant shows the cost when they
  nearly do: `False` records no reason, so the failure reaches the operator without a cause.
- `AsyncExitStack` is the right primitive for unwinding a partial start and the wrong one for
  reporting a failed stop. Its unwind promise is documented and total; its behaviour with
  several simultaneous exit failures is undocumented, single-exception, and silently lossy on a
  clean shutdown. A host that wants to report every plugin that failed to stop must collect the
  failures itself rather than rely on the stack.
- `asyncio.TaskGroup` already solves the n-simultaneous-failures problem in the standard
  library, and documents the solution: grouping into `BaseExceptionGroup`, cancellation
  subordinate to real errors, and two named escapes for `SystemExit`/`KeyboardInterrupt` and
  `GeneratorExit`. The pattern is available to any host that wants closed shutdown semantics.
- A failed stop needs a defined resting state. Home Assistant's `FAILED_UNLOAD` is explicitly
  non-recoverable, which makes the entry un-reloadable until restart — a decision, visible in
  the enum, that the host prefers a wedged plugin to an unknown one. Django's registry
  demonstrates the alternative: no defined state, `loading` left `True`, and
  `RuntimeError("populate() isn't reentrant")` on every subsequent attempt.
- Ordering a teardown hook's registration before the corresponding start-up work decides whether
  teardown runs after a failed start. Litestar registers `on_shutdown` first and therefore
  always runs it; aiogram emits startup outside the guarded block and therefore never runs
  shutdown; both are one-line consequences of where the registration sits.
- Signalling readiness before the last dependency is connected produces a genuinely degraded
  start. `AsgiFastStream` calls `task_status.started()` before `await self._start_broker()`, so
  the server is told start-up completed while brokers are still connecting.

## 3 The plugin-to-plugin channel

Six hosts sanction six different channels. Every one of them is a host-owned lookup — a registry
object, a domain-keyed dict, or an object the plugin handed the host at activation. None of the five
Python hosts examined documents type-keyed dependency injection as the channel between plugins.

### Litestar `PluginRegistry`

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

### Home Assistant `dependencies`, `after_dependencies`, and the runtime channel

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

### Django `apps.get_app_config`

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

### Sphinx `setup_extension`, `app.extensions` and `needs_extensions`

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

### pytest `get_plugin` / `getplugin`

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

### VS Code `activate()` exports

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

### The documented hazard

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

### Dependency injection as the alternative channel

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

### Comparison

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

### What §3 establishes

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

## 4 Conflicts, refusals and the negative space

Every host in this survey refuses something. What differs is *what* it treats as a conflict, *when*
it notices, and whether the answer is an exception, a warning or silence. This section collects the
exact strings and the moment each one fires.

### 1. Duplicate identity

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

### 2. Two plugins claiming one thing

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

### 3. Disabling and unloading

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
against: `pydantic/plugin/__init__.py` still points at `[Build a
Plugin](../concepts/plugins.md#build-a-plugin)`, but `docs/concepts/plugins.md` does not exist in
the repository and is absent from the `mkdocs.yml` nav
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

### 4. The negative space: explicit prohibitions

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

### 5. Order determinism

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

### 6. Static validation before start-up

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

### A table of refusals

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

### What §4 establishes

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

## 5 The third-party author kit

Protocol definitions tell an author what to implement. This section asks what else a host hands
them: a way to test the implementation, a way to start the project, a name to publish it under, a
reference page they can trust, and conventions for the two things a plugin emits into a shared
namespace — log records and configuration keys.

### The contract test kit

pytest ships one, and it is the only kit in this survey whose stated purpose is testing a plugin
rather than testing an application. It is a plugin itself, off by default:

> pytest comes with a plugin named `pytester` that helps you write tests for your plugin code. The
> plugin is disabled by default, so you will have to enable it before you can use it.

([`doc/en/how-to/writing_plugins.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_plugins.rst))

An author enables it with `pytest_plugins = ["pytester"]` in a `conftest.py`, or with `-p pytester`
on the command line
([same page](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_plugins.rst)).
The `Pytester` class states its own scope:

> Facilities to write tests/configuration files, execute pytest in isolation, and match against
> expected output, perfect for black-box testing of pytest plugins.
>
> It attempts to isolate the test run from external factors as much as possible, modifying the
> current working directory to `path` and environment variables during initialization.

([`src/_pytest/pytester.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pytester.py))

The documented assertion loop is four calls: `makeconftest()` writes a temporary `conftest.py`,
`makepyfile()` writes a temporary test module, `runpytest()` runs pytest over them, and
`RunResult.assert_outcomes(passed=4)` checks the tallies
([`writing_plugins.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_plugins.rst)).
The kit names its own fragility in the same place:

> `pytest.RunResult.assert_outcomes` parses pytest's standard terminal summary. A plugin that
> changes or removes that summary can make outcome parsing fail. Disable the output-changing plugin
> for the nested run with `-p no:<plugin>`, or set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` when the
> nested run should not discover third-party plugins.

([`writing_plugins.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_plugins.rst))

`pytester_example_dir` is an ini option, registered with the help text `Directory to take the
pytester example files from`, that lets an author keep fixture projects as real files instead of
embedded strings
([`src/_pytest/pytester.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pytester.py)).
`copy_example()` refuses to work without it, with the message `pytester_example_dir is unset, can't
copy examples` ([same
file](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pytester.py)). A per-test override
exists as a marker: `pytester_example_path(*path_segments): join the given path segments to
`pytester_example_dir` for this test.` ([same
file](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pytester.py)).

The `runpytest` family splits along process boundary and along how much detail comes back.

| Method | Docstring or behaviour | Returns |
|---|---|---|
| `runpytest()` | "Run pytest inline or in a subprocess, depending on the command line option `--runpytest`" | `RunResult` |
| `runpytest_inprocess()` | "Return result of running pytest in-process, providing a similar interface to what self.runpytest() provides." | `RunResult` |
| `runpytest_subprocess()` | "Run pytest as a subprocess with given arguments." | `RunResult` |
| `inline_run()` | "Run `pytest.main()` in-process, returning a HookRecorder." | `HookRecorder` |
| `spawn_pytest()` | "Run pytest using pexpect." | `pexpect.spawn` |

([`src/_pytest/pytester.py`](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pytester.py))

`--runpytest` defaults to `inprocess`, with `choices=("inprocess", "subprocess")` and the help text
`Run pytest sub runs in tests using an 'inprocess' or 'subprocess' (python -m main) method`
([same file](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pytester.py)). The two
modes are not interchangeable: subprocess mode rejects plugin objects with `Specifying plugins as
objects is not supported in pytester subprocess mode; specify by name instead: {plugin}`
([same file](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pytester.py)).
`inline_run()` documents why an author would give up isolation: it "can return a `HookRecorder`
instance which gives more detailed results from that run than can be done by matching
stdout/stderr from `runpytest`"
([same file](https://github.com/pytest-dev/pytest/blob/main/src/_pytest/pytester.py)).

Sphinx ships the second kit, and addresses extension authors directly:

> Utility functions and pytest fixtures for testing are provided in `sphinx.testing`. If you are a
> developer of Sphinx extensions, you can write unit tests with pytest.

([`doc/extdev/testing.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/extdev/testing.rst))

Activation is the same pattern as pytester — `pytest_plugins = ('sphinx.testing.fixtures',)` — and
the module is marked `.. versionadded:: 1.6` ([same
page](https://github.com/sphinx-doc/sphinx/blob/master/doc/extdev/testing.rst)). The fixtures are
`app`, `status`, `warning`, `make_app`, `rootdir`, `app_params`, `test_params`, `shared_result`,
`sphinx_test_tempdir`, `rollback_sysmodules` and `if_graphviz_found`, and the plugin registers two
markers, `sphinx(buildername="html", *, testroot="root", srcdir=None, ...): arguments to initialize
the sphinx test application.` and `test_params(shared_result=...): test parameters.`
([`sphinx/testing/fixtures.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/testing/fixtures.py)).
`SphinxTestApp` is "A subclass of `sphinx.application.Sphinx` for tests" and its docstring pushes
authors toward the marker rather than direct construction
([`sphinx/testing/util.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/testing/util.py)).
The page then hands the reader back to the host's own suite: "If you want to know more detailed
usage, please refer to `tests/conftest.py` and other `test_*.py` files under the `tests/`
directory."
([`doc/extdev/testing.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/extdev/testing.rst))

Litestar ships nothing for plugin authors. `litestar/testing/` exports `TestClient`,
`AsyncTestClient`, `WebSocketTestSession`, `AsyncWebSocketTestSession`, `RequestFactory`,
`create_test_client`, `create_async_test_client`, `subprocess_sync_client` and
`subprocess_async_client` — an application test client, not a plugin harness
([`litestar/testing/__init__.py`](https://github.com/litestar-org/litestar/blob/main/litestar/testing/__init__.py)).
I searched the `litestar/` package for `PluginTest`, `plugin_test`, `conformance` and
`assert_plugin` and found no matches. The plugin guide never mentions testing
([`docs/usage/plugins/index.rst`](https://github.com/litestar-org/litestar/blob/main/docs/usage/plugins/index.rst)),
and the testing guide mentions the word "plugin" once, referring to anyio's pytest plugin
([`docs/usage/testing.rst`](https://github.com/litestar-org/litestar/blob/main/docs/usage/testing.rst)).

FastStream ships nothing, because it has no third-party plugin surface to test against. Its test
doubles are per-broker — `faststream/kafka/testing.py`, `faststream/rabbit/testing.py`,
`faststream/nats/testing.py`, `faststream/redis/testing.py`, `faststream/mqtt/testing.py`,
`faststream/confluent/testing.py` — built on a `TestBroker` base that lives under
[`faststream/_internal/testing/broker.py`](https://github.com/ag2ai/faststream/blob/main/faststream/_internal/testing/broker.py),
inside a package named `_internal`. Searching `pyproject.toml` for `plugin` returns three mkdocs
documentation dependencies, mypy's `plugins = ["pydantic.mypy"]` and coverage's `plugins =
["covdefaults"]`, and no entry-point group
([`pyproject.toml`](https://github.com/ag2ai/faststream/blob/main/pyproject.toml)). In FastStream's
documentation "plugin" means FastStream mounted into FastAPI, the reverse direction
([`docs/docs/en/getting-started/integrations/frameworks/index.md`](https://github.com/ag2ai/faststream/blob/main/docs/docs/en/getting-started/integrations/frameworks/index.md)).

Home Assistant ships nothing either, and the reason is packaging. Its kit exists — the `hass`
fixture is defined in
[`tests/conftest.py`](https://github.com/home-assistant/core/blob/dev/tests/conftest.py), and
`tests/common.py` carries helpers the developer docs name, including
`import_and_test_deprecated_constant` and `help_test_all`
([`deprecating.md`](https://github.com/home-assistant/developers.home-assistant/blob/master/docs/deprecating.md))
— but the distribution excludes it: `[tool.setuptools.packages.find]` sets `include =
["homeassistant*"]`
([`pyproject.toml`](https://github.com/home-assistant/core/blob/dev/pyproject.toml)). I listed every
path under `homeassistant/` matching `test`, `conftest` or `fixture` and found only
`homeassistant/components/assist_satellite/connection_test.py` and unrelated matches. The gap is
filled by a personal repository, not the project: `pytest-homeassistant-custom-component` describes
itself as a "Package to automatically extract testing plugins from Home Assistant for custom
component testing. The goal is to provide the same functionality as the tests in
home-assistant/core."
([`MatthewFlamm/pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)).

| Host | Ships a plugin-author test kit | Where it lives |
|---|---|---|
| pytest | Yes — `pytester`, off by default | `pytest.Pytester`, `pytest.RunResult` |
| Sphinx | Yes — `sphinx.testing.fixtures` | `sphinx/testing/` |
| Litestar | No — app test client only | `litestar/testing/` |
| FastStream | No — per-broker doubles, base under `_internal` | `faststream/<broker>/testing.py` |
| Home Assistant | No — kit exists in-repo, not in the wheel | `tests/` (excluded from the distribution) |

### The scaffold

`cookiecutter-pytest-plugin` is first-party by organisation: it sits in the `pytest-dev` org
alongside pytest itself, and pytest's own plugin guide recommends it.

> Make sure to check out the excellent `cookiecutter-pytest-plugin` project, which is a cookiecutter
> template for authoring plugins.
>
> The template provides an excellent starting point with a working plugin, tests running with tox, a
> comprehensive README file as well as a pre-configured entry-point.

([`doc/en/how-to/writing_plugins.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_plugins.rst))

Its own README calls it a "Minimal Cookiecutter template for authoring pytest plugins that help you
write better programs."
([`README.md`](https://github.com/pytest-dev/cookiecutter-pytest-plugin/blob/main/README.md)). Its
`CONTRIBUTORS.md` names one "Development Lead", Raphael Pierzina (`@hackebrot`), with pytest core
developers among the contributors
([`CONTRIBUTORS.md`](https://github.com/pytest-dev/cookiecutter-pytest-plugin/blob/main/CONTRIBUTORS.md)).
The generated project bakes in the whole kit from the previous sub-question: the output directory is
`pytest-{{cookiecutter.plugin_name}}` and the module is `src/pytest_{{cookiecutter.module_name}}/`
([tree](https://github.com/pytest-dev/cookiecutter-pytest-plugin)), `tests/conftest.py` contains
exactly `pytest_plugins = 'pytester'`
([`tests/conftest.py`](https://github.com/pytest-dev/cookiecutter-pytest-plugin/blob/main/pytest-%7B%7Bcookiecutter.plugin_name%7D%7D/tests/conftest.py)),
and the sample test calls `pytester.makepyfile()`, `pytester.runpytest('--foo=europython2015',
'-v')` and `result.stdout.fnmatch_lines([...])`
([`tests/test_{{cookiecutter.module_name}}.py`](https://github.com/pytest-dev/cookiecutter-pytest-plugin/blob/main/pytest-%7B%7Bcookiecutter.plugin_name%7D%7D/tests/test_%7B%7Bcookiecutter.module_name%7D%7D.py)).
The generated `pyproject.toml` pre-fills `[project.entry-points.pytest11]` and the classifier
`"Framework :: Pytest"`
([`pytest-{{cookiecutter.plugin_name}}/pyproject.toml`](https://github.com/pytest-dev/cookiecutter-pytest-plugin/blob/main/pytest-%7B%7Bcookiecutter.plugin_name%7D%7D/pyproject.toml)).
`cookiecutter.json` also offers a docs tool (`mkdocs`, `sphinx`, `none`) and a licence
([`cookiecutter.json`](https://github.com/pytest-dev/cookiecutter-pytest-plugin/blob/main/cookiecutter.json)).

Home Assistant's scaffold is first-party and in-tree — `script/scaffold` inside
`home-assistant/core` — and the developer docs make it the first instruction a new author reads:
"From a Home Assistant development environment, type the following and follow the instructions:
`python3 -m script.scaffold integration`"
([`creating_component_index.md`](https://developers.home-assistant.io/docs/creating_component_index)).
The same page states what it produces: "When using the scaffold script, it will go past the bare
minimum of an integration. It will include a config flow, tests for the config flow and basic
translation infrastructure to provide internationalization for your config flow." ([same
page](https://developers.home-assistant.io/docs/creating_component_index)). Eleven templates ship:
`backup`, `config_flow`, `config_flow_discovery`, `config_flow_helper`, `config_flow_oauth2`,
`device_action`, `device_condition`, `device_trigger`, `integration`, `reproduce_state` and
`significant_change`
([`script/scaffold/templates/`](https://github.com/home-assistant/core/tree/dev/script/scaffold/templates)).
It is a core-development tool rather than a distributable generator: `main()` opens with `if not
Path("requirements_all.txt").is_file(): print("Run from project root"); return 1`
([`script/scaffold/__main__.py`](https://github.com/home-assistant/core/blob/dev/script/scaffold/__main__.py)),
and the tests it writes import `homeassistant.components.NEW_DOMAIN...` and take the `hass` fixture
that only exists inside the core checkout
([`script/scaffold/templates/config_flow/tests/test_config_flow.py`](https://github.com/home-assistant/core/blob/dev/script/scaffold/templates/config_flow/tests/test_config_flow.py)).

`yo code` is first-party to Visual Studio Code: the npm package is `generator-code`, the repository
is `microsoft/vscode-generator-code`, and `package.json` records `"author": {"name": "VS Code Team",
"url": "https://github.com/Microsoft"}`
([`package.json`](https://github.com/microsoft/vscode-generator-code/blob/main/package.json)). The
README states the output plainly:

> These templates will:
>
> * Create a base folder structure
> * Template out a rough `package.json`
> * Import any assets required for your extension e.g. tmBundles or the VS Code Library
> * For Extensions: Set-up `launch.json` for running your extension and attaching to a process

([`README.md`](https://github.com/microsoft/vscode-generator-code/blob/main/README.md))

It covers extension kinds rather than one shape, with generators for TypeScript and JavaScript
commands, web commands, colour themes, languages, snippets, keymaps, extension packs, notebook
renderers and localizations
([`generators/app/`](https://github.com/microsoft/vscode-generator-code/tree/main/generators/app)).

The other three hosts ship no extension scaffold. Sphinx ships `sphinx-quickstart`, but its man page
scopes it to documentation projects: it "asks some questions about your project and then generates a
complete documentation directory and sample Makefile to be used with sphinx-build(1)"
([`doc/man/sphinx-quickstart.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/man/sphinx-quickstart.rst));
extension authoring is taught instead by tutorials with copyable example modules `helloworld.py`,
`todo.py`, `recipe.py` and `autodoc_intenum.py`
([`doc/development/tutorials/examples/`](https://github.com/sphinx-doc/sphinx/tree/master/doc/development/tutorials/examples)).
Litestar's CLI registers `info`, `run`, `routes`, `version`, `sessions` and `schema` and nothing
that creates a project
([`litestar/cli/main.py`](https://github.com/litestar-org/litestar/blob/main/litestar/cli/main.py)).
FastStream's CLI registers `run`, `publish` and a `docs` group with `serve` and `gen`
([`faststream/_internal/cli/main.py`](https://github.com/ag2ai/faststream/blob/main/faststream/_internal/cli/main.py),
[`faststream/_internal/cli/docs.py`](https://github.com/ag2ai/faststream/blob/main/faststream/_internal/cli/docs.py)).
Litestar's documentation mentions no cookiecutter or template project. FastStream's documents one,
`ag2ai/cookiecutter-faststream`, but it generates an application rather than an extension: "a basic
Python application as a starting point for your project", with pytest, linting, a Dockerfile and
three GitHub Actions workflows
([`docs/docs/en/getting-started/template/index.md`](https://github.com/ag2ai/faststream/blob/main/docs/docs/en/getting-started/template/index.md)).

Django ships two generators, but neither targets a distributable app.
`django/conf/project_template/` holds `manage.py-tpl` beside a `project_name/` directory of
`__init__.py-tpl`, `settings.py-tpl`, `urls.py-tpl`, `asgi.py-tpl` and `wsgi.py-tpl`
([tree](https://github.com/django/django/tree/main/django/conf/project_template)), and
`django/conf/app_template/` holds `__init__.py-tpl`, `admin.py-tpl`, `apps.py-tpl`, `models.py-tpl`,
`views.py-tpl`, `tests.py-tpl` and a `migrations` directory
([tree](https://github.com/django/django/tree/main/django/conf/app_template)) — an app inside a
project, not a package. Turning that app into a distribution is a manual tutorial: the author
creates the `django-polls` parent directory, `README.rst`, `LICENSE`, `pyproject.toml` and
`MANIFEST.in` by hand
([`docs/intro/reusable-apps.txt`](https://github.com/django/django/blob/main/docs/intro/reusable-apps.txt)).

### Name convention and registry

The `pytest-` convention is documented in three places and mandatory in exactly one. The install
instructions use it as the shape of a plugin name, `pip install pytest-NAME`
([`doc/en/how-to/plugins.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/plugins.rst)).
The plugin list describes it as a selection rule: the page "includes PyPI projects whose names begin
with `pytest-` or `pytest_` and a handful of manually selected projects"
([`doc/en/reference/plugin_list.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/reference/plugin_list.rst)).
Only the contribution guide states it as a requirement, and only for adoption into the org — the
first bullet a plugin must satisfy to be transferred to `pytest-dev` is:

> PyPI presence with packaging metadata that contains a `pytest-` prefixed name, version number,
> authors, short and long description.

([`CONTRIBUTING.rst`](https://github.com/pytest-dev/pytest/blob/main/CONTRIBUTING.rst))

Nothing in pytest keys off the `pytest-` prefix of a distribution name — `-p pytester` and
`pytest_plugins` load by module or entry-point name. Discovery is by entry point — "pytest looks up
the `pytest11` entrypoint to discover its plugins" — and findability is by trove classifier: "Make
sure to include `Framework :: Pytest` in your list of PyPI classifiers to make it easy for users to
find your plugin."
([`doc/en/how-to/writing_plugins.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_plugins.rst))

Django recommends a prefix and mandates something else:

> When choosing a name for your package, check PyPI to avoid naming conflicts with existing
> packages. We recommend using a `django-` prefix for package names, to identify your package as
> specific to Django, and a corresponding `django_` prefix for your module name. For example, the
> `django-ratelimit` package contains the `django_ratelimit` module.
>
> Application labels (that is, the final part of the dotted path to application packages) *must* be
> unique in `INSTALLED_APPS`.

([`docs/intro/reusable-apps.txt`](https://github.com/django/django/blob/main/docs/intro/reusable-apps.txt))

Sphinx documents no distribution-name convention. It points at classifiers — `Framework :: Sphinx ::
Extension` and `Framework :: Sphinx :: Theme` — and at a GitHub organisation that is explicitly
optional: "If you wish to include your extension in this organization, simply follow the
instructions provided in the github-administration project. This is optional and there are several
extensions hosted elsewhere."
([`doc/usage/extensions/index.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/usage/extensions/index.rst))

Home Assistant does not name a distribution at all; its unit of identity is the integration domain,
and it is immutable:

> The domain is a short name consisting of characters and underscores. This domain has to be unique
> and cannot be changed. Example of the domain for the mobile app integration: `mobile_app`. The
> domain key has to match the directory this file is in.

([`creating_integration_manifest.md`](https://developers.home-assistant.io/docs/creating_integration_manifest))

The brands repository is the asset registry behind that domain: `home-assistant/brands` "holds the
icons and logos for all the brands Home Assistant supports", with `core_integrations/` for
integrations bundled with core and a now-legacy `custom_integrations/` folder
([`README.md`](https://github.com/home-assistant/brands/blob/master/README.md)). For a new core
integration it is mandatory, because the bronze tier is "the baseline standard and requirement for
all new integrations"
([`integration-quality-scale/index.md`](https://developers.home-assistant.io/docs/core/integration-quality-scale/))
and the bronze `brands` rule closes the door: "## Exceptions — There are no exceptions to this
rule."
([`rules/brands.md`](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/brands)).
For a custom integration it stopped being mandatory: "Before Home Assistant 2026.3, custom
integrations were also required to add their brand images to the brands repository. Starting with
Home Assistant 2026.3, custom integrations can include their own brand images by adding a `brand/`
directory inside the integration directory."
([`brand_images.md`](https://developers.home-assistant.io/docs/core/integration/brand_images))

Litestar and FastStream document no naming convention. Litestar's first-party plugins do carry a
`litestar-` prefix — `litestar-piccolo` is described in the database docs as "a plugin called
`litestar-piccolo` for working with this ORM"
([`docs/usage/databases/piccolo.rst`](https://github.com/litestar-org/litestar/blob/main/docs/usage/databases/piccolo.rst))
— but the CLI-extension guide's `name="my-litestar-plugin"` is an illustrative `setup()` call, not a
stated rule
([`docs/usage/cli.rst`](https://github.com/litestar-org/litestar/blob/main/docs/usage/cli.rst)).

No host reserves a PyPI namespace, and none can. PyPI's own organization-accounts FAQ states: "No,
organizations accounts do not support namespaces. While this is a feature that is on our to-do
list, we do not have any immediate development plans for namespaces."
([PyPI docs](https://docs.pypi.org/organization-accounts/org-acc-faq/)). The mechanism exists on
paper only: [PEP 752](https://peps.python.org/pep-0752/), "Implicit namespaces for package
repositories", "specifies a way for organizations to reserve package name prefixes for future
uploads" and carries `Status: Accepted` with `Resolution: 29-Jun-2026`, while the PyPI-specific
policy in [PEP 755](https://peps.python.org/pep-0755/) is still `Status: Draft`. Every host in this
survey therefore relies on convention alone.

### The plugin-API reference page

Two of the six publish a plugin-API reference separated from user documentation. Sphinx splits the
tree: `doc/usage/` is for people writing documents, `doc/extdev/` is titled "Sphinx API" and opens
"Since many projects will need special features in their documentation, Sphinx is designed to be
extensible on several levels"
([`doc/extdev/index.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/extdev/index.rst)).
Its stability promise is stated at the head of the deprecated-APIs page in that same section:

> On developing Sphinx, we are always careful to the compatibility of our APIs. But, sometimes, the
> change of interface are needed for some reasons. In such cases, we've marked them as deprecated.
> And they are kept during the two major versions.

([`doc/extdev/deprecated.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/extdev/deprecated.rst))

The referenced policy is numeric: "If a feature is deprecated in a release A.x, it will continue to
work in all A.x.x versions (for all versions of x). It will continue to work in all B.x.x versions
but raise deprecation warnings. Deprecated features will be removed at the C.0.0. It means the
deprecated feature will work during 2 MAJOR releases at least."
([`doc/internals/release-process.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/internals/release-process.rst)),
and the versioning rule ties the major number to it: "The major version part should be incremented
for incompatible behavior change and public API updates." ([same
page](https://github.com/sphinx-doc/sphinx/blob/master/doc/internals/release-process.rst))

Home Assistant goes further and splits the site: user documentation is `home-assistant.io`, and the
developer documentation is a separate Docusaurus site whose config sets `url:
"https://developers.home-assistant.io"`
([`docusaurus.config.js`](https://github.com/home-assistant/developers.home-assistant/blob/master/docusaurus.config.js)).
Its promise is a period, stated as a table, and it defines its own scope:

> Anything other integrations import or subclass counts as a core API, whether it lives in
> `homeassistant/helpers/`, `homeassistant/const.py`, or an entity platform such as
> `homeassistant/components/sensor/`. Deprecating one affects custom integration authors, who need a
> release cycle of their own to react. These get 12 months, and an announcement post on this site's
> blog naming the replacement if applicable and the removal version.

([`deprecating.md`](https://developers.home-assistant.io/docs/deprecating))

The same page states the floor and its asymmetry: "Any removals must be deprecated first. This
holds even when you believe only a handful of users are affected" and "A deprecation period may be
extended if the ecosystem has not caught up, but it is never shortened."
([same page](https://developers.home-assistant.io/docs/deprecating))

pytest does not separate the pages. There is one `API Reference`, and hooks are a section inside it,
introduced as "Reference to all hooks which can be implemented by conftest.py files and plugins"
([`doc/en/reference/reference.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/reference/reference.rst)).
The promise lives in a policy document that names plugin authors as the population it protects:

> True breakage should only be considered when a normal transition is unreasonably unsustainable and
> would offset important developments or features by years. In addition, they should be limited to
> APIs where the number of actual users is very small (for example, only impacting some plugins) and
> can be coordinated with the community in advance.

([`doc/en/backwards-compatibility.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/backwards-compatibility.rst))

Its ordinary case is the transitional one: "We will only start the removal of deprecated
functionality in major releases (e.g., if we deprecate something in 3.0, we will start to remove it
in 4.0), and keep it around for at least two minor releases"
([same page](https://github.com/pytest-dev/pytest/blob/main/doc/en/backwards-compatibility.rst)).

Django keeps one documentation set and makes membership of it the definition of stable:

> All the public APIs (everything in this documentation) will not be moved or renamed without
> providing backwards-compatible aliases.
>
> In general, everything covered in the documentation -- with the exception of anything in the
> internals area is considered stable.

([`docs/misc/api-stability.txt`](https://github.com/django/django/blob/main/docs/misc/api-stability.txt))

Litestar publishes a `plugins` page inside its single API reference, generated from
`litestar.plugins`
([`docs/reference/plugins/index.rst`](https://github.com/litestar-org/litestar/blob/main/docs/reference/plugins/index.rst)),
with a separate narrative guide
([`docs/usage/plugins/index.rst`](https://github.com/litestar-org/litestar/blob/main/docs/usage/plugins/index.rst)).
I found no stability statement in the repository; the contribution guide defers to an external page
and to semver: "The version number should follow semantic versioning and PEP 440"
([`CONTRIBUTING.rst`](https://github.com/litestar-org/litestar/blob/main/CONTRIBUTING.rst)). The
external page it names, `https://litestar.dev/about/litestar-releases#version-numbering`, returns
HTTP 404 when fetched, with and without a trailing slash, so the promise behind that link could not
be read. The tree is on `version = "3.0.0b0"`
([`pyproject.toml`](https://github.com/litestar-org/litestar/blob/main/pyproject.toml)).

FastStream publishes no plugin-API page, because there is no plugin API — see the search above.

### The logger name

Two hosts instruct the author, and one of them removes the choice. Sphinx supplies the logger
factory and states why:

> Get logger wrapped by `sphinx.util.logging.SphinxLoggerAdapter`.
>
> Sphinx logger always uses `sphinx.*` namespace to be independent from settings of root logger. It
> ensures logging is consistent even if a third-party extension or imported application resets
> logger settings.
>
> Example usage::
>
>     >>> from sphinx.util import logging
>     >>> logger = logging.getLogger(__name__)

([`sphinx/util/logging.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/util/logging.py))

The prefix is not advice. `NAMESPACE = 'sphinx'`, the implementation is `logger =
logging.getLogger(NAMESPACE + '.' + name)`, and the comment above it reads `# add sphinx prefix to
name forcely` ([same
file](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/util/logging.py)). The function is
part of the extension-development section, published as the "Logging API"
([`doc/extdev/logging.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/extdev/logging.rst)).

Django gives the instruction as a named documentation section, "Use logger namespacing", and works
the example in an app:

> The namespace of a logger instance is defined using `getLogger()`. For example in `views.py` of
> `my_app`::
>
>     logger = logging.getLogger(__name__)
>
> will create a logger in the `my_app.views` namespace. `__name__` allows you to organize log
> messages according to their provenance within your project's applications automatically. It also
> ensures that you will not experience name collisions.

([`docs/howto/logging.txt`](https://github.com/django/django/blob/main/docs/howto/logging.txt))

The same page states the choice earlier: "Provide the `getLogger()` method with a name to identify
it and the records it emits. A good option is to use `__name__`"
([same page](https://github.com/django/django/blob/main/docs/howto/logging.txt)).

Home Assistant instructs on the message, not on the logger name, and gets the namespace for free
because the convention is uniform. The guideline is:

> There is no need to add the platform or component name to the log messages. This will be added
> automatically.

([`development_guidelines.md`](https://developers.home-assistant.io/docs/development_guidelines))

The worked output on that page shows what "automatically" means — `2017-05-01 14:28:07 ERROR
[homeassistant.components.sensor.arest] No route to device: 192.168.0.18` ([same
page](https://developers.home-assistant.io/docs/development_guidelines)) — and every documented
integration module opens with `_LOGGER = logging.getLogger(__name__)`
([`dev_101_states.md`](https://developers.home-assistant.io/docs/dev_101_states),
[`integration_fetching_data.md`](https://developers.home-assistant.io/docs/integration_fetching_data)).
Home Assistant does have one explicit logger-name field, and it is for the author's *dependencies*
rather than the author's own code: "The `loggers` field is a list of names that the integration's
requirements use for their getLogger calls."
([`creating_integration_manifest.md`](https://developers.home-assistant.io/docs/creating_integration_manifest))

pytest gives no instruction. Its plugin guide covers hooks, entry points, assertion rewriting,
markers and testing, and never mentions logging
([`doc/en/how-to/writing_plugins.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_plugins.rst)),
nor does the hook-writing guide
([`doc/en/how-to/writing_hook_functions.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/writing_hook_functions.rst)).
`doc/en/how-to/logging.rst` is about capturing log records inside a test with `caplog`, and the only
`getLogger` call on the page is `logging.getLogger().info("boo %s", "arg")` in a capture example
([`doc/en/how-to/logging.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/logging.rst)).
Searching all of `doc/en/` for `getLogger` returns that one line and nothing else.

Litestar and FastStream give no instruction either. Grepping `litestar/` and `docs/` for
`logger_name` and `logger name` returns nothing, and the plugin guide names no logger — its one
logging-adjacent example, a `RouteLoggerPlugin`, calls `print()`
([`docs/usage/plugins/index.rst`](https://github.com/litestar-org/litestar/blob/main/docs/usage/plugins/index.rst)).
FastStream's logging page teaches the opposite direction — the application hands the broker a logger
of its own, `logger = logging.getLogger("my_logger")` — and never names a namespace
([`docs/docs/en/getting-started/observability/logging.md`](https://github.com/ag2ai/faststream/blob/main/docs/docs/en/getting-started/observability/logging.md)).

### Configuration field names

Four hosts treat a configuration field name as versioned API, each by a different mechanism.

Home Assistant states it as a period, and gives configuration keys the same standing as entities
and actions:

> | Who is affected | Minimum period | | --- | --- | | Users (YAML configuration, actions, entities,
> attributes, integrations) | 6 months | | Developers (constants, helpers, entity properties,
> platform APIs used by custom integrations) | 12 months |

([`deprecating.md`](https://developers.home-assistant.io/docs/deprecating))

A single key gets its own procedure — "we raise a repair issue in `async_setup`, where the YAML is
read, and only when the key is actually present. The key keeps working until the deprecation period
is over" — and removal does not mean deletion: "Once the period is over, do not just drop the key
from the schema. Leave `cv.removed(CONF_IPV6)` in its place, which tells the user the option is gone
instead of failing with a generic validation error."
([same page](https://developers.home-assistant.io/docs/deprecating))

Sphinx lists configuration value names in the same table as code APIs, with the same `Deprecated`
and `Removed` columns — `autodoc_default_flags` (1.8 → 4.0, replaced by `autodoc_default_options`),
`viewcode_import` marked `(config value)` (1.8 → 3.0), and `source_parsers` (1.8 → 3.0)
([`doc/extdev/deprecated.rst`](https://github.com/sphinx-doc/sphinx/blob/master/doc/extdev/deprecated.rst)).
A rename keeps both names live in code: `Config.__setattr__` carries the comment `# Ensure aliases
update their counterpart.` and mirrors `master_doc` to `root_doc` and `copyright` to
`project_copyright` in both directions
([`sphinx/config.py`](https://github.com/sphinx-doc/sphinx/blob/master/sphinx/config.py)).

Django covers settings names by the general rule rather than a settings-specific one: settings are
documented in `docs/ref/settings.txt`
([reference](https://github.com/django/django/blob/main/docs/ref/settings.txt)), and "everything
covered in the documentation" is stable and "will not be moved or renamed without providing
backwards-compatible aliases"
([`docs/misc/api-stability.txt`](https://github.com/django/django/blob/main/docs/misc/api-stability.txt)).
The machinery matches: settings names raise the same `RemovedInDjango2028Warning` class as code,
with messages written per name — `"The USE_BLANK_CHOICE_DASH setting is deprecated. If you wish to
define your own default blank choice label, override django.db.models.fields.BLANK_CHOICE_LABEL in
your app's ready() method."` and `"The {name} setting is deprecated. Migrate to MAILERS before
Django 2028."`
([`django/conf/__init__.py`](https://github.com/django/django/blob/main/django/conf/__init__.py)) —
and the deprecation timeline enumerates settings by name alongside functions and classes
([`docs/internals/deprecation.txt`](https://github.com/django/django/blob/main/docs/internals/deprecation.txt)).
The policy is release-counted: "If a feature is deprecated in feature release A.x, it will continue
to work in all A.x versions (for all versions of x) but raise warnings. Deprecated features will be
removed in the B.0 release, or B.1 for features deprecated in the last A.x feature release"
([`docs/internals/release-process.txt`](https://github.com/django/django/blob/main/docs/internals/release-process.txt)).

pytest applies the alias pattern to its own option names. Renaming three strictness options in 9.0
added new names without removing old ones: "Added `strict_xfail` as an alias to the `xfail_strict`
option, `strict_config` as an alias to the `--strict-config` flag, and `strict_markers` as an alias
to the `--strict-markers` flag. This makes all strictness options consistently have configuration
options with the prefix `strict_`."
([`doc/en/changelog.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/changelog.rst)). An
option name can also be deprecated over naming and then reinstated. The deprecations page heads the
entry "The `--strict` command-line option (reintroduced)", marks it `.. deprecated:: 6.2` and `..
versionchanged:: 9.0`, gives the reason as naming — it "had been deprecated in favor of
`--strict-markers`, which better conveys what the option does" — and then records that "In version
8.1, we accidentally un-deprecated `--strict`"
([`doc/en/deprecations.rst`](https://github.com/pytest-dev/pytest/blob/main/doc/en/deprecations.rst)).

Litestar and FastStream state nothing. And no host in this survey says anything about the stability
of a *third-party plugin's own* configuration field names: every rule found governs the host's own
settings. Home Assistant comes closest to covering the plugin's fields, because a custom
integration's YAML keys are user-facing configuration under the same 6-month rule, and the same
page tells the author which mechanism to use
([`deprecating.md`](https://developers.home-assistant.io/docs/deprecating)).

### Comparison

| Host | Contract test kit | Scaffold | Name convention | Separate plugin-API reference | Says anything about logger names |
|---|---|---|---|---|---|
| pytest | Yes — `pytester`, off by default, in-tree | Yes — `cookiecutter-pytest-plugin`, `pytest-dev` org | Yes — `pytest-` prefix; mandatory only for org adoption | No — hooks are a section of the one API Reference | No |
| Sphinx | Yes — `sphinx.testing.fixtures`, since 1.6 | No extension scaffold; `sphinx-quickstart` targets doc projects | No name convention; trove classifiers plus an optional GitHub org | Yes — `doc/extdev/`, "Sphinx API" | Yes — `sphinx.util.logging.getLogger`, forces a `sphinx.*` prefix |
| Home Assistant | No — kit is in `tests/`, excluded from the wheel | Yes — `python3 -m script.scaffold`, core-checkout only | Domain, not a distribution name; brands repo mandatory for core | Yes — a separate site, `developers.home-assistant.io` | Indirectly — `logging.getLogger(__name__)` everywhere, plus a `loggers` manifest field for dependencies |
| Django | Partly — `django.test` plus a documented `runtests.py` recipe | `startapp`/`startproject` templates; no reusable-app scaffold | Yes — `django-` recommended; unique app label required | No — one doc set; `internals/` excluded from the promise | Yes — "Use logger namespacing", `__name__` |
| Litestar | No — app test client only | No | No documented convention | Partly — a `plugins` page inside the one API reference | Not found |
| FastStream | No — no plugin surface; broker doubles under `_internal` | No | No documented convention | No | Not found |

Django's row needs one qualification: `django.test` is an application-testing API, and the plugin
angle is a documented recipe rather than a harness — "If you are writing a reusable application you
may want to use the Django test runner to run your own test suite and thus benefit from the Django
testing infrastructure", followed by a `runtests.py` that calls `get_runner(settings)`
([`docs/topics/testing/advanced.txt`](https://github.com/django/django/blob/main/docs/topics/testing/advanced.txt)).

### What §5 establishes

- A contract test kit is rare and, where it exists, it is a pytest plugin the author opts into.
  Both instances — pytest's `pytester` and `sphinx.testing.fixtures` — are activated by
  `pytest_plugins = [...]`, and both are documented on the extension-authoring page, not the
  user-testing page.
- The strongest kit is a black-box one. `pytester` writes a throwaway project, runs the host over
  it in-process or as a subprocess, and asserts on outcomes and output; it does not expose the
  host's internals. `inline_run()` and `HookRecorder` exist as the documented escape hatch when
  stdout matching is not enough.
- Shipping a kit and shipping it *in the distribution* are separate decisions. Home Assistant's kit
  is complete and its scaffold generates tests that use it, yet `include = ["homeassistant*"]`
  keeps it out of the wheel, so a third-party author gets it from a personal repository instead.
- A scaffold's value is that it pre-wires the conventions the author would otherwise have to find:
  `cookiecutter-pytest-plugin` bakes in the `pytest-` directory name, the `pytest11` entry point,
  the `Framework :: Pytest` classifier and a `conftest.py` that enables `pytester`.
- A scaffold can be a core-development tool rather than an author tool. Home Assistant's refuses to
  run outside a core checkout, and the tests it writes need a fixture the distribution does not
  ship.
- A name convention is enforced by discovery, never by the loader. pytest loads by entry point and
  finds by classifier; the `pytest-` prefix is binding only as an admission requirement to the
  `pytest-dev` organisation.
- Namespace reservation is not an option. PyPI does not implement namespaces, PEP 752 is accepted
  but PEP 755's PyPI policy is still a draft, so convention plus a trove classifier is the whole
  mechanism available to any host today.
- A separate plugin-API reference correlates with a longer stated deprecation period. Sphinx keeps
  extension APIs across two major releases; Home Assistant gives developer-facing APIs 12 months
  against 6 for user-facing ones. The hosts with one documentation set — pytest and Django — instead
  define the promise by membership of the docs.
- Home Assistant is the only host that states its promise in months rather than releases, and the
  only one that says the period "is never shortened".
- Only Sphinx removes the logger-name decision from the author, by supplying the factory and forcing
  a `sphinx.` prefix. Django and Home Assistant document `__name__` and let the module path do the
  namespacing. pytest says nothing at all.
- A logger name and a log *message* are separate conventions. Home Assistant's rule is about the
  message — do not repeat the component name, because the logger name already carries it — which
  only works because the logger name is uniform.
- Configuration field names are versioned API at four of six hosts, and the enforcement mechanism
  is an alias at three of them: Sphinx mirrors `master_doc`/`root_doc` in `Config.__setattr__`,
  Django promises no rename "without providing backwards-compatible aliases", and pytest added
  `strict_xfail` beside `xfail_strict` rather than replacing it.
- Removing a configuration key is not the same as deleting it. Home Assistant requires
  `cv.removed(CONF_IPV6)` to stay behind so the user gets a specific message instead of a generic
  validation error.
- No host says anything about the stability of a third-party plugin's *own* configuration field
  names. Every rule found governs the host's settings; Home Assistant is the only one whose rule
  reaches the plugin's keys, and it does so because those keys are user-facing YAML.

## 6 What the evidence supports

Each section closes with what its own hosts establish. These are the patterns that hold across all
five, and they are what a decision can rest on.

- **A host can refuse a conflict only where it owns a namespace.** Django, Litestar, Sphinx and
  pluggy raise on duplicate identity because each keeps a dictionary keyed by the contested name;
  where the key is derived rather than declared — a Litestar plugin's concrete class, a pydantic
  entry-point value — the collision resolves in silence (§4). The version, the capability name and
  the lookup key of §1, §3 and §4 are therefore one design act: naming what the host keys on.
- **Nobody versions a plugin API in process.** Of the six hosts with any gate, only Terraform
  versions the interface independently of both release numbers, and it runs its plugins out of
  process. Of the five in-process Python hosts read, four ask for no number at all, and the one that
  hands over its own version — mypy — delegates the whole decision and enforces nothing (§1). Python
  packaging offers no field to borrow: `Provides-Dist` has the right shape and sits under "Rarely
  Used Fields" with the specification conceding "it isn't at all clear how tools should interpret
  them".
- **The gate that catches host-plugin skew in Python is structural, not numeric.** pluggy's
  per-argument set difference against the hookspec, Litestar's `isinstance` against six
  `@runtime_checkable` Protocols, and mypy's six-step ladder over the shape of the entry point are
  the three that actually fire, and none of them compares a version (§1).
- **A written compatibility window carries the weight a number does not, and warnings alone have a
  recorded failure.** Sphinx keeps a deprecated feature "during 2 MAJOR releases at least", Django
  promises no rename "without providing backwards-compatible aliases", and pytest 8.1.0 was yanked
  from PyPI because "it broke some plugins without the proper warning period, due to some warnings
  not showing up as expected" (§1). A host that omits the gate ends up maintaining a per-plugin
  blocklist after each incident, which is what `BLOCKED_CUSTOM_INTEGRATIONS` is.
- **Unwinding a partial start is solved in the standard library; reporting a failed stop is not.**
  `contextlib.AsyncExitStack` unwinds what already entered and documents the promise; with several
  `__aexit__` calls raising it is single-exception and silently lossy. `asyncio.TaskGroup` documents
  the opposite answer — grouping into `BaseExceptionGroup`, cancellation subordinate to real errors
  — so a host that wants every plugin that failed to stop named has to collect the failures itself
  (§2).
- **A typed start-up taxonomy earns its place only through the member that means "not ready yet".**
  Home Assistant's four members differ by *host reaction* rather than by cause, and exactly one of
  them produces a second attempt; every other surveyed host, and a plain `False` return, is terminal
  (§2). Where `False` and `raise` nearly coincide, the failure reaches the operator without a
  reason.
- **The sanctioned channel between plugins is always a host-owned lookup, and the type-keyed form
  has no Python precedent.** A registry object, a dictionary on the core object, a label registry, a
  loader call, or an object the plugin handed the host at activation — no host documents plugins
  importing one another, and type-keyed injection between extension units is documented only outside
  Python, by Spring's bean container and NestJS's module exports (§3). A declared dependency buys
  order, not data, so a host that promises order still owes the caller a presence check.
- **What a plugin may not do clusters on three things, and is documented rather than prevented.**
  Process-global state, side effects during registration, and internal setters are the categories
  every host prohibits first (§4). Sphinx's `parallel_read_safe` shows the price of a capability
  flag whose absence degrades a shared path: one undeclared extension serialises the whole build.
- **A contract kit is rare, a scaffold rarer, and PyPI has no namespaces.** Two of the surveyed
  hosts ship a kit — pytest's `pytester` and `sphinx.testing.fixtures` — both activated by an
  explicit `pytest_plugins` line and both documented on the extension-authoring page. Home Assistant
  has a complete kit and keeps it out of the wheel. PEP 752 is accepted while PEP 755's index policy
  is still a draft, so a convention plus a trove classifier is the whole mechanism available (§5).
- **Configuration field names are versioned API at four of six hosts, and the enforcement is an
  alias.** Nobody says anything about the stability of a *third-party* plugin's own field names, and
  only Sphinx removes the logger-name decision from the plugin author, by supplying the factory and
  forcing its own prefix (§5).

## Sources

Every claim above carries its own link inline. This section names the trees and reference pages read
end to end.

Sphinx:

- <https://github.com/sphinx-doc/sphinx> — `sphinx/application.py`, `sphinx/registry.py`,
  `sphinx/extension.py`, `sphinx/environment/__init__.py`, `sphinx/config.py`,
  `sphinx/builders/__init__.py`, `sphinx/util/docutils.py`, `sphinx/util/logging.py`,
  `sphinx/testing/fixtures.py`, `sphinx/testing/util.py`, `sphinx/__init__.py`
- <https://www.sphinx-doc.org/en/master/extdev/index.html> ·
  <https://www.sphinx-doc.org/en/master/usage/configuration.html> ·
  <https://www.sphinx-doc.org/en/master/internals/release-process.html> ·
  <https://www.sphinx-doc.org/en/master/extdev/deprecated.html>

Home Assistant:

- <https://github.com/home-assistant/core> — `homeassistant/loader.py`,
  `homeassistant/bootstrap.py`, `homeassistant/config_entries.py`, `homeassistant/exceptions.py`,
  `homeassistant/const.py`, `homeassistant/core_config.py`,
  `homeassistant/helpers/entity_platform.py`, `homeassistant/helpers/event.py`,
  `homeassistant/util/hass_dict.py`, `script/hassfest/manifest.py`,
  `script/hassfest/requirements.py`, `script/hassfest/dependencies.py`, `script/scaffold/`
- <https://developers.home-assistant.io/docs/creating_integration_manifest> ·
  <https://developers.home-assistant.io/docs/config_entries_index/> ·
  <https://developers.home-assistant.io/docs/integration_setup_failures/> ·
  <https://developers.home-assistant.io/docs/api_lib_index/> ·
  <https://developers.home-assistant.io/blog/2021/01/29/custom-integration-changes>
- <https://github.com/home-assistant/brands> ·
  <https://github.com/MatthewFlamm/pytest-homeassistant-custom-component>

pytest and pluggy:

- <https://github.com/pytest-dev/pytest> — `src/_pytest/config/__init__.py`,
  `src/_pytest/pytester.py`, `src/_pytest/fixtures.py`, `src/_pytest/main.py`,
  `src/_pytest/stash.py`, `src/_pytest/warning_types.py`, `src/_pytest/assertion/rewrite.py`
- <https://github.com/pytest-dev/pluggy> — `src/pluggy/_manager.py`, `src/pluggy/_hooks.py`,
  `src/pluggy/_callers.py`, `docs/index.rst`
- <https://docs.pytest.org/en/stable/how-to/writing_plugins.html> ·
  <https://docs.pytest.org/en/stable/reference/reference.html> ·
  <https://docs.pytest.org/en/stable/backwards-compatibility.html> ·
  <https://docs.pytest.org/en/stable/changelog.html> ·
  <https://github.com/pytest-dev/pytest/issues/12069>
- <https://github.com/pytest-dev/cookiecutter-pytest-plugin>

Django:

- <https://github.com/django/django> — `django/apps/registry.py`, `django/conf/__init__.py`,
  `django/core/exceptions.py`, `django/db/backends/utils.py`, `django/__init__.py`,
  `docs/ref/applications.txt`, `docs/misc/api-stability.txt`

Litestar:

- <https://github.com/litestar-org/litestar> — `litestar/plugins/base.py`,
  `litestar/plugins/__init__.py`, `litestar/app.py`, `litestar/config/app.py`, `litestar/di.py`,
  `litestar/routes/http.py`, `litestar/_asgi/asgi_router.py`,
  `litestar/_asgi/routing_trie/validate.py`, `litestar/cli/main.py`,
  `litestar/exceptions/base_exceptions.py`, `litestar/exceptions/http_exceptions.py`,
  `litestar/testing/__init__.py`
- <https://docs.litestar.dev/latest/usage/plugins/index.html>

mypy and pydantic:

- <https://github.com/python/mypy> — `mypy/build.py`, `mypy/plugin.py`, `mypy/version.py`,
  `mypy/errors.py`, `mypy/util.py`, `mypy/dmypy_server.py`, `mypy/dmypy/client.py`,
  `docs/source/extending_mypy.rst`, `docs/source/config_file.rst`,
  `docs/source/command_line.rst`, `test-data/unit/check-custom-plugin.test`,
  `test-data/unit/daemon.test`
- <https://github.com/pydantic/pydantic> — `pydantic/mypy.py`, `pydantic/v1/mypy.py`,
  `pydantic/plugin/__init__.py`, `pydantic/plugin/_loader.py`, `pydantic/version.py`

Other Python hosts:

- <https://github.com/ag2ai/faststream> — `faststream/_internal/application.py`,
  `faststream/asgi/app.py`, `faststream/_internal/testing/broker.py`, the per-broker
  `testing.py` modules, `faststream/exceptions.py`, `faststream/_internal/cli/main.py`
- <https://github.com/encode/starlette> — `starlette/routing.py` ·
  <https://github.com/encode/uvicorn> — `uvicorn/server.py`, `uvicorn/config.py`
- <https://github.com/aiogram/aiogram> — `aiogram/dispatcher/dispatcher.py`,
  `aiogram/dispatcher/router.py` · <https://github.com/Rapptz/discord.py> ·
  <https://github.com/python-telegram-bot/python-telegram-bot> · <https://github.com/django/asgiref>

The language and the packaging specifications:

- <https://docs.python.org/3/library/contextlib.html> ·
  <https://docs.python.org/3/library/asyncio-task.html> ·
  <https://docs.python.org/3/c-api/stable.html>
- <https://github.com/python/cpython> — `Lib/contextlib.py`, `Lib/asyncio/taskgroups.py`
- <https://packaging.python.org/en/latest/specifications/core-metadata/> ·
  <https://packaging.python.org/en/latest/specifications/entry-points/> ·
  <https://docs.pypi.org/project-management/namespaces/>
- <https://peps.python.org/pep-0384/> · <https://peps.python.org/pep-0425/> ·
  <https://peps.python.org/pep-0752/> · <https://peps.python.org/pep-0755/>

Hosts outside Python:

- <https://code.visualstudio.com/api/references/extension-manifest> ·
  <https://code.visualstudio.com/api/references/vscode-api> · <https://github.com/microsoft/vscode>
  — `src/vs/platform/extensions/common/extensionValidator.ts` ·
  <https://github.com/microsoft/vscode-vsce> · <https://github.com/microsoft/vscode-generator-code>
- <https://docs.ansible.com/ansible/latest/dev_guide/developing_collections_structure.html> ·
  <https://github.com/ansible/ansible> — `lib/ansible/plugins/loader.py`,
  `lib/ansible/config/base.yml`
- <https://docs.obsidian.md/Reference/Manifest> · <https://docs.obsidian.md/Reference/Versions>
- <https://developer.hashicorp.com/terraform/plugin/terraform-plugin-protocol> ·
  <https://github.com/hashicorp/terraform> · <https://github.com/hashicorp/go-plugin>
- <https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html> ·
  <https://docs.nestjs.com/modules>
