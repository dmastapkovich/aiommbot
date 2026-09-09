---
status: accepted
date: 2026-09-03
ticket: "#13"
amended-by: [ADR-0008]
---

# The core admits a capability only if every bot needs it identically or it is chat-specific with no library equivalent

A core that owns scheduling, metrics, retries, a circuit breaker, storage profiles and a CLI becomes
a god object nothing can replace piecewise, and no peer bot framework owns any of that in core
([`docs/research/08`](../research/08-peer-responsibility-boundaries.md)). We decided that the
**Core** admits a capability only when it passes one of two tests: (1) *every* bot needs it and
needs it identically — event envelope, routing and filters, middleware chain, dependency injection,
lifecycle and graceful shutdown, the Transport seam, the error taxonomy, the Plugin registry, the
Dispatch concurrency; or (2) it is *specific to a chat protocol and has no mature library
equivalent* — per-key event isolation for conversation state, webhook callback signing, dedup of
stale interactive actions, flood control keyed on chat identity. Everything else is a Plugin, an
extra or a documented recipe over an ecosystem library; the extras that exist and the rule for
adding one are
[ADR-0041](0041-default-dependencies-and-one-extra-per-optional-library.md)'s, the Check phase is
[ADR-0016](0016-three-phase-start-with-checks.md)'s, and where a capability still without a home
will live is the map's *Not yet specified* — observability #29, the CLI #30.

Consequences fixed with the same decision:

- **Core refuses**: knowing Mattermost; scheduling; implementing metrics or tracing (it exposes the
  Observability seam only); retries, dead-letter, circuit breaking; any storage backend other than
  in-memory; running an HTTP server (the webhook Plugin exposes an ASGI application for any server);
  selecting an event loop; a CLI framework (placement is #30's decision; the Core offers only the
  `run()` and `serve()` entry points of
  [ADR-0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md)).
- **Core runtime dependencies: standard library only**, with `typing_extensions` as the single
  exception admitted by [ADR-0008](0008-python-floor-3-12-with-typing-extensions.md) while Python
  3.12 is supported. Core contracts are `dataclass(slots=True)` and `Protocol`; serialisation
  (msgspec), HTTP and WebSocket clients (httpx2, websockets), observability (whatever library #29 chooses) live
  in the Adapter and in Plugins behind Core-owned Protocols. Enforced by an import-linter
  `forbidden` contract and a smoke import of the Core with no extras installed.
- **One distribution**, `aiommbot`, with the Core, the Mattermost Adapter and first-party Plugins as
  subpackages; boundaries are import-linter `layers` and `forbidden` contracts, optional
  dependencies are extras. One version, one changelog.
- **Explicit composition**: functionality is enabled by listing it in code (`Bot(plugins=[...])`,
  explicit router inclusion). Nothing is active because it is installed or imported. Composition is
  staged — compose, check, start ([ADR-0016](0016-three-phase-start-with-checks.md)) — with
  per-plugin settings objects, and nothing is enabled by a string list; the Django apps precedent is
  [`docs/research/10`](../research/10-plugin-systems.md).

## Considered options

- *Batteries included as first-party plugins for everything a bot might need* — rejected: it keeps
  a maintenance surface without evidence of use; a plugin can be added later when a bot
  needs it, a shipped plugin can never be removed quietly.
- *Wide core with redesigned reliability and observability* — rejected: contradicts every peer and
  the two-condition test; reliability primitives have mature libraries (stamina, purgatory,
  broker-native DLQ — [`docs/research/08`](../research/08-peer-responsibility-boundaries.md)) that a
  framework only wraps worse.
- *Several distributions (`aiommbot-core`, `aiommbot-mattermost`, …)* — rejected for 0.5.0: one
  adapter and a handful of plugins do not justify version skew and multi-package releases; the
  import-linter boundary gives the same isolation inside one wheel.
