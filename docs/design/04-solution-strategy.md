# 4. Solution strategy

_Status: reviewed (#38)._

The handful of decisions that shape everything else. Each item is one paragraph and links to the
ADR that holds the decision.

## A small Core admitted by a two-condition test

The Core contains only what every bot needs identically or what is chat-specific with no library
equivalent; everything else is a Plugin, an extra or a recipe. The Core depends on the standard
library alone, ships in one distribution with the Adapter and first-party Plugins, and is enabled by
explicit composition in code. → [ADR-0002](../adr/0002-core-scope-two-condition-test.md)

## A stateless Core, state as a Plugin with an explicit backend

The Core holds nothing between events. Conversation state, isolation and backends belong to the
State Plugin, which cannot start without a backend; in-memory storage needs an explicit
single-process declaration. → [ADR-0003](../adr/0003-stateless-core-state-plugin-with-explicit-backend.md)

## Asyncio only, with a narrow synchronous Face

Dispatch is asyncio-only on the standard library, under a fixed structured-concurrency discipline,
and the framework never chooses the event loop. A synchronous Handler or Provider is accepted only
by an explicit `sync_to_thread` declaration, runs in the Sync executor and may be
abandoned at drain; Filters and Extractors run inline; everything else the framework calls is a
coroutine function. The synchronous Face covers the API client and the Event-free Workspace and is
a thin I/O layer over a sans-I/O Exchange, not generated.
→ [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md),
[ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md),
[ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md)

## One consumer, many workers

A bot is one WebSocket consumer, replicated Webhook processes and any number of workers that reach
the server through the Workspace; processes declare their role. → [ADR-0005](../adr/0005-one-ingress-many-workers.md)

## Composition over Core-owned Protocols, named patterns, strict typing

Bot has routers and plugins rather than inheriting them; the Core owns the Protocols that adapters
and plugins implement; patterns are named and justified per component; no singletons; immutable
events; declarative thin handlers; Python 3.12+ typing as the contract; fail closed.
→ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md)

## A tiny public root

`aiommbot` re-exports Core concepts only; the Adapter, Plugins and testing toolkit are explicit
subpackages; the rest is `_internal`. → [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md)

## One event envelope, type-driven routing, typed extraction

Every inbound event is `Event[P, R]`; the Adapter owns payload types and an explicit registry with
`RawEvent` as the fallback. Handlers subscribe by the annotation of their first parameter on a
router tree walked depth-first to the first match; dispatch returns a typed outcome; unreachable
handlers stop start-up. Filters are predicates, Extractors produce typed values, signatures are
closed. → [ADR-0012](../adr/0012-generic-event-envelope-with-adapter-payloads.md),
[ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md),
[ADR-0014](../adr/0014-filters-and-extractors-with-closed-handler-signatures.md)

## One Adapter, explicit Plugins, three-phase start, typed Signals

Exactly one Adapter supplies the platform vocabulary; every optional capability, transports
included, is a Plugin with a frozen declaration and narrow contribution Protocols, generic or
adapter-specific, ordered topologically by declared dependencies and configured through typed
frozen settings objects. The Bot composes, checks against a ProcessProfile with the full list of
failures, then starts; lifecycle notifications are typed async Signals.
→ [ADR-0015](../adr/0015-plugin-contract-and-composition.md),
[ADR-0016](../adr/0016-three-phase-start-with-checks.md),
[ADR-0017](../adr/0017-typed-async-lifecycle-signals.md)

## Core-owned, type-keyed dependency injection

A small stdlib resolver in the Core behind the `DependencyProvider` Protocol: dependencies keyed by
type with `Qualifier` for homonyms, two Scopes (App, Event), typed Providers from plugins and the
application, a graph validated and resolution plans compiled in the check phase. Extractors win
over providers; built-ins are minimal and never the Bot; overrides live only in the testing
toolkit; external containers plug in as bridge plugins.
→ [ADR-0018](../adr/0018-core-owned-type-keyed-dependency-injection.md),
[ADR-0019](../adr/0019-handler-parameter-resolution-rules.md)

## Two-layer middleware with a narrow error boundary

Inbound and Handler middleware layers, registered on the Bot or a Router, with an async
`__call__(event, call_next, *deps) -> Outcome` contract, typed Event-scope publication instead of a
data dictionary, typed handler Flags, topological order from explicit lists and plugin
declarations. The outermost link is the Core's ErrorBoundary: log without payload, report, return
`Failed`; a failing process is an explicit policy.
→ [ADR-0020](../adr/0020-two-layer-middleware-chain.md),
[ADR-0021](../adr/0021-core-error-boundary.md)

## Typed, isolated, bounded conversation state

The State plugin keys state by a `StateKey`, models dialogues as `Flow[Data]` with typed versioned
data, stores through the Core's `KeyValueStore` (compare-and-set) and `LockProvider`, isolates
events per key by default, surfaces conflicts and stale records as typed outcomes, and bounds
every record with a sliding logical TTL of one hour by default. In-memory and Redis first-party.
→ [ADR-0022](../adr/0022-state-plugin-model.md)

## A supervised, resumable, never-stalling WebSocketTransport

One supervised reconnect loop per socket with resume and sequence continuity, a heartbeat and
silence monitor, a reader that never stalls into a bounded queue with typed per-kind overflow, a
graceful drain, a declared single consumer with an optional lease, and auth-loss detection that ends
in `FatalError(AuthRevoked)`; the socket library sits behind one Core Protocol.
→ [ADR-0023](../adr/0023-websocket-gateway-resilience.md)

## Callbacks as events with a reply channel; default-on callback authenticity

Button clicks and dialog submissions are Events in the same routers, distinguished only by the
payload-bound, single-use Reply channel with a deadline and an empty-200 default. The Webhook is a
bare ASGI callable plus `handle_callback`. Authenticity is a self-issued Callback token behind
`CallbackTokenCodec`, on by default with an explicit off; an expired or replayed token becomes a
`StaleAction` event.
→ [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md)

## A generated, standalone Mattermost API client behind Core-owned Protocols

Models are generated from a pinned, overlaid OpenAPI spec into standard-library dataclasses and
serialised through the Core's `Codec` Protocol. The REST client is a standalone typed API client
over an `HTTPTransport` Protocol, with generated `Operation` descriptors, pagination, a narrow retry
policy and a hand-written synchronous Face; API failures are a typed exception hierarchy with a
retryable flag. The Runtime is a thin Event-aware layer over the client with a fixed helper set;
identity resolution is uncached and caching is a Plugin. Observability is an optional, replaceable
observer that never changes behaviour.
→ [ADR-0025](../adr/0025-generated-dataclass-models-with-a-codec-protocol.md),
[ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md),
[ADR-0027](../adr/0027-api-error-taxonomy.md),
[ADR-0028](../adr/0028-runtime-helpers-and-identity-resolution.md)

## Five layers, four import ranks, one direction

Imports point at the Core: testing toolkit → adapter-specific plugins → (Adapter · generic plugins)
→ Core, and the Core imports nothing above it. The Adapter and the generic plugins share one rank, so
a generic Plugin cannot import the Adapter and "generic" stays a checked property; plugins are
independent of one another and collaborate only through Core-owned Protocols; nothing imports the
testing toolkit. The building-block view draws exactly this direction and the import-linter contract
enforces it.
→ [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md)

## Typed outcomes for caller branches, exceptions for broken contracts

A component returns a closed union of domain-named values when its immediate caller must branch in
normal operation, and raises when a contract is broken or a dependency has failed. The rulebook
holds this and every other tenet as identified, tiered rules with a derived review checklist, and
component documents are written in the order their structural contracts require.
→ [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md),
[ADR-0033](../adr/0033-identified-tiered-rules-with-a-derived-review-checklist.md),
[ADR-0035](../adr/0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md)

## Quality by mechanism, not by memory

Python `>=3.12` until each version's EOL, with `typing_extensions` as the Core's only runtime
dependency and one compat module. Four type checkers — mypy, pyright, pyrefly, ty — all beyond
strict and all blocking, with `tests/typing` asserting the public contract and negative cases. No
suppression exists in the package outside Quarantine modules, whose baseline only decreases. ruff
with every rule plus preview and explained ignores, wemake-python-styleguide, semgrep rules for
banned patterns, import-linter for the layer contract above, slotscheck, and the supply-chain
checks, driven by `just` and pre-commit.
→ [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md),
[ADR-0009](../adr/0009-four-strict-type-checkers.md),
[ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md),
[ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md)
