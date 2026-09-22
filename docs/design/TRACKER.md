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
| 1 | `01-introduction-and-goals.md` | reviewed | #37 | #13 |
| 2 | `02-constraints.md` | reviewed | #37 | #13 |
| 3 | `03-context-and-scope.md` | reviewed | #38 | #13 #14 #15 #18 #19 #20 #21 #22 |
| 4 | `04-solution-strategy.md` | reviewed | #109 | same |
| 5 | `05-building-block-view.md` | reviewed | #85 | same |
| 6 | `06-runtime-view.md` | reviewed | #39 | #38 #16 #17 |
| 7 | `07-deployment-view.md` | reviewed | #40 | #38 #24 #29 |
| 8 | `08-cross-cutting-concepts.md` | reviewed | #40 | same |
| 9 | `docs/adr/` | rolling | every grilling ticket | not started |
| 10 | `10-quality-requirements.md` | reviewed | #37 | #13 |
| 11 | `11-risks-and-technical-debt.md` | not started | #42 | #40 #41 |
| 12 | `CONTEXT.md` | rolling | every ticket | not started |
| not started | `engineering-style.md` | reviewed | #36 | #23 #13 |
| not started | `diagrams.md` | reviewed | #35 | not started |
| not started | `components/_template.md` | reviewed | #56 | not started |
| not started | `docs/documentation-style.md` | reviewed | #35 | not started |
| not started | `docs/adr/_template.md`, `docs/adr/README.md` | reviewed | #35 | not started |
| not started | Docs-as-code linting: `check-docs.py` (width, links, anchors), `check-index.py`, `check-diagrams.py`, markdownlint, typos and zizmor before every commit and in CI, lychee nightly on external URLs | in progress | #43 | not started |

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
| WebSocketTransport resilience (reconnect, resume, heartbeat, backpressure, Drain, auth loss, library) | #19 | 0023 | reviewed |
| Webhook: events + reply channel, bare ASGI, callback authenticity, replay policy | #20 | 0024 | reviewed |
| Mattermost API layer: generated dataclass models, Codec Protocol, server version policy | #21 | 0025 | reviewed |
| Standalone typed API client: HTTPTransport, httpx2, Operation descriptors, pagination, retries, faces | #21 | 0026 | reviewed |
| API error taxonomy | #21 | 0027 | reviewed |
| Runtime helpers, identity resolution, IdentityCache plugin | #21 | 0028 | reviewed |
| Message composition: attachment, button, select and dialog builders embedding Callback tokens | #52 | | not started |
| File API ergonomics: limits, resumable uploads, streaming | #53 | | not started |
| Execution model: sync face scope, `Workspace` split, thin Faces instead of codegen | #22 | 0029 | reviewed |
| Synchronous callables: `sync_to_thread`, Sync executor, abandon at the Drain | #22 | 0030 | reviewed |
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
| Testing toolkit: pytest as an Extra, explicit plugin activation, three fixtures | #25 | 0044 | reviewed |
| Platform double: one stateful `FakeMattermost` with ports, typed faults and seeding | #25 | 0045 | reviewed |
| `TestBot` over the composed Bot, and no second composition path | #25 | 0046 | reviewed |
| Conformance suite per Core seam: delivery form, capabilities, stability | #25 | 0047 | reviewed |
| Documentation stack and executable docs | #26 | | not started |
| Agent-native repository and AI policy | #27 | | not started |
| CI, release, versioning, changelog, deprecation | #28 | | not started |
| Observability boundary: no Core Protocol, the `Outcome` and Middleware, the `RequestObserver` pair | #29 | 0048 | reviewed |
| What the framework makes observable and on which existing mechanism each fact travels | #29 | 0049 | reviewed |
| Bounded-resource state read from a frozen `bot.stats()` snapshot | #29 | 0050 | reviewed |
| First-party observability plugin: two extras, conventions, registry ownership, cardinality | #29 | 0051 | reviewed |
| Log levels by frequency and audience | #29 | 0052 | reviewed |
| Log records as a documented contract; no logging configuration by us | #29 | 0053 | reviewed |
| Log correlation: `extra`, the task name, a contextvar with a shipped filter | #29 | 0054 | reviewed |
| Redaction list: two sinks, forty names, exact normalised matching | #29 | 0055 | reviewed |
| No scheduler: a periodic task is a Plugin lifecycle, a calendar schedule is a process beside the bot | #30 | 0056 | reviewed |
| Retries of a delivery, dead-letter, circuit breaking and error reporting stay outside, and the breaker recipe names no library | #30 | 0057 | reviewed |
| The `aiommbot` command: a console script behind the `click` extra, no server, `--log-config` only | #30 | 0058 | reviewed |
| `Clock` as the Core's thirteenth seam, with `FakeClock` as its second implementation | #30 | 0059 | reviewed |
| Flood control and delivery dedup as one generic Plugin, and a declined Event as `Unhandled` plus a published `Suppression` | #30 | 0060 | reviewed |
| Health as a generic Plugin over `/livez` and `/readyz`, with application-supplied `ReadinessCheck`s | #30 | 0061 | reviewed |
| What a §8 concept contains once the decision, the rule and the term live elsewhere | #40 | 0062 | reviewed |
| What a §6 scenario is, how a failure branch is split between the picture and a table, and the line between §6, §8 and §10 | #39 | 0067 | reviewed |
| What a storage-backed Plugin does when its backend is unreachable at runtime | #107 | | not started |
| `ProcessProfile`'s full field list, the declared shutdown budget and the bounded stop phase | #40 | 0063 | reviewed |
| Which entry point owns the stop signals, and what a second signal means | #40 | 0064 | reviewed |
| `Standby` as a third Transport state, and what readiness reports for a waiting consumer | #40 | 0065 | reviewed |
| Owner of the single-process Check for a process-local storage backend | #40 | 0066 | reviewed |
| Plugin contract mechanics: the contract version, the collaboration channel, `provides`, the conflict matrix and what a Plugin may not do | #102 | 0069, 0070, 0071, 0072, 0073 | reviewed |
| Plugin lifecycle failure, settings field names under the semver promise, and the third-party author's kit | #103 | 0074, 0075, 0076, 0077, 0078, 0079, 0080 | reviewed |
| Error-tracker integration: whether ADR-0057 stands, and who forks the isolation scope per Event | #104 | | not started |
| Engineering style and ideology: rule form, pattern tiers, derived review checklist | #36 | 0033 | reviewed |
| Error mechanism: typed outcome versus exception | #36 | 0034 | reviewed |
| Quality goals, constraints, quality scenarios | #37 | 0068 | reviewed |
| arc42 conformance of §4 and §5: the building block levels, the whitebox rationale, and §4's tie to the quality goals | #109 | 0081, 0082 | reviewed |
| LLD writing order and parallelism | #41 | 0035 | reviewed |
| Reply-slot typing: second type parameter declared contravariant, `ReplyChannel` as the Core's twelfth seam, `ReplyAlreadySent` Core-owned | #57 | 0036 | reviewed |
| Envelope enrichment: `derive(meta: EventMeta[R2])` only; `dataclasses.replace`, `copy.replace` and `__replace__` on an `Event` banned | #57 | 0037 | reviewed |
| Seam inventory: direction of the call recorded per row, `required` and `provided`, and the count reconciled | #84 | 0038 | reviewed |
| Where the seven `Contributes*`/`HasLifecycle` plugin Protocols live in §5, and what a rank classifies | #85 | 0083, 0084 | reviewed |
| Public API shape (prototype) | #31 | | not started |
| Toolchain skeleton verified (prototype) | #32 | | not started |
| Risk register | #42 | | not started |

## C. Component design documents (LLD)

The inventory summary of `05-building-block-view.md` lists **32 components** across five layers,
with 32 part rows and two interface inventories — sixteen Protocols on thirteen *seam* rows, twelve
required and one provided (§5.1.1), and the seven Contribution Protocols of the plugin contract
(§5.1.2) — none of which gets a document of its own. One row per component here and one
`LLD: <component>` ticket each. The file name is the `CONTEXT.md` term in kebab-case.

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
| Observability plugin | Generic plugin | `components/observability.md` | not started | #92 |
| FloodControl | Generic plugin | `components/flood-control.md` | not started | #96 |
| Health | Generic plugin | `components/health.md` | not started | #97 |
| FakeMattermost | Testing toolkit | `components/fake-mattermost.md` | not started | #88 |
| Testing toolkit | Testing toolkit | `components/testing-toolkit.md` | not started | #89 |

## D. Cross-cutting concerns

Each concern must be decided (ADR), described (§8 or an LLD) and testable (§10 scenario). This table
is the register both §8 and §10 are written from: fifteen of the seventeen rows name a §8 subsection
and every row names a §10 scenario, and neither section holds anything without a row here
([ADR-0062](../adr/0062-a-cross-cutting-concept-is-a-mechanism-a-grid-and-a-limit.md),
[ADR-0068](../adr/0068-a-quality-scenario-is-a-registered-concern-measured-by-a-fixed-number-or-a-named-check.md)).
A row still reading `in progress` is waiting on a decision of its own, named in the status.

| Concern | Decided in | Described in | Quality scenario | Status |
|---|---|---|---|---|
| Typing discipline and banned patterns | ADR-0006 (Protocols and frozen values), ADR-0009, ADR-0010, ADR-0011 (mechanics), ADR-0025 (optionality at the wire edge), ADR-0033 (rule form), ADR-0034 (typed outcome versus exception) | style §4, §3.3; §8.1 | [§10.3](10-quality-requirements.md#103-correctness-by-mechanism) | reviewed |
| Error taxonomy (domain / validation / dependency / retryable / permanent / user-visible) | ADR-0014 (values), ADR-0021 (boundary, `FatalError`), ADR-0027 (API exceptions, `retryable`), ADR-0034 (which mechanism), ADR-0057 (what the framework refuses to do about a failure), research 31 | style §6; §8.2 | [§10.2](10-quality-requirements.md#102-reliability) | in progress (ADR-0057's premise about error reporting pending #104) |
| Async, cancellation, timeouts, structured concurrency | ADR-0031 (stdlib asyncio, TaskGroup ownership, explicit timeouts, no `CancelledError` capture, `shield` only in the Drain, exception-group unwrapping), ADR-0030 (uncancellable threads), ADR-0059 (`Clock` as the seam every duration is measured and slept through), ADR-0063 (`stop_timeout` as the bound on cleanup) | style §5; §8.3 | [§10.2](10-quality-requirements.md#102-reliability) | reviewed |
| Configuration and settings, plugin-contributed settings | ADR-0015 (typed frozen settings objects; loading is the app's), ADR-0016 (the check phase reports a wrong combination), ADR-0053 and ADR-0058 (`--log-config` as one of the two operator-opted exceptions), ADR-0030 (the other), ADR-0077 (a field name is public, carried there by its type, and a rename is breaking), ADR-0078 (a logger is one such field), research 35, 44 | §8.7 | [§10.3](10-quality-requirements.md#103-correctness-by-mechanism) | reviewed |
| Logging and redaction (no message text, tokens, PII) | ADR-0026 (client: never bodies, headers, tokens), ADR-0033 (the rulebook), ADR-0052 (levels), ADR-0053 (the record catalogue, no configuration), ADR-0054 (correlation), ADR-0055 (the forty names over two sinks), ADR-0058 (the command's `--log-config`, the one exception), ADR-0078 (a logger arrives in the settings, typed `logging.Logger`), ADR-0079 (what `ST-LOG-01` binds, and why the catalogue survives), research 43 | style §9, §10 (`ST-DOC-08`); §8.12 | [§10.6](10-quality-requirements.md#106-security) | reviewed |
| Observability seam and naming | ADR-0048 (no Core Protocol; the `RequestObserver` pair), ADR-0049 (what is observable), ADR-0050 (`bot.stats()`), ADR-0051 (extras, OpenTelemetry conventions, registry, cardinality), ADR-0061 (the probe paths as the sixth mechanism), research 17, 23 | §8.13; `components/observability.md` | [§10.5](10-quality-requirements.md#105-modifiability) | reviewed |
| Security: callback signing, secrets, PII, replay | ADR-0024 (default-on HMAC token, `CallbackTokenCodec`, nonce opt-in, logging rules), ADR-0023 (`TokenProvider`, rotation is the application's), ADR-0027 (what an auth failure may report), ADR-0055 (the redaction list) | §8.14; §7 for the credentials each Process shape needs | [§10.6](10-quality-requirements.md#106-security) | reviewed |
| Dependency injection scopes and lifecycle | ADR-0018, ADR-0019, ADR-0046 (overrides exist only in the toolkit) | §8.5 | [§10.3](10-quality-requirements.md#103-correctness-by-mechanism) | reviewed |
| Extension points and plugin isolation (import-linter) | ADR-0002, ADR-0015 (contract), ADR-0016 (compose, check, start), ADR-0032 (layers and direction), ADR-0038 (the seam inventory), ADR-0040 (directories and contract shape), ADR-0069 (no version, the contract only grows), ADR-0070 (no channel: the composition hands one instance to each consumer), ADR-0071 (list order, no declared dependency), ADR-0072 (what the check phase refuses and where the catalogue lives), ADR-0073 (what a Plugin may not do), ADR-0074 (a failed start runs the one Stop phase and nothing retries), ADR-0075 (the failure names its Plugin, several are one group), ADR-0076 (a Bot runs once), ADR-0080 (the author's kit: a section of the reference page, a name convention, no scaffold), ADR-0083 (the contract is the level-1 whitebox's second interface, specified where each contribution is handled), ADR-0084 (an interface carries no rank), research 30, 33, 34, 41, 42 | style §8; §5.1.2, §8.6 | [§10.5](10-quality-requirements.md#105-modifiability) | reviewed |
| Sync/async duality | ADR-0031 (one asyncio engine), ADR-0026 (bare name async, `Sync` prefix), ADR-0029 (scope, thin Faces, paired `SyncHTTPTransport`, parity and conformance mechanisms), ADR-0030 (callable colours), ADR-0008 (free threading claimed only where the 3.14t job tests it) | §8.4 | [§10.3](10-quality-requirements.md#103-correctness-by-mechanism) | reviewed |
| Testing strategy (unit / contract / integration / typing / property) | ADR-0033 and style §11 (how tests are written), ADR-0044 (packaging and activation), ADR-0045 (the platform double), ADR-0046 (`TestBot`), ADR-0047 (conformance suites), ADR-0059 (`FakeClock`) | style §11; §5.2.5; §8.15 | [§10.4](10-quality-requirements.md#104-testability) | reviewed |
| Backpressure and flow control between transport and handlers | ADR-0023 (never-stalling reader, bounded queue, per-kind `OverflowPolicy`), ADR-0030 (Sync executor sized against the Dispatch concurrency, checked at start), ADR-0050 (depth is read, not pushed), ADR-0060 (declining a delivery before the walk, keyed on chat identity) | §8.8, gateway LLD | [§10.2](10-quality-requirements.md#102-reliability) | reviewed |
| Idempotency and stale-action handling | ADR-0022 (CAS, locks), ADR-0024 (optional TTL, opt-in nonce store, `StaleAction` events), ADR-0030 (an abandoned synchronous Handler must be idempotent), ADR-0060 (delivery dedup by platform identity, failing open) | §8.9; §7 for which processes must share a store | [§10.2](10-quality-requirements.md#102-reliability) | reviewed |
| Single WebSocket consumer and horizontal scaling | ADR-0005, ADR-0023 (`ProcessProfile.websocket_consumer` + optional lease), ADR-0056 (no second single-instance process of ours), ADR-0061 (readiness as the only rollout signal a Pod with no Service has), ADR-0065 (`Standby` and what readiness reports for it) | §7 | [§10.2](10-quality-requirements.md#102-reliability) | reviewed |
| Graceful shutdown and the Drain | ADR-0023 (close first, Drain ≤ 25 s, `DrainTimedOut`), ADR-0030 (a synchronous Handler is abandoned, `HandlerAbandoned`), ADR-0031 (bounded cleanup, `shield` only here), ADR-0061 (readiness turns false at the Drain, liveness does not), ADR-0063 (the declared budget and the bounded stop phase), ADR-0064 (which entry point catches the signal) | §6, §8.10; §7 for the arithmetic | [§10.2](10-quality-requirements.md#102-reliability) | reviewed |
| Runtime probes: liveness, readiness and what a prober may learn | ADR-0061 (the two paths, the empty body, the cached aggregate, application-supplied checks), ADR-0065 (a standby Transport counts as connected), research 26, 27, 29 | §7, §8.11; `components/health.md` | [§10.2](10-quality-requirements.md#102-reliability) | reviewed |
| Deprecation and public-API definition for semver | ADR-0007 (the four criteria of public), ADR-0042 (the documented path), ADR-0043 (re-export form, reference page, internal-API page), ADR-0047 (what tightening a conformance suite means), research 22 §6.4 (the shim shape), #28 (semver and deprecation window) | the rulebook's §8 and §10, not arc42 §8 | [§10.5](10-quality-requirements.md#105-modifiability) | in progress (window pending #28) |

## E. Fog and backlog

The map (#1) is the source of truth for *Not yet specified* and *Out of scope*; backlog ideas are
`enhancement` issues (currently #34). This tracker does not mirror them — check the map.
