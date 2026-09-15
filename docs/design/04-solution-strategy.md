# 4. Solution strategy

_Status: reviewed (#109)._

The handful of decisions that shape everything else. Each item is one paragraph and links to the
ADR that holds the decision.

## What each quality goal is bought with

The five goals of [§1.2](01-introduction-and-goals.md#12-quality-goals), in the order they are
ranked, against the approaches below that serve them. A goal with no approach beside it would be a
goal the strategy ignores, which is what this table is here to make visible. The scenarios that
decide whether a goal is met are [§10](10-quality-requirements.md)'s and are not repeated here
([ADR-0082](../adr/0082-section-4-ties-its-approaches-to-the-ranked-quality-goals-in-one-table.md)).

| Quality goal | The approaches that serve it | Why those | ADR |
|---|---|---|---|
| 1 **Reliability** | A supervised, resumable, never-stalling WebSocketTransport; one consumer and many workers; typed, isolated, bounded conversation state; a narrow error boundary | The failure that hurts a bot is not a crash but an event silently missed, so recovery lives in the transport and memory lives in a store, and both outlive the process that held them | [ADR-0023](../adr/0023-websocket-gateway-resilience.md), [ADR-0005](../adr/0005-one-ingress-many-workers.md), [ADR-0022](../adr/0022-state-plugin-model.md), [ADR-0021](../adr/0021-core-error-boundary.md) |
| 2 **Correctness by mechanism** | The three-phase start with a check phase that lists every failure; type-driven routing that refuses an unreachable handler; four strict type checkers with no suppressions | Each of them moves a mistake from run time to start-up or to the build, which are the only two places a library gets to refuse one | [ADR-0016](../adr/0016-three-phase-start-with-checks.md), [ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md), [ADR-0009](../adr/0009-four-strict-type-checkers.md), [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md) |
| 3 **Testability** | A sans-I/O Exchange under both Faces; one stateful platform double with a conformance suite per Core seam | What is hard to test is I/O, so the decisions are made where there is none and the one place that performs it is doubled once for everybody | [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md), [ADR-0045](../adr/0045-one-stateful-fake-mattermost-is-the-only-platform-double.md), [ADR-0047](../adr/0047-a-conformance-suite-per-core-seam.md) |
| 4 **Modifiability** | Composition over Core-owned Protocols; five layers on four import ranks; every optional capability a Plugin; observability over mechanisms that already exist | Replacing a part has to be a change to the composition and nothing else, so each part is a Protocol the Core owns and the build refuses the import that would have defeated the substitution | [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md), [ADR-0015](../adr/0015-plugin-contract-and-composition.md), [ADR-0048](../adr/0048-observability-is-not-a-core-seam.md) |
| 5 **Security** | Default-on callback authenticity with an explicit off; a record catalogue the framework writes and never configures, guarded by a redaction list | A callback arrives from outside and a log leaves the process: both are edges where the framework, not the application, has to be the one that fails closed | [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md), [ADR-0053](../adr/0053-log-records-are-a-documented-contract.md), [ADR-0055](../adr/0055-one-redaction-list-over-two-sinks.md) |

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
abandoned at the Drain; Filters and Extractors run inline; everything else the framework calls is a
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
included, is a Plugin with a frozen declaration and narrow Contribution Protocols, generic or
adapter-specific, entered in the order the composition lists them and configured through typed
frozen settings objects — which is also where a Plugin receives every capability it consumes, since
Plugins never reach one another and the contract they implement carries no version but only grows.
The Bot composes, checks against a ProcessProfile with the full list of failures, then starts;
lifecycle notifications are typed async Signals.
→ [ADR-0015](../adr/0015-plugin-contract-and-composition.md),
[ADR-0016](../adr/0016-three-phase-start-with-checks.md),
[ADR-0017](../adr/0017-typed-async-lifecycle-signals.md),
[ADR-0069](../adr/0069-the-plugin-contract-carries-no-version-and-grows-by-adding-a-protocol.md),
[ADR-0070](../adr/0070-plugins-do-not-collaborate-the-composition-hands-one-instance-to-both.md),
[ADR-0071](../adr/0071-plugins-start-in-list-order-and-declare-no-dependency-on-each-other.md),
[ADR-0072](../adr/0072-duplicate-names-are-refused-and-every-refusal-is-one-catalogue-row.md),
[ADR-0073](../adr/0073-what-a-plugin-may-not-do.md)

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
Drain, a declared single consumer with an optional lease, and auth-loss detection that ends
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

## Observability over mechanisms that already exist, and a log contract we never configure

The framework owns no observability Protocol. A dispatch fact is the typed outcome a Middleware
reads, an HTTP attempt reaches the `RequestObserver` pair, bounded-resource state is read from a
frozen `bot.stats()` snapshot rather than pushed, and the first-party plugin is one more Plugin
behind the extra named after its library. Logging is a documented catalogue of records whose levels
are chosen by frequency and audience; the framework installs no handler, sets no level and picks no
format, and one redaction list guards the two sinks that could otherwise carry a token, a message
body or a user's data. → [ADR-0048](../adr/0048-observability-is-not-a-core-seam.md),
[ADR-0049](../adr/0049-what-the-framework-makes-observable.md),
[ADR-0050](../adr/0050-bounded-resource-state-is-read-not-pushed.md),
[ADR-0051](../adr/0051-first-party-observability-plugin.md),
[ADR-0053](../adr/0053-log-records-are-a-documented-contract.md),
[ADR-0055](../adr/0055-one-redaction-list-over-two-sinks.md)

## Five layers, four import ranks, one direction

Imports point at the Core: testing toolkit → adapter-specific plugins → (Adapter · generic plugins)
→ Core, and the Core imports nothing above it. The Adapter and the generic plugins share one rank,
so a generic Plugin cannot import the Adapter and "generic" stays a checked property; plugins are
independent of one another and reach each other not at all; nothing imports the testing toolkit. The
building-block view draws exactly this direction and the import-linter contract enforces it.
→ [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md),
[ADR-0070](../adr/0070-plugins-do-not-collaborate-the-composition-hands-one-instance-to-both.md)

## Typed outcomes for caller branches, exceptions for broken contracts

A component returns a closed union of domain-named values when its immediate caller must branch in
normal operation, and raises when a contract is broken or a dependency has failed. The rulebook
holds this and every other tenet as identified, tiered rules with a derived review checklist, and
component documents are written in the order their structural contracts require.
→ [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md),
[ADR-0033](../adr/0033-identified-tiered-rules-with-a-derived-review-checklist.md),
[ADR-0035](../adr/0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md)

## One platform double, one conformance suite per seam

A test of a bot and a test of a storage backend run against the same two things: one stateful
in-memory Mattermost with typed fault injection, and one conformance suite per Core seam that any
implementation — ours or a third party's — is expected to pass. `TestBot` wraps the composed Bot
instead of offering a second composition path, and the toolkit ships behind its own extra, so
nothing in it reaches a test session that did not ask for it by name.
→ [ADR-0044](../adr/0044-the-testing-toolkit-requires-pytest-and-is-activated-explicitly.md),
[ADR-0045](../adr/0045-one-stateful-fake-mattermost-is-the-only-platform-double.md),
[ADR-0046](../adr/0046-testbot-wraps-the-composed-bot.md),
[ADR-0047](../adr/0047-a-conformance-suite-per-core-seam.md)

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
