# 8. Cross-cutting concepts

_Status: reviewed (#40)._

The concerns that no single component owns. Each section below says how the concern works in this
system, which components carry it, and where it stops; the choice behind it is its ADR, the rule it
becomes is [`engineering-style.md`](engineering-style.md), and the word is
[`CONTEXT.md`](../../CONTEXT.md). None of the three is restated here
([ADR-0062](../adr/0062-a-cross-cutting-concept-is-a-mechanism-a-grid-and-a-limit.md)).

The register of concerns is [`TRACKER.md`](TRACKER.md) §D: every row whose *Described in* names §8
has a section, and there is no section without a row.

## 8.0 Which components carry which concept

The grid the rest of the catalogue does not hold: [§5](05-building-block-view.md) maps components to
their decisions and §D maps concerns to theirs, and neither joins the two. An
`LLD: <component>` ticket reads its column before it writes anything.

| Concept | Core | Adapter | Generic plugin | Adapter-specific plugin | Testing toolkit |
|---|---|---|---|---|---|
| 8.1 Typing | Event, Extractor, DependencyProvider, Filter | Generated model, Codec, Operation | — | — | Testing toolkit |
| 8.2 Errors | ErrorBoundary, Extractor, Dispatcher | API client, AuthLossDetector | State, KeyValueStore backends | Callback token, Webhook | FakeMattermost |
| 8.3 Async | Bot, Dispatcher, Sync executor, Signal | — | Health | WebSocketTransport, Webhook | Testing toolkit |
| 8.4 Duality | Sync executor | Exchange, Face, Workspace, API client | — | — | Testing toolkit |
| 8.5 Injection | DependencyProvider, Bot, Dispatcher, Router | Runtime | — | — | Testing toolkit |
| 8.6 Extension | Bot, Signal | EventRegistry | State, FloodControl, Health, Observability plugin | WebSocketTransport, Webhook, IdentityCache | — |
| 8.7 Configuration | Bot | — | every Plugin | every Plugin | TestBot |
| 8.8 Backpressure | Dispatcher, Sync executor | — | — | WebSocketTransport | — |
| 8.9 Idempotency | — | — | State, FloodControl | Callback token, Webhook, WebSocketTransport | FakeMattermost |
| 8.10 Drain | Bot, Sync executor | — | Health | WebSocketTransport, Webhook | — |
| 8.11 Probes | Bot, Signal | — | Health | WebSocketTransport | — |
| 8.12 Logging | ErrorBoundary, Bot | API client, AuthLossDetector | — | WebSocketTransport, Webhook, Callback token | — |
| 8.13 Observability | Middleware, Bot | API client | Observability plugin, KeyValueStore backends | — | — |
| 8.14 Security | — | Face, API client, AuthLossDetector | — | Callback token, Webhook | FakeMattermost |
| 8.15 Testing | every component | every component | every component | every component | Testing toolkit, FakeMattermost |

## 8.1 Typing discipline

A contract crossing a boundary is a `Protocol`, and a value crossing it is a frozen
`dataclass(slots=True)`; generics carry the variation — `Event[P, R]` is the envelope every other
block reads without knowing a payload — and `Annotated` carries the qualification. A branch the
caller must take in normal operation is a Typed outcome, so `Value | NoMatch | Invalid`, `Conflict`
and `Verified | Expired | Replayed` are values rather than exceptions. Optionality is expressed
once, at the edge where the wire says it: a response model carries `required` from the overlay and a
request model carries `UNSET`. **Where it stops**: the framework types what it owns; a payload that
Mattermost leaves as a bare object is a hand-written model, and a third-party library with
incomplete stubs is adapted in a Quarantine module and nowhere else.

_Decided in_: [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md),
[ADR-0009](../adr/0009-four-strict-type-checkers.md),
[ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md),
[ADR-0025](../adr/0025-generated-dataclass-models-with-a-codec-protocol.md),
[ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md),
[ADR-0036](../adr/0036-reply-slot-as-a-second-type-parameter-over-a-core-owned-reply-channel.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §4 (`ST-TYP-01`…`ST-TYP-17`) and §3.3.
_Carried by_: Event, Extractor, Filter, DependencyProvider, Generated model, Codec.

## 8.2 Error taxonomy

Two mechanisms, chosen by who must act. A caller that has a branch to take gets a Typed outcome; a
broken contract or a failed dependency raises, from one root — `AiommbotError`, with `FatalError`
beside it for the failures no retry can fix. Dispatch never propagates an exception to a Transport:
the ErrorBoundary is the outermost link, it writes the one record the framework allows a traceback
in, and it returns `Failed(error)`, so a Transport reacts to a value. The Adapter's REST failures
carry the platform's own fields — status, `error_id`, `request_id` — and a `retryable` property that
says whether repeating the call can help; `FatalError` and `BaseException` pass the boundary
untouched, which is how an authentication loss stops a process instead of looping. **Where it
stops**: the framework decides nothing about *recovering* from a failure — retry of a delivery,
dead-letter and circuit breaking are outside it.

_Decided in_: [ADR-0014](../adr/0014-filters-and-extractors-with-closed-handler-signatures.md),
[ADR-0021](../adr/0021-core-error-boundary.md),
[ADR-0027](../adr/0027-api-error-taxonomy.md),
[ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md),
[ADR-0057](../adr/0057-reliability-middlewares-and-error-reporting-stay-outside.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §6 (`ST-ERR-01`…`ST-ERR-10`).
_Carried by_: ErrorBoundary, Dispatcher, Extractor, API client, AuthLossDetector, State,
Callback token, Webhook.

## 8.3 Async, cancellation and timeouts

One engine, standard-library asyncio, and one discipline over it: every task lives in a `TaskGroup`
owned by a named component, every await that touches I/O sits under an explicit `asyncio.timeout`,
and `CancelledError` is never caught. Cleanup is `try`/`finally` and `except*`, bounded in time by
the Bot's `stop_timeout`, and `asyncio.shield` appears in exactly one named place, the Drain. A
solitary exception is lifted out of a `BaseExceptionGroup` with `__cause__` and `__context__`
preserved before it reaches a public API, and siblings are never discarded. Every duration — a
timeout, a TTL, a backoff — is measured and slept through the `Clock` seam, which is why a test
advances time instead of waiting. **Where it stops**: trio is unsupported and `anyio` is never a
Core dependency; the event loop belongs to the application, which passes a `loop_factory` if it
wants one of its own.

_Decided in_: [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md),
[ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md),
[ADR-0059](../adr/0059-clock-is-the-thirteenth-seam-of-the-core.md),
[ADR-0063](../adr/0063-the-process-declares-its-shutdown-budget-and-the-bot-bounds-the-stop.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §5 (`ST-ASY-01`…`ST-ASY-12`).
_Carried by_: Bot, Dispatcher, Signal, Sync executor, WebSocketTransport, Webhook, Health.

## 8.4 Sync/async duality

The bare name is asynchronous and the `Sync` prefix marks a synchronous Face; exactly two surfaces
have one, `SyncMattermostClient` and `SyncWorkspace`, and no code is generated to produce them.
Every decision — build the request, classify the response, decide the retry, advance the page —
lives in the sans-I/O Exchange and is tested once; a Face only performs I/O, which is why the pair
costs a few dozen lines rather than a mirrored module. A callable the framework calls is a coroutine
function unless it is declared otherwise: a Handler or Provider may be synchronous only by an
explicit `sync_to_thread`, and it then runs in the Sync executor, whose size is checked against the
Dispatch concurrency. Duality is held by mechanism — a typed name-parity test over the two Faces,
and one conformance suite parametrised over both. **Where it stops**: the Event-bound Runtime has no
synchronous face and never will, because its helpers read a channel, a thread root or a
`trigger_id` from an Event; the synchronous Face promises no thread safety and documents one
instance per thread; and free-threaded execution is claimed only where it is tested, which is the
blocking 3.14t job over the Core and the Exchange.

_Decided in_:
[ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md),
[ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md),
[ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md),
[ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §5, §7 (`ST-NAM-01`…`ST-NAM-08`).
_Carried by_: Exchange, Face, Workspace, API client, Sync executor, Testing toolkit.

## 8.5 Dependency injection

A dependency is keyed by type plus an optional `Qualifier`, produced by a Provider in one of two
Scopes — `App` for the life of the Bot, `Event` for one dispatched Event — and reaches a Handler
through its annotation. The whole graph is validated in the check phase and each Handler's
parameters are compiled into a frozen Resolution plan there, so dispatch performs no introspection.
Where a parameter could come from either side, an Extractor wins over a Provider. An external
container serves through the same `DependencyProvider` Protocol as a bridge Plugin, so nothing in
the Core knows which container an application uses. **Where it stops**: the Core injects a
deliberately small built-in set and never the Bot itself, and overriding a dependency is possible
only through the testing toolkit's `TestBot`.

_Decided in_: [ADR-0018](../adr/0018-core-owned-type-keyed-dependency-injection.md),
[ADR-0019](../adr/0019-handler-parameter-resolution-rules.md),
[ADR-0046](../adr/0046-testbot-wraps-the-composed-bot.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §2 (`ST-SOL-01`…`ST-SOL-05`).
_Carried by_: DependencyProvider, Bot, Dispatcher, Router, Runtime.

## 8.6 Extension points and isolation

A capability is enabled by being listed in the composition, never by being installed or imported. A
Plugin carries a frozen `PluginSpec` and implements only the contribution Protocols it needs;
`requires` and `after` order the list topologically, and start-up runs compose → check → start with
stop in reverse. The layers are four import ranks all pointing at the Core, and they are enforced
rather than agreed: `layers`, `independence`, `protected` and `forbidden` contracts of import-linter
are what stop a generic Plugin importing the Adapter and what keeps the two Transports apart.
Substitution happens at the Core's thirteen seam rows and nowhere else; a Plugin that needs a
platform fact receives it through a seam or a typed setting rather than by importing the layer that
holds it. **Where it stops**: there is no entry-point discovery, no import-time side effect and no
plugin-contributed command; a Plugin whose contract version does not match is a check error.

_Decided in_: [ADR-0002](../adr/0002-core-scope-two-condition-test.md),
[ADR-0015](../adr/0015-plugin-contract-and-composition.md),
[ADR-0016](../adr/0016-three-phase-start-with-checks.md),
[ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md),
[ADR-0038](../adr/0038-seam-inventory-records-the-direction-of-the-call.md),
[ADR-0040](../adr/0040-one-package-directory-per-import-rank.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §8 (`ST-MOD-01`…`ST-MOD-11`).
_Carried by_: Bot, Signal, EventRegistry, every Plugin. Structure:
[§5.3](05-building-block-view.md), [§5.4](05-building-block-view.md).

## 8.7 Configuration and settings

Every setting is a frozen typed object the application constructs and hands to the thing it
configures: a Plugin declares its settings type in its `PluginSpec` and receives an instance, and
the Bot takes its own. Nothing is configured by a string, a dictionary or a dotted path, and the
check phase is where a wrong combination is reported — as the full list of failures, not the first.
Loading — from a file, an environment variable, a secret manager — is the application's, so the
framework reads no environment variable for configuration and no configuration file of any kind.
**Where it stops**: two documented exceptions exist and both are opt-in by the operator, the
`--log-config` file the shipped command applies on request and the environment variable that
silences the implicit-colour warning for a project.

_Decided in_: [ADR-0015](../adr/0015-plugin-contract-and-composition.md),
[ADR-0016](../adr/0016-three-phase-start-with-checks.md),
[ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md),
[ADR-0053](../adr/0053-log-records-are-a-documented-contract.md),
[ADR-0058](../adr/0058-the-command-is-a-console-script-behind-the-click-extra.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §8.
_Carried by_: Bot, every Plugin; overridden in a test only through `TestBot`.

## 8.8 Backpressure and flow control

Backpressure is bounded queues with a declared policy, never a stalled reader: the
WebSocketTransport drains the socket into a bounded queue served by the Dispatch concurrency,
because a full server send queue costs the connection and the resume window with it. Overflow is a
typed `OverflowPolicy` per event kind — low-value kinds drop the oldest with a Signal, posts and
callbacks grow to a hard ceiling first — and a drop is always a Signal, never silence. The Sync
executor is the second bounded resource, sized against the Dispatch concurrency and checked at start
so that synchronous Handlers cannot starve dispatch. Depth is read, not pushed: both contribute to
the frozen `bot.stats()` snapshot. **Where it stops**: FloodControl declines an Event before the
Router walk for a chat identity, which is a different question from the queue and is 8.9.

_Decided in_: [ADR-0023](../adr/0023-websocket-gateway-resilience.md),
[ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md),
[ADR-0050](../adr/0050-bounded-resource-state-is-read-not-pushed.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §5.
_Carried by_: WebSocketTransport, Dispatcher, Sync executor.

## 8.9 Idempotency and stale actions

Duplicate work is refused at four distinct grains, because four different things can repeat. Inside
one connection, a replayed frame is deduplicated by `(connection_id, seq)` in memory. Across
connections and replicas, FloodControl's delivery dedup declines an Event whose platform delivery id
has been seen, over a `KeyValueStore` and failing open when the store is unreachable. A conversation
write is compare-and-set, so two events racing on one `StateKey` produce a typed `Conflict` rather
than a lost update, and per-key isolation over a `LockProvider` keeps them from racing at all. An
interactive callback carries a self-issued Callback token whose optional TTL and opt-in `NonceStore`
turn a replayed button into a routable `StaleAction` Event instead of a second action. **Where it
stops**: a synchronous Handler may be abandoned at the Drain and must therefore be idempotent by its
author's hand — the framework cannot stop a thread.

_Decided in_: [ADR-0022](../adr/0022-state-plugin-model.md),
[ADR-0023](../adr/0023-websocket-gateway-resilience.md),
[ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md),
[ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md),
[ADR-0060](../adr/0060-flood-control-and-delivery-dedup-are-one-generic-plugin.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §6.
_Carried by_: WebSocketTransport, FloodControl, State, Callback token, Webhook. Which processes must
share one store for each grain: [§7](07-deployment-view.md).

## 8.10 Graceful shutdown and the Drain

Stopping is one bounded phase with a fixed order. `run()` catches the stop signal and enters it; the
WebSocketTransport closes its socket first, so the server stops queueing for a consumer that is
leaving, then drains its queue and in-flight handlers within its grace period and cancels the rest
with `DrainTimedOut(count)`. Plugins stop in reverse topological order inside the Bot's
`stop_timeout`, which is itself inside the `shutdown_budget` the process declares — an arithmetic a
start-up Check enforces rather than a document. Readiness turns false the moment the Drain begins;
liveness does not move. A second stop signal collapses the timeout to zero. **Where it stops**: a
synchronous Handler in the Sync executor cannot be cancelled by anyone, so the Drain drops the wait
on its deadline and reports the abandoned thread with `HandlerAbandoned`; and nothing survives the
host's kill, which is why the budget is a requirement on the host and not a setting of ours.

_Decided in_: [ADR-0023](../adr/0023-websocket-gateway-resilience.md),
[ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md),
[ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md),
[ADR-0061](../adr/0061-health-is-a-generic-plugin-over-application-supplied-checks.md),
[ADR-0063](../adr/0063-the-process-declares-its-shutdown-budget-and-the-bot-bounds-the-stop.md),
[ADR-0064](../adr/0064-run-owns-the-stop-signals-and-serve-owns-none.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §5.
_Carried by_: Bot, WebSocketTransport, Webhook, Sync executor, Health. Numbers and the host's part:
[§7](07-deployment-view.md).

## 8.11 Runtime probes

A probe is answered by a status code over a bare ASGI callable the application hosts, and the body
is always empty. Liveness runs no check and reads no dependency: it answers 204 for as long as the
process can still make progress, through the whole Drain, and 503 only once the Bot has stopped on a
`FatalError` while the process is still up. Readiness is a conjunction the framework can already
evaluate — the Bot is started, it is not draining, every Transport is connected or `Standby`, and
every `ReadinessCheck` the application supplied passes — run concurrently under per-check timeouts
and cached for a short TTL, because a probe arrives per replica per probe kind and re-running a
dependency check on each is how an endpoint becomes load. A check that throws is one failed check
and one WARNING record. **Where it stops**: the name of a failing check goes to the log and never to
the response, the endpoint is unauthenticated, and nothing in the framework starts the server that
hosts it — a process with no Health Plugin in its composition answers 404, and that is a composition
error the deployment view names.

_Decided in_:
[ADR-0061](../adr/0061-health-is-a-generic-plugin-over-application-supplied-checks.md),
[ADR-0065](../adr/0065-a-transport-waiting-on-the-consumer-lease-is-standby-and-counts-as-ready.md),
[ADR-0002](../adr/0002-core-scope-two-condition-test.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §9.
_Carried by_: Health, Bot, Signal, WebSocketTransport. Hosting and probe fields:
[§7](07-deployment-view.md).

## 8.12 Logging and redaction

The framework writes records and configures nothing: no handler beyond `NullHandler`, no level, no
format, no helper — the application owns its logging, so a library cannot take that decision away. A
record's level follows how often the fact happens and who needs it, so nothing per delivery rises
above DEBUG, INFO marks lifecycle transitions only, and the single ERROR the framework writes is the
ErrorBoundary's one traceback per escaped exception. Correlation reaches a record in three layers —
the call's own `extra`, the name of the asyncio task the delivery runs in, and a Core `ContextVar`
with a filter the application attaches to its own handler — and never through the process-global
record factory, which has one owner and it is not us. The set of records is a documented catalogue
checked against the code in both directions. **Where it stops**: `REDACTED_FIELDS` is forty field
names that may never appear in a log record or a Request record, matched on the normalised name, and
a safe fact whose name collides is recorded under another key; no switch anywhere adds a body, a
header, a query string, a URL or a token.

_Decided in_: [ADR-0021](../adr/0021-core-error-boundary.md),
[ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md),
[ADR-0052](../adr/0052-log-levels-by-frequency-and-audience.md),
[ADR-0053](../adr/0053-log-records-are-a-documented-contract.md),
[ADR-0054](../adr/0054-correlation-reaches-a-log-record-in-three-layers.md),
[ADR-0055](../adr/0055-one-redaction-list-over-two-sinks.md),
[ADR-0058](../adr/0058-the-command-is-a-console-script-behind-the-click-extra.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §9 (`ST-LOG-01`…`ST-LOG-10`), §10
(`ST-DOC-08`).
_Carried by_: ErrorBoundary, Bot, API client, AuthLossDetector, WebSocketTransport, Webhook,
Callback token.

## 8.13 Observability

The framework emits no metric and no span of its own; it makes facts available on mechanisms that
already exist, and a Plugin turns them into telemetry. A dispatch fact travels no Protocol at all —
it is the typed `Outcome`, observed by a Middleware — so the Core owns exactly one observation seam,
`RequestObserver` with its synchronous twin, over a frozen per-attempt Request record. Bounded
resources are read from `bot.stats()` when asked, never pushed; lifecycle transitions travel as
Signals; storage is observed by decorating its Protocol rather than by a hook inside it. The
first-party Observability plugin lives behind the extras named after `opentelemetry` and
`prometheus`, follows the OpenTelemetry conventions, takes the registry as an argument and touches
no process-global state, and bounds its cardinality with a label allow-list and a start-up Check.
**Where it stops**: an observer never changes the call and its failure is caught, logged and never
reaches the caller; modifying behaviour is done by decorating the `HTTPTransport` or by a
Middleware, which are different things with different names.

_Decided in_: [ADR-0048](../adr/0048-observability-is-not-a-core-seam.md),
[ADR-0049](../adr/0049-what-the-framework-makes-observable.md),
[ADR-0050](../adr/0050-bounded-resource-state-is-read-not-pushed.md),
[ADR-0051](../adr/0051-first-party-observability-plugin.md),
[ADR-0061](../adr/0061-health-is-a-generic-plugin-over-application-supplied-checks.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §9.
_Carried by_: Middleware, API client, Bot, Observability plugin, KeyValueStore and LockProvider
backends. Facts:
[`docs/research/17`](../research/17-http-client-observability.md),
[`docs/research/23`](../research/23-dispatch-observability-in-async-frameworks.md).

## 8.14 Security

Mattermost signs no callback and gives an external bot no authenticity primitive, so the bot issues
its own: a versioned, `kid`-keyed HMAC-SHA256 Callback token placed in a button `context` or a
dialog `state` and verified before an Event exists, on by default and turned off only by an explicit
word. Verification answers a typed union rather than a boolean, so an expired or replayed token
becomes a routable `StaleAction` instead of a silent failure. A credential is never held by the
framework: the bot's token arrives from the `TokenProvider` seam on every connection and every
request, so rotation is the application's business, and the token is never logged, never placed in a
URL and never carried by an exception — an authentication failure reports ids and a digest. **Where
it stops**: authorising *who* may press a button is not decided yet, and it is on the map's frontier
rather than here; transport security is the host's; and the framework names no secret manager,
because the only thing it needs is an object that answers with a token.

_Decided in_: [ADR-0023](../adr/0023-websocket-gateway-resilience.md),
[ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md),
[ADR-0027](../adr/0027-api-error-taxonomy.md),
[ADR-0055](../adr/0055-one-redaction-list-over-two-sinks.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §9.
_Carried by_: Callback token, Webhook, Face, API client, AuthLossDetector. Facts:
[`docs/research/16`](../research/16-webhook-callback-standards.md). Which credentials each process
shape needs: [§7](07-deployment-view.md).

## 8.15 Testing strategy

Tests are written against contracts, not against implementations. A Protocol's contract is
executable as a Conformance suite — one per Core seam plus the plugin lifecycle — delivered as a
factory over the implementer's factory, so tightening a suite is a change to the Protocol itself and
an external backend proves what it is by running ours. A bot is tested by wrapping the composed Bot
in `TestBot`, which is the only override API and the only path: the toolkit composes no Bot of its
own. There is one double of the platform, the stateful `FakeMattermost`, and a test reaches every
seam it implements through that object's ports, prepares it by seeding and asserts on it by record,
with typed fault injection instead of a scripted transport. Time is `FakeClock`, so a timeout, a TTL
and a backoff are advanced rather than waited for. **Where it stops**: `aiommbot.testing` imports
pytest through the extra of that name and its plugin is activated by one explicit line in the root
`conftest.py`, never by an entry point; and it may import every layer while no layer may import it,
which is what keeps doubles out of the shipped runtime.

_Decided in_:
[ADR-0044](../adr/0044-the-testing-toolkit-requires-pytest-and-is-activated-explicitly.md),
[ADR-0045](../adr/0045-one-stateful-fake-mattermost-is-the-only-platform-double.md),
[ADR-0046](../adr/0046-testbot-wraps-the-composed-bot.md),
[ADR-0047](../adr/0047-a-conformance-suite-per-core-seam.md),
[ADR-0059](../adr/0059-clock-is-the-thirteenth-seam-of-the-core.md).
_Ruled by_: [`engineering-style.md`](engineering-style.md) §11 (`ST-TST-01`…`ST-TST-09`).
_Carried by_: Testing toolkit, FakeMattermost, and every component through its suite
([§5.9](05-building-block-view.md)).
