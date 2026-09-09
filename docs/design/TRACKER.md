# Documentation readiness tracker

The single view of what the design catalogue must contain and how far each piece is. Every ticket
resolution updates its rows **in the same commit**. The hand-off ticket (#33) may close only when
every row reads `reviewed` or has an explicit *deferred to implementation* note.

Legend: `not started` · `in progress` · `reviewed` (passes `.agents/design-quality-checklist.md`) ·
`rolling` (grows with every ticket) · `n/a` (say why) — the grammar of `docs/documentation-style.md`
§3; the ticket is the row's *Ticket* column.

## A. Architecture document (arc42)

| § | Document | Status | Ticket | Depends on |
|---|---|---|---|---|
| 1 | `01-introduction-and-goals.md` | not started | #37 | #13 |
| 2 | `02-constraints.md` | in progress | #37 | #13 |
| 3 | `03-context-and-scope.md` | reviewed | #38 | #13 #14 #15 #18 #19 #20 #21 #22 |
| 4 | `04-solution-strategy.md` | reviewed | #38 | same |
| 5 | `05-building-block-view.md` | reviewed | #38 | same |
| 6 | `06-runtime-view.md` | not started | #39 | #38 #16 #17 |
| 7 | `07-deployment-view.md` | in progress | #40 | #38 #24 #29 #30 |
| 8 | `08-cross-cutting-concepts.md` | not started | #40 | same |
| 9 | `docs/adr/` | rolling | every grilling ticket | not started |
| 10 | `10-quality-requirements.md` | not started | #37 | #13 |
| 11 | `11-risks-and-technical-debt.md` | not started | #42 | #40 #41 |
| 12 | `CONTEXT.md` | rolling | every ticket | not started |
| not started | `engineering-style.md` | reviewed | #36 | #23 #13 |
| not started | `diagrams.md` | reviewed | #35 | not started |
| not started | `components/_template.md` | reviewed | #56 | not started |
| not started | `docs/documentation-style.md` | reviewed | #35 | not started |
| not started | `docs/adr/_template.md`, `docs/adr/README.md` | reviewed | #35 | not started |
| not started | Docs-as-code linting (markdown, Vale, lychee, Mermaid, index check) | not started | #43 | #26 |

## B. Decision areas → ADR

One row per design decision the map must make. `ADR` is filled when the ticket closes.

| Area | Ticket | ADR | Status |
|---|---|---|---|
| Fresh public start, no compatibility promise toward any earlier release | charting | 0001 | reviewed |
| Core scope: what the bare core owns and refuses | #13 | 0002 | reviewed |
| Stateless core; State plugin with mandatory backend | #13 (→ #18) | 0003 | reviewed |
| Execution model boundary: one asyncio engine, a narrow synchronous Face | #13 (→ #22) | 0004 retired → 0029, 0030, 0031 | reviewed |
| Scaling model: one consumer, many workers | #13 (→ #19, #40) | 0005 | reviewed |
| Architectural tenets: composition, Core-owned Protocols, named patterns, typing, fail closed | #13 (→ #36) | 0006 | reviewed |
| Public API surface: tiny root + explicit subpackages | #13 (→ #24, #36) | 0007 | reviewed |
| Plugin contract, adapter role, ordering, settings, discovery, stability | #14 | 0015 | reviewed |
| Three-phase start, checks framework, ProcessProfile | #14 | 0016 | reviewed |
| Lifecycle Signals | #14 | 0017 | reviewed |
| Event model: envelope, payload registry, first-class kinds | #15 | 0012 | reviewed |
| Routing: type-driven subscription, tree walk, typed outcome, reachability | #15 | 0013 | reviewed |
| Filters, extractors, closed handler signatures | #15 | 0014 | reviewed |
| Full typed coverage of the event catalogue | #45 | | not started |
| Dependency injection: ownership, key, scopes, providers, graph | #16 | 0018 | reviewed |
| Handler parameter resolution rules, built-ins, test overrides | #16 | 0019 | reviewed |
| Middleware layers, contract, publication, flags, ordering | #17 | 0020 | reviewed |
| Core error boundary | #17 | 0021 | reviewed |
| State/FSM, event isolation, storage contract, first-party backends, lifetime | #18 | 0022 | reviewed |
| Declarative scenes on top of State | #48 | | not started |
| Resync backfill: first-party plugin or documented recipe | #55 | | not started |
| WebSocketTransport resilience (reconnect, resume, heartbeat, backpressure, drain, auth loss, library) | #19 | 0023 | reviewed |
| Webhook: events + reply channel, bare ASGI, callback authenticity, replay policy | #20 | 0024 | reviewed |
| Mattermost API layer: generated dataclass models, Codec Protocol, server version policy | #21 | 0025 | reviewed |
| Standalone typed API client: HTTPTransport, httpx2, Operation descriptors, pagination, retries, faces | #21 | 0026 | reviewed |
| API error taxonomy | #21 | 0027 | reviewed |
| Runtime helpers, identity resolution, IdentityCache plugin | #21 | 0028 | reviewed |
| Message composition: attachment, button, select and dialog builders embedding Callback tokens | #52 | | not started |
| File API ergonomics: limits, resumable uploads, streaming | #53 | | not started |
| Execution model: sync face scope, `Workspace` split, thin Faces instead of codegen | #22 | 0029 | reviewed |
| Synchronous callables: `sync_to_thread`, Sync executor, abandon at drain | #22 | 0030 | reviewed |
| Concurrency discipline, event-loop ownership, process entry points | #22 | 0031 | reviewed |
| Python floor and support policy | #23 | 0008 | reviewed |
| Type checkers and typing tests | #23 | 0009 | reviewed |
| Zero suppressions and quarantine | #23 (→ #36) | 0010 | reviewed |
| Lint, format, architecture toolchain, task runner | #23 | 0011 | reviewed |
| Layer model and the direction of allowed dependencies | #38 | 0032 | reviewed |
| Repository layout: `src/`, tests, examples | #24 | 0039 | reviewed |
| Package layout: one directory per import rank, module named after its term | #24 | 0040 | reviewed |
| Default dependencies, one extra per optional library, dependency groups | #24 | 0041 | reviewed |
| The documented import path of a public name | #24 | 0042 | reviewed |
| Public surface mechanism: explicit re-export, reference page, internal-API page | #24 | 0043 | reviewed |
| Testing toolkit | #25 | | not started |
| Documentation stack and executable docs | #26 | | not started |
| Agent-native repository and AI policy | #27 | | not started |
| CI, release, versioning, changelog, deprecation | #28 | | not started |
| Observability boundary | #29 | | not started |
| Scheduling, reliability middlewares, CLI boundaries | #30 | | not started |
| Engineering style and ideology: rule form, pattern tiers, derived review checklist | #36 | 0033 | reviewed |
| Error mechanism: typed outcome versus exception | #36 | 0034 | reviewed |
| Quality goals, constraints, quality scenarios | #37 | | not started |
| LLD writing order and parallelism | #41 | 0035 | reviewed |
| Reply-slot typing: second type parameter declared contravariant, `ReplyChannel` as the Core's twelfth seam, `ReplyAlreadySent` Core-owned | #57 | 0036 | reviewed |
| Envelope enrichment: `derive(meta: EventMeta[R2])` only; `dataclasses.replace`, `copy.replace` and `__replace__` on an `Event` banned | #57 | 0037 | reviewed |
| Seam inventory: direction of the call recorded per row, `required` and `provided`, and the count reconciled | #84 | 0038 | reviewed |
| Rank of the six `Contributes*`/`HasLifecycle` plugin Protocols in §5 | #85 | | not started |
| Public API shape (prototype) | #31 | | not started |
| Toolchain skeleton verified (prototype) | #32 | | not started |
| Risk register | #42 | | not started |

## C. Component design documents (LLD)

§5.10 of `05-building-block-view.md` lists **28 components** across five layers, with 27 part
rows and fourteen Protocols on twelve *seam* rows — eleven required, one provided — that get no
document of their own. One row per component here and one `LLD: <component>` ticket each; the
testing toolkit's row appears once #25 has decided its shape. The file name is the `CONTEXT.md`
term in kebab-case.

| Component | Layer | File | Status | Ticket |
|---|---|---|---|---|
| Event | Core | `components/event.md` | reviewed | #86 |
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
| Typing discipline and banned patterns | ADR-0009, ADR-0010, ADR-0011 (mechanics), ADR-0033 (rule form) | style §4, §3.3; §8 | | in progress (§10 scenario pending #37) |
| Error taxonomy (domain / validation / dependency / retryable / permanent / user-visible) | ADR-0014 (values), ADR-0021 (boundary, `FatalError`), ADR-0027 (API exceptions, `retryable`), ADR-0034 (which mechanism) | style §6; §8 | | in progress (§10 scenario pending #37) |
| Async, cancellation, timeouts, structured concurrency | ADR-0031 (stdlib asyncio, TaskGroup ownership, explicit timeouts, no `CancelledError` capture, `shield` only in drain, exception-group unwrapping), ADR-0030 (uncancellable threads), #19 | style §5; §8 | | in progress (§10 scenario pending #37) |
| Configuration and settings, plugin-contributed settings | ADR-0015 (typed frozen settings objects; loading is the app's) | §8 | | in progress |
| Logging and redaction (no message text, tokens, PII) | ADR-0026 (client: never bodies, headers, tokens), #36 (framework-wide rule, no content switch, one redaction list), #29 (observer record) | style §9; §8 | | in progress (list finalised by #29) |
| Observability seam and naming | ADR-0026 (optional composable `RequestObserver`, first-party extra, transport/Middleware for modification; record shape provisional), research 17, #29 | §8 | | in progress |
| Security: callback signing, secrets, PII, replay | ADR-0024 (default-on HMAC token, `CallbackTokenCodec`, nonce opt-in, logging rules) | §8 | | in progress |
| Dependency injection scopes and lifecycle | ADR-0018, ADR-0019 | §8 | | in progress |
| Extension points and plugin isolation (import-linter) | ADR-0002, ADR-0015 (contract), ADR-0032 (layers and direction), ADR-0040 (directories and contract shape) | style §8; §5, §8 | | in progress |
| Sync/async duality | ADR-0031 (one asyncio engine), ADR-0026 (bare name async, `Sync` prefix), ADR-0029 (scope, thin Faces, paired `SyncHTTPTransport`, parity and conformance mechanisms), ADR-0030 (callable colours) | §8 | | in progress |
| Testing strategy (unit / contract / integration / typing / property) | #36 (how tests are written), #25 (toolkit shape) | style §11; §8 | | in progress |
| Backpressure and flow control between transport and handlers | ADR-0023 (never-stalling reader, bounded queue, per-kind `OverflowPolicy`), ADR-0030 (Sync executor sized against the Dispatch concurrency, checked at start) | §8, gateway LLD | | in progress |
| Idempotency and stale-action handling | ADR-0022 (CAS, locks), ADR-0024 (optional TTL, opt-in nonce store, `StaleAction` events) | §8 | | in progress |
| Single WebSocket consumer and horizontal scaling | ADR-0005, ADR-0023 (`ProcessProfile.websocket_consumer` + optional lease), #40 | §7 | | in progress |
| Graceful shutdown and drain | ADR-0023 (close first, drain ≤ 25 s, `DrainTimedOut`), ADR-0030 (a synchronous Handler is abandoned, `HandlerAbandoned`), ADR-0031 (bounded cleanup, `shield` only here) | §6, §8 | | in progress |
| Deprecation and public-API definition for semver | ADR-0007 (the four criteria of public), ADR-0042 (the documented path), ADR-0043 (re-export form, reference page, internal-API page), research 22 §6.4 (the shim shape), #28 (semver and deprecation window) | style §8, §10 | | in progress |

## E. Fog and backlog

The map (#1) is the source of truth for *Not yet specified* and *Out of scope*; backlog ideas are
`enhancement` issues (currently #34). This tracker does not mirror them — check the map.
