---
status: accepted
date: 2026-09-03
ticket: "#14"
---

# A Plugin is a frozen declaration plus narrow contribution Protocols; exactly one Adapter; plugins are either generic or adapter-specific

ADR-0002 fixed explicit composition. This decision fixes what is composed and how the pieces
relate, designed so that a second platform adapter would be an addition, not a rewrite.

- **Roles.** `Bot(adapter=..., plugins=[...])`. The **Adapter** is a distinct role and there is
  exactly one: it supplies the platform vocabulary — payload types and the `EventRegistry`
  (ADR-0012), the REST client and Runtime, platform filters and router aliases. Everything
  optional is a **Plugin**, including the Transports (`WebSocketTransport`, `Webhook`), which
  implement the Core-owned `Transport` Protocol. A Bot with an Adapter and no Transport is a valid
  runtime-only process (ADR-0005).
- **Generic vs adapter-specific plugins.** A plugin declares whether it is generic (depends on the
  Core only: State, observability hooks, scheduling bridges) or bound to an adapter
  (`for_adapter=Mattermost`). Composing an adapter-specific plugin with the wrong adapter is a
  start-up check failure. Adapter-specific plugins live under the adapter's package; generic ones
  under the Core's plugin package (layout in #24).
- **Contract = declaration + narrow Protocols.** A plugin object carries an immutable
  `PluginSpec` (name, contract version, `requires` and `after` dependencies on other plugins by
  name, adapter binding, settings type) and implements only the narrow Protocols it needs:
  `ContributesRouters`, `ContributesMiddleware`, `ContributesDependencies`,
  `ContributesEventTypes`, `ContributesChecks`, `HasLifecycle` (an async context manager for
  start/stop). No base class, no inheritance (ADR-0006); the declaration is readable without
  running code.
- **Ordering.** `requires` is hard (missing → start-up error), `after` is soft (orders when both
  are present). Activation is topological with list position as the tie-break; shutdown runs in
  reverse; a cycle is a start-up error. Plugins collaborate only through Core-owned Protocols,
  never by importing each other; import-linter's `independence` contract enforces it.
- **Settings.** Each plugin takes a typed frozen settings object in its constructor
  (`@dataclass(frozen=True, slots=True, kw_only=True)`, validated in `__post_init__`). Where the
  values come from — environment, a settings library, a vault — is the application's business;
  the framework documents a recipe and keeps field names stable. This ends the "seven names for
  one setting" pattern of 0.4.8.
- **Discovery.** A third-party plugin is an ordinary package whose object is imported and placed
  in `plugins=[...]`. Nothing activates by being installed; entry points stay out of 0.5.0.
- **Contract stability.** The plugin Protocols and `PluginSpec` are public API under semantic
  versioning; the declared contract version is checked at start-up and an incompatible plugin
  fails with a clear message. First-party plugins are subpackages of the single distribution with
  extras and a friendly missing-dependency error; each ships with a component design document
  and passes the contract test kit in `aiommbot.testing` (conformance suites for `Storage`,
  `Transport` and the plugin lifecycle).

## Considered options

- *Adapter as just another plugin in the list* — rejected: "exactly one" would need a separate
  check and list order would acquire hidden meaning.
- *Transports built into the adapter behind flags* — rejected: two extension models, and the
  runtime-only process becomes a special case instead of "no transport plugins".
- *One fat `Plugin` base class* — rejected: inheritance and empty hooks in every plugin (ADR-0006,
  ISP).
- *List order only, no declared dependencies* — rejected: the user carries the ordering burden
  and missing dependencies surface at runtime.
- *Framework reads environment variables itself* — rejected: a settings library in the Core or
  plugins and hidden configuration.
- *Entry-point discovery now* — deferred: no demand yet; when it comes, copy pydantic's guards.
