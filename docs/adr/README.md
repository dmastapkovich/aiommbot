# Architecture decision records

One decision per file, numbered in order of acceptance. An ADR always states the current decision:
a later decision that changes it rewrites it in the same commit, and the two link each other through
`amends` / `amended-by`; a decision withdrawn in full retires its file, and its number stays below
with a pointer to the ADRs that replaced it. Format and triggers: [`_template.md`](_template.md).
ADRs are produced by wayfinder tickets; the map (#1) and `docs/design/TRACKER.md` §B list which
ticket owns which decision.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-fresh-start-as-a-public-package.md) | aiommbot 0.5.0 is designed from scratch as a public package with no compatibility promise toward any earlier release | accepted |
| [0002](0002-core-scope-two-condition-test.md) | The core admits a capability only if every bot needs it identically or it is chat-specific with no library equivalent; stdlib-only core, one distribution, explicit composition | accepted |
| [0003](0003-stateless-core-state-plugin-with-explicit-backend.md) | The core is stateless; conversation state is a plugin that cannot start without an explicit backend | accepted |
| 0004 | Retired. One asyncio engine with a narrow synchronous Face — decided in [0029](0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md), [0030](0030-synchronous-callables-by-explicit-declaration.md) and [0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md) | retired |
| [0005](0005-one-ingress-many-workers.md) | A bot scales as one WebSocket consumer, replicated Webhook processes and many workers, never as identical replicas | accepted |
| [0006](0006-architectural-tenets-of-the-core.md) | The core is built by composition over Protocols it owns, with named patterns and strict typing | accepted |
| [0007](0007-tiny-public-root-with-explicit-subpackages.md) | The public API is a tiny root namespace plus explicit subpackages; everything else is internal | accepted |
| [0008](0008-python-floor-3-12-with-typing-extensions.md) | Python 3.12 is the floor, supported until EOL, with typing_extensions as the Core's only runtime dependency (amends 0002) | accepted |
| [0009](0009-four-strict-type-checkers.md) | Four type checkers run at maximum strictness and all of them block | accepted |
| [0010](0010-zero-suppressions-with-a-quarantine.md) | Zero lint and type suppressions in the package; foreign types wrapped in quarantine modules | accepted |
| [0011](0011-lint-format-and-architecture-toolchain.md) | One toolchain enforces style, complexity, architecture and dependencies; `just` is the single entry point | accepted |
| [0012](0012-generic-event-envelope-with-adapter-payloads.md) | Inbound events are one generic envelope `Event[P, R]`; payload types and their registry belong to the Adapter | accepted |
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
| [0023](0023-websocket-gateway-resilience.md) | The WebSocketTransport is one supervised reconnect loop with heartbeat, resume, seq continuity, a never-stalling reader, a graceful drain, auth-loss detection and a replaceable library (websockets primary, picows optional) | accepted |
| [0024](0024-webhook-ingress-and-callback-security.md) | Interactive callbacks are events with a payload-bound reply channel; the webhook plugin is a bare ASGI callable; authenticity is a default-on self-issued HMAC token with no expiry unless configured | accepted |
| [0025](0025-generated-dataclass-models-with-a-codec-protocol.md) | Mattermost models are generated from a pinned, overlaid OpenAPI spec into standard-library dataclasses; serialisation goes through a Core-owned `Codec` Protocol with msgspec as the shipped implementation | accepted |
| [0026](0026-standalone-typed-api-client-over-an-http-transport-protocol.md) | The Mattermost REST client is a standalone typed API client: httpx2 behind an `HTTPTransport` Protocol, generated `Operation` descriptors under resource methods, pagination iterators, a narrow built-in retry policy, async first with a synchronous Face | accepted |
| [0027](0027-api-error-taxonomy.md) | API failures are exceptions in a typed hierarchy carrying Mattermost's `AppError` fields and a retryable classification | accepted |
| [0028](0028-runtime-helpers-and-identity-resolution.md) | The Runtime is a thin Event-aware layer over the API client with a fixed helper set; resolution is uncached in the Runtime, caching is an optional plugin | accepted |
| [0029](0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) | The synchronous Face covers only the API client and an Event-free `Workspace`, and is a thin I/O layer over a sans-I/O Exchange instead of async-to-sync code generation | accepted |
| [0030](0030-synchronous-callables-by-explicit-declaration.md) | A synchronous Handler or Provider is declared with `sync_to_thread` and runs in the Sync executor, abandonable at drain; Filters and Extractors run inline; everything else is a coroutine function (amends 0014, 0019, 0023) | accepted |
| [0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md) | The Core runs on standard-library asyncio under a fixed structured-concurrency discipline, and the framework never chooses the event loop | accepted |
| [0032](0032-layer-model-and-direction-of-allowed-dependencies.md) | Imports point at the Core — testing toolkit → adapter-specific plugins → (Adapter · generic plugins) → Core — and a generic Plugin may never import the Adapter | accepted |
| [0033](0033-identified-tiered-rules-with-a-derived-review-checklist.md) | A style rule is an identified, tiered statement carrying a reason, an example and its limits, and the review checklist is derived from the rules and nothing else | accepted |
| [0034](0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md) | A typed outcome expresses a branch the immediate caller must take; an exception expresses a broken contract or a failed dependency | accepted |
| [0035](0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md) | The order in which component design documents are written is a topological sort of structural §3 dependencies, not the layer table | accepted |
| [0036](0036-reply-slot-as-a-second-type-parameter-over-a-core-owned-reply-channel.md) | The reply slot is a second, declared-contravariant type parameter on `Event` typed by a Core-owned `ReplyChannel[R]` Protocol — the Core's twelfth seam; `ReplyAlreadySent` is Core-owned beside it | accepted |
| [0037](0037-derive-is-the-only-enrichment-path-for-an-event.md) | `Event.derive(meta: EventMeta[R2]) -> Event[P, R2]` is the only way to obtain an enriched envelope, and `dataclasses.replace`, `copy.replace` and `__replace__` on an `Event` are banned | accepted |
| [0038](0038-seam-inventory-records-the-direction-of-the-call.md) | The Core's seam inventory records the direction of the call — eleven required Protocols and one provided | accepted |
| [0039](0039-src-layout-with-tests-and-examples-beside-the-package.md) | The repository is a `src/` layout, with tests, runnable examples and the catalogue beside the package | accepted |
| [0040](0040-one-package-directory-per-import-rank.md) | Every import rank is a package directory, and every module is named after the `CONTEXT.md` term it holds | accepted |
| [0041](0041-default-dependencies-and-one-extra-per-optional-library.md) | The distribution installs the four libraries a Mattermost bot cannot run without, and every other library is an extra named after it | accepted |
| [0042](0042-a-public-name-is-documented-at-its-package-path.md) | A public name is documented at its package path, and a module path is never part of the public surface | accepted |
| [0043](0043-explicit-re-export-with-a-reference-page-as-the-public-list.md) | A public name is a redundant-alias re-export listed on a hand-written reference page, and the package carries no `__all__` | accepted |
| [0044](0044-the-testing-toolkit-requires-pytest-and-is-activated-explicitly.md) | The testing toolkit imports pytest through an extra named after it, and one line in the root `conftest.py` activates its plugin (amends 0041) | accepted |
| [0045](0045-one-stateful-fake-mattermost-is-the-only-platform-double.md) | One stateful `FakeMattermost` is the only platform double, and its ports, its faults and its events are its own surface | accepted |
| [0046](0046-testbot-wraps-the-composed-bot.md) | A bot is tested by wrapping the composed `Bot`, and the toolkit offers no second way to compose one | accepted |
| [0047](0047-a-conformance-suite-per-core-seam.md) | Every Core seam has a conformance suite, delivered as a factory over the implementer's factory, and tightening one is a change to the Protocol (amends 0015) | accepted |
| [0048](0048-observability-is-not-a-core-seam.md) | The Core has no observability Protocol of its own: a dispatch fact travels on the typed `Outcome` through the Middleware layers, and the observability seam is `RequestObserver` with its synchronous pair (amends 0002, 0006, 0013, 0017, 0021, 0022, 0026, 0030, 0033, 0038, 0047) | accepted |
| [0049](0049-what-the-framework-makes-observable.md) | Every fact the framework makes observable travels on a mechanism that already exists, and storage is observed by decorating its Protocol (amends 0023) | accepted |
| [0050](0050-bounded-resource-state-is-read-not-pushed.md) | The depth of a bounded resource is read from a frozen `bot.stats()` snapshot, contributed by a seventh `Contributes*` Protocol, never pushed (amends 0015, 0023) | accepted |
| [0051](0051-first-party-observability-plugin.md) | Observability ships as one generic plugin behind two library-named extras, follows the OpenTelemetry conventions with the transport stream as the destination, takes the Prometheus registry as an argument, and bounds its cardinality with an allow-list and a start-up Check (amends 0041) | accepted |
| [0052](0052-log-levels-by-frequency-and-audience.md) | A record's level is decided by how often the fact happens and who needs it: nothing per delivery above DEBUG, INFO for lifecycle transitions only, one ERROR per escaped exception, and neither CRITICAL nor a custom level ever | accepted |
| [0053](0053-log-records-are-a-documented-contract.md) | The set of log records is a documented contract checked against the code in both directions, and the framework never configures logging, ships no handler beyond `NullHandler` and offers no helper | accepted |
| [0054](0054-correlation-reaches-a-log-record-in-three-layers.md) | A correlation identifier reaches a log record through the call's own `extra`, the name of the asyncio task and a Core `ContextVar` with a filter the application attaches — never through the process-global record factory | accepted |
| [0055](0055-one-redaction-list-over-two-sinks.md) | `REDACTED_FIELDS` is forty field names that may never appear in a log record or an observability record, matched exactly on the normalised name; an exception's contents stay `ST-ERR-08`'s | accepted |
