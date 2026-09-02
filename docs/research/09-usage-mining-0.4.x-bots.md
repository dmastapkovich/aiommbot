# Research: how the eleven 0.4.x bots actually use aiommbot

Resolves GitHub issue #11. Local code mining across
`backoffice-portal/mattermost-bots` — 11 bots (`backoffice-bot`, `crq-bot`,
`duty-bot`, `expenses-bot`, `incident-bot`, `mm-overtime-bot`, `office-bot`,
`postmortem-bot`, `santa-bot`, `support-bot`, `tour-bot`) all pinned to
`aiommbot>=0.4.5`–`0.4.7`, against the framework at `aiommbot/aiommbot/`.
Counts are `grep -rc` line-hits under each bot's `src/` (tests counted
separately; `.venv`/`__pycache__` sit outside `src/` in this layout, so no
exclusion was needed). A hit is a *line containing the pattern*, not a
unique call site — treat counts as relative-usage signal. Every "zero usage"
claim below was cross-checked against the framework source to rule out a
wrong class/method name before being called a gap.

**`AIOMMBOT_DECLARATIVE_STANDARD.md`** (monorepo root) already codifies an
anti-crutch table from prior cross-bot review; its "Current fleet reality"
and "Upstream aiommbot opportunities" sections are cited where they overlap
with what grep found independently.

## 1. Router decorators & request types

| Decorator | bo | crq | duty | exp | inc | mmo | off | pm | santa | sup | tour | bots>0 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `@router.message` | 2 | 1 | 0 | 16 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 10/11 |
| `@router.action` | 8 | 12 | 2 | 37 | 9 | 6 | 10 | 9 | 30 | 9 | 10 | **11/11** |
| `@router.dialog` | 3 | 4 | 1 | 9 | 3 | 4 | 4 | 3 | 9 | 3 | 2 | **11/11** |
| `@router.schedule` | 3 | 8 | 0 | 0 | 5 | 3 | 0 | 7 | 0 | 0 | 5 | 6/11 |
| `@router.direct_added` | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 6/11 |
| `@router.external` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1/11 |
| `@router.group_added` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/11** |
| `@router.reaction` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/11** |
| `@router.post_lifecycle` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/11** |
| `@router.channel_event` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/11** |
| `@router.user_event` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/11** |
| `@router.thread_event` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/11** |
| `@router.websocket_event` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/11** |

Request-type imports track the decorators 1:1 (`ActionRequest`/`DialogRequest`
in all 11; `ScheduleRequest`/`DirectAddedRequest`/`PostRequest` in the same
6/6/10 bots as their decorators; the remaining seven request types at 0
imports fleet-wide). `expenses-bot` leads message-handler volume (16 hits —
the one bot with a genuinely message-driven conversational flow rather than
action/dialog-only); `backoffice-bot` is the sole `@router.external` user.

Of 13 declared event types, **7 have zero fleet usage**: group-added,
reaction, post-lifecycle, channel-event, user-event, thread-event, and the
generic websocket-event decorator. `@router.external` is used by exactly one
bot. That's 8/13 request kinds effectively cold.

## 2. Filters

| Pattern | bo | crq | duty | exp | inc | mmo | off | pm | santa | sup | tour |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `DIRECT_CHAT_TYPE_FILTER` | 2 | 2 | 3 | 5 | 2 | 2 | 3 | 2 | 4 | 2 | 2 |
| `NOT_BOT_FILTER` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `VERIFIED_ACTOR_FILTER` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `WhitelistFilter`/`BlacklistFilter` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `StateFilter` (custom subclass) | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| `states=` (list form) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| ` state=` (singular kwarg) | 1 | 3 | 4 | 31 | 6 | 3 | 12 | 2 | 22 | 1 | 2 |
| `matched_params` | 0 | 3 | 0 | 2 | 0 | 3 | 0 | 0 | 0 | 4 | 0 |
| `submission[...]` (manual dialog parsing) | 4 | 4 | 0 | 4 | 4 | 4 | 7 | 4 | 4 | 6 | 4 |

`DIRECT_CHAT_TYPE_FILTER` is universal (root-router gate, exactly the golden
pattern). `NOT_BOT_FILTER` is used by exactly one bot (backoffice-bot);
`VERIFIED_ACTOR_FILTER` and `WhitelistFilter`/`BlacklistFilter` are declared in
`aiommbot/filters/` but have **zero** callers anywhere in the fleet — the actor
verification story is not exercised through the filter API at all (confirmed
`actor_policy` — the alternate, non-filter path via `WebhookConfig` — is also
0/11). The declarative `matched_params` (named regex groups) is used by only
4/11 bots; the other 7 parse `event.submission[...]` manually in every dialog
handler — a crutch the standard explicitly calls out
(`request.event.context.get("x")` / `submission["x"]` row). `states=` (list)
is essentially tour-bot only; most bots use the singular `state=` kwarg
instead, which is fine per the framework but means the plural form barely
exists as evidence of multi-state gating.

## 3. DI / handler params

| Pattern | bo | crq | duty | exp | inc | mmo | off | pm | santa | sup | tour |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `api_manager: ApiManager` | 13 | 18 | 4 | 84 | 13 | 15 | 19 | 22 | 42 | 17 | 25 |
| `context: Context` | 7 | 9 | 4 | 79 | 15 | 13 | 18 | 5 | 35 | 18 | 13 |
| `request: ActionRequest` | 9 | 13 | 3 | 38 | 9 | 7 | 10 | 19 | 30 | 9 | 14 |
| `bot: Bot` (param) | 2 | 2 | 5 | 4 | 4 | 3 | 1 | 21 | 7 | 1 | 6 |
| `**kwargs: Any` | 11 | 24 | 0 | 65 | 13 | 12 | 17 | 14 | 45 | 19 | 8 |
| `request.bot.state.<svc>` | 7 | 10 | 0 | 22 | 11 | 6 | 13 | 24 | 27 | 5 | 11 |

All bots follow the framework-injected triple (`request`, `api_manager`,
`context`) for action/dialog handlers; **duty-bot is the only bot with zero
`**kwargs: Any`** boilerplate lines — likely a size/age artifact (newest,
smallest bot) rather than a deliberate framework-usage choice. Services are
fetched exclusively via typed `_deps.py` helpers wrapping
`request.bot.state.<attr>` (e.g. `tour-bot/src/routers/_deps.py:16`,
`postmortem-bot/src/routers/scheduled.py:49`) — every bot has at least one
`_deps.py` per router subpackage, i.e. the same 3–5 line
`def get_x_service(request): return request.bot.state.x_service` pattern is
independently written 40+ times fleet-wide. No bot fetches services from
bare module globals — DI wiring is consistent.

## 4. State / storage

| Pattern | bo | crq | duty | exp | inc | mmo | off | pm | santa | sup | tour |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `StatesGroup` | 0 | 0 | 0 | 5 | 2 | 0 | 0 | 0 | 0 | 0 | 2 |
| `get_data`/`update_data` | 4/2 | 5/2 | 1/0 | 21/23 | 7/7 | 6/5 | 8/10 | 3/2 | 24/20 | 9/9 | 3/2 |
| `src.database` (Mongo repos) | 9 | 11 | 8 | 20 | 10 | 8 | 7 | 45 | 38 | 9 | 72 |
| `storage_profile=` (new unified config) | 6 | 0 | 9 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| `def get_mongo_storage()` (bot-local) | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 1 |
| `def get_context_storage()` (bot-local) | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 |
| `def get_in_memory_storage()` (bot-local) | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Every bot has a `src/database` repository layer (durable Mongo state) — fully
adopted. But **`StatesGroup` FSM usage is rare** (3/11: expenses-bot,
incident-bot, tour-bot) — most bots gate on plain string `state=` values or
skip FSM state, relying on Mongo compare-and-set instead. More interesting:
**the framework has two incompatible storage-config styles live at once.**
3 bots (`backoffice-bot`, `duty-bot`, `mm-overtime-bot`) use the newer
unified `storage_profile=` kwarg on `Bot(...)`; the other 8 still use the
older `storage=<instance>` + `taskiq_broker=<instance>` pair, each with its
**own bot-local, independently-written** helper — `get_mongo_storage()`
(`crq-bot`, `incident-bot`, `postmortem-bot`, `santa-bot`, `tour-bot`),
`get_context_storage()` (`office-bot`, `support-bot`), or
`get_in_memory_storage()` (`expenses-bot`). `duty-bot/src/main.py` even
carries an explicit comment that `storage_profile` is mutually exclusive
with the older pair "other bots in this repo use" — the migration is
mid-flight and undocumented as a fleet-wide decision. `RedisStorageProfile`
has **zero** usage anywhere.

## 5. Runtime / API surface

| Method | bo | crq | duty | exp | inc | mmo | off | pm | santa | sup | tour |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `.answer(` | 15 | 34 | 6 | 100 | 11 | 6 | 17 | 22 | 78 | 16 | 4 |
| `.update_post(` | 7 | 7 | 2 | 7 | 12 | 5 | 9 | 9 | 29 | 5 | 5 |
| `send_dialog(` | 2 | 4 | 1 | 16 | 3 | 4 | 5 | 4 | 9 | 3 | 3 |
| `.send_file(` | 0 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| `receive_file(` | 0 | 0 | 0 | 3 | 0 | 0 | 2 | 0 | 0 | 2 | 0 |
| `.reply(` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `.create_reaction(` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `.pin_post(` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `EventPreparer` | 16 | 12 | 0 | 0 | 3 | 3 | 0 | 11 | 6 | 0 | 0 |
| `BotRuntime`/`SyncBotRuntime` | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 5/0 | 0/0 | 0/0 | 5/0 |
| `httpx.AsyncClient`/`aiohttp.ClientSession` (raw) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

`answer`/`update_post`/`send_dialog` are the workhorse trio, used by all 11.
`.reply(`, `.create_reaction(`, `.pin_post(` are declared on `ApiManager` but
have **zero** callers anywhere — no bot replies in-thread, reacts, or pins.
No bot bypasses the framework with a raw `httpx`/`aiohttp` client against
Mattermost. `BotRuntime` (a higher-level scripted-runtime facade) is used by
only 2/11 (`postmortem-bot`, `tour-bot`); `SyncBotRuntime` by none.
`EventPreparer` is used by 6/11 (`backoffice-bot`, `crq-bot`, `incident-bot`,
`mm-overtime-bot`, `postmortem-bot`, `santa-bot`) — the other 5 either don't
need cross-system user resolution or still roll ad-hoc lookups.

## 6. Webhook / interactive elements

| Pattern | bo | crq | duty | exp | inc | mmo | off | pm | santa | sup | tour |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `Attachment(` | 7 | 7 | 3 | 19 | 8 | 7 | 5 | 9 | 43 | 5 | 13 |
| `Button.create(` | 7 | 15 | 2 | 36 | 9 | 7 | 9 | 11 | 32 | 12 | 8 |
| `SelectElement` (dialog field) | 0 | 0 | 0 | 7 | 6 | 0 | 4 | 0 | 0 | 8 | 0 |
| `Dialog.create(`/`Dialog(` | 1 | 3 | 1 | 8 | 3 | 3 | 2 | 2 | 8 | 2 | 1 |
| `WebhookConfig(...)` | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |

All 11 configure `WebhookConfig` once in the composition root and build
`Attachment`/`Button.create(...)`/`Dialog.create(...)` for interactivity —
`Button(...)`/`Select(...)` are never constructed directly; only the
`.create()` factory is exercised (this initially looked like "zero usage"
until cross-checked against `tour-bot/src/assets/welcome/ui_components.py:42`).
`SelectElement` dialog fields are used by 4/11 (expenses, incident, office,
support). Enforcement mode is set in every bot's `dependencies.py`/
`bot_config.py`, but **the settings-field name for it is independently
invented per bot** — seven distinct names across seven bots (e.g.
`MATTERMOST_BACKOFFICE_BOT_WEBHOOK_PAYLOAD_ENFORCEMENT` vs.
`MATTERMOST_CRQ_BOT_WEBHOOK_CALLBACK_PAYLOAD_ENFORCEMENT` vs.
`MATTERMOST_INCIDENT_BOT_WEBHOOK_ENFORCEMENT`, for the same concept) — while
`office-bot`, `santa-bot`, and `tour-bot` skip the settings indirection
entirely and hardcode `WebhookEnforcementMode.strict`/`.STRICT` (note the
case inconsistency between the two hardcoded forms).

## 7. Scheduling & reliability

| Pattern | bo | crq | duty | exp | inc | mmo | off | pm | santa | sup | tour |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `taskiq` (any mention) | 35 | 27 | 36 | 4 | 22 | 27 | 3 | 27 | 3 | 3 | 25 |
| `InMemoryBroker` | 0 | 5 | 0 | 0 | 3 | 2 | 0 | 4 | 0 | 0 | 4 |
| Redis/AMQP taskiq broker | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `aiobreaker` (3rd-party circuit breaker) | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| `aiommbot.middlewares.circuit_breaker` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `config.reliability` / `RetryableError`/`PermanentError`/`AckMessage`/`QueuePolicy`/`worker_concurrency` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The 6 bots with `@router.schedule` all run on `InMemoryBroker` — **no bot
uses a distributed taskiq broker**, so the "in-process cron fires once per
replica" risk applies fleet-wide by construction, not by oversight in one
bot. The framework's structured reliability vocabulary (`exceptions.py`:
`RetryableError`, `PermanentError`, `AckMessage`; `types/config.py`:
`QueuePolicy`, `worker_concurrency`; `types/reliability.py`) has **zero**
callers in any bot. Most strikingly, the framework ships an
`aiommbot.middlewares.circuit_breaker` middleware that no bot registers —
instead, `crq-bot/src/clients/jirasm_adapter_client.py` and
`postmortem-bot/src/dependencies/jira_client.py` each independently vendor
the third-party `aiobreaker` library with **near-identical code**, including
the same non-obvious workaround comment about `aiobreaker`'s
`CircuitBreakerBaseState`/`CircuitBreakerState` narrowing quirk, to guard
their Jira/JiraSM HTTP clients — either the built-in middleware doesn't fit
the "wrap one HTTP client, not a whole handler chain" shape bots need, or
two bots simply didn't know it existed.

## 8. Observability

| Pattern | bo | crq | duty | exp | inc | mmo | off | pm | santa | sup | tour |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `HandlerObserver` (Protocol) | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| `Prometheus*Observer` | 14 | 21 | 11 | 21 | 21 | 21 | 21 | 19 | 21 | 21 | 21 |
| Outbound-HTTP `*Observer` | 6 | 11 | 5 | 14 | 8 | 6 | 6 | 8 | 6 | 6 | 6 |
| `sentry`/`Sentry` (any mention) | 50 | 58 | 50 | 30 | 45 | 47 | 32 | 41 | 33 | 38 | 46 |
| `src/utils/observability` (per-bot toolkit package) | 24 | 38 | 23 | 30 | 25 | 23 | 24 | 40 | 50 | 18 | 37 |
| `TaskiqObserver`/Mongo `*Observer` (direct reference) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

`PrometheusObservability`/`ObservabilityProvider` as literally-named classes
do not exist in the framework — the real pattern is a `*Observer` `Protocol`
+ `Noop*Observer`/`Prometheus*Observer` pair per metric domain, and every bot
has its own `src/utils/observability/` copy of that toolkit (all 11, 18–50
hits each — the single most consistently-copied non-trivial package in the
whole fleet). Sentry integration is universal. `TaskiqObserver` and a
Mongo-domain observer exist in the framework
(`observability/domains/taskiq.py`) but are never referenced by name in any
bot — likely wired transitively through generic middleware rather than
touched directly, so this reads as "indirect," not "unused."

## 9. Lifespan / composition

| Pattern | bo | crq | duty | exp | inc | mmo | off | pm | santa | sup | tour |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `lifespan=` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `combine_lifespans` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `add_middleware(` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| `add_outer_middleware(` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `def main()` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `aiommbot run` CLI entrypoint | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 (doc mention) | 0 | 0 | 0 |

Every bot has exactly one `@asynccontextmanager lifespan(bot)` and a custom
`def main()` — **none use the `aiommbot run` CLI entrypoint** as their
startup path (the one hit is a docstring mention in postmortem-bot, not real
usage). `combine_lifespans` has zero callers — unsurprising since every bot
wires exactly one lifespan already; this looks like a feature built ahead of
a need that hasn't materialized. Most bots pass a static `middlewares=[...]`
list into `Bot(...)` rather than calling `.add_middleware()`; only
`duty-bot`/`tour-bot` call it once each, and `add_outer_middleware` (meant
for the one legitimate custom middleware, `SafeErrorNotificationMiddleware`)
is never called anywhere — bots order it via `list(reversed(middlewares))`
in the static list instead, per `backoffice-bot/src/dependencies.py:get_middlewares`.

Per the standard's own audit (reproduced here by searching for
`safe_error_notification.py`): only **3/11** bots (`backoffice-bot`,
`duty-bot`, `tour-bot`) override the built-in `SafeErrorNotificationMiddleware`
with a redacting subclass; the other 8 register the framework default
directly, which logs the full `request.event.model_dump()` (message text /
dialog submission / PII) and swallows the exception before Sentry/metrics
ever see it.

## 10. Testing

| Pattern (in `tests/`) | bo | crq | duty | exp | inc | mmo | off | pm | santa | sup | tour |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `aiommbot.testing` (any import) | 3 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `TestClient` (framework) | 20 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| `build_*_event` builders | 4 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `RecordingApiFactory` | 1 | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `AsyncMock` (ad-hoc mocking) | 245 | 966 | 15 | 647 | 126 | 326 | 84 | 987 | 303 | 308 | 266 |
| `mongomock`/`mongomock-motor` | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 14 | 0 | 21 |
| Test files (`test_*.py`) | 25 | 332 | 25 | 386 | 21 | 29 | 131 | 29 | 57 | 102 | 53 |

This is the sharpest gap in the whole survey: **only 2/11 bots
(`backoffice-bot`, `duty-bot`) use `aiommbot.testing` at all**, and only
`backoffice-bot` has an in-repo precedent doing real router-dispatch testing
with it (`backoffice-bot/tests/utils/test_notification_router.py`, cited by
the standard itself). The other 9 — including large, mature ones like
`crq-bot` (332 test files) and `postmortem-bot` (987 `AsyncMock` hits) — test
handlers entirely through hand-rolled `AsyncMock`/`MagicMock` fakes instead
of `TestClient` + event builders + `RecordingApiFactory`. `mongomock-motor`
is used by only 3/11 for repository tests; the rest presumably mock the
Mongo layer at the repository-method boundary instead of exercising real
query semantics.

## 11. Recurring workarounds and crutches

The standard's own anti-crutch table (derived from `tour-bot`,
`postmortem-bot`, `mm-overtime-bot`) lists 14 handler-level crutches it
standardizes around; independent grepping confirms most are still live in at
least some bots, and adds a few the standard doesn't cover:

1. **Per-bot duplicated `get_*_storage()` helpers** — 5 near-identical
   `get_mongo_storage()` defs, 2 `get_context_storage()`, 1
   `get_in_memory_storage()`, plus an unmigrated parallel `storage_profile=`
   path in 3 bots (§4) — the clearest "framework config surface changed,
   consumers didn't converge" signal.
2. **Vendored `aiobreaker` circuit breaker**, copy-pasted verbatim (workaround
   comment included) into `crq-bot` and `postmortem-bot` instead of the
   framework's own `circuit_breaker` middleware (§7).
3. **7 independently-named settings fields** for `WebhookConfig(enforcement=
   ...)`, plus 3 bots hardcoding the enum with inconsistent case (§6).
4. **Manual `event.submission[...]` parsing** in 7/11 bots instead of typed
   parse-helpers or named regex groups (`matched_params` used by only 4/11) —
   exactly the standard's flagged row on manual state slicing.
5. **`src/utils/observability/` fully duplicated per bot** (11 independent
   copies of the same collectors/`*Observer`/middleware package) — not wrong
   per the "copy-paste package" model, but the largest duplicated block in
   the fleet and a natural candidate for an installable sub-package.
6. **`SafeErrorNotificationMiddleware` unwrapped in 8/11 bots** — logs full
   event payloads (PII/message text) and swallows exceptions; the standard
   names this a known, unresolved, per-bot gap.
7. **9/11 bots skip `aiommbot.testing` entirely**, reimplementing
   handler-dispatch tests with `AsyncMock`/`MagicMock` despite the framework
   harness being feature-complete and documented as preferred.
8. **`**kwargs: Any` boilerplate required on almost every handler** (10/11,
   hundreds of hits) — the standard marks it "REQUIRED catch-all for
   middleware injection," so handlers can't declare a closed parameter list
   even when none of the extras are used.
9. **`# noqa` suppressions in 10/11 bots** (0–27 per bot) — not investigated
   line-by-line, but a volume this consistent across independently written
   bots suggests recurring ruff/ty friction rather than one-offs.
10. **Deep/internal import surface**: the standard flags a missing public
    re-export of `EventCommon` as an open upstream ask; grep found zero
    current bot code hitting this, so either it was already fixed or the
    scenario hasn't recurred yet — worth reconciling with the note's author.

No `getattr`/`hasattr`/`setattr` were found anywhere in `src/` across all 11
bots — the ruff `banned-api` ban is fully effective fleet-wide, the one
crutch category with perfect compliance.

## Features of 0.4.8 with zero usage (drop/deprecate candidates)

- 6 of 13 websocket/webhook event kinds: `@router.group_added`,
  `@router.reaction`, `@router.post_lifecycle`, `@router.channel_event`,
  `@router.user_event`, `@router.thread_event` (and their typed requests) —
  0/11, feature exists, no caller.
- `@router.websocket_event` (generic decorator) — 0/11 (internal
  `PostEventObserver`/etc. still power message dispatch; it's the
  user-facing generic hook that's cold).
- `ApiManager.reply()`, `.create_reaction()`, `.pin_post()` — declared,
  0/11 callers.
- `VERIFIED_ACTOR_FILTER`, `WhitelistFilter`, `BlacklistFilter` — 0/11.
- `combine_lifespans` — 0/11 (every bot has exactly one lifespan already).
- `Bot.add_outer_middleware()` — 0/11, even for the one middleware
  (`SafeErrorNotificationMiddleware`) this method exists for.
- The entire structured-reliability vocabulary — `RetryableError`,
  `PermanentError`, `AckMessage`, `QueuePolicy`, `worker_concurrency`,
  `config.reliability` — 0/11.
- `aiommbot.middlewares.circuit_breaker` — 0/11 (bots vendor `aiobreaker`
  instead, §7 item 2).
- `RedisStorageProfile`, `SyncBotRuntime`, and any distributed taskiq broker
  beyond `InMemoryBroker` — 0/11 each.

## Features used by ≥8/11 bots (core candidates — keep, document, harden)

- `@router.action`, `@router.dialog`, their typed `ActionRequest`/
  `DialogRequest` (11/11) — the two dominant interaction primitives.
- `api_manager: ApiManager`, `context: Context` DI params (11/11);
  `request.bot.state.<service>` fetched via a bot-local `_deps.py` typed
  helper (11/11, ~40+ independently-written thin wrappers).
- `Attachment(...)`, `Button.create(...)`, `Dialog.create(...)`,
  `send_dialog(...)`, `.update_post(...)` (11/11).
- `WebhookConfig(...)` composed once per bot; `DIRECT_CHAT_TYPE_FILTER` on
  the root router (11/11 each).
- Single `lifespan=` composition root + custom `def main()`; `src/database`
  Mongo repository layer for durable state (11/11 each).
- Sentry integration + bot-local `src/utils/observability/` toolkit copy;
  `HandlerObserver` Protocol wiring + `Prometheus*Observer` (11/11 each).
- Manual `AsyncMock`/`MagicMock`-based handler testing (11/11 — dominant
  even though the framework offers a better path; see §10).
- `**kwargs: Any` catch-all on handlers; `get_data`/`update_data` `Context`
  accessors for transient dialog state; `# noqa` suppressions present
  (10/11 each — the noqa consistency hints at recurring ruff friction worth
  a framework/lint-config look rather than 10 separate local issues).
- `.answer(...)` as the primary reply mechanism, `@router.message` +
  `PostRequest` (10/11 — every bot but duty-bot, or tour-bot for `answer`
  volume, which leans on `update_post` instead).

## Top 10 recurring workarounds (design inputs for aiommbot)

1. **Storage/broker config split-brain**: `storage_profile=` (3 bots) vs.
   `storage=`/`taskiq_broker=` + 5 duplicated storage-getter helpers (8
   bots, §4). *Fix*: finish the `storage_profile=` migration fleet-wide and
   delete the older dual-kwarg path.
2. **Vendored `aiobreaker` circuit breaker**, byte-for-byte duplicated
   between `crq-bot` and `postmortem-bot` (§7), bypassing
   `aiommbot.middlewares.circuit_breaker`. *Fix*: promote a per-client
   circuit-breaker helper in aiommbot, or document why the built-in
   middleware doesn't fit this shape.
3. **`SafeErrorNotificationMiddleware` unwrapped in 8/11 bots** (§9),
   leaking PII into logs and swallowing exceptions from Sentry. *Fix*: flip
   the framework default to redact-and-reraise instead of requiring each bot
   to discover and subclass it.
4. **7 differently-named settings fields for `WebhookConfig(enforcement=...)`**
   plus 3 bots hardcoding the enum with inconsistent case (§6). *Fix*: one
   documented settings-field convention, or a framework-level
   `WEBHOOK_ENFORCEMENT` env var read directly by `WebhookConfig`.
5. **Manual `event.submission[...]` parsing in 7/11 bots** instead of a
   typed helper (§2). *Fix*: a typed `DialogRequest.parsed_submission(Model)`
   convenience, since `matched_params` only covers action/message regex.
6. **`src/utils/observability/` copy-pasted into all 11 bots** (§8, largest
   duplicated package fleet-wide). *Fix*: extract as an installable
   `aiommbot[observability]` sub-package rather than a copy-paste starter kit.
7. **`aiommbot.testing` adoption at 2/11** (§10) despite being
   feature-complete and documented as preferred. *Fix*: an
   adoption/onboarding problem, not a framework gap — a cookiecutter default
   wiring one `TestClient`-based test would help new bots start on it.
8. **`**kwargs: Any` required on nearly every handler** (10/11, hundreds of
   sites) even when unused. *Fix*: handler introspection that tolerates a
   closed parameter list, making the catch-all opt-in only when needed.
9. **~40+ independently-written `_deps.py` one-liners** (§3) — thin,
   consistent, pure boilerplate. *Fix*: a small `@state_dependency("x_service")`
   decorator could collapse this without losing the typed-helper discipline.
10. **Structured reliability primitives entirely unused** (`RetryableError`/
    `PermanentError`/`AckMessage`/`QueuePolicy`/`worker_concurrency`,
    §7), alongside `InMemoryBroker`-only taskiq fleet-wide. *Fix*: either
    they're aimed at a broker (Redis/AMQP) no bot has adopted yet and are
    fine to keep forward-looking, or demote/simplify them, since the
    "cron fires once per replica" risk they'd mitigate is currently
    unmitigated everywhere.

## Caveats

- Counts are line-hits via `grep -rc`, not unique call-site or AST-level
  counts — a reasonable proxy, not exact.
- A few patterns were first miscounted at "0" because the real call site
  uses a factory method, not the bare class name (`Button.create(...)` not
  `Button(...)`; `send_dialog(...)` not `open_dialog(...)`) — every
  zero-usage claim here was re-verified against the actual framework source
  before being reported as a gap, not just against a guessed name.
- `duty-bot` is the newest/smallest bot (25 test files, 64 src files) and
  already on the newer `storage_profile=` API — its outlier stats (zero
  `**kwargs: Any`, zero `@router.message`) may reflect size/age rather than
  a considered framework-usage decision; worth a follow-up once it grows.
