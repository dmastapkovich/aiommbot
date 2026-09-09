# Reference sources

The design cites primary sources — peer framework code, protocol specs, language documentation.
Reading them over the network costs a session time and tokens, and the same files are fetched again
every session. This file is the curated list of those sources; `scripts/sync-refs.sh` clones each
one into `.refs/` at the repository root, which git ignores.

## How an agent uses it

- A source URL maps to a local path mechanically: `github.com/<org>/<repo>/blob/<ref>/<path>` and
  `raw.githubusercontent.com/<org>/<repo>/<ref>/<path>` both live at `.refs/<org>/<repo>/<path>`.
- **Read `.refs/` first.** Go to the network only for a source that is not in the list, or when a
  claim depends on a change newer than the clone.
- Clones are shallow (`--depth=1`, single branch, blobless): the working tree of the default branch
  is there, the history is not. `git log`, `git blame` and pull-request discussions still need the
  network.
- A note or ADR cites the canonical URL, never a `.refs/` path — the cache is local scaffolding, not
  a source (`docs/documentation-style.md` §9).

## Syncing

```sh
.agents/scripts/sync-refs.sh            # clone what is missing, skip what is there
.agents/scripts/sync-refs.sh --update   # also fetch the default branch of every existing clone
.agents/scripts/sync-refs.sh aiogram    # only entries whose slug matches the argument
.agents/scripts/sync-refs.sh --purge    # delete .refs/ entirely
```

Cloning is one-off by design: an existing clone is left untouched unless `--update` is passed.

## Lifetime

The cache serves the design and implementation phases, where sessions read peer code constantly. It
is scaffolding, not part of the package: `--purge` removes it, and this file together with the
script goes with it once the work no longer needs peer sources at hand.

## Adding a source

Add a row to the table below, keep the sections ordered by what the source answers, then run the
script. A row earns its place by being read across sessions — a URL cited once belongs in the
research note, not here.

## Mattermost — the platform being wrapped

| Source | What it answers |
|---|---|
| [mattermost/mattermost](https://github.com/mattermost/mattermost) | WebSocket protocol, session handling, REST handlers, interactive actions, `model` types — the server itself and its web client |
| [mattermost/mattermost-api-reference](https://github.com/mattermost/mattermost-api-reference) | The OpenAPI v4 specification behind the typed REST layer |
| [mattermost/docs](https://github.com/mattermost/docs) | Administrator and developer documentation, including integration and webhook behaviour |
| [mattermost/mattermost-plugin-apps](https://github.com/mattermost/mattermost-plugin-apps) | How Mattermost itself frames an HTTP upstream and its callback contract |
| [attzonko/mmpy_bot](https://github.com/attzonko/mmpy_bot) | The existing Python Mattermost bot framework: what it covers and where it stops |
| [Vaelor/python-mattermost-driver](https://github.com/Vaelor/python-mattermost-driver) | The long-standing Python client for the same REST and WebSocket surface |

## Bot frameworks — the peers

| Source | What it answers |
|---|---|
| [aiogram/aiogram](https://github.com/aiogram/aiogram) | Router tree, filters, middleware layers, FSM storage, DI through handler parameters, testing surface |
| [Rapptz/discord.py](https://github.com/Rapptz/discord.py) | Gateway client, reconnect and heartbeat, event dispatch, error boundary defaults |
| [hikari-py/hikari](https://github.com/hikari-py/hikari) | A strictly typed, component-separated alternative to discord.py |
| [slackapi/bolt-python](https://github.com/slackapi/bolt-python) | Socket Mode and HTTP ingress in one framework, listener middleware, acknowledgement timing |
| [slackapi/python-slack-sdk](https://github.com/slackapi/python-slack-sdk) | The transport layer under Bolt: Socket Mode client, retry handlers, dual sync/async clients |
| [python-telegram-bot/python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | Persistence interfaces, conversation state lifetime, application lifecycle |
| [Tishka17/aiogram_dialog](https://github.com/Tishka17/aiogram_dialog) | Multi-step dialogs built on top of a router framework, and the state they need |
| [RasaHQ/rasa](https://github.com/RasaHQ/rasa) | Tracker stores as a durable conversation-state contract |
| [microsoft/botbuilder-python](https://github.com/microsoft/botbuilder-python) | Storage abstraction and turn state in a vendor bot SDK |

## Async frameworks and plugin models

| Source | What it answers |
|---|---|
| [litestar-org/litestar](https://github.com/litestar-org/litestar) | Plugin protocols, DI, layered configuration, application lifecycle hooks |
| [ag2ai/faststream](https://github.com/ag2ai/faststream) | Broker-agnostic dispatch, middleware, testing doubles, a framework that renamed its org |
| [fastapi/fastapi](https://github.com/fastapi/fastapi) | Dependency injection from handler signatures, routers, and the cost of that design |
| [encode/starlette](https://github.com/encode/starlette) | Minimal ASGI core, lifespan, middleware stack, `TestClient` |
| [encode/django-rest-framework](https://github.com/encode/django-rest-framework) | Settings objects and extension points in a framework built to be subclassed |
| [pytest-dev/pluggy](https://github.com/pytest-dev/pluggy) | Hook specifications and implementations — the canonical Python plugin system |
| [encode/uvicorn](https://github.com/encode/uvicorn) | Server lifecycle, signal handling, graceful shutdown |
| [sanic-org/sanic](https://github.com/sanic-org/sanic) | Background task management and exception handling in a long-running server |
| [django/django](https://github.com/django/django) | The app registry, signals and settings as the oldest plugin model in Python |
| [pydantic/pydantic](https://github.com/pydantic/pydantic) | Plugin loading through entry points, and a strictly typed public surface |
| [wemake-services/django-modern-rest](https://github.com/wemake-services/django-modern-rest) | The strictness benchmark: import-linter contracts, four type checkers, zero suppressions |

## Dependency injection

| Source | What it answers |
|---|---|
| [reagento/dishka](https://github.com/reagento/dishka) | A container with explicit scopes, and how it stays out of handler signatures |
| [Lancetnik/FastDepends](https://github.com/Lancetnik/FastDepends) | FastAPI-style parameter resolution extracted from the web framework |

## Task execution and scheduling

| Source | What it answers |
|---|---|
| [taskiq-python/taskiq](https://github.com/taskiq-python/taskiq) | Receiver loop, middleware, result backends in an async task system |
| [celery/celery](https://github.com/celery/celery) | Task tracing, error handling and retry semantics of the reference implementation |
| [Bogdanp/dramatiq](https://github.com/Bogdanp/dramatiq) | A smaller broker-based worker with an explicit middleware contract |
| [python-arq/arq](https://github.com/python-arq/arq) | An asyncio-native worker loop, job lifecycle and cancellation |

## HTTP and WebSocket transports

| Source | What it answers |
|---|---|
| [encode/httpx](https://github.com/encode/httpx) | Transport protocol, event hooks, dual sync/async client from one implementation |
| [pydantic/httpx2](https://github.com/pydantic/httpx2) | The successor line: what changed, and what the changelog says about it |
| [encode/httpcore](https://github.com/encode/httpcore) | Connection pooling and the extensions mechanism under httpx |
| [aio-libs/aiohttp](https://github.com/aio-libs/aiohttp) | Client tracing, logging policy and a WebSocket client in one library |
| [urllib3/urllib3](https://github.com/urllib3/urllib3) | Retry and pool semantics, and the instrumentation seams other libraries hook |
| [python-websockets/websockets](https://github.com/python-websockets/websockets) | The asyncio WebSocket client contract, keepalive and close handling |
| [tarasko/picows](https://github.com/tarasko/picows) | The fast alternative WebSocket client and its benchmark claims |
| [openai/openai-python](https://github.com/openai/openai-python) | A generated, strictly typed API client with a logging convention |
| [python-hyper/wsproto](https://github.com/python-hyper/wsproto) | The WebSocket protocol as a sans-io state machine |
| [python-hyper/h11](https://github.com/python-hyper/h11) | The same discipline for HTTP/1.1, and the argument for it |
| [frankie567/httpx-ws](https://github.com/frankie567/httpx-ws) | A WebSocket client built on the same transport as the REST client |

## Resilience

| Source | What it answers |
|---|---|
| [jd/tenacity](https://github.com/jd/tenacity) | Retry policies as composable objects |
| [hynek/stamina](https://github.com/hynek/stamina) | Retries with typed, opinionated defaults and testability |
| [danielfm/pybreaker](https://github.com/danielfm/pybreaker) | The circuit-breaker state machine and its listeners |

## Code generation and serialisation

| Source | What it answers |
|---|---|
| [koxudaxi/datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) | Generating dataclasses and models from an OpenAPI schema |
| [openapi-generators/openapi-python-client](https://github.com/openapi-generators/openapi-python-client) | The alternative: a generated client, not just models |
| [aiogram/tg-codegen](https://github.com/aiogram/tg-codegen) | How a bot framework keeps generated models in step with a moving platform |
| [jcrist/msgspec](https://github.com/jcrist/msgspec) | Fast typed decoding without a validation framework |
| [python-attrs/attrs](https://github.com/python-attrs/attrs) | Class construction, slots and converters under the dataclass alternative |

## Observability

| Source | What it answers |
|---|---|
| [open-telemetry/opentelemetry-python](https://github.com/open-telemetry/opentelemetry-python) | The API/SDK split, and the logging bridge implementation |
| [open-telemetry/opentelemetry-python-contrib](https://github.com/open-telemetry/opentelemetry-python-contrib) | How instrumentation attaches to httpx, urllib3 and friends from the outside |
| [open-telemetry/semantic-conventions](https://github.com/open-telemetry/semantic-conventions) | Attribute names for HTTP spans, HTTP metrics and messaging |
| [prometheus/client_python](https://github.com/prometheus/client_python) | Metric types, registries and label handling |
| [prometheus/docs](https://github.com/prometheus/docs) | Naming and instrumentation practice, and cardinality guidance |
| [trallnag/prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator) | A worked example of framework instrumentation shipped outside the framework |
| [hynek/structlog](https://github.com/hynek/structlog) | Structured logging that cooperates with the standard library |
| [getsentry/sentry-python](https://github.com/getsentry/sentry-python) | Integration discovery and how an SDK attaches to frameworks it does not own |

## Concurrency and the language

| Source | What it answers |
|---|---|
| [python/cpython](https://github.com/python/cpython) | `asyncio`, `logging`, `contextvars` — the standard library and its documentation under `Doc/` |
| [python/peps](https://github.com/python/peps) | Every PEP the design cites, in source form |
| [python/typing](https://github.com/python/typing) | The typing specification and its conformance suite |
| [agronholm/anyio](https://github.com/agronholm/anyio) | Structured concurrency and task groups over asyncio |
| [python-trio/trio](https://github.com/python-trio/trio) | Nurseries, cancellation scopes and the sans-io argument |
| [sqlalchemy/sqlalchemy](https://github.com/sqlalchemy/sqlalchemy) | A sync core with a generated async face — the largest dual-face precedent |
| [mongodb/motor](https://github.com/mongodb/motor) | The async wrapper pattern over a sync driver, and its deprecation |
| [mongodb/mongo-python-driver](https://github.com/mongodb/mongo-python-driver) | The driver that absorbed motor, and the async API a state backend would use |
| [redis/redis-py](https://github.com/redis/redis-py) | The other state backend, and how it exposes sync and async from one package |
| [python-trio/unasync](https://github.com/python-trio/unasync) | Generating the sync face from async sources at build time |
| [django/asgiref](https://github.com/django/asgiref) | `sync_to_async` and `async_to_sync`, and what each costs |

## Toolchain

| Source | What it answers |
|---|---|
| [astral-sh/ruff](https://github.com/astral-sh/ruff) | Rule semantics and configuration for lint and format |
| [astral-sh/ty](https://github.com/astral-sh/ty) | The behaviour and limits of the newest type checker |
| [microsoft/pyright](https://github.com/microsoft/pyright) | Strict-mode rules and the configuration reference |
| [python/mypy](https://github.com/python/mypy) | The oldest checker of the four, its strict flags and its error codes |
| [facebook/pyrefly](https://github.com/facebook/pyrefly) | The fourth checker, and where it disagrees with the other three |
| [seddonym/import-linter](https://github.com/seddonym/import-linter) | Layer and independence contracts that keep the import ranks enforceable |
| [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | Plugin API, fixtures and the shape of a distributed testing toolkit |
| [HypothesisWorks/hypothesis](https://github.com/HypothesisWorks/hypothesis) | Property-based testing — the shape a conformance suite can take |

## Protocols and security specifications

| Source | What it answers |
|---|---|
| [standard-webhooks/standard-webhooks](https://github.com/standard-webhooks/standard-webhooks) | Signature, timestamp and replay rules for webhook callbacks, with a reference implementation |
| [paseto-standard/paseto-spec](https://github.com/paseto-standard/paseto-spec) | The rationale for tokens without algorithm negotiation |
| [OWASP/ASVS](https://github.com/OWASP/ASVS) | Verification requirements for self-contained tokens and API surfaces |
| [discord/discord-api-docs](https://github.com/discord/discord-api-docs) | Gateway opcodes, close codes and interaction response timing |
