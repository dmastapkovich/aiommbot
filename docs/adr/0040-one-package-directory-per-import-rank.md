---
status: accepted
date: 2026-09-09
ticket: "#24"
---

# Every import rank is a package directory, and every module is named after the `CONTEXT.md` term it holds

[ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md) fixed five layers on four
import ranks and left the paths to this ticket. We decided that **each rank is a directory** —
`core/`, `mattermost/` with its own `plugins/`, the generic `plugins/`, `testing/` — so the layer
table is also the directory listing and the import-linter contract names modules that exist, and
that **a module carries the glossary term of the single thing inside it**, in snake case, so no
future ticket has to argue where a name goes.

```text
src/aiommbot/
  py.typed
  __init__.py                        the closed headline set, re-exported
  _internal/compat/typing.py         the one compat module; stdlib and typing_extensions only
  core/
    __init__.py                      the Core's public surface
    bot.py  dispatcher.py  router.py  middleware.py  error_boundary.py
    dependency_provider.py  signal.py  sync_executor.py  event.py
    filters.py  extractors.py                      components of §5.5
    transport.py  key_value_store.py  lock_provider.py  codec.py
    http_transport.py  websocket_connection.py  state_key_provider.py
    token_provider.py  callback_token_codec.py  request_observer.py
                                                   seams of §5.4, one Protocol group per module
    log_correlation.py               the contextvar and the filter callable of ADR-0054
    errors.py                        AiommbotError, FatalError, AiommbotWarning, MissingExtraError
    _internal/
  mattermost/
    __init__.py
    event_registry.py  generated_model.py  model_generator.py  codec.py
    api_client.py  exchange.py  face.py  workspace.py  runtime.py
    auth_loss_detector.py  filters.py                components of §5.6
    _internal/
    plugins/                         the adapter-specific rank
      websocket_transport/  webhook/  callback_token/  identity_cache/
  plugins/                           the generic rank
    state/  backends/  observability/  dishka.py  wireup.py
  testing/                           the testing toolkit rank
    __init__.py                      the toolkit's public surface
    fake_mattermost.py  test_bot.py  fake_adapter.py  fake_clock.py
    builders.py  assertions.py                     components and parts of §5.9
    conformance/                     one module per conformance suite
    plugin.py                        the pytest plugin named in `pytest_plugins`
```

None of these module names is a documented import path — a public name is documented at its
package path ([ADR-0042](0042-a-public-name-is-documented-at-its-package-path.md)) — which is
what lets `ST-MOD-09` split any of them later without a deprecation shim.

Three rules produce every name above, and one of them is enough for any block the design adds
later:

- **A component is a module named after its term** — `sync_executor.py` for the Sync executor, not
  `executor.py`, which the glossary lists as a word to avoid. A component large enough to need parts
  in their own files becomes a package of the same name (`ST-MOD-09`).
- **A seam is a module named after its Protocol**, in the rank that owns it — every Core-owned
  Protocol of §5.4 is a module of `core/`, and the two paired Protocols of one seam share it
  (`http_transport.py` holds `HTTPTransport` and `SyncHTTPTransport`).
- **Plural marks a family of interchangeable peers**, singular one concept (`ST-NAM-07`):
  `filters.py`, `extractors.py`, `plugins/backends/`.

Everything not public sits under the `_internal/` of its own rank, and a Quarantine module lives in
the `_internal/compat/` of the rank that owns the library it wraps
([ADR-0010](0010-zero-suppressions-with-a-quarantine.md)) — `msgspec` under the Adapter's,
`websockets` under the WebSocketTransport's, `redis` under `plugins/backends/`. The one exception is
the typing compat module of [ADR-0008](0008-python-floor-3-12-with-typing-extensions.md): every rank
imports from it, so it sits below the Core in `aiommbot/_internal/compat/`, where it depends on the
standard library and `typing_extensions` and on nothing of ours. That makes it one more position in
the import contract and **not** a fifth layer of the architecture — it holds the names the
language floor lacks and no design at all, so the five layers on four ranks of
[ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md) are unchanged.

## Considered options

- *The Core at the package root, with `mattermost/`, `plugins/` and `testing/` beside it* —
  rejected: it gives the shortest imports (`from aiommbot.event import Event`) and reads exactly
  like [ADR-0007](0007-tiny-public-root-with-explicit-subpackages.md), but the Core rank then has no
  name — it is "the root minus four directories" — so the import-linter contract has to list the
  Core's modules and stays correct only while somebody maintains that list.
- *One `plugins/` tree for both plugin ranks, with the adapter binding declared only in
  `PluginSpec`* — rejected: the tree stops showing the rank, and "a generic Plugin never imports
  the Adapter" — the property [ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md)
  exists to keep checkable — becomes invisible to a reader of the directory listing.
- *Topical modules (`routing.py`, `dispatch.py`, `seams.py`)* — rejected: fewer and shorter paths,
  but every component design document would then reopen the question of which module its parts
  belong to, and `dispatch.py` starts life holding two components and three parts.
- *A subpackage per component (`router/__init__.py`, `router/_tree.py`)* — rejected: it puts the
  component boundary in the filesystem, at the price of eleven directories in the Core, several with
  one file, and two spellings of "internal" instead of one.

## Consequences

- `mattermost/plugins/` is named for the rank, not for the declaration: the Callback token is a
  member of that rank without a `PluginSpec`, composed by the Webhook (§5.8). Anything in the
  Adapter that needs to issue a token — the message builders of #52 — depends on the Core
  `callback_token_codec` seam and receives the implementation by injection, so the import still runs
  upward.
- [ADR-0015](0015-plugin-contract-and-composition.md)'s placement sentence resolves here:
  adapter-specific plugins live in `aiommbot/mattermost/plugins/`, generic ones in
  `aiommbot/plugins/`, which is a sibling of `core/` and not a subpackage of it.
- Two module names in the tree shadow standard-library modules — `signal.py` and the compat
  module's `typing.py` — and both keep the name of the thing they hold, because ruff's
  [`A005`](https://docs.astral.sh/ruff/rules/stdlib-module-shadowing/) compares the module *path*
  relative to `src/`, not the last component, unless `strict-checking` is switched on, which
  [ADR-0011](0011-lint-format-and-architecture-toolchain.md) does not do. No suppression and no
  allow-list is involved.
- **The ranks are checked, not reviewed**, and this layout is what makes the contracts short: a
  `layers` contract over the `aiommbot` container puts `testing` above the independent siblings
  `mattermost` and `plugins`, those above `core`, and `core` above `_internal`; a
  [`protected`](https://import-linter.readthedocs.io/en/stable/contract_types/protected/) contract
  admits `aiommbot.mattermost.plugins` to the testing toolkit alone, which is the one direction a
  `layers` contract cannot express — a package and its own subpackage in different layers is
  undocumented in import-linter and must not be relied on; an `independence` contract covers every
  first-party plugin; and a `forbidden` contract keeps third-party packages out of `core` and
  `_internal`. The configuration is
  [ADR-0011](0011-lint-format-and-architecture-toolchain.md)'s.
- The distribution ships `py.typed` at the package root, so the four checkers of
  [ADR-0009](0009-four-strict-type-checkers.md) see our annotations in a consumer's project.
