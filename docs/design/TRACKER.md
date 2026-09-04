# Documentation readiness tracker

The single view of what the design catalogue must contain and how far each piece is. Every ticket
resolution updates its rows **in the same commit**. The hand-off ticket (#33) may close only when
every row reads `reviewed` or has an explicit *deferred to implementation* note.

Legend: `—` not started · `wip (#N)` in progress under ticket N · `reviewed` passes
`docs/agents/design-quality-checklist.md` · `n/a` deliberately not applicable (say why).

## A. Architecture document (arc42)

| § | Document | Status | Ticket | Depends on |
|---|---|---|---|---|
| 1 | `01-introduction-and-goals.md` | — | #37 | #13 |
| 2 | `02-constraints.md` | wip (#23 → #37) | #37 | #13 |
| 3 | `03-context-and-scope.md` | reviewed | #38 | #13 #14 #15 #18 #19 #20 #21 #22 |
| 4 | `04-solution-strategy.md` | reviewed | #38 | same |
| 5 | `05-building-block-view.md` | reviewed | #38 | same |
| 6 | `06-runtime-view.md` | — | #39 | #38 #16 #17 |
| 7 | `07-deployment-view.md` | wip (hosting shapes and topology inputs from #19, #20; #40 completes) | #40 | #38 #24 #29 #30 |
| 8 | `08-cross-cutting-concepts.md` | — | #40 | same |
| 9 | `docs/adr/` | rolling | every grilling ticket | — |
| 10 | `10-quality-requirements.md` | — | #37 | #13 |
| 11 | `11-risks-and-technical-debt.md` | — | #42 | #40 #41 |
| 12 | `CONTEXT.md` | rolling (17 terms added by #38) | every ticket | — |
| — | `engineering-style.md` | — | #36 | #23 #13 |
| — | `diagrams.md` | reviewed | #35 | — |
| — | `components/_template.md` | reviewed | #35 | — |
| — | `docs/documentation-style.md` | reviewed | #35 | — |
| — | `docs/adr/_template.md`, `docs/adr/README.md` | reviewed | #35 | — |
| — | Docs-as-code linting (markdown, Vale, lychee, Mermaid, index check) | — | #43 | #26 |

## B. Decision areas → ADR

One row per design decision the map must make. `ADR` is filled when the ticket closes.

| Area | Ticket | ADR | Status |
|---|---|---|---|
| Fresh public start, no 0.4.x compatibility | charting | 0001 | reviewed |
| Core scope: what the bare core owns and refuses | #13 | 0002 | reviewed |
| Stateless core; State plugin with mandatory backend | #13 (→ #18) | 0003 | reviewed |
| Execution model boundary: async engine, generated sync Runtime | #13 (→ #22) | 0004 | reviewed |
| Scaling model: one ingress, many workers | #13 (→ #19, #40) | 0005 | reviewed |
| Architectural tenets: composition, Core-owned Protocols, named patterns, typing, fail closed | #13 (→ #36) | 0006 | reviewed |
| Public API surface: tiny root + explicit subpackages | #13 (→ #24) | 0007 | reviewed |
| Plugin contract, adapter role, ordering, settings, discovery, stability | #14 | 0015 | reviewed |
| Three-phase start, checks framework, ProcessProfile | #14 | 0016 | reviewed |
| Lifecycle Signals | #14 | 0017 | reviewed |
| Event model: envelope, payload registry, first-class kinds | #15 | 0012 | reviewed |
| Routing: type-driven subscription, tree walk, typed outcome, reachability | #15 | 0013 | reviewed |
| Filters, extractors, closed handler signatures | #15 | 0014 | reviewed |
| Full typed coverage of the event catalogue | #45 | | — |
| Dependency injection: ownership, key, scopes, providers, graph | #16 | 0018 | reviewed |
| Handler parameter resolution rules, built-ins, test overrides | #16 | 0019 | reviewed |
| Middleware layers, contract, publication, flags, ordering | #17 | 0020 | reviewed |
| Core error boundary | #17 | 0021 | reviewed |
| State/FSM, event isolation, storage contract, first-party backends, lifetime | #18 | 0022 | reviewed |
| Declarative scenes on top of State | #48 | | — |
| WebSocket gateway resilience (reconnect, resume, heartbeat, backpressure, drain, auth loss, library) | #19 | 0023 | reviewed |
| Webhook ingress: events + reply channel, bare ASGI, callback authenticity, replay policy | #20 | 0024 | reviewed |
| Mattermost API layer: generated dataclass models, Codec Protocol, server version policy | #21 | 0025 | reviewed |
| Standalone typed API client: HTTPTransport, httpx2, Operation descriptors, pagination, retries, faces | #21 | 0026 | reviewed |
| API error taxonomy | #21 | 0027 | reviewed |
| Runtime helpers, identity resolution, IdentityCache plugin | #21 | 0028 | reviewed |
| Message composition: attachment, button, select and dialog builders embedding Callback tokens | graduated from #21 (ticket pending) | | — |
| File API ergonomics: limits, resumable uploads, streaming | graduated from #21 (ticket pending) | | — |
| Execution model: sync face scope, `Workspace` split, thin drivers instead of codegen | #22 | 0029 | reviewed |
| Synchronous callables: `sync_to_thread`, own executor, abandon at drain | #22 | 0030 | reviewed |
| Concurrency discipline, event-loop ownership, process entry points | #22 | 0031 | reviewed |
| Python floor and support policy | #23 | 0008 | reviewed |
| Type checkers and typing tests | #23 | 0009 | reviewed |
| Zero suppressions and quarantine | #23 | 0010 | reviewed |
| Lint, format, architecture toolchain, task runner | #23 | 0011 | reviewed |
| Layer model and the direction of allowed dependencies | #38 | 0032 | reviewed |
| Repository layout, public/internal boundary, extras | #24 | | — |
| Testing toolkit | #25 | | — |
| Documentation stack and executable docs | #26 | | — |
| Agent-native repository and AI policy | #27 | | — |
| CI, release, versioning, changelog, deprecation | #28 | | — |
| Observability boundary | #29 | | — |
| Scheduling, reliability middlewares, CLI boundaries | #30 | | — |
| Engineering style and ideology | #36 | | — |
| Quality goals, constraints, quality scenarios | #37 | | — |
| Public API shape (prototype) | #31 | | — |
| Toolchain skeleton verified (prototype) | #32 | | — |
| Risk register | #42 | | — |

## C. Component design documents (LLD)

The inventory is settled: §5.10 of `05-building-block-view.md` lists **28 components** across four
layers, with about forty *parts* and thirteen Protocols on eleven *seam* rows that deliberately get
no document of their own. #41 turns that inventory into one row per component here and one
`LLD: <component>` ticket each — 27 now, plus the testing toolkit once #25 has decided its shape.
The file name is the `CONTEXT.md` term in kebab-case.

| Component | Layer | File | Status | Ticket |
|---|---|---|---|---|
| _(rows generated by #41 from §5.10; the inventory itself is settled)_ | | | | |

## D. Cross-cutting concerns

Each concern must be decided (ADR), described (§8 or an LLD) and testable (§10 scenario).

| Concern | Decided in | Described in | Quality scenario | Status |
|---|---|---|---|---|
| Typing discipline and banned patterns | ADR-0009, ADR-0010, ADR-0011 (mechanics), #36 (rules) | §8, style | | wip |
| Error taxonomy (domain / validation / dependency / retryable / permanent / user-visible) | ADR-0014 (values), ADR-0021 (boundary, `FatalError`), ADR-0027 (API exceptions, `retryable`) | §8 | | wip |
| Async, cancellation, timeouts, structured concurrency | ADR-0031 (stdlib asyncio, TaskGroup ownership, explicit timeouts, no `CancelledError` capture, `shield` only in drain, exception-group unwrapping), ADR-0030 (uncancellable threads), #19 | §8, style | | wip |
| Configuration and settings, plugin-contributed settings | ADR-0015 (typed frozen settings objects; loading is the app's) | §8 | | wip |
| Logging and redaction (no message text, tokens, PII) | ADR-0026 (client: never bodies, headers, tokens), #36 #29 | §8 | | wip |
| Observability hooks and naming | ADR-0026 (optional composable `RequestObserver`, first-party extra, transport/Middleware for modification; record shape provisional), research 17, #29 | §8 | | wip |
| Security: callback signing, secrets, PII, replay | ADR-0024 (default-on HMAC token, `CallbackTokenCodec`, nonce opt-in, logging rules) | §8 | | wip |
| Dependency injection scopes and lifecycle | ADR-0018, ADR-0019 | §8 | | wip |
| Extension points and plugin isolation (import-linter) | ADR-0002, ADR-0015 (contract), ADR-0032 (layers and direction), #24 (layout) | §5, §8 | | wip |
| Sync/async duality | ADR-0004 (boundary), ADR-0026 (bare name async, `Sync` prefix), ADR-0029 (scope, thin drivers, paired `SyncHTTPTransport`, parity and conformance mechanisms), ADR-0030 (callable colours) | §8 | | wip |
| Testing strategy (unit / contract / integration / typing / property) | #25 | §8 | | — |
| Backpressure and flow control between transport and handlers | ADR-0023 (never-stalling reader, bounded queue, per-kind `OverflowPolicy`), ADR-0030 (own executor sized against the worker count, checked at start) | §8, gateway LLD | | wip |
| Idempotency and stale-action handling | ADR-0022 (CAS, locks), ADR-0024 (optional TTL, opt-in nonce store, `StaleAction` events) | §8 | | wip |
| Single WebSocket consumer and horizontal scaling | ADR-0005, ADR-0023 (`ProcessProfile.websocket_consumer` + optional lease), #40 | §7 | | wip |
| Graceful shutdown and drain | ADR-0023 (close first, drain ≤ 25 s, `DrainTimedOut`), ADR-0030 (a synchronous Handler is abandoned, `HandlerAbandoned`), ADR-0031 (bounded cleanup, `shield` only here) | §6, §8 | | wip |
| Deprecation and public-API definition for semver | #28 | §8 | | — |

## E. Disposition of every 0.4.8 capability

Each capability of the old framework gets an explicit decision: **keep** (re-designed in 0.5.0
core or first-party plugin), **recipe** (documented with an external library), **drop**. Filled by
the ticket in the *Decided in* column; evidence of real use is in `docs/research/09`.

| 0.4.8 capability | Used by (of 11 bots) | Disposition | Decided in | Status |
|---|---|---|---|---|
| WebSocket channel (posts, events) | 11 | keep, redesigned as the resilient `WebSocketTransport` (ADR-0023) | #19 | reviewed |
| Webhook channel + interactive actions/dialogs | 10 | keep, redesigned: events with reply channel, bare ASGI callable (ADR-0024) | #20 | reviewed |
| Signed callback tokens (bespoke crypto, 2.1k lines) | 10 | redesign: ~40-line stdlib HMAC-SHA256 token per Standard Webhooks/RFC 8725 behind a codec Protocol, PASETO extra; Fernet path segment dropped (ADR-0024) | #20 | reviewed |
| Message / action / dialog handlers, `direct_added` | ≥8 | keep as first-class payloads (ADR-0012) | #15 | reviewed |
| 8 rarely used event kinds (reaction, group_added, post_lifecycle, channel/user/thread, websocket_event) | 0 | drop as separate classes; reactions/group/user events stay first-class payloads, the rest via RawEvent (ADR-0012) | #15 | reviewed |
| `external` events | 1 | not a platform event; revisit as a plugin-registered payload if a need appears (ADR-0012) | #15 | reviewed |
| Filters (`DIRECT_CHAT_TYPE_FILTER`, `StateFilter`, regex `matched_params`) | ≥8 | redesign: Filter predicates + typed Extractors (ADR-0014) | #15 | reviewed |
| DI by handler signature, `**kwargs: Any` boilerplate | 11 | redesign: closed signature, type-keyed resolution with compiled plans (ADR-0014, 0018, 0019) | #16 | reviewed |
| Inner/outer middleware, auto-wired reliability stack | 11 / 0 | redesign: Inbound/Handler layers, typed contract, no auto-wiring (ADR-0020); reliability as plugin middleware pending #30 | #17 #30 | wip |
| Default error middleware (swallows exceptions, leaks PII) | 8 (unoverridden) | replace with Core ErrorBoundary: no payload, no swallow, typed `Failed` (ADR-0021) | #17 | reviewed |
| FSM (`StatesGroup`, `Context`) | ≥8 | keep, redesigned as `Flow[Data]` + `StateContext` + `InState` filter (ADR-0022) | #18 | reviewed |
| Storage backends: memory / Redis / Mongo | mixed | in-memory + Redis first-party behind `KeyValueStore`/`LockProvider`; Mongo/SQL external packages with the conformance suite (ADR-0022) | #18 | reviewed |
| Storage profiles (one backend for state + broker + breaker) | 3 | drop: two separate Core Protocols instead, no profile (ADR-0022) | #18 | reviewed |
| Taskiq scheduling (`@router.schedule`) | few, in-memory broker only | not core (ADR-0002); placement pending | #30 | — |
| Retry / idempotency / dead-letter middlewares, `RetryableError` family | 0 | not core (ADR-0002); placement pending | #30 | — |
| Circuit breaker (purgatory) | 0 (two bots vendor aiobreaker) | not core (ADR-0002); placement pending | #30 | — |
| Backpressure queue, `QueuePolicy`, `worker_concurrency` | 0 explicit | keep the idea, redesigned: bounded queue, N workers, typed per-kind `OverflowPolicy` with `Dropped` Signal (ADR-0023) | #19 | reviewed |
| `ObservabilityProvider` / Prometheus, Sentry middleware | some | not core (ADR-0002); placement pending | #29 | — |
| `BotRuntime` / `SyncBotRuntime`, runtime-only processes | some | keep `BotRuntime` as the Runtime; **drop `SyncBotRuntime`** — 0 of 11 bots used it, and its Event-free slice becomes the `Workspace` with a hand-written synchronous face (ADR-0029) | #22 | reviewed |
| `EventPreparer` (user/channel resolution) | 6 | redesign: `runtime.users.resolve(UserRef)` and `runtime.channels.direct`, uncached; `IdentityCache` optional plugin (ADR-0028) | #21 | reviewed |
| `ApiManager` (answer, update, dialogs, files) and typed API modules | 11 | redesign: standalone generated API client (ADR-0025, 0026) + Runtime helpers (ADR-0028); errors per ADR-0027 | #21 | reviewed |
| Attachments, buttons, selects, dialog element builders | 10 | keep; models as dataclasses in the Adapter (ADR-0025), builders decided in the message-composition ticket graduated from #21 | pending | — |
| Lifespan, `combine_lifespans`, `bot.state` | ≥8 | redesign: plugin `HasLifecycle` + Signals replace lifespan composition (ADR-0015/0017); `bot.state` replaced by App-scoped Providers, Bot never injected (ADR-0019) | #16 | reviewed |
| CLI runner (`aiommbot run\|websocket\|webhook\|worker\|scheduler`) | some | not core (ADR-0002); placement pending | #30 | — |
| `aiommbot.testing` toolkit, mock Mattermost server | 2 | keep: the blocks earlier decisions already require by name are listed in §5.9; the toolkit's shape is #25's | #25 | wip |
| `extras.py` friendly missing-extra errors, nine extras | — | keep the idea: extras per first-party plugin with a friendly error (ADR-0015); count and names in #24 | #24 | wip |
| uvloop/winloop switching | 0 of 11 installed the extra | drop: no extra, no auto-installation, no policy API; the process entry point takes `loop_factory` and the documentation shows uvloop (ADR-0031) | #22 | reviewed |
| Cache utilities | — | drop as utilities; `IdentityCache` optional plugin on `KeyValueStore` (ADR-0028) | #21 | reviewed |

## F. Fog and backlog

The map (#1) is the source of truth for *Not yet specified* and *Out of scope*; backlog ideas are
`enhancement` issues (currently #34). This tracker does not mirror them — check the map.
