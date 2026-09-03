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
The binding of the Core to one chat platform — for 0.5.0, Mattermost: wire models, REST client,
WebSocket and webhook Transports, platform-specific filters.
_Avoid_: platform, driver, connector, integration

**Plugin**:
An optional capability enabled by listing it explicitly in the Bot's composition. It contributes
routers, middleware, dependencies, settings and lifecycle hooks; it is never active merely because
it is installed.
_Avoid_: extension, app, addon, module

**Transport**:
A source of inbound events for the Core — the Mattermost WebSocket connection or the webhook
callback endpoint. A Transport delivers events; it does not interpret them.
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

**Quarantine**:
A module under `_internal/compat/` that adapts one third-party library with incomplete typing to a
Core-owned Protocol. The only place a lint or type suppression may exist, each tied to an upstream
issue and counted against a baseline that only decreases.
_Avoid_: shim, wrapper module, compat layer (as a general term)

**State**:
The first-party Plugin that gives a conversation a finite-state machine and per-key event
isolation over an explicitly chosen storage backend.
_Avoid_: FSM plugin, context storage, session
