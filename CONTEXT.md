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

**Runtime**:
The API a process uses to act on the platform without consuming events — send and edit posts,
open dialogs, resolve users — available in an asynchronous face and a generated synchronous face.
_Avoid_: client (too broad), API manager, bot runtime

**Handler**:
A user function registered on a router for a kind of event. Declarative and thin: filters, state
gates, parsing and dependency injection happen outside its body; the body makes one service call
and answers.
_Avoid_: callback, listener, endpoint, view

**State**:
The first-party Plugin that gives a conversation a finite-state machine and per-key event
isolation over an explicitly chosen storage backend.
_Avoid_: FSM plugin, context storage, session
