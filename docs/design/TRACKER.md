# Documentation readiness tracker

The single view of what the design catalogue must contain and how far each piece is. Every ticket
resolution updates its rows **in the same commit**. The hand-off ticket (#33) may close only when
every row reads `reviewed` or has an explicit *deferred to implementation* note.

Legend: `—` not started · `wip (#N)` in progress under ticket N · `reviewed` passes
`.agents/design-quality-checklist.md` · `n/a` deliberately not applicable (say why).

## A. Architecture document (arc42)

| § | Document | Status | Ticket | Depends on |
|---|---|---|---|---|
| 1 | `01-introduction-and-goals.md` | — | #37 | #13 |
| 2 | `02-constraints.md` | wip (#23 → #37) | #37 | #13 |
| 3 | `03-context-and-scope.md` | reviewed | #38 | #13 #14 #15 #18 #19 #20 #21 #22 |
| 4 | `04-solution-strategy.md` | reviewed | #38 | same |
| 5 | `05-building-block-view.md` | reviewed (§5.0, §5.4, §5.9, §5.10 amended by #84) | #38 | same |
| 6 | `06-runtime-view.md` | — | #39 | #38 #16 #17 |
| 7 | `07-deployment-view.md` | wip (hosting shapes and topology inputs from #19, #20; #40 completes) | #40 | #38 #24 #29 #30 |
| 8 | `08-cross-cutting-concepts.md` | — | #40 | same |
| 9 | `docs/adr/` | rolling | every grilling ticket | — |
| 10 | `10-quality-requirements.md` | — | #37 | #13 |
| 11 | `11-risks-and-technical-debt.md` | — | #42 | #40 #41 |
| 12 | `CONTEXT.md` | rolling (2 terms added by #36, 2 by #57) | every ticket | — |
| — | `engineering-style.md` | reviewed (§1 amended by #84) | #36 | #23 #13 |
| — | `diagrams.md` | reviewed | #35 | — |
| — | `components/_template.md` | reviewed | #35 | #56 — restates rules §12.1 now owns |
| — | `docs/documentation-style.md` | reviewed | #35 | — |
| — | `docs/adr/_template.md`, `docs/adr/README.md` | reviewed | #35 | — |
| — | Docs-as-code linting (markdown, Vale, lychee, Mermaid, index check) | — | #43 | #26 |

## B. Decision areas → ADR

One row per design decision the map must make. `ADR` is filled when the ticket closes.

| Area | Ticket | ADR | Status |
|---|---|---|---|
| Fresh public start, no compatibility promise toward any earlier release | charting | 0001 | reviewed |
| Core scope: what the bare core owns and refuses | #13 | 0002 | reviewed |
| Stateless core; State plugin with mandatory backend | #13 (→ #18) | 0003 | reviewed |
| Execution model boundary: async engine, generated sync Runtime | #13 (→ #22) | 0004 | reviewed |
| Scaling model: one ingress, many workers | #13 (→ #19, #40) | 0005 | reviewed |
| Architectural tenets: composition, Core-owned Protocols, named patterns, typing, fail closed | #13 (→ #36) | 0006 | reviewed (amended by #36, count by #84) |
| Public API surface: tiny root + explicit subpackages | #13 (→ #24, #36) | 0007 | reviewed (amended by #36) |
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
| Resync backfill: first-party plugin or documented recipe | #55 | | — |
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
| Zero suppressions and quarantine | #23 (→ #36) | 0010 | reviewed (amended by #36) |
| Lint, format, architecture toolchain, task runner | #23 | 0011 | reviewed |
| Layer model and the direction of allowed dependencies | #38 | 0032 | reviewed |
| Repository layout, public/internal boundary, extras | #24 | | — |
| Testing toolkit | #25 | | — |
| Documentation stack and executable docs | #26 | | — |
| Agent-native repository and AI policy | #27 | | — |
| CI, release, versioning, changelog, deprecation | #28 | | — |
| Observability boundary | #29 | | — |
| Scheduling, reliability middlewares, CLI boundaries | #30 | | — |
| Engineering style and ideology: rule form, pattern tiers, derived review checklist | #36 | 0033 | reviewed |
| Error mechanism: typed outcome versus exception | #36 | 0034 | reviewed |
| Quality goals, constraints, quality scenarios | #37 | | — |
| LLD writing order and parallelism | #41 | 0035 | reviewed |
| Reply-slot typing: second type parameter, `ReplyChannel` as the Core's twelfth seam | #57 | 0036 | reviewed |
| Envelope enrichment: `derive` only, `dataclasses.replace` on an `Event` banned | #57 | 0037 | reviewed |
| Seam inventory: direction of the call recorded per row, `required` and `provided`, and the count reconciled | #84 | 0038 | reviewed |
| Rank of the six `Contributes*`/`HasLifecycle` plugin Protocols in §5 | #85 | | — |
| Public API shape (prototype) | #31 | | — |
| Toolchain skeleton verified (prototype) | #32 | | — |
| Risk register | #42 | | — |

## C. Component design documents (LLD)

The inventory is settled: §5.10 of `05-building-block-view.md` lists **28 components** across four
layers, with about forty *parts* and fourteen Protocols on twelve *seam* rows — eleven required, one
provided — that deliberately get no document of their own. #41 turns that inventory into one row per component here and one
`LLD: <component>` ticket each — 27 now, plus the testing toolkit once #25 has decided its shape.
The file name is the `CONTEXT.md` term in kebab-case.

| Component | Layer | File | Status | Ticket |
|---|---|---|---|---|
| Event | Core | `components/event.md` | reviewed | #57 |
| Signal | Core | `components/signal.md` | not started | #58 |
| DependencyProvider | Core | `components/dependency-provider.md` | not started | #59 |
| Generated model | Adapter | `components/generated-model.md` | not started | #60 |
| Codec | Adapter | `components/codec.md` | not started | #61 |
| Face | Adapter | `components/face.md` | not started | #62 |
| KeyValueStore and LockProvider backends | Generic plugin | `components/key-value-store.md` | not started | #63 |
| Filter | Core | `components/filter.md` | not started | #64 |
| Extractor | Core | `components/extractor.md` | not started | #65 |
| Sync executor | Core | `components/sync-executor.md` | not started | #66 |
| Model generator | Adapter | `components/model-generator.md` | not started | #67 |
| API client | Adapter | `components/api-client.md` | not started | #68 |
| EventRegistry | Adapter | `components/event-registry.md` | not started | #69 |
| Callback token | Adapter-specific plugin | `components/callback-token.md` | not started | #70 |
| Router | Core | `components/router.md` | not started | #71 |
| Exchange | Adapter | `components/exchange.md` | not started | #72 |
| Workspace | Adapter | `components/workspace.md` | not started | #73 |
| AuthLossDetector | Adapter | `components/auth-loss-detector.md` | not started | #74 |
| Dispatcher | Core | `components/dispatcher.md` | not started | #75 |
| Runtime | Adapter | `components/runtime.md` | not started | #76 |
| IdentityCache | Adapter-specific plugin | `components/identity-cache.md` | not started | #77 |
| Middleware | Core | `components/middleware.md` | not started | #78 |
| ErrorBoundary | Core | `components/error-boundary.md` | not started | #79 |
| Webhook | Adapter-specific plugin | `components/webhook.md` | not started | #80 |
| WebSocketTransport | Adapter-specific plugin | `components/websocket-transport.md` | not started | #81 |
| Bot | Core | `components/bot.md` | not started | #82 |
| State | Generic plugin | `components/state.md` | not started | #83 |

## D. Cross-cutting concerns

Each concern must be decided (ADR), described (§8 or an LLD) and testable (§10 scenario).

| Concern | Decided in | Described in | Quality scenario | Status |
|---|---|---|---|---|
| Typing discipline and banned patterns | ADR-0009, ADR-0010 (amended by #36), ADR-0011 (mechanics), ADR-0033 (rule form) | style §4, §3.3; §8 | | wip (§10 scenario pending #37) |
| Error taxonomy (domain / validation / dependency / retryable / permanent / user-visible) | ADR-0014 (values), ADR-0021 (boundary, `FatalError`), ADR-0027 (API exceptions, `retryable`), ADR-0034 (which mechanism) | style §6; §8 | | wip (§10 scenario pending #37) |
| Async, cancellation, timeouts, structured concurrency | ADR-0031 (stdlib asyncio, TaskGroup ownership, explicit timeouts, no `CancelledError` capture, `shield` only in drain, exception-group unwrapping), ADR-0030 (uncancellable threads), #19 | style §5; §8 | | wip (§10 scenario pending #37) |
| Configuration and settings, plugin-contributed settings | ADR-0015 (typed frozen settings objects; loading is the app's) | §8 | | wip |
| Logging and redaction (no message text, tokens, PII) | ADR-0026 (client: never bodies, headers, tokens), #36 (framework-wide rule, no content switch, one redaction list), #29 (observer record) | style §9; §8 | | wip (list finalised by #29) |
| Observability hooks and naming | ADR-0026 (optional composable `RequestObserver`, first-party extra, transport/Middleware for modification; record shape provisional), research 17, #29 | §8 | | wip |
| Security: callback signing, secrets, PII, replay | ADR-0024 (default-on HMAC token, `CallbackTokenCodec`, nonce opt-in, logging rules) | §8 | | wip |
| Dependency injection scopes and lifecycle | ADR-0018, ADR-0019 | §8 | | wip |
| Extension points and plugin isolation (import-linter) | ADR-0002, ADR-0015 (contract), ADR-0032 (layers and direction), #24 (layout) | style §8; §5, §8 | | wip |
| Sync/async duality | ADR-0004 (boundary), ADR-0026 (bare name async, `Sync` prefix), ADR-0029 (scope, thin drivers, paired `SyncHTTPTransport`, parity and conformance mechanisms), ADR-0030 (callable colours) | §8 | | wip |
| Testing strategy (unit / contract / integration / typing / property) | #36 (how tests are written), #25 (toolkit shape) | style §11; §8 | | wip |
| Backpressure and flow control between transport and handlers | ADR-0023 (never-stalling reader, bounded queue, per-kind `OverflowPolicy`), ADR-0030 (own executor sized against the worker count, checked at start) | §8, gateway LLD | | wip |
| Idempotency and stale-action handling | ADR-0022 (CAS, locks), ADR-0024 (optional TTL, opt-in nonce store, `StaleAction` events) | §8 | | wip |
| Single WebSocket consumer and horizontal scaling | ADR-0005, ADR-0023 (`ProcessProfile.websocket_consumer` + optional lease), #40 | §7 | | wip |
| Graceful shutdown and drain | ADR-0023 (close first, drain ≤ 25 s, `DrainTimedOut`), ADR-0030 (a synchronous Handler is abandoned, `HandlerAbandoned`), ADR-0031 (bounded cleanup, `shield` only here) | §6, §8 | | wip |
| Deprecation and public-API definition for semver | ADR-0007 (amended by #36: the four criteria of public), #28 (semver and deprecation window) | style §8, §10 | | wip |

## E. Fog and backlog

The map (#1) is the source of truth for *Not yet specified* and *Out of scope*; backlog ideas are
`enhancement` issues (currently #34). This tracker does not mirror them — check the map.
