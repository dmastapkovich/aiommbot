---
status: accepted
date: 2026-09-03
ticket: "#13"
---

# The core admits a capability only if every bot needs it identically or it is chat-specific with no library equivalent

aiommbot 0.4.8 grew a `Bot(Router)` god object that owned scheduling, metrics, retries, a circuit
breaker, storage profiles and a CLI; usage mining shows most of that surface had zero consumers,
and no peer bot framework owns any of it in core (`docs/research/08`, `09`). We decided that the
**Core** admits a capability only when it passes one of two tests: (1) *every* bot needs it and
needs it identically — event envelope, routing and filters, middleware chain, dependency injection,
lifecycle and graceful shutdown, the Transport seam, the error taxonomy, the Plugin registry, a
thin concurrency cap; or (2) it is *specific to a chat protocol and has no mature library
equivalent* — per-key event isolation for conversation state, webhook callback signing, dedup of
stale interactive actions, flood control keyed on chat identity. Everything else is a Plugin, an
extra or a documented recipe over an ecosystem library; placement per capability is decided in
#14, #29 and #30 and recorded in `docs/design/TRACKER.md` §E.

Consequences fixed with the same decision:

- **Core refuses**: knowing Mattermost; scheduling; implementing metrics or tracing (it exposes
  hooks only); retries, dead-letter, circuit breaking; any storage backend other than in-memory;
  running an HTTP server (the webhook Plugin exposes an ASGI application for any server);
  selecting an event loop; a CLI framework (the CLI is an extra on typer; the Core offers
  `bot.run()`).
- **Core runtime dependencies: standard library only.** Core contracts are `dataclass(slots=True)`
  and `Protocol`; serialisation (msgspec), HTTP/WebSocket (aiohttp), observability
  (opentelemetry-api) live in the Adapter and in Plugins behind Core-owned Protocols. Enforced by
  an import-linter `forbidden` contract and a smoke import of the Core with no extras installed.
- **One distribution**, `aiommbot`, with the Core, the Mattermost Adapter and first-party Plugins as
  subpackages; boundaries are import-linter `layers` and `forbidden` contracts, optional
  dependencies are extras. One version, one changelog.
- **Explicit composition**: functionality is enabled by listing it in code
  (`Bot(plugins=[...])`, explicit router inclusion). Nothing is active because it is installed or
  imported. From Django we take the staged boot, `ready()`-style hooks, the checks framework and
  per-plugin settings objects, not string-based `INSTALLED_APPS`.

## Considered options

- *Batteries included as first-party plugins for everything 0.4.8 had* — rejected: it keeps the
  maintenance surface of 0.4.8 without evidence of use; a plugin can be added later when a bot
  needs it, a shipped plugin can never be removed quietly.
- *Wide core with redesigned reliability and observability* — rejected: contradicts every peer and
  the two-condition test; reliability primitives have mature libraries (stamina, purgatory,
  broker-native DLQ) that a framework only wraps worse.
- *Several distributions (`aiommbot-core`, `aiommbot-mattermost`, …)* — rejected for 0.5.0: one
  adapter and a handful of plugins do not justify version skew and multi-package releases; the
  import-linter boundary gives the same isolation inside one wheel.
