---
status: accepted
date: 2026-09-03
ticket: "#13"
amended-by: [ADR-0008, ADR-0048, ADR-0058, ADR-0060]
---

# The framework admits a capability only if every bot needs it identically or it is chat-specific with no library equivalent, and only a stateless universal lands in the Core

A core that owns scheduling, metrics, retries, a circuit breaker, storage profiles and a CLI becomes
a god object nothing can replace piecewise, and no peer bot framework owns any of that in core
([`docs/research/08`](../research/08-peer-responsibility-boundaries.md)). We decided that the
**framework** admits a capability only when it passes one of two tests: (1) *every* bot needs it and
needs it identically — event envelope, routing and filters, middleware chain, dependency injection,
lifecycle and graceful shutdown, the Transport seam, the error taxonomy, the Plugin registry, the
Dispatch concurrency; or (2) it is *specific to a chat protocol and has no mature library
equivalent* — per-key event isolation for conversation state, webhook callback signing, dedup of
stale interactive actions, flood control keyed on chat identity. Everything else is a documented
recipe over an ecosystem library, in the form
[ADR-0056](0056-the-framework-owns-no-scheduler.md) fixes.

**Passing the test says the capability is ours; where it lands is a second question.** The **Core**
takes only what test (1) admits *and* needs no state between events
([ADR-0003](0003-stateless-core-state-plugin-with-explicit-backend.md)); everything admitted by
test (2) needs a store or a platform vocabulary and is therefore a first-party Plugin — conversation
state and its isolation ([ADR-0022](0022-state-plugin-model.md)), callback signing and stale-action
dedup ([ADR-0024](0024-webhook-ingress-and-callback-security.md)), flood control and delivery dedup
([ADR-0060](0060-flood-control-and-delivery-dedup-are-one-generic-plugin.md)). The extras that exist
and the rule for adding one are
[ADR-0041](0041-default-dependencies-and-one-extra-per-optional-library.md)'s, the Check phase is
[ADR-0016](0016-three-phase-start-with-checks.md)'s, observability is a generic Plugin behind two
library-named extras ([ADR-0051](0051-first-party-observability-plugin.md)), and the probe endpoints
are a third ([ADR-0061](0061-health-is-a-generic-plugin-over-application-supplied-checks.md)).

Consequences fixed with the same decision:

- **Core refuses**: knowing Mattermost; scheduling; emitting a metric or a span of its own — it
  offers the Middleware layers, the typed `Outcome`, the Signals and the `RequestObserver` pair, and
  a Plugin turns those into telemetry
  ([ADR-0048](0048-observability-is-not-a-core-seam.md),
  [ADR-0049](0049-what-the-framework-makes-observable.md)); retries of a delivery, dead-letter,
  circuit breaking and error reporting
  ([ADR-0057](0057-reliability-middlewares-and-error-reporting-stay-outside.md)); any storage
  backend other than in-memory; **running an HTTP server** — the Webhook and Health Plugins expose
  ASGI applications and a server the application runs hosts them, and the shipped command starts
  none ([ADR-0058](0058-the-command-is-a-console-script-behind-the-click-extra.md)); selecting an
  event loop; and a CLI framework of its own — the Core offers the `run()` and `serve()` entry
  points of [ADR-0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md), and the
  `aiommbot` command is a console script behind the `click` extra (ADR-0058).
- **Core runtime dependencies: standard library only**, with `typing_extensions` as the single
  exception admitted by [ADR-0008](0008-python-floor-3-12-with-typing-extensions.md) while Python
  3.12 is supported. Core contracts are `dataclass(slots=True)` and `Protocol`; serialisation
  (msgspec), HTTP and WebSocket clients (httpx2, websockets) and observability
  (`opentelemetry-api`, `prometheus-client`) live
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
  the two-condition test. Where a mature library exists — `stamina` for retries, a broker's own
  dead-letter queue — a framework only wraps it worse; where none does, as for an asyncio-native
  circuit breaker, the answer is a documented seam and no recommendation
  ([ADR-0057](0057-reliability-middlewares-and-error-reporting-stay-outside.md),
  [`docs/research/26`](../research/26-schedule-reliability-and-probe-primitives.md)).
- *Several distributions (`aiommbot-core`, `aiommbot-mattermost`, …)* — rejected for 0.5.0: one
  adapter and a handful of plugins do not justify version skew and multi-package releases; the
  import-linter boundary gives the same isolation inside one wheel.
