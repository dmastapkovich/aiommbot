# aiommbot

The ubiquitous language of the aiommbot 0.5.0 design. One canonical term per concept; the
synonyms to avoid are listed so documents, diagrams, issues and code use the same words.

## Language

**Core**:
The platform-independent part of the framework: event envelope, routing and filters, middleware
chain, dependency injection, lifecycle, the Transport seam, the error taxonomy and the Plugin
registry. Standard library only; holds no state between events.
_Avoid_: engine, kernel, framework core, runtime

**Adapter**:
The binding of the Core to one chat platform — for 0.5.0, Mattermost. Exactly one per Bot. It
supplies the platform vocabulary: payload types and the EventRegistry, the REST client and Runtime,
platform filters and router aliases. Its Transports are adapter-specific Plugins.
_Avoid_: platform, driver, connector, integration

**Plugin**:
An optional capability enabled by listing it explicitly in the Bot's composition. Carries a frozen
PluginSpec and implements only the contribution Protocols it needs. Either generic (depends on the
Core only) or adapter-specific (bound to one Adapter). Never active merely because it is installed.
_Avoid_: extension, app, addon, module

**PluginSpec**:
The immutable declaration of a Plugin: name, contract version, `requires` and `after` dependencies
on other plugins, adapter binding, settings type. Readable without running code.
_Avoid_: manifest, metadata, config

**Check**:
A side-effect-free validation run in the check phase of start-up, contributed by the Core, the
Adapter or a Plugin: id, severity, message, hint. Any error-severity Check stops the start with the
full list of failures.
_Avoid_: validation, assertion, health check (that is a runtime probe)

**ProcessProfile**:
The typed declaration of what kind of process is starting (at least whether it is a single
process), which Checks are evaluated against.
_Avoid_: mode, role (informal), deployment flag

**Signal**:
A typed asynchronous lifecycle notification of the Core or a Transport (started, stopping,
connected, disconnected, resumed), delivered to every subscriber. Not a platform Event.
_Avoid_: hook, lifecycle event, callback

**Transport**:
A source of inbound events for the Core — the Mattermost WebSocket connection or the webhook
callback endpoint. An adapter-specific Plugin implementing the Core-owned Transport Protocol; it
delivers events and does not interpret them. A Bot may have none.
_Avoid_: channel (reserved for the Mattermost channel), ingress, source, gateway, connection

**Bot**:
The composition root: it is configured with an Adapter, Plugins and routers, owns the lifecycle
and runs the dispatch loop. One Bot per process is the documented model.
_Avoid_: app, application, dispatcher (the dispatcher is a component inside the Bot)

**Event**:
The immutable generic envelope `Event[P]` the Core dispatches: the platform event name (`kind`),
a typed `payload`, and `meta` (transport, receive time, correlation id, sequence, raw data, optional
reply channel). The Core knows the envelope, never a concrete payload.
_Avoid_: request, update, message (as the generic term), incoming

**Payload**:
The typed body of an Event, defined by the Adapter for one platform event name and registered in
the EventRegistry. `RawEvent` is the payload for any name without a registered type.
_Avoid_: data, body, model (as the generic term)

**Router**:
A node in the handler tree. Holds handlers and child routers in registration order and may carry
filter gates. Dispatch walks the tree depth-first and stops at the first match.
_Avoid_: dispatcher (the dispatcher walks routers), blueprint, cog

**Filter**:
A pure predicate over an Event, composable with `&`, `|`, `~`. Decides whether a handler is a
candidate; never produces data.
_Avoid_: matcher, guard, check

**Extractor**:
A typed parser that turns an Event into a value a handler receives by annotation, or reports
`NoMatch` (skip this handler) or `Invalid` (the event is about this, the data is bad).
_Avoid_: converter, parser (as the generic term), transformer

**Provider**:
A declaration that a dependency key (type plus optional Qualifier) is produced by a factory in a
given Scope. Contributed by Plugins or the application; its own parameters are injected.
_Avoid_: factory (as the whole), binding, registration, dependency (for the declaration)

**Qualifier**:
The `Annotated` marker that tells two dependencies of the same type apart, on both the Provider and
the consuming parameter.
_Avoid_: name, tag, label

**Scope**:
The lifetime of a resolved dependency: `App` (one per Bot, start to shutdown) or `Event` (one per
dispatched Event, closed after the handler).
_Avoid_: lifetime, context (as the generic term), request scope

**Resolution plan**:
The frozen sequence of steps compiled once per Handler in the check phase that produces its
parameters from extractor values and Providers. No introspection at dispatch time.
_Avoid_: injection plan, dependency graph (that is the whole), wiring

**Middleware**:
An asynchronous link in the dispatch chain: `__call__(event, call_next, *deps) -> Outcome`. Lives in
one of two layers — **Inbound** (every event, before the router walk) or **Handler** (around the
matched Handler) — registered on the Bot or on a Router for its subtree.
_Avoid_: interceptor, hook (that is a Signal subscriber), outer/inner middleware

**Outcome**:
The typed result of dispatching an Event: `Handled`, `Unhandled`, or `Failed(error)` from the
ErrorBoundary. Returned by `call_next` and by the dispatcher to the Transport, which reacts to it.
_Avoid_: result, response, status

**Flag**:
A typed object attached to a Handler at its subscription to parametrise a Middleware (a timeout, a
required role, a rate limit); stored in the HandlerSpec by type. A Flag with no consuming
Middleware is a Check error.
_Avoid_: option, annotation (as the generic term), marker

**MatchedHandler**:
The Event-scoped value the Core publishes after a match: the HandlerSpec and the resolved extractor
values, available to Handler-layer Middleware by annotation.
_Avoid_: route match, target, handler context

**ErrorBoundary**:
The non-removable outermost Middleware of the Core. Catches `Exception`, logs without payload,
reports to observability, returns `Failed`. Lets `BaseException` and `FatalError` through.
_Avoid_: error handler, exception middleware, catch-all

**HandlerSpec**:
The frozen record built when a Handler is registered: name, router path, event kind, filters and
extractors as data, declared dependencies, docstring, location, metadata flags. Exposed as
`bot.routes()`.
_Avoid_: route, handler object, observer

**Runtime**:
The API a process uses to act on the platform without consuming events — send and edit posts,
open dialogs, resolve users — available in an asynchronous face and a generated synchronous face.
_Avoid_: client (too broad), API manager, bot runtime

**Handler**:
A user function registered on a router for a kind of event. Declarative and thin: filters, state
gates, parsing and dependency injection happen outside its body; the body makes one service call
and answers.
_Avoid_: callback, listener, endpoint, view

**StateKey**:
The frozen identity of a conversation's state: channel, user, thread root and a scope name, built by
the Adapter from an Event according to the plugin's strategy (`USER_IN_CHANNEL` by default).
_Avoid_: storage key, session id, chat id

**Flow**:
A typed group of states with a typed, versioned data model — `class Order(Flow[OrderData])` —
describing one multi-step dialogue. Its data is the draft of the current dialogue, never business
data.
_Avoid_: states group, FSM (as the thing), scene (that is #48), conversation

**StateContext**:
The Event-scoped handle a Handler receives for a Flow: typed `state`, `data`, `set_state()`,
`update()`; writes are compare-and-set. May be `StaleState` when the record is expired, from
another schema version or in an unknown state.
_Avoid_: FSM context, context (bare), session

**KeyValueStore**:
Core Protocol for versioned bytes by key with compare-and-set and optional TTL capability. Used by
State and by other plugins (dedup). In-memory and Redis are first-party implementations.
_Avoid_: storage (bare), backend (for the Protocol), database

**LockProvider**:
Core Protocol for a per-key asynchronous lock with a TTL and a wait timeout. Used for event
isolation and dedup; separate from KeyValueStore.
_Avoid_: event isolation (that is the middleware using it), mutex, semaphore

**Reply channel**:
The typed, single-use response slot in `meta.reply` of a webhook-delivered Event: `ActionReply` for
an InteractiveAction, `DialogReply` for a DialogSubmission. Unused by the deadline, it sends an
empty 200 and later sends yield `ReplyAlreadySent`.
_Avoid_: response (bare), ack (that is the default reply), HTTP response

**Callback token**:
The self-issued signed credential the bot places in a button `context` or dialog `state` and verifies
when the callback returns: versioned, keyed by `kid`, HMAC-SHA256 by default, with optional expiry,
actor binding and nonce. The only authenticity primitive Mattermost leaves to an external bot.
_Avoid_: signature (of the request), secret, cookie

**StaleAction**:
The routable Event produced when a Callback token is `Expired` or `Replayed`; its default handler
tells the user the action has expired and disables the buttons.
_Avoid_: stale callback, dead button, timeout (bare)

**Resync**:
The moment the server hands the gateway a fresh `connection_id` after an unrecoverable gap: buffered
events are lost, the sequence restarts, and the `Resynced(since)` Signal reports the loss window so a
plugin or the application can backfill over REST.
_Avoid_: reconnect (that may resume without loss), full sync, catch-up (bare)

**Quarantine**:
A module under `_internal/compat/` that adapts one third-party library with incomplete typing to a
Core-owned Protocol. The only place a lint or type suppression may exist, each tied to an upstream
issue and counted against a baseline that only decreases.
_Avoid_: shim, wrapper module, compat layer (as a general term)

**State**:
The first-party Plugin that gives a conversation a finite-state machine and per-key event
isolation over an explicitly chosen storage backend.
_Avoid_: FSM plugin, context storage, session
