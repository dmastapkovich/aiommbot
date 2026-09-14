# 10. Quality requirements

_Status: reviewed (#37)._

The five goals [§1.2](01-introduction-and-goals.md#12-quality-goals) ranks, made decidable.
Seventeen scenarios, one for each concern the design registered, each saying in what context which
stimulus produces which response and how fulfilment is decided.

## 10.0 How to read this section

**What admits a scenario.** A row of [`TRACKER.md`](TRACKER.md) §D, and nothing else: every
registered concern owes one scenario and there is no scenario without a row
([ADR-0068](../adr/0068-a-quality-scenario-is-a-registered-concern-measured-by-a-fixed-number-or-a-named-check.md)).
§1.2 ranks the goals, §10.1 files every concern under exactly one of them, and the two tables are
each other's completeness test.

**What a measure is.** A duration or a size only where a decision already fixed one; everywhere
else the name of a check that will run — a Conformance suite, an `ST-<AREA>-NN` rule of
[`engineering-style.md`](engineering-style.md), a typing test or an import-linter contract. A
library produces no operational number, so a threshold nobody will measure is not a measure, while
a named check is one a reader can run (ADR-0068).

**The form of a row.** Context, stimulus, response, measure — arc42's own short form with the
response named separately, so that a behavioural response stays visible beside the criterion that
decides it. The seventeen span all three kinds arc42 publishes: most are *failure* scenarios; §10.4
and the last two rows of §10.5 are *change* scenarios, since their stimulus is somebody modifying
the system; and §10.2's backpressure row and §10.5's observability row are *usage* scenarios.

**Where a failure goes.** The same failure reaches three sections on three different questions:
[§6](06-runtime-view.md) states the order and where it splits,
[§8](08-cross-cutting-concepts.md) states the rule the mechanism follows, and this section states
the measurable stimulus and response
([ADR-0067](../adr/0067-a-runtime-scenario-is-one-order-between-boxes.md)). Nothing here repeats a
mechanism or an order.

**Performance is not a goal and has no scenario.** No throughput, latency or memory target exists
for 0.5.0 and none is invented to fill the slot; the question stays open on the map.

## 10.1 Quality tree

Goals to concerns. Its use is the one arc42 keeps for a tree: a goal with no concern under it would
be a goal nothing tests, and a concern under no goal would be a concern nothing ranks.

| Goal | Concerns filed under it (§D) | Scenarios |
|---|---|---|
| 1. Reliability | Error taxonomy · Async, cancellation, timeouts · Backpressure and flow control · Idempotency and stale actions · Single WebSocket consumer and horizontal scaling · Graceful shutdown and the Drain · Runtime probes | [§10.2](#102-reliability) |
| 2. Correctness by mechanism | Typing discipline and banned patterns · Configuration and settings · Dependency injection scopes and lifecycle · Sync/async duality | [§10.3](#103-correctness-by-mechanism) |
| 3. Testability | Testing strategy | [§10.4](#104-testability) |
| 4. Modifiability | Observability seam and naming · Extension points and plugin isolation · Deprecation and public-API definition | [§10.5](#105-modifiability) |
| 5. Security | Logging and redaction · Security: callback signing, secrets, PII, replay | [§10.6](#106-security) |

## 10.2 Reliability

| Concern | Context | Stimulus | Response | Measure |
|---|---|---|---|---|
| Error taxonomy | A Bot dispatching events, with the Core ErrorBoundary as the outermost link of the Handler layer | A Handler raises an exception the framework did not expect | One ERROR record carrying no payload, `Failed` returned to both Middleware layers, and the Dispatcher takes the next Event; the process exits only under an explicit policy | The ErrorBoundary conformance case: one record, no payload field, `Failed` observed by Middleware, and the next Event dispatched |
| Async, cancellation and timeouts | A process started through `run()`, with Handlers in flight and every Plugin started | A stop signal arrives | Every task is cancelled inside the `TaskGroup` that owns it, `CancelledError` is never captured, and `shield` appears only in the Drain | The whole stop completes inside `stop_timeout`, shipped at 28 s ([ADR-0063](../adr/0063-the-process-declares-its-shutdown-budget-and-the-bot-bounds-the-stop.md)), asserted under `FakeClock` |
| Backpressure and flow control | A connected WebSocketTransport whose bounded queue is full because Handlers retire events more slowly than they arrive | Events keep arriving | The reader never stalls, the per-kind `OverflowPolicy` decides what gives way, and the heartbeat keeps its cadence | No `ping` missed at its 30 s cadence and no silence reaching 60 s ([ADR-0023](../adr/0023-websocket-gateway-resilience.md)); queue depth readable from `bot.stats()` |
| Idempotency and stale actions | A Bot with FloodControl composed and Callback tokens carrying a TTL over an opt-in nonce store | The same delivery arrives twice — a replayed callback, or a post redelivered after a Resync | The replayed callback becomes a `StaleAction` Event; the duplicate delivery is declined before the tree walk and publishes a `Suppression` | The replay cases of the `CallbackTokenCodec` and FloodControl suites: exactly one Handler invocation per platform identity |
| Single WebSocket consumer and horizontal scaling | Two replicas of one composition, both declaring `websocket_consumer`, with a consumer lease configured | Both processes start | One holds the lease and connects; the other enters `Standby`, opens no socket and still reports ready | The lease case of the WebSocketTransport suite, and `/readyz` answering 204 for the standby replica ([ADR-0065](../adr/0065-a-transport-waiting-on-the-consumer-lease-is-standby-and-counts-as-ready.md)) |
| Graceful shutdown and the Drain | A Bot process with a non-empty queue, Handlers in flight, and a 30 s Shutdown budget declared to the Process host | The stop signal arrives | The socket closes first, the queue and the in-flight Handlers drain, Plugins stop in reverse topological order, and what is left is cancelled with `DrainTimedOut(count)` | A 25 s Drain inside a 28 s stop inside the declared 30 s budget ([ADR-0063](../adr/0063-the-process-declares-its-shutdown-budget-and-the-bot-bounds-the-stop.md)), asserted under `FakeClock` |
| Runtime probes | A running consumer whose Health Plugin is composed and whose probe paths a host is polling | The socket stops producing data of any kind | The silence monitor fires and the Transport reconnects; readiness turns false while it is disconnected and liveness does not move | 60 s without data is the trigger ([ADR-0023](../adr/0023-websocket-gateway-resilience.md)); `/livez` answers 204 throughout ([ADR-0061](../adr/0061-health-is-a-generic-plugin-over-application-supplied-checks.md)) |

## 10.3 Correctness by mechanism

| Concern | Context | Stimulus | Response | Measure |
|---|---|---|---|---|
| Typing discipline and banned patterns | The check phase of a composition whose Router tree has been frozen | A Handler subscribes to a payload type no `EventRegistry` entry can produce | The start is refused with every unreachable Handler listed; no socket is opened and no Plugin is started | The unreachable-handler case of the Router suite plus a `tests/typing` negative case, with no suppression outside a Quarantine module ([ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md)) |
| Configuration and settings | A composition whose `ProcessProfile` declares the process replicated | It also composes an in-memory `KeyValueStore`, and a second Plugin's settings contradict a third's | The check phase collects every failing Check and stops the start with the full list, before any side effect runs | The process exits non-zero and the message names every failure rather than the first ([ADR-0016](../adr/0016-three-phase-start-with-checks.md)) |
| Dependency injection scopes and lifecycle | The check phase, validating the dependency graph and compiling each Handler's plan | A Handler parameter has neither a Provider nor an Extractor, or a Provider's own dependency is unsatisfiable | Validation fails, naming the key and the Handler that needs it | The `DependencyProvider` conformance suite ([ADR-0047](../adr/0047-a-conformance-suite-per-core-seam.md)) |
| Sync/async duality | A Router taking Handler registrations before the tree is frozen | A `def` Handler is registered without `sync_to_thread`, or an `async def` one with it | The first refuses the start naming the rule; the second warns | Both cases in the routing conformance suite ([ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md)) |

## 10.4 Testability

| Concern | Context | Stimulus | Response | Measure |
|---|---|---|---|---|
| Testing strategy | A third-party implementation of a Core seam, and an application's own bot, with no Mattermost server available to either | The implementation is handed to that seam's conformance factory, and the bot is fed events through `TestBot` over `FakeMattermost` | Every case of the suite runs against the implementation, including the capabilities it declines; the bot runs on the composed Bot, and the toolkit composes none of its own | The seam's suite, one of the fourteen, reporting each named case's expectation and observation as typed data ([ADR-0047](../adr/0047-a-conformance-suite-per-core-seam.md)) |

## 10.5 Modifiability

| Concern | Context | Stimulus | Response | Measure |
|---|---|---|---|---|
| Observability seam and naming | A Bot composed with no observability Plugin and none of its extras installed | The bot dispatches events and calls the API | No metric and no span is produced, and no OpenTelemetry module is imported | The smoke-import test without extras ([ADR-0051](../adr/0051-first-party-observability-plugin.md)) |
| Extension points and plugin isolation | The package's import graph under its layer contract | A generic Plugin imports the Adapter, or one Plugin imports another | The build fails before a test runs | The `layers` and `independence` contracts of import-linter ([ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md)) |
| Deprecation and public-API definition | The public surface and the reference page that lists it | A name is added to or removed from either one | The two disagree | The guard test that reads the reference page and the package in both directions ([ADR-0043](../adr/0043-explicit-re-export-with-a-reference-page-as-the-public-list.md)) |

## 10.6 Security

| Concern | Context | Stimulus | Response | Measure |
|---|---|---|---|---|
| Logging and redaction | Any log record or observability record being built anywhere in the framework | A field whose normalised name is one of the forty | The value reaches neither sink | The redaction test over all forty names and both sinks ([ADR-0055](../adr/0055-one-redaction-list-over-two-sinks.md)) |
| Security: callback signing, secrets, PII, replay | A Webhook ingress with Callback tokens on by default, serving buttons a bot issued earlier | A callback arrives whose `context` was altered, or whose token is past its TTL | `CallbackTokenCodec` reports the token expired or replayed, no Handler runs for the altered payload, and the ingress still answers inside its deadline | The verified, expired and replayed cases of the `CallbackTokenCodec` suite, with no Handler invocation recorded, answered within the 10 s reply deadline ([ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md)) |
