# Architecture decision records

One decision per file, numbered in order of acceptance, never rewritten: a changed mind is a new
ADR that supersedes the old one. Format and triggers: [`_template.md`](_template.md). ADRs are
produced by wayfinder tickets; the map (#1) and `docs/design/TRACKER.md` §B list which ticket owns
which decision.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-fresh-start-as-a-public-package.md) | aiommbot 0.5.0 is a from-scratch public rewrite with no compatibility with 0.4.x | accepted |
| [0002](0002-core-scope-two-condition-test.md) | The core admits a capability only if every bot needs it identically or it is chat-specific with no library equivalent; stdlib-only core, one distribution, explicit composition | accepted |
| [0003](0003-stateless-core-state-plugin-with-explicit-backend.md) | The core is stateless; conversation state is a plugin that cannot start without an explicit backend | accepted |
| [0004](0004-async-engine-with-generated-sync-runtime.md) | One asyncio engine; the synchronous face is limited to the Runtime and generated from async (amended by 0029, 0030, 0031) | accepted |
| [0005](0005-one-ingress-many-workers.md) | A bot scales as one event ingress and many workers, never as identical replicas | accepted |
| [0006](0006-architectural-tenets-of-the-core.md) | The core is built by composition over Protocols it owns, with named patterns and strict typing | accepted |
| [0007](0007-tiny-public-root-with-explicit-subpackages.md) | The public API is a tiny root namespace plus explicit subpackages; everything else is internal | accepted |
| [0008](0008-python-floor-3-12-with-typing-extensions.md) | Python 3.12 is the floor, supported until EOL, with typing_extensions as the Core's only runtime dependency (amends 0002) | accepted |
| [0009](0009-four-strict-type-checkers.md) | Four type checkers run at maximum strictness and all of them block | accepted |
| [0010](0010-zero-suppressions-with-a-quarantine.md) | Zero lint and type suppressions in the package; foreign types wrapped in quarantine modules | accepted |
| [0011](0011-lint-format-and-architecture-toolchain.md) | One toolchain enforces style, complexity, architecture and dependencies; just is the entry point | accepted |
| [0012](0012-generic-event-envelope-with-adapter-payloads.md) | Inbound events are one generic envelope `Event[P]`; payload types and their registry belong to the Adapter | accepted |
| [0013](0013-type-driven-routing-with-a-typed-dispatch-outcome.md) | Handlers subscribe by annotation on a router tree walked depth-first to the first match, with a typed outcome and reachability checks | accepted |
| [0014](0014-filters-and-extractors-with-closed-handler-signatures.md) | Filters are pure predicates, Extractors produce typed values, handler signatures are closed | accepted |
| [0015](0015-plugin-contract-and-composition.md) | A Plugin is a frozen declaration plus narrow contribution Protocols; exactly one Adapter; plugins are generic or adapter-specific | accepted |
| [0016](0016-three-phase-start-with-checks.md) | The Bot starts in three phases — compose, check, start — and stops on the full list of check failures | accepted |
| [0017](0017-typed-async-lifecycle-signals.md) | Lifecycle notifications are typed asynchronous Signals separate from platform events | accepted |
| [0018](0018-core-owned-type-keyed-dependency-injection.md) | The Core owns a type-keyed dependency resolver with two scopes, declared providers and a start-up-compiled graph; external containers plug in behind a Protocol | accepted |
| [0019](0019-handler-parameter-resolution-rules.md) | Handler parameters resolve from extractors first, then providers; minimal built-ins, never the Bot; overrides only in the testing toolkit | accepted |
| [0020](0020-two-layer-middleware-chain.md) | Middleware is an async chain in two named layers with typed outcomes, typed Event-scope publication and typed handler flags | accepted |
| [0021](0021-core-error-boundary.md) | The Core owns a narrow, non-removable error boundary: log without payload, report, return `Failed`; a failing process is an explicit policy | accepted |
| [0022](0022-state-plugin-model.md) | Conversation state is a typed `Flow[Data]` keyed by a `StateKey`, stored through two Core Protocols with compare-and-set, isolated per key, bounded by a sliding logical TTL | accepted |
| [0023](0023-websocket-gateway-resilience.md) | The WebSocket gateway is one supervised reconnect loop with heartbeat, resume, seq continuity, a never-stalling reader, a graceful drain, auth-loss detection and a replaceable library (websockets primary, picows optional) | accepted |
| [0024](0024-webhook-ingress-and-callback-security.md) | Interactive callbacks are events with a payload-bound reply channel; the webhook plugin is a bare ASGI callable; authenticity is a default-on self-issued HMAC token with no expiry unless configured | accepted |
| [0025](0025-generated-dataclass-models-with-a-codec-protocol.md) | Mattermost models are generated from a pinned, overlaid OpenAPI spec into standard-library dataclasses; serialisation goes through a Core-owned `Codec` Protocol with msgspec as the shipped implementation | accepted |
| [0026](0026-standalone-typed-api-client-over-an-http-transport-protocol.md) | The Mattermost REST client is a standalone typed API client: httpx2 behind an `HTTPTransport` Protocol, generated `Operation` descriptors under resource methods, pagination iterators, a narrow built-in retry policy, async first with a generated `Sync` face | accepted |
| [0027](0027-api-error-taxonomy.md) | API failures are exceptions in a typed hierarchy carrying Mattermost's `AppError` fields and a retryable classification | accepted |
| [0028](0028-runtime-helpers-and-identity-resolution.md) | The Runtime is a thin Event-aware layer over the API client with a fixed helper set; resolution is uncached in the Runtime, caching is an optional plugin (amended by 0029) | accepted |
| [0029](0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) | The synchronous face covers only the API client and an Event-free `Workspace`, and comes from a sans-I/O core with two thin drivers rather than code generation (amends 0004, 0028) | accepted |
| [0030](0030-synchronous-callables-by-explicit-declaration.md) | A synchronous Handler or Provider is declared with `sync_to_thread` and runs in the Bot's own bounded executor, abandonable at drain; Filters and Extractors run inline; everything else is a coroutine function (amends 0004, 0023) | accepted |
| [0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md) | The Core runs on standard-library asyncio under a fixed structured-concurrency discipline, and the framework never chooses the event loop (amends 0004) | accepted |
