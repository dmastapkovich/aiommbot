# 5. Building block view

_Status: reviewed (#38)._

The static decomposition, opened one level at a time. It is the **inventory** the
`LLD: <component>` tickets are generated from (#41), and the direction of every arrow is the layer
contract of [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md), which
becomes the import-linter contract.

## 5.0 How to read this section

**Levels.** Level 1 is the Bot process as one box — that is [§3](03-context-and-scope.md).
Level 2 is the containers a deployment runs (5.2). Level 2 is opened once more into the four
**layers** inside a process (5.3). Level 3 is the components inside each layer, one diagram per
layer (5.5–5.9), because one diagram answers one question.

**Two ranks of block.** Every row of every inventory table is one of:

| Kind | Meaning | Gets a design document |
|---|---|---|
| **component** | A designable unit with its own contract, failure modes and pattern story | yes — `components/<term>.md` |
| **part** | A named piece that only makes sense inside one component | no — described inside that component's document |
| **seam** | A Protocol the Core owns so implementations can be substituted | no — described inside the document of the component that consumes it; all of them listed in 5.4 |

The distinction exists so that `RetryPolicy` and `NonceStore` are documented where they are used
instead of becoming two-page documents of their own, while `Workspace` and the two Faces — which
[ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) requires to be
designed — each get one.

**Diagram boxes and their documents.** `diagrams.md` requires every box on a Component diagram to
link to its document; Mermaid's C4 boxes carry no reliable link on GitHub, so the inventory table
directly under each diagram is where the link lives, one row per box.

**Names.** Every block is named with its `CONTEXT.md` term, exactly. A block that needed a term got
one in this ticket rather than a synonym.

## 5.1 Level 1 — the system

One box: the **Bot** process, an application's code composed with aiommbot. Its partners and its
interfaces are [§3](03-context-and-scope.md).

## 5.2 Level 2 — containers

The framework has no container of its own; what a deployment runs are processes composed from the
same `Bot` object, differing only in which Transports are in the plugin list and what the
`ProcessProfile` declares. Exactly one WebSocket consumer per bot account is the one hard
constraint ([ADR-0005](../adr/0005-one-ingress-many-workers.md)); the rest replicates.

```mermaid
C4Container
    title Containers — a bot deployed in the split shape
    Person(user, "Mattermost user", "Posts, clicks buttons, submits dialogs")
    System_Ext(mm, "Mattermost server", "Events, REST API, callbacks")
    Container_Boundary(deployment, "One bot account") {
        Container(consumer, "WebSocket consumer", "Python process", "Exactly one. WebSocketTransport plugin; ProcessProfile.websocket_consumer")
        Container(ingress, "Webhook ingress", "Python process x N", "Webhook plugin behind an ASGI server the application runs")
        Container(worker, "Worker or script", "Python process x N", "No Transport. Uses Workspace or SyncWorkspace")
    }
    ContainerDb_Ext(redis, "State store", "Redis", "Conversation state, isolation locks, nonces, identity cache")
    Rel(user, mm, "posts, clicks")
    Rel(mm, consumer, "events", "WebSocket")
    Rel(mm, ingress, "callbacks", "HTTPS POST")
    Rel(consumer, mm, "REST", "HTTPS")
    Rel(ingress, mm, "reply + REST", "HTTPS")
    Rel(worker, mm, "REST", "HTTPS")
    Rel(consumer, redis, "state, locks")
    Rel(ingress, redis, "state, locks, nonces")
```

| Container | Responsibility | Composition | Replicates |
|---|---|---|---|
| WebSocket consumer | Holds the one long-lived socket, decodes events, dispatches them | `WebSocketTransport` in the plugin list, `websocket_consumer=True` | no — a second replica is a standby behind a `LockProvider` lease |
| Webhook ingress | Serves interactive callbacks within the reply deadline | `Webhook` in the plugin list; the application's ASGI server hosts it | yes, behind a load balancer |
| Worker or script | Acts on Mattermost with no inbound events | no Transport at all; `Workspace` or `SyncWorkspace` | yes |

All three collapse into one process in the all-in-one shape; which shape to run, and the
Kubernetes consequences of the drain budget, are [§7](07-deployment-view.md).

## 5.3 Level 2 opened — the layers inside a process

```mermaid
C4Component
    title Layers inside a Bot process — arrows are the allowed direction of imports
    Component(testing, "Testing toolkit", "aiommbot.testing", "Doubles, conformance suites, TestBot")
    Component(aplugins, "Adapter-specific plugins", "Plugin", "WebSocketTransport, Webhook, IdentityCache")
    Component(adapter, "Adapter", "Mattermost", "Platform vocabulary, API client, Workspace, Runtime")
    Component(gplugins, "Generic plugins", "Plugin", "State, storage backends, DI bridges, observer extra")
    Component(core, "Core", "stdlib only", "Envelope, routing, dispatch, middleware, DI, lifecycle, Protocols")
    Rel(testing, aplugins, "doubles and drives")
    Rel(testing, adapter, "doubles and drives")
    Rel(testing, gplugins, "doubles and drives")
    Rel(testing, core, "doubles and drives")
    Rel(aplugins, adapter, "uses the platform vocabulary")
    Rel(aplugins, core, "implements Core Protocols")
    Rel(adapter, core, "implements Core Protocols")
    Rel(gplugins, core, "implements Core Protocols")
```

The two middle boxes are **one rank, not two**: a generic Plugin may not import the Adapter, which
is what makes "generic" a checked property rather than a claim. Plugins are independent of each
other in both directions; a plugin that needs another's capability reaches the Core Protocol behind
it. The Core imports no third-party package. Nothing imports the testing toolkit.
→ [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md),
[ADR-0015](../adr/0015-plugin-contract-and-composition.md),
[ADR-0002](../adr/0002-core-scope-two-condition-test.md)

Where this meets #24: the layer names and their direction are this section's line; the package
paths, the `__all__` policy and the extras that realise them are #24's.

## 5.4 The seams of the Core

The single point of dependency inversion ([ADR-0006](../adr/0006-architectural-tenets-of-the-core.md)
tenet 2): every Protocol the Core owns, who implements it, and the document that specifies it.
None of these rows is a component — a Protocol is specified inside the document of the component
that consumes it, so that the contract and its reason stay in one place.

| Seam | Consumed by | Shipped implementations | Specified in | Decision |
|---|---|---|---|---|
| `Transport` | Dispatcher | WebSocketTransport, Webhook | `dispatcher.md` | [ADR-0015](../adr/0015-plugin-contract-and-composition.md) |
| `DependencyProvider` | Bot | the Core's own resolver; dishka and wireup bridges | `dependency-provider.md` | [ADR-0018](../adr/0018-core-owned-type-keyed-dependency-injection.md) |
| `KeyValueStore` | State, Webhook, IdentityCache | in-memory, Redis | `key-value-store.md` | [ADR-0022](../adr/0022-state-plugin-model.md) |
| `LockProvider` | State, WebSocketTransport | in-memory, Redis | `key-value-store.md` | [ADR-0022](../adr/0022-state-plugin-model.md) |
| `Codec` | API client, Transports, State | `MsgspecCodec` | `codec.md` | [ADR-0025](../adr/0025-generated-dataclass-models-with-a-codec-protocol.md) |
| `HTTPTransport`, `SyncHTTPTransport` | Face | httpx2; the in-memory double implements both in one class | `face.md` | [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md), [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) |
| `WebSocketConnection` | WebSocketTransport | `websockets` 17 primary, `picows` extra, in-memory connector | `websocket-transport.md` | [ADR-0023](../adr/0023-websocket-gateway-resilience.md) |
| `StateKeyProvider` | State | the Adapter's | `state.md` | [ADR-0022](../adr/0022-state-plugin-model.md) |
| `TokenProvider`, `SyncTokenProvider` | WebSocketTransport, API client, Face | none — the application's | `face.md` | [ADR-0023](../adr/0023-websocket-gateway-resilience.md), [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) |
| `CallbackTokenCodec` | Webhook | stdlib HMAC-SHA256; `pyseto` PASETO extra | `callback-token.md` | [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md) |
| `RequestObserver` | API client | none by default; a first-party extra | `api-client.md` | [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md) |

## 5.5 Level 3 — the Core

```mermaid
C4Component
    title Components of the Core
    Component(bot, "Bot", "Composition root", "compose, check, start; owns everything below")
    Component(dispatcher, "Dispatcher", "Mediator", "Walks the tree, drives both middleware layers, returns Outcome")
    Component(mw, "Middleware", "Chain of Responsibility", "Inbound and Handler layers, typed publication")
    Component(eb, "ErrorBoundary", "Outermost link", "Catches Exception, logs without payload, returns Failed")
    Component(router, "Router", "Handler tree", "Registration, freeze, HandlerSpec, reachability")
    Component(filter, "Filter", "Strategy + Composite", "Pure predicates over an Event")
    Component(extractor, "Extractor", "Typed parser", "Value, NoMatch or Invalid")
    Component(di, "DependencyProvider", "Resolver", "Type-keyed providers, two Scopes, compiled plans")
    Component(signal, "Signal", "Observer", "Typed asynchronous lifecycle notifications")
    Component(executor, "Sync executor", "Bounded pool", "Runs declared synchronous callables; abandons at drain")
    Component(event, "Event", "Immutable envelope", "Event[P], EventMeta, the reply-channel slot")
    Rel(bot, dispatcher, "starts and feeds", "TaskGroup")
    Rel(bot, signal, "publishes lifecycle")
    Rel(bot, executor, "owns and sizes")
    Rel(bot, di, "compiles the graph at check")
    Rel(dispatcher, mw, "drives", "await")
    Rel(dispatcher, eb, "wraps every dispatch in")
    Rel(dispatcher, router, "walks depth-first")
    Rel(dispatcher, di, "resolves the plan")
    Rel(dispatcher, executor, "offloads declared sync handlers")
    Rel(router, filter, "gates with")
    Rel(router, extractor, "parses with")
    Rel(mw, event, "derives enriched")
    Rel(filter, event, "reads")
    Rel(extractor, event, "reads")
```

| Block | Kind | Responsibility | Document | Decisions |
|---|---|---|---|---|
| **Bot** | component | Composition root: gathers plugin contributions, orders them topologically, runs the three-phase compose → check → start, owns the lifecycle and the entry points | `bot.md` | [ADR-0015](../adr/0015-plugin-contract-and-composition.md), [ADR-0016](../adr/0016-three-phase-start-with-checks.md), [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md) |
| `PluginSpec`, `Check`, `ProcessProfile`, `run()`/`serve()` | part | The plugin declaration, the typed check objects, the process role, the two entry points | `bot.md` | same |
| **Dispatcher** | component | Receives an Event from a Transport, drives Inbound then Handler middleware, walks the Router tree to the first match, resolves parameters, returns the typed `Outcome` to the Transport | `dispatcher.md` | [ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md), [ADR-0020](../adr/0020-two-layer-middleware-chain.md) |
| `Outcome`, `MatchedHandler`, `Skip` | part | The typed dispatch result, the Event-scoped publication after a match, the rare continue-the-walk signal | `dispatcher.md` | same |
| **Router** | component | The handler tree: registration by annotation, adapter aliases, filter gates, freeze, `bot.routes()`, unreachable-handler check | `router.md` | [ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md) |
| `HandlerSpec`, `Flag` | part | The frozen record of a registration, and the typed objects that parametrise middleware from a subscription | `router.md` | [ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md), [ADR-0020](../adr/0020-two-layer-middleware-chain.md) |
| **Filter** | component | Pure predicates over an Event, composable with `&`, `\|`, `~`, renderable as data | `filter.md` | [ADR-0014](../adr/0014-filters-and-extractors-with-closed-handler-signatures.md) |
| **Extractor** | component | Typed parsing of an Event into a handler parameter, yielding `Value`, `NoMatch` or `Invalid` | `extractor.md` | [ADR-0014](../adr/0014-filters-and-extractors-with-closed-handler-signatures.md) |
| **Middleware** | component | The two named layers, the `__call__(event, call_next, *deps) -> Outcome` contract, typed Event-scope publication, topological ordering frozen as `bot.middleware()` | `middleware.md` | [ADR-0020](../adr/0020-two-layer-middleware-chain.md) |
| **ErrorBoundary** | component | The non-removable outermost link: catch `Exception`, log without payload, report, return `Failed`; let `BaseException` and `FatalError` through | `error-boundary.md` | [ADR-0021](../adr/0021-core-error-boundary.md) |
| `AiommbotError`, `FatalError`, `AiommbotWarning` | part | The roots of the exception hierarchy and the public warning class | `error-boundary.md` | [ADR-0021](../adr/0021-core-error-boundary.md), [ADR-0027](../adr/0027-api-error-taxonomy.md), [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md) |
| **DependencyProvider** | component | The Core's small type-keyed resolver behind the Protocol of the same name: providers, two Scopes, graph validation and per-handler resolution plans compiled at check time | `dependency-provider.md` | [ADR-0018](../adr/0018-core-owned-type-keyed-dependency-injection.md), [ADR-0019](../adr/0019-handler-parameter-resolution-rules.md) |
| `Provider`, `Qualifier`, `Scope`, `Resolution plan`, the built-in set, dishka and wireup bridges | part | The declaration, the homonym marker, the two lifetimes, the compiled plan, what the Core injects, and the two bridge plugins | `dependency-provider.md` | same |
| **Signal** | component | `Signal[T]`: typed asynchronous lifecycle notification, every subscriber runs, failures collected not swallowed | `signal.md` | [ADR-0017](../adr/0017-typed-async-lifecycle-signals.md) |
| **Sync executor** | component | The Bot's own bounded thread pool: colour resolution at registration, `sync_to_thread` warnings, `contextvars` copying, dropping the wait at drain with `HandlerAbandoned` | `sync-executor.md` | [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md) |
| **Event** | component | The immutable generic envelope and its metadata; the only Core type every other block reads | `event.md` | [ADR-0012](../adr/0012-generic-event-envelope-with-adapter-payloads.md) |
| `EventMeta`, `CorrelationId`, the reply-channel slot | part | Transport, receive time, correlation, sequence, raw data, and the optional typed reply slot | `event.md` | [ADR-0012](../adr/0012-generic-event-envelope-with-adapter-payloads.md), [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md) |

## 5.6 Level 3 — the Mattermost Adapter

```mermaid
C4Component
    title Components of the Mattermost Adapter
    Component(runtime, "Runtime", "Event-aware", "answer, reply, update, delete, open_dialog")
    Component(workspace, "Workspace", "Event-free", "send, send_direct, ephemeral, upload, download, resolve")
    Component(client, "API client", "Standalone", "Resource groups over Operation descriptors, pagination, retries")
    Component(face, "Face", "Thin I/O layer", "Two of them: asynchronous and synchronous")
    Component(exchange, "Exchange", "sans-I/O", "Build request, parse response, decide retry, advance a page")
    Component(codec, "Codec", "MsgspecCodec", "Strict encode, decode, convert")
    Component(models, "Generated model", "Committed output", "Frozen dataclasses and Operation descriptors")
    Component(generator, "Model generator", "Build time", "Pinned spec + Overlay -> committed models, --check")
    Component(registry, "EventRegistry", "Platform vocabulary", "Event name -> payload type, RawEvent fallback")
    Component(auth, "AuthLossDetector", "Shared probe", "ping reply + /users/me, one refresh, then FatalError")
    Rel(runtime, workspace, "composes and re-exposes")
    Rel(runtime, client, "reaches the rest through", "runtime.api")
    Rel(workspace, client, "calls")
    Rel(client, exchange, "asks what to do next")
    Rel(client, face, "performs I/O through")
    Rel(face, exchange, "feeds responses back into")
    Rel(exchange, models, "reads Operation from")
    Rel(client, codec, "encodes and decodes with")
    Rel(codec, models, "decodes into")
    Rel(registry, models, "reuses REST models")
    Rel(registry, codec, "decodes payloads with")
    Rel(auth, client, "probes /users/me through")
    Rel(generator, models, "emits", "build time")
```

| Block | Kind | Responsibility | Document | Decisions |
|---|---|---|---|---|
| **EventRegistry** | component | The platform vocabulary: event name → payload type, explicit registration, duplicate-name check, and the wire quirks handled once at decode | `event-registry.md` | [ADR-0012](../adr/0012-generic-event-envelope-with-adapter-payloads.md) |
| The 15 first-class payloads, `RawEvent` | part | The typed payloads of 0.5.0 and the fallback that keeps every other name routable | `event-registry.md` | [ADR-0012](../adr/0012-generic-event-envelope-with-adapter-payloads.md); full catalogue is #45 |
| Platform filters and router aliases | part | `ChatType`, `Text`, `@router.message`/`action`/`dialog` reducing to `@router.on` | `filter.md`, `router.md` | [ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md), [ADR-0014](../adr/0014-filters-and-extractors-with-closed-handler-signatures.md) |
| `StateKeyProvider` implementation | part | Builds a `StateKey` from an Event according to the strategy the State plugin is configured with | `state.md` | [ADR-0022](../adr/0022-state-plugin-model.md) |
| **Model generator** | component | Build time only: applies the OpenAPI Overlay to the ESR-pinned spec, emits models and `Operation` descriptors for both Faces idempotently, fails the build on a hand edit, watches upstream drift nightly | `model-generator.md` | [ADR-0025](../adr/0025-generated-dataclass-models-with-a-codec-protocol.md) |
| **Generated model** | component | The committed frozen dataclasses and the `Operation` descriptors: the optionality rules, `UNSET` on requests, the hand-written models for what the spec leaves as `object` | `generated-model.md` | [ADR-0025](../adr/0025-generated-dataclass-models-with-a-codec-protocol.md) |
| `Operation` | part | The frozen descriptor of one REST call, public and user-constructible for endpoints outside the spec | `generated-model.md` | [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md) |
| **Codec** | component | `MsgspecCodec`, the only shipped implementation of the Core seam, registered as an App-scoped provider; the `dec_hook` that unpacks Mattermost's JSON-in-JSON | `codec.md` | [ADR-0025](../adr/0025-generated-dataclass-models-with-a-codec-protocol.md) |
| **API client** | component | The standalone `MattermostClient`: resource groups by spec tag, `execute` as the typed escape hatch, pagination iterators, the observability seam | `api-client.md` | [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md) |
| `RetryPolicy`, `ApiError` and its subclasses, `iter_*`, the first-party observer extra | part | The narrow retry setting, the failure hierarchy with `retryable`, the pagination iterators, and the optional observer | `api-client.md` | [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md), [ADR-0027](../adr/0027-api-error-taxonomy.md); observer shape finalised in #29 |
| **Exchange** | component | The sans-I/O heart shared by both Faces: build the request from an `Operation`, classify the response, decide the retry, advance a page — pure functions, tested once without a network | `exchange.md` | [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) |
| **Face** | component | The two thin I/O layers over the Exchange — asynchronous and synchronous — and the parity mechanisms that keep them in step | `face.md` | [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) |
| The httpx2 binding of `HTTPTransport`/`SyncHTTPTransport`, `TokenProvider`/`SyncTokenProvider` use, the one-instance-per-thread contract | part | The shipped transport implementation, how credentials are read on each face, and the threading promise the synchronous face does *not* make | `face.md` | [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md), [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) |
| **Workspace** | component | The Event-free handle on one server — `send`, `send_direct`, `ephemeral`, `upload`, `download`, `users.resolve`, `channels.direct` — independently constructible, and the only helper layer with a synchronous face | `workspace.md` | [ADR-0028](../adr/0028-runtime-helpers-and-identity-resolution.md), [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) |
| `UserRef` resolution | part | The typed union resolved in priority order, with ambiguity and absence as typed outcomes | `workspace.md` | [ADR-0028](../adr/0028-runtime-helpers-and-identity-resolution.md) |
| **Runtime** | component | The Event-bound layer a Handler receives: `answer`, `reply`, `update`, `delete`, `open_dialog`, taking channel, `root_id` and `trigger_id` from the Event; composes a Workspace and exposes `runtime.api` | `runtime.md` | [ADR-0028](../adr/0028-runtime-helpers-and-identity-resolution.md), [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) |
| **AuthLossDetector** | component | Turns a mute socket into a decision: parse every `ping` reply, probe `/users/me`, refresh once, then `FatalError(AuthRevoked)` carrying ids and never the token. Shared by the gateway and the client | `auth-loss-detector.md` | [ADR-0023](../adr/0023-websocket-gateway-resilience.md), [ADR-0027](../adr/0027-api-error-taxonomy.md) |

## 5.7 Level 3 — generic plugins

Bound to the Core only. They may not import the Adapter
([ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md)).

```mermaid
C4Component
    title Components of the generic plugins
    Component(state, "State", "Plugin", "Flow, StateContext, isolation, schema versions, TTL")
    Component(backends, "KeyValueStore and LockProvider backends", "Plugin", "In-memory and Redis")
    Rel(state, backends, "stores and locks through", "Core Protocols, never by import")
```

State reaches the backends the way every plugin reaches every other capability — through the Core
Protocol, never by importing the plugin that also implements it.

State is also the case that justifies the rank of
[ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md): it needs a `StateKey`
built from Mattermost identifiers, yet it may not import the Adapter. It consumes the Core
`StateKeyProvider` seam and the Adapter's implementation is injected — which is precisely what
keeps the State plugin usable under a second adapter that does not exist yet.

| Block | Kind | Responsibility | Document | Decisions |
|---|---|---|---|---|
| **State** | component | Conversation state: `Flow[Data]`, `StateContext`, the `InState` filter, per-key isolation as Inbound middleware, compare-and-set writes, schema versions, the sliding logical TTL | `state.md` | [ADR-0003](../adr/0003-stateless-core-state-plugin-with-explicit-backend.md), [ADR-0022](../adr/0022-state-plugin-model.md) |
| `StateKey`, `Flow`, `StateContext`, the isolation middleware, `Conflict`, `StaleState` | part | The key and its strategy, the typed flow and its versioned data, the handle a handler receives, and the two typed failure outcomes | `state.md` | [ADR-0022](../adr/0022-state-plugin-model.md) |
| **KeyValueStore** and **LockProvider** backends | component | The two first-party implementations of both storage seams — in-memory for a declared single process, Redis for TTL and distributed locks — plus the conformance suite external backends must pass | `key-value-store.md` | [ADR-0022](../adr/0022-state-plugin-model.md) |
| dishka and wireup bridges | part | Serving dependencies from an external container behind `DependencyProvider`, shipped as extras | `dependency-provider.md` | [ADR-0018](../adr/0018-core-owned-type-keyed-dependency-injection.md) |
| First-party `RequestObserver` extra | part | Spans and metrics under recognised conventions, registered in one line; no observer by default | `api-client.md` | [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md); boundary finalised in #29 |

## 5.8 Level 3 — adapter-specific plugins

Bound to the Mattermost Adapter; each implements the Core `Transport` seam or extends the Adapter.

```mermaid
C4Component
    title Components of the adapter-specific plugins
    Component(ws, "WebSocketTransport", "Transport", "One supervised reconnect loop, resume, bounded queue, drain")
    Component(webhook, "Webhook", "Transport", "Bare ASGI callable, Reply channel, verification before an Event exists")
    Component(token, "Callback token", "Authenticity", "Self-issued signed credential in button context and dialog state")
    Component(cache, "IdentityCache", "Optional", "Resolved users and direct channels on a KeyValueStore")
    Rel(webhook, token, "verifies every callback with")
```

The two Transports never touch: an `independence` contract keeps them apart, and the one thing
Webhook's nonce store and IdentityCache have in common is the Core `KeyValueStore` seam.

| Block | Kind | Responsibility | Document | Decisions |
|---|---|---|---|---|
| **WebSocketTransport** | component | The gateway: one reconnect loop with a `TaskGroup` per connection, the transient/resumable/fatal exit table, heartbeat and silence monitor, full-jitter backoff, resume with sequence continuity, a reader that never stalls, the graceful drain, the single-consumer declaration and optional lease | `websocket-transport.md` | [ADR-0023](../adr/0023-websocket-gateway-resilience.md), [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md) |
| The bounded queue and `OverflowPolicy`, the dedup of `(connection_id, seq)`, the drain, the `websockets`/`picows` bindings, the gateway Signals | part | Backpressure with a typed per-kind policy, replay dedup, the 25 s drain, the two `WebSocketConnection` implementations, and `Connected`…`DrainTimedOut` | `websocket-transport.md` | [ADR-0023](../adr/0023-websocket-gateway-resilience.md) |
| Resync backfill | part, **open** | Recovering the loss window a `Resynced(since)` Signal reports. ADR-0023 leaves first-party plugin versus documented recipe undecided; a ticket owns the choice before #41 can give it a document | — | [ADR-0023](../adr/0023-websocket-gateway-resilience.md) |
| **Webhook** | component | `webhook_app(bot) -> ASGIApp` and `handle_callback`, the payload-bound single-use Reply channel with its 10 s deadline and empty-200 default, verification before an Event exists, the 1 MiB reply cap, the logging rules | `webhook.md` | [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md) |
| The Reply channel (`ActionReply`, `DialogReply`, `ReplyAlreadySent`), `StaleAction` | part | The typed reply slot bound to the payload, and the routable event an expired or replayed token produces | `webhook.md` | [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md) |
| **Callback token** | component | The self-issued credential: the compact HMAC-SHA256 format, the claim set, key rotation by `kid`, the typed verification union, and the default-on policy with its explicit `off` | `callback-token.md` | [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md) |
| `NonceStore`, the PASETO extra | part | Opt-in single-use enforcement on a `KeyValueStore`, and `pyseto` behind the same `CallbackTokenCodec` | `callback-token.md` | [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md) |
| **IdentityCache** | component | Optional caching of resolved users and direct channels on a `KeyValueStore` with a one-hour TTL and event-driven invalidation; absent, the Workspace queries every time. The Workspace consults it through an **Adapter-owned Protocol**, so the import still points plugin → Adapter and never back | `identity-cache.md` | [ADR-0028](../adr/0028-runtime-helpers-and-identity-resolution.md), [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md) |

## 5.9 Level 3 — the testing toolkit

`aiommbot.testing` may import every layer and is imported by none
([ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md)). Its blocks are
listed here because earlier decisions already require them by name; **its shape is #25's decision**,
so #41 creates its design documents only after #25 closes.

| Block | Kind | Required by | Decision |
|---|---|---|---|
| **Testing toolkit** | component | — | #25 |
| In-memory `HTTPTransport`/`SyncHTTPTransport` double, both faces in one class | part | the parametrised conformance suite of both client Faces | [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) |
| In-memory `WebSocketConnection` connector | part | the contract suite both gateway libraries run in CI | [ADR-0023](../adr/0023-websocket-gateway-resilience.md) |
| Conformance suites: `KeyValueStore`, `LockProvider`, `Transport`, plugin lifecycle | part | external storage backends and third-party plugins | [ADR-0015](../adr/0015-plugin-contract-and-composition.md), [ADR-0022](../adr/0022-state-plugin-model.md) |
| `TestBot` with typed overrides by key | part | the only override API that exists — production has none | [ADR-0019](../adr/0019-handler-parameter-resolution-rules.md) |
| The typed name-parity test of the two Faces | part | holding duality by mechanism rather than review | [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) |
| `assert_matches(event, handler)` | part | shadowing between arbitrary filters, which start-up cannot decide | [ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md) |

## 5.10 Inventory summary

28 components, about forty parts, and thirteen Protocols on eleven seam rows. The count matters in
one way only: **27 `LLD: <component>` tickets** for #41 to generate now, and a twenty-eighth — the
testing toolkit — held until #25 decides its shape. Parts and seams generate nothing; they are
specified inside the document of the component named beside them.

| Layer | Components |
|---|---|
| Core | Bot, Dispatcher, Router, Filter, Extractor, Middleware, ErrorBoundary, DependencyProvider, Signal, Sync executor, Event |
| Adapter | EventRegistry, Model generator, Generated model, Codec, API client, Exchange, Face, Workspace, Runtime, AuthLossDetector |
| Generic plugins | State, KeyValueStore and LockProvider backends |
| Adapter-specific plugins | WebSocketTransport, Webhook, Callback token, IdentityCache |
| Testing toolkit | Testing toolkit (deferred to #25) |
