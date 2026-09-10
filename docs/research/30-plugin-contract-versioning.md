# 30. How a plugin host versions the contract it offers

**Question.** How does a plugin host version the contract it offers plugins, separately from its own
release version — what carries the number, at what granularity, by which comparison rule, checked
when, failing how, and moved by whom?

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

Ten hosts were read for a number that names the contract offered to plugins. One has it.

The decision this note is evidence for is #102.

Findings only, and no recommendation. Sources are primary — project source at the default branch,
reference and developer documentation, PEPs, the Python packaging specifications,
`docs.python.org`, PyPI metadata and project issue trackers — read on 2026-09-10. Anything a
primary source did not confirm is marked **[unverified]**.

Eight hosts were read for a number that names the contract offered to plugins, separately from the
host's own release version. One has it. Five version the host release or the plugin release instead,
and two have no number at all.

## 1 Sphinx: three numbers, none of them the API

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

## 2 Home Assistant: the plugin's version, and a host-maintained blocklist

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

## 3 VS Code, Ansible, Obsidian: the host release as a range

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

## 4 Terraform: the only real protocol number

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

## 5 pytest: no plugin API version, by design

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

## 6 Python packaging: nothing, having looked

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

## 7 What the standard library offers a host that must compare versions itself

The hosts above split into two groups: those that delegate version comparison to `packaging` or to
`AwesomeVersion`, and those that hand-roll it and carry a quiet bug. A host whose own dependency
policy admits neither library is left with what the language ships, and the language ships less
than it used to.

**The one version-comparison helper the standard library had is gone, at 3.12.** `distutils.version`
held `LooseVersion` and `StrictVersion`; [PEP 632](https://peps.python.org/pep-0632/) removed the
whole `distutils` package, and Python 3.12's own release notes list it among the important removals:
"Of note, the `distutils` package has been removed from the standard library", with
"[PEP 632](https://peps.python.org/pep-0632/): Remove the `distutils` package"
([*What's New In Python 3.12*](https://docs.python.org/3/whatsnew/3.12.html)). The PEP's migration
advice names the replacement in one line, under the heading for modules whose substitute is a
Python Packaging Authority package rather than a standard-library one:

> `distutils.version` — use the `packaging` package

**`importlib.metadata` reads a version and does not order one.** `version(distribution_name)`
returns the distribution version as the string recorded in the metadata, and the module documents no
comparison, parsing or specifier API at all
([`importlib.metadata`](https://docs.python.org/3/library/importlib.metadata.html)).

**What is left is tuple comparison.** The language reference states it as a rule of the built-in
containers — "Sequences compare lexicographically using comparison of corresponding elements"
([*Comparisons*](https://docs.python.org/3/reference/expressions.html#comparisons)) — and the
standard library uses it for exactly this purpose itself: the documentation of `sys.version_info`
compares it as a tuple, `sys.version_info >= (3, 5)`
([`sys.version_info`](https://docs.python.org/3/library/sys.html#sys.version_info)). An integer, or
a tuple of integers, is orderable with no library and no parser; a version *string* is not.

**The library the PEP points at costs one dependency and no transitive ones.** `packaging` 26.3
declares `requires_dist: null` and `requires_python: ">=3.9"` — no runtime dependencies at all
([PyPI JSON](https://pypi.org/pypi/packaging/json)). Whether a host may take it is therefore a
question of its own policy rather than of what the dependency would drag in.

## 8 The incident: pytest 8.1.0, yanked for breaking plugins

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

## 9 Comparison across hosts

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

## 10 mypy: the host hands the plugin its version, then hashes the plugin behind its back

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

## 11 The worked example: pydantic's mypy plugin declares a cache generation, not a compatibility range

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

## 12 The load-time gate that is structural rather than numeric: pluggy

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

## 13 The Protocol-shaped hosts: no version member anywhere

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

## 14 The four in-process Python hosts, compared

| Host | Load-time gate | What the plugin declares | Comparison | Failure | Compatibility promise |
|---|---|---|---|---|---|
| mypy | six shape checks on the entry point, then a SHA-1 of the module file | nothing required; an optional module `__version__` for cache invalidation only | none on any version; dict inequality of `{module: "ver:sha1"}` for the cache | `CompileError` at the config-file line; a raising entry point becomes a traceback | "there are no guarantees about backwards compatibility […] Backwards incompatible changes may be made without a deprecation period" |
| pluggy / pytest | `_verify_hook` at `register()`; `check_pending()` later | hook argument names; `optionalhook=True` to opt out; `specname` to rename | set difference of argument names against the hookspec | `PluginValidationError`, e.g. `Argument(s) {notinspec} are declared in the hookimpl but can not be found in the hookspec` | pytest's written policy, "at least two minor releases" |
| Litestar | `isinstance` against six `@runtime_checkable` protocols | which protocols it satisfies, structurally | none | no failure — a plugin matching nothing is stored and never called | `.. deprecated:: 2.15` markers on the protocols themselves |
| pydantic | none | nothing; `PydanticPluginProtocol` is not `@runtime_checkable` | none | `warnings.warn` on `ImportError`/`AttributeError` only; anything else propagates | none stated in the plugin module |
| Django (apps) | app label validity and uniqueness only | nothing; eight documented `AppConfig` attributes, none a version | none | — | "code you develop against a version of Django will continue to work with future releases"; deprecation kept "at least two feature releases" |

## 15 What the in-process Python hosts change

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

## 16 What the evidence supports

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

- **The standard library stopped offering version comparison at 3.12.** `distutils.version` was the
  only helper it had, PEP 632 removed the package at exactly that release, and its migration advice
  points at `packaging`; `importlib.metadata` reads a version without ordering one. A host that may
  not take `packaging` can order an integer or a tuple of integers, which the language compares
  lexicographically, and nothing else — which is what makes the choice between a bare number and a
  version string a choice about the comparison rule as much as about the declaration.
- **When the comparison rule is written by hand, it goes wrong quietly.** Sphinx's `needs_sphinx`
  compares version strings lexicographically, so `'10.0' > '8.3.0'` is `False` and the gate does not
  fire; `require_sphinx()` truncates to `(major, minor)`, so a patch-level requirement cannot be
  expressed. Hosts that delegate to `packaging` (`needs_extensions`, `requires_ansible`,
  `required_plugins`, `minversion`) or to `AwesomeVersion` (Home Assistant) do not have this class
  of bug.

## 17 What these findings establish across the five notes

The sections above close with what their own hosts establish. Three patterns hold across the family
and belong to no single note.

- **A host can refuse a conflict only where it owns a namespace**, so the contract version, the
  capability name and the lookup key are one design act: naming what the host keys on. Django,
  Litestar, Sphinx and pluggy raise on duplicate identity because each keeps a dictionary keyed by
  the contested name; where the key is derived rather than declared, the collision resolves in
  silence ([`34`](34-plugin-conflicts-and-prohibitions.md),
  [`33`](33-the-plugin-to-plugin-channel.md)).
- **The gate that catches host-plugin skew in Python is structural, not numeric.** pluggy's
  per-argument set difference against the hookspec, Litestar's `isinstance` against six
  `@runtime_checkable` Protocols and mypy's six-step ladder over the shape of the entry point are
  the three that actually fire, and none of them compares a version (§10 and §12 above,
  [`33`](33-the-plugin-to-plugin-channel.md)).
- **A written compatibility window carries the weight a number does not, and warnings alone have a
  recorded failure.** Sphinx keeps a deprecated feature "during 2 MAJOR releases at least", Django
  promises no rename "without providing backwards-compatible aliases", and pytest 8.1.0 was yanked
  from PyPI because "it broke some plugins without the proper warning period, due to some warnings
  not showing up as expected" — while a host that omits the gate maintains a per-plugin blocklist
  after each incident ([`35`](35-the-third-party-author-kit.md) for the same promise measured over
  configuration field names).

## Sources

Every claim above carries its own link inline. This section names what was read.

pytest:

- <https://github.com/pytest-dev/pytest> — `pyproject.toml`, `src/_pytest/assertion/rewrite.py`,
  `src/_pytest/config/__init__.py`, `src/_pytest/main.py`
- <https://github.com/pytest-dev/pytest-asyncio> — `pyproject.toml`
- <https://github.com/pytest-dev/pytest-cov> — `pyproject.toml`
- <https://github.com/pytest-dev/pytest-xdist> — `pyproject.toml`
- <https://docs.pytest.org/en/stable/backwards-compatibility.html> ·
  <https://docs.pytest.org/en/stable/changelog.html> ·
  <https://docs.pytest.org/en/stable/how-to/assert.html>
- <https://docs.pytest.org/en/stable/how-to/writing_plugins.html> ·
  <https://docs.pytest.org/en/stable/reference/reference.html#confval-minversion> ·
  <https://docs.pytest.org/en/stable/reference/reference.html#confval-required_plugins>
- <https://github.com/pytest-dev/pytest/issues/12069> ·
  <https://github.com/pytest-dev/pytest/pull/11757> ·
  <https://github.com/pytest-dev/pytest/tree/main/src/_pytest>

mypy:

- <https://github.com/python/mypy> — `docs/source/command_line.rst`, `docs/source/config_file.rst`,
  `docs/source/extending_mypy.rst`, `mypy/build.py`, `mypy/dmypy/client.py`, `mypy/dmypy_server.py`,
  `mypy/errors.py`, `mypy/plugin.py`, `mypy/util.py`, `mypy/version.py`,
  `test-data/unit/check-custom-plugin.test`, `test-data/unit/daemon.test`

Home Assistant:

- <https://github.com/home-assistant/core> — `homeassistant/loader.py`,
  `script/hassfest/manifest.py`, `script/hassfest/requirements.py`
- <https://developers.home-assistant.io/blog/2021/01/29/custom-integration-changes> ·
  <https://developers.home-assistant.io/blog/2021/01/29/custom-integration-changes#versions> ·
  <https://developers.home-assistant.io/docs/creating_integration_manifest>
- <https://developers.home-assistant.io/docs/creating_integration_manifest#dependencies> ·
  <https://developers.home-assistant.io/docs/creating_integration_manifest#requirements> ·
  <https://developers.home-assistant.io/docs/creating_integration_manifest#version>
- <https://github.com/home-assistant/core/issues/112464>

Sphinx:

- <https://github.com/sphinx-doc/sphinx> — `sphinx/__init__.py`, `sphinx/application.py`,
  `sphinx/environment/__init__.py`, `sphinx/extension.py`, `sphinx/registry.py`
- <https://www.sphinx-doc.org/en/master/extdev/deprecated.html> ·
  <https://www.sphinx-doc.org/en/master/extdev/index.html#ext-metadata> ·
  <https://www.sphinx-doc.org/en/master/internals/release-process.html#deprecation-policy>
- <https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-needs_extensions> ·
  <https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-needs_sphinx>

Terraform:

- <https://github.com/hashicorp/go-plugin> — `client.go`, `server.go`
- <https://github.com/hashicorp/terraform> — `internal/command/meta_providers.go`,
  `internal/plugin/plugin.go`, `internal/plugin/serve.go`
- <https://developer.hashicorp.com/terraform/plugin/terraform-plugin-protocol>

pydantic:

- <https://github.com/pydantic/pydantic> — `pydantic/mypy.py`, `pydantic/plugin/__init__.py`,
  `pydantic/plugin/_loader.py`, `pydantic/v1/mypy.py`, `pydantic/version.py`

Ansible:

- <https://github.com/ansible/ansible> — `lib/ansible/config/base.yml`,
  `lib/ansible/plugins/loader.py`,
  `test/lib/ansible_test/_util/controller/sanity/code-smell/runtime-metadata.py`
- <https://docs.ansible.com/ansible/latest/dev_guide/developing_collections_structure.html>

Python packaging and PEPs:

- <https://packaging.python.org/en/latest/specifications/core-metadata/> ·
  <https://packaging.python.org/en/latest/specifications/entry-points/> ·
  <https://peps.python.org/pep-0384/>
- <https://peps.python.org/pep-0425/>
- <https://peps.python.org/pep-0632/> · <https://pypi.org/pypi/packaging/json>

VS Code:

- <https://github.com/microsoft/vscode> — `src/vs/platform/extensions/common/extensionValidator.ts`
- <https://code.visualstudio.com/api/advanced-topics/extension-host> ·
  <https://code.visualstudio.com/api/references/extension-manifest> ·
  <https://code.visualstudio.com/api/working-with-extensions/publishing-extension>

Litestar:

- <https://github.com/litestar-org/litestar> — `litestar/app.py`, `litestar/plugins/base.py`,
  `litestar/plugins/pydantic/plugins/schema.py`

pluggy:

- <https://github.com/pytest-dev/pluggy> — `docs/index.rst`, `src/pluggy/_manager.py`
- <https://github.com/pytest-dev/pluggy>

Django:

- <https://github.com/django/django> — `docs/misc/api-stability.txt`, `docs/ref/applications.txt`

Obsidian:

- <https://docs.obsidian.md/Reference/Manifest> · <https://docs.obsidian.md/Reference/Versions>

CPython:

- <https://docs.python.org/3/c-api/stable.html#c.Py_LIMITED_API>
- <https://docs.python.org/3/whatsnew/3.12.html> ·
  <https://docs.python.org/3/library/importlib.metadata.html> ·
  <https://docs.python.org/3/library/sys.html#sys.version_info>
- <https://docs.python.org/3/reference/expressions.html#comparisons>
