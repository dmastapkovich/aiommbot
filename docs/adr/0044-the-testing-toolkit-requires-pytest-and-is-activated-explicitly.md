---
status: accepted
date: 2026-09-09
ticket: "#25"
amends: [ADR-0041]
---

# The testing toolkit imports pytest through an extra named after it, and one line in the root `conftest.py` activates its plugin

[ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md) placed `aiommbot.testing`
above every other layer without saying what it may depend on, and a toolkit that ships fixtures and
executable conformance suites cannot avoid pytest. We decided that **`aiommbot.testing` imports
pytest at module scope**, installed by the extra `pytest` under
[ADR-0041](0041-default-dependencies-and-one-extra-per-optional-library.md)'s rule of one extra per
optional library named after the library, and that **nothing of ours registers itself with pytest by
being installed**: the fixtures arrive when the application writes
`pytest_plugins = ["aiommbot.testing.plugin"]` in its root `conftest.py`, which is the same
"explicit or absent" stance [ADR-0015](0015-plugin-contract-and-composition.md) takes on plugin
discovery and `ST-MOD-07` takes on imports.

- **The `pytest11` entry point is not used.** A distribution declaring it has its plugin module
  imported at *every* pytest start-up in any environment where the distribution is installed, for
  sessions that never touch our fixtures, unless the user disables it by name
  ([pytest, *Plugin discovery order at tool startup*](https://docs.pytest.org/en/stable/how-to/writing_plugins.html#plugin-discovery-order-at-tool-startup)).
  SQLAlchemy refuses the entry point for its dialect compliance suite for exactly that reason and
  requires the explicit import instead
  ([`README.dialects.rst`](https://github.com/sqlalchemy/sqlalchemy/blob/main/README.dialects.rst)).
- **`aiommbot.testing.plugin` is a pinned configuration string, not a public name.** Users write it
  in a configuration file, so it is fixed by this decision and may not move — the one module path
  in the project that anything promises. It buys nothing to document it as an import path, and
  `ST-MOD-11` still forbids that.
- **The plugin adds three fixtures and nothing else** — `fake_mattermost`, `test_bot` and
  `fake_clock`, the snake-case names of the types they build. No command-line option, no marker, no
  hook: an option may only be declared in a plugin or the root `conftest.py` and would then appear
  in every session, and an unregistered marker is an error under `--strict-markers`
  ([pytest, *How to mark test functions*](https://docs.pytest.org/en/stable/how-to/mark.html)).
  pytest neither detects nor prevents fixture-name collisions
  ([pytest#3966](https://github.com/pytest-dev/pytest/issues/3966)), and explicit activation is what
  makes a collision the application's own choice.
- **The suites explain their own failures.** `pytest.register_assert_rewrite` must run before the
  module it rewrites is imported, and importing `aiommbot.testing.plugin` imports the package that
  holds the suites first, so assertion rewriting is unreachable for our own code by construction
  ([pytest, *Writing plugins*](https://docs.pytest.org/en/stable/how-to/writing_plugins.html)). A
  conformance case therefore reports what it expected and what it observed as typed data
  (`ST-TST-07`), which is what [ADR-0047](0047-a-conformance-suite-per-core-seam.md) needs anyway.

## Considered options

- *The `pytest11` entry point under the plugin name `aiommbot`* — rejected: it needs no line from
  the user and pins a plugin name rather than a module path, but it makes an unrelated project's
  pytest start-up import our whole framework and its opt-out is a flag the surprised user has to
  find.
- *A pytest-free `aiommbot.testing` with the fixtures and suite factories under
  `aiommbot.testing.pytest`* — rejected: it keeps the doubles importable without a test runner, at
  the price of a sixth documented path form, which is an amendment to
  [ADR-0042](0042-a-public-name-is-documented-at-its-package-path.md) and to `ST-MOD-11`'s "no
  exceptions" for a case that only ever arises inside a test session.
- *No pytest anywhere: suites as data plus a runner, no fixtures, no plugin* — rejected: it is the
  FastStream and dishka shape and costs the toolkit nothing to import, but every user and every
  third-party plugin then rewrites the same parametrisation boilerplate.
- *A separate `pytest-aiommbot` distribution* — rejected: one distribution is
  [ADR-0002](0002-core-scope-two-condition-test.md)'s, and a second one would version separately
  from the Protocols its suites check.

## Consequences

- [ADR-0041](0041-default-dependencies-and-one-extra-per-optional-library.md)'s line that
  development tooling is never an extra is rewritten there: the test *runner* is an extra when a
  published module of ours imports it, and the tooling *we* run stays in the PEP 735 groups.
- `aiommbot.testing` is the one public package whose smoke import runs with an extra installed
  rather than without one; `ST-MOD-07`'s limits record it, and the per-extra smoke import of
  [ADR-0011](0011-lint-format-and-architecture-toolchain.md) covers it like every other extra.
  `ST-MOD-08`'s `MissingExtraError` does not apply: there is no constructor to defer to when the
  missing library is the runner that would have called it.
- Doctests in the framework's own docstrings may name toolkit types (`ST-DOC-02`), because doctest
  collection runs under pytest, where the extra is installed.
