# 35. What a host hands a third-party plugin author

**Question.** What does a host hand a third-party plugin author besides the Protocol definitions — a
contract test kit, a scaffold, a naming convention, a plugin-API reference page, an instruction on
what to name a logger, and a promise about configuration field names?

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

The decision this note is evidence for is #103.

Findings only, and no recommendation. Sources are primary — project source at the default branch,
reference and developer documentation, PEPs, the Python packaging specifications,
`docs.python.org`, PyPI metadata and project issue trackers — read on 2026-09-10. Anything a
primary source did not confirm is marked **[unverified]**.

Protocol definitions tell an author what to implement. This section asks what else a host hands
them: a way to test the implementation, a way to start the project, a name to publish it under, a
reference page they can trust, and conventions for the two things a plugin emits into a shared
namespace — log records and configuration keys.

## 1 The contract test kit

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

## 2 The scaffold

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

## 3 Name convention and registry

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

## 4 The plugin-API reference page

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

## 5 The logger name

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

## 6 Configuration field names

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

## 7 Comparison

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

## 8 What the evidence supports

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

## Sources

Every claim above carries its own link inline. This section names what was read.

Home Assistant:

- <https://github.com/home-assistant/brands> — `README.md`
- <https://github.com/home-assistant/core> — `pyproject.toml`, `script/scaffold/__main__.py`,
  `script/scaffold/templates/config_flow/tests/test_config_flow.py`, `tests/conftest.py`
- <https://github.com/home-assistant/developers.home-assistant> — `docs/deprecating.md`,
  `docusaurus.config.js`
- <https://developers.home-assistant.io> ·
  <https://developers.home-assistant.io/docs/core/integration-quality-scale/> ·
  <https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/brands>
- <https://developers.home-assistant.io/docs/core/integration/brand_images> ·
  <https://developers.home-assistant.io/docs/creating_component_index> ·
  <https://developers.home-assistant.io/docs/creating_integration_manifest>
- <https://developers.home-assistant.io/docs/deprecating> ·
  <https://developers.home-assistant.io/docs/dev_101_states> ·
  <https://developers.home-assistant.io/docs/development_guidelines>
- <https://developers.home-assistant.io/docs/integration_fetching_data> ·
  <https://github.com/MatthewFlamm/pytest-homeassistant-custom-component> ·
  <https://github.com/home-assistant/core/tree/dev/script/scaffold/templates>

pytest:

- <https://github.com/pytest-dev/cookiecutter-pytest-plugin> — `CONTRIBUTORS.md`, `README.md`,
  `cookiecutter.json`, `pytest-%7B%7Bcookiecutter.plugin_name%7D%7D/pyproject.toml`,
  `pytest-%7B%7Bcookiecutter.plugin_name%7D%7D/tests/conftest.py`,
  `pytest-%7B%7Bcookiecutter.plugin_name%7D%7D/tests/test_%7B%7Bcookiecutter.module_name%7D%7D.py`
- <https://github.com/pytest-dev/pytest> — `CONTRIBUTING.rst`, `doc/en/backwards-compatibility.rst`,
  `doc/en/changelog.rst`, `doc/en/deprecations.rst`, `doc/en/how-to/logging.rst`,
  `doc/en/how-to/plugins.rst`, `doc/en/how-to/writing_hook_functions.rst`,
  `doc/en/how-to/writing_plugins.rst`, `doc/en/reference/plugin_list.rst`,
  `doc/en/reference/reference.rst`, `src/_pytest/pytester.py`
- <https://github.com/pytest-dev/cookiecutter-pytest-plugin>

Sphinx:

- <https://github.com/sphinx-doc/sphinx> — `doc/extdev/deprecated.rst`, `doc/extdev/index.rst`,
  `doc/extdev/logging.rst`, `doc/extdev/testing.rst`, `doc/internals/release-process.rst`,
  `doc/man/sphinx-quickstart.rst`, `doc/usage/extensions/index.rst`, `sphinx/config.py`,
  `sphinx/testing/fixtures.py`, `sphinx/testing/util.py`, `sphinx/util/logging.py`
- <https://github.com/sphinx-doc/sphinx/tree/master/doc/development/tutorials/examples>

Django:

- <https://github.com/django/django> — `django/conf/__init__.py`, `docs/howto/logging.txt`,
  `docs/internals/deprecation.txt`, `docs/internals/release-process.txt`,
  `docs/intro/reusable-apps.txt`, `docs/misc/api-stability.txt`, `docs/ref/settings.txt`,
  `docs/topics/testing/advanced.txt`
- <https://github.com/django/django/tree/main/django/conf/app_template> ·
  <https://github.com/django/django/tree/main/django/conf/project_template>

Litestar:

- <https://github.com/litestar-org/litestar> — `CONTRIBUTING.rst`,
  `docs/reference/plugins/index.rst`, `docs/usage/cli.rst`, `docs/usage/databases/piccolo.rst`,
  `docs/usage/plugins/index.rst`, `docs/usage/testing.rst`, `litestar/cli/main.py`,
  `litestar/testing/__init__.py`, `pyproject.toml`
- <https://litestar.dev/about/litestar-releases#version-numbering`>

FastStream:

- <https://github.com/ag2ai/faststream> —
  `docs/docs/en/getting-started/integrations/frameworks/index.md`,
  `docs/docs/en/getting-started/observability/logging.md`,
  `docs/docs/en/getting-started/template/index.md`, `faststream/_internal/cli/docs.py`,
  `faststream/_internal/cli/main.py`, `faststream/_internal/testing/broker.py`, `pyproject.toml`

Python packaging and PEPs:

- <https://docs.pypi.org/organization-accounts/org-acc-faq/> · <https://peps.python.org/pep-0752/> ·
  <https://peps.python.org/pep-0755/>

VS Code:

- <https://github.com/microsoft/vscode-generator-code> — `README.md`, `package.json`
- <https://github.com/microsoft/vscode-generator-code/tree/main/generators/app>

Other Python hosts:

- <https://github.com/Microsoft>
