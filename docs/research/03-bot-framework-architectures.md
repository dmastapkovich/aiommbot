# Bot-framework architectures: what to borrow for a Python Mattermost framework

Research date: 2026-09-02. Sources are primary (framework source on GitHub, official docs). Claims I could not confirm from a primary source are marked **[unverified]**.

## 1. aiogram 3 (Telegram)

**Public API shape.** `Dispatcher(storage=..., fsm_strategy=..., events_isolation=..., disable_fsm=..., name=..., **kwargs)` is the root `Router`; `**kwargs` become `self.workflow_data: dict[str, Any]` and the Dispatcher exposes `__setitem__/__getitem__/get` so `dp["db"] = pool` later lands in handler kwargs (`dispatcher/dispatcher.py`). `Router` holds ~27 `TelegramEventObserver`s in `observers: dict[str, TelegramEventObserver]` (`"message"`, `"callback_query"`, `"error"`, ...) plus `startup`/`shutdown` `EventObserver`s. `include_router(router)` / `include_routers(*routers)` set `parent_router`, whose setter rejects re-attachment, `"Self-referencing routers"` and `"Circular referencing of Router"`. Propagation (`_propagate_event`) is depth-first: own `observer.trigger()`, return on first non-`UNHANDLED`, else walk `sub_routers` in insertion order; `REJECTED` collapses to `UNHANDLED` (`dispatcher/router.py`). Registration is `@router.message(*filters, flags=None)` and `register(callback: CallbackType, *filters: CallbackType, flags: dict[str, Any] | None = None)`.

**Typing of handlers.** Weak by design: `CallbackType = Callable[..., Any]` (`dispatcher/event/handler.py`). `CallableObject` runs `inspect.signature(callback)` once, stores `params: set[str]` and `varkw: bool`, and `_prepare_kwargs()` passes only the names the handler declares (or everything if `**kwargs`). Sync callables are run via `asyncio.to_thread()`. No `ParamSpec`/`Protocol`; type-checkers cannot verify that `state: FSMContext` is actually injected.

**Filters & matching.** Filters are callables returning `bool | dict[str, Any]`; `HandlerObject.check()` awaits each `FilterObject`, and a dict result is merged into kwargs before the next filter runs (this is the DI hook). `FilterObject` special-cases `magic_filter.MagicFilter` by substituting `callback = callback.resolve`. aiogram's `MagicFilter` subclass adds `.as_(name)` → `AsFilterResultOperation`, returning `{name: value}` (or `None` for empty), so `F.text.regexp(r"\d+").as_("digits")` injects `digits` (`utils/magic_filter.py`). Composition `&`, `|`, `~` is inherited from `magic-filter`. `Command(commands=..., prefix="/", ignore_case=False, ignore_mention=False, magic=None)` returns `{"command": CommandObject(prefix, command, mention, args, regexp_match, magic_result)}` and, via `update_handler_flags`, appends itself to `flags["commands"]` so tooling can enumerate commands (`filters/command.py`). Flags (`dispatcher/flags.py`): `FlagGenerator` → `FlagDecorator`, stored on the handler as `aiogram_flag`, read with `get_flag(data, "rate_limit")` — the sanctioned way to feed per-handler metadata to middleware (throttling was removed from core in v3 and delegated to this mechanism).

**DI.** Kwargs-by-name only: `workflow_data`, middleware `data[...]`, filter dicts, and built-in keys `bot`, `event_from_user`, `event_chat`, `state`, `raw_state`, `fsm_storage`, `dispatcher`, `handler`. Third-party: `dishka.integrations.aiogram` registers a `ContainerMiddleware` (outer), opens a `Scope.REQUEST` child container per event with context `{TelegramObject: event, AiogramMiddlewareData: data}`, stores it under `"dishka_container"`, and `setup_dishka(container, router, auto_inject=True)` walks all handlers at startup and wraps them with `inject` so `FromDishka[Repo]` annotations resolve (an `AutoInjectMiddleware` exists but carries a performance warning). 

**FSM.** `StorageKey(bot_id: int, chat_id: int, user_id: int, thread_id: int | None = None, business_connection_id: str | None = None, destiny: str = DEFAULT_DESTINY)` (`fsm/storage/base.py`). `BaseStorage` = `set_state/get_state/set_data/get_data/update_data/close` (+ concrete `get_value`); `BaseEventIsolation` = `lock(key)` async CM + `close`. `FSMStrategy` ∈ {`USER_IN_CHAT`, `CHAT`, `GLOBAL_USER`, `USER_IN_TOPIC`, `CHAT_TOPIC`}; `apply_strategy` maps to `(chat_id, user_id, thread_id)` e.g. `CHAT → (chat_id, chat_id, None)` (`fsm/strategy.py`). `FSMContextMiddleware` (`fsm/middleware.py`) resolves `EventContext`, builds the key, then `async with self.events_isolation.lock(key=...)`: — with the comment "State should be loaded after lock is acquired" — injects `data["state"]`, `data["raw_state"]`, `data["fsm_storage"]`. `SimpleEventIsolation` is `defaultdict[Hashable, asyncio.Lock]` with a `TODO: Unused locks cleaner is needed`; `DisabledEventIsolation` yields immediately; `RedisEventIsolation` exists for multi-replica. Storages: `MemoryStorage`, `RedisStorage`, `MongoStorage`. **Scenes** (`fsm/scene.py`, docs flag it "experimental"): `class QuizScene(Scene, state="quiz")` with `@on.message.enter()`, `@on.message(F.text)`, `@on.message.exit()`, `@on.callback_query.back()`; `SceneConfig(state, reset_data_on_enter, reset_history_on_enter, callback_query_without_state)`; `SceneWizard.goto/retake/back/exit/leave`; `HistoryManager` keeps 10 snapshots for `back()`; `After.goto(...)` declares post-handler transitions; `SceneRegistry(router).add(...)` applies `StateFilter(scene.state)` to every observer and injects `scenes: ScenesManager`.

**Middleware.** `BaseMiddleware.__call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: dict[str, Any]) -> Any`. Docs: outer scope runs "before processing filters" on every event; inner scope "after processing filters but before handler"; "Inner middlewares is always calls for Update event type" because everything enters through the built-in `update` observer. Dispatcher pre-registers `ErrorsMiddleware`, `UserContextMiddleware`, `FSMContextMiddleware` on `update`.

**Lifecycle/concurrency.** `Dispatcher` no longer owns the `Bot` (multibot: `start_polling(*bots)`, `feed_update(bot, update)`, `feed_raw_update`). `handle_as_tasks` spawns a task per update tracked in `_handle_update_tasks: set[asyncio.Task[Any]]`, bounded by `tasks_concurrency_limit`. `emit_startup`/`emit_shutdown` recurse through routers. `DefaultBotProperties(parse_mode, disable_notification, protect_content, link_preview..., show_caption_above_media)` replaced constructor kwargs; a `Default("parse_mode")` sentinel is resolved at request-build time so method models stay pure.

**Testing.** Not public: `tests/mocked_bot.py` defines `MockedSession.make_request` (pushes the `TelegramMethod` to `requests`, pops a queued `Response`) and `MockedBot.add_result_for(method, ok, result, ...)` / `get_request()`. Community `aiogram_tests` (`MockedBot`, `MessageHandler`, `MESSAGE.as_object(text=...)`, `calls.send_message.fetchone()`) fills the gap.

**Codegen.** "All methods and types is fully autogenerated from Telegram Bot API docs by parser with code-generator" (docs). Generator inputs live in-repo: `.butcher/{enums,methods,schema,templates,types}`; each method dir e.g. `.butcher/methods/sendMessage/{entity.json, default.yml}` — `entity.json` is the parsed spec, YAML files are hand-maintained overrides. `AGENTS.md` (dev-3.x) says: "Prefer editing generator inputs (`.butcher/**/*.yml`) instead of hand-editing generated code"; regen is `butcher parse`, `refresh`, `apply all`. Runtime: `class TelegramMethod(BotContextController, BaseModel, Generic[TelegramType], ABC)` with `model_config = {extra="allow", populate_by_name=True, arbitrary_types_allowed=True}`, `__api_method__: ClassVar[str]`, `__returning__: ClassVar[Any]`, `async def emit(self, bot) -> TelegramType`, and `__await__` that requires a mounted bot (`as_(bot)`) — so `await message.answer(...)` and `await SendMessage(...).as_(bot)` share one typed path. Incoming types are frozen; mutate via `model_copy(update=...)`.

**Maintainer lessons (migration guide).** Keyword filters removed ("use explicit filter objects"); implicit defaults removed (`content_types=TEXT`, `state=None`) — the guide calls the state-filter inversion a *silent breaking change*; `Bot.get_current()` contextvars removed; `dp.throttle()` removed; `bot.me` became `await bot.me()`; positional Bot API calls are unsafe because Telegram inserts params mid-signature — "Always use keyword arguments".

## 2. discord.py 2.x

**API shape.** `commands.Bot` + `Cog`s. `class Command(_BaseCommand, Generic[CogT, P, T])` where `P` is a `ParamSpec`; callback typed `Callable[Concatenate[CogT, Context[Any], P], Coro[T]]` — the strongest static typing of any framework here. `GroupMixin.command()` overloads return `_CogCommandDecoratorWithCls[CogT, CommandT]`. `CogMeta` collects `__cog_commands__`, `__cog_listeners__` (`(listener_name, method_name)` tuples) and `__cog_app_commands__` at class-creation time; `Cog.listener(name=MISSING) -> Callable[[FuncT], FuncT]`.

**Filters/matching.** Argument parsing from annotations: `get_signature_parameters` → `params`, `transform()` handles `Greedy`, `Optional`, `discord.Attachment`, then `run_converters(ctx, converter, argument, param)`. For slash commands, `app_commands.Transformer` ABC (`transform`, `type`, `autocomplete`), `Transform[T, Transformer]` (behaves as `Annotated`), `Range[int, 1, 10]`, `annotation_to_parameter → CommandParameter`, `BUILT_IN_TRANSFORMERS`. Checks: `checks: List[UserCheck[Context[Any]]]`, `add_check`, `can_run` raising `CheckFailure`; `cooldown` via `CooldownMapping`.

**DI.** None beyond `Context` and `bot` attributes; state lives on `Cog` instances.

**Middleware.** No chain; instead hooks: `before_invoke/after_invoke`, `cog_check`, `cog_before_invoke`, `cog_command_error`, `interaction_check`, `bot_check_once`.

**Lifecycle.** `setup_hook()` runs after login, before gateway; `async with client:`; `load_extension` and `setup()` are async; `cog_load()`/`cog_unload()` async (unload exceptions suppressed); `_inject`/`_eject` register commands/listeners/checks.

**Typing layer.** `discord/types/*.py` are hand-written `TypedDict`s with `NotRequired`, `Snowflake` alias, `Literal` unions; models are hand-written classes fed from those dicts. No codegen.

**Testing.** Third-party `dpytest` (`dpytest.configure(bot)`, `dpytest.message()`, `dpytest.verify().message().content()`, `FakeHttp`), self-described "still in alpha".

**Lessons (migrating.html).** Intents mandatory "to better educate users"; in-place `edit()` removed to prevent "race conditions between in-place edits and gateway events"; custom `AsyncIterator` removed in favour of standard `async for`; naive datetimes → UTC-aware; `InvalidArgument` → `TypeError/ValueError`; lazy read-only sequences for large collections.

## 3. hikari + lightbulb / arc

**hikari core.** Models are `@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)` with `attrs.field(hash=..., eq=False, repr=...)`, an `app: traits.RESTAware` back-reference, and the three-state `undefined.UndefinedOr[T]` sentinel (`hikari/messages.py`). Deserialization is centralised in an `abc.ABC` `EntityFactory` (`deserialize_message`, `serialize_embed`, ...) over `JSONObject = Mapping[str, Any]`; `JSONObjectBuilder.put()` skips `UNDEFINED`; `orjson` is used when importable (`internal/data_binding.py`). Event subscription is type-driven: `CallbackT = Callable[[EventT], Coroutine[Any, Any, None]]`; `listen()` infers the event class from the annotation; `wait_for(event_type, /, timeout, predicate)` and `stream(...)` (`api/event_manager.py`). `GatewayBot.run()` → `start()` → `join()`; `close()` dispatches `StoppingEvent`/`StoppedEvent`; `enable_signal_handlers`; components (`CacheImpl`, `EntityFactoryImpl`, `EventManagerImpl`, `RESTClientImpl`) are swappable.

**lightbulb v3.** Class-based commands: `@client.register() class Ping(lightbulb.SlashCommand, name="ping", description=...)` with `@lightbulb.invoke async def invoke(self, ctx: lightbulb.Context)`; `lightbulb.client_from_app(bot)`. DI was extracted into **linkd**: `DependencyInjectionManager`, `registry_for(Contexts.ROOT)`, `register_value`, `@linkd.inject`, `@manager.contextual()`; option descriptors like `lightbulb.string(...)` and `lightbulb.di.INJECTED` **[unverified — the DI guide page 404'd]**.

**hikari-arc.** "focus on type-safety and correctness"; options via `Annotated[str, arc.StrParams(...)]`; DI via Alluka: `client.set_type_dependency(MyDatabase, db)`, `db: MyDatabase = arc.inject()`, `@client.inject_dependencies` (must be bottom-most decorator); type-keyed only, no scopes; hooks `arc.with_hook`, `arc.guild_only`.

## 4. Slack Bolt for Python

**API shape.** `App(token, signing_secret, authorize, installation_store, process_before_response, request_verification_enabled, ssl_check_enabled, url_verification_enabled, ignoring_self_events_enabled, listener_executor, raise_error_for_unhandled_request, ...)`; `AsyncApp` mirrors it (AGENTS.md rule: "When modifying any sync module, you MUST also update the corresponding async module"). Listener decorators `@app.event/message/command/action/shortcut/view/options(constraint, matchers=[...], middleware=[...])`; return type `Callable[..., Optional[Callable[..., Awaitable[Optional[BoltResponse]]]]]` and `func: Callable[..., Awaitable[Optional[BoltResponse]]]` — i.e. untyped injection.

**Matching.** `listener_matcher/builtins.py`: `event(constraints)`, `message_event(constraints, keyword)`, `command`, `action → block_action/attachment_action/dialog_submission`, `view_submission`, `options`; `_matches(str_or_pattern, input)` accepts `str` or compiled `Pattern`; custom `matchers` are plain functions receiving kwargs and returning `bool`.

**DI.** By parameter name: `build_required_kwargs` filters `all_available_args` by the signature (`kwargs = {k: v for k, v in all_available_args.items() if k in required_arg_names}`); `"next"` and `"next_"` alias (`# for the middleware using Python's built-in next()`); `args` gives the whole `Args` bundle; unknown names get `None` plus `logger.warning(f"{name} is not a valid argument")` — fails open. `Args` fields: `logger, client: WebClient, req, resp, context: BoltContext, body, payload, options, shortcut, action, view, command, event, message, ack: Ack, say: Say, respond: Respond, complete, fail, next`.

**Middleware.** Global `@app.use` / `app.middleware(fn)` and per-listener `middleware=[...]`, both must call `next()`; `dispatch()` = global chain → matchers → listener middleware → ack fn → `lazy` fns (executor). Built-in middlewares (`RequestVerification`, `SslCheck`, `UrlVerification`, `IgnoringSelfEvents`, `SingleTeamAuthorization`) are just the same abstraction.

**FSM.** None; state is user-land. Ack-within-3-seconds and `process_before_response`/`lazy` shape the design.

**Adapters.** `slack_bolt/adapter/{aiohttp, asgi, aws_lambda, bottle, cherrypy, django, falcon, fastapi, flask, google_cloud_functions, pyramid, sanic, socket_mode, starlette, tornado, wsgi}`.

**Testing.** No official toolkit; issue #380 ("Document about the ways to write unit tests for Bolt apps") still open; maintainer advice is to copy `tests/mock_web_api_server` and drive `app.dispatch(BoltRequest(...))`.

**Agent-friendliness.** `docs.slack.dev/llms.txt`, `llms-sitemap.md`, every page available as `.md`; repo `AGENTS.md` (architecture, sync/async mirroring, "Single Dependency Rule": core depends only on `slack_sdk`); Slack MCP server + Slackbot MCP client (June 2026).

## 5. python-telegram-bot v20+

Rationale for asyncio: PTB "spent significant time waiting for web responses… instead of sitting around, your program could already do other stuff". `Application` replaces `Updater`/`Dispatcher` ("binds all its components together"), built via `Application.builder().token(...).build()`; `pass_*` kwargs replaced by `CallbackContext` (`context.user_data/chat_data/bot_data`); `run_async` → `block`; `TelegramObject` immutable, lists → tuples; pluggable `BaseRequest` (httpx). `ConversationHandler(entry_points, states, fallbacks, allow_reentry, per_chat, per_user, per_message, conversation_timeout, persistent, map_to_parent, block)`: callbacks *return* the next state; `END=-1`, `TIMEOUT=-2`, `WAITING=-3`; documented footguns around `per_message` with callback queries and that it requires sequential processing. No official test toolkit.

## 6. Zulip / Rocket.Chat / MS Bot Framework

Zulip `zulip_bots`: minimal contract (`usage()`, `handle_message(message, bot_handler)`, `initialize`), `BotHandler.send_reply/send_message/storage.put/get/contains`; notable for shipping a **first-party test lib** (`BotTestCase`, `StubBotHandler` with `transcript`, `verify_reply(request, response)`, `verify_dialog([(req, resp), ...])`, `mock_http_conversation(fixture)`, `mock_config_info`). Rocket.Chat has no framework of note: `rocketchat-async` (WS realtime, partial coverage), `rocketchat_API` (sync REST), `rocketbotte` (small discord.py-style wrapper). MS Bot Framework skipped (enterprise, .NET-centric).

## 7. DI libraries compared

| Lib | Injection marker | Scopes | Async resources | Test overrides | Typing | Used by |
|---|---|---|---|---|---|---|
| **dishka** | `FromDishka[T]` / `Annotated`, `@inject`, `from_context` | `APP, SESSION, REQUEST, ACTION, STEP` (+custom) | yield-generators finalised on scope exit | `provide(..., override=True)`, container overrides | type keys, no plugin; graph validated at startup | aiogram, aiogram_dialog, FastAPI, Litestar, FastStream, taskiq, gRPC integrations |
| **fast-depends** | `Depends()`, `@inject` (pydantic casts args) | none (per-call cache: "called at ONCE" per `@apply_types` stack) | yield deps | `dependency_overrides_provider` / `Provider` | pydantic-validated, no plugin | FastStream (`@apply_types`), Propan |
| **that-depends** | `Provide[...]`, `@inject`; providers `Singleton, Factory, AsyncFactory, Resource, ContextResource, Selector, Object, List` | `ContextScopes` | `tear_down` | `override`, `override_context`, `reset_override` | "mypy strict", zero deps, 3.10+ | FastAPI/FastStream/Litestar integrations |
| **wireup** | `Injected[T]` / `Inject()`, `@injectable` | `singleton, scoped, transient`; `enter_scope` | async container | `container.override()` CM | no plugin; "if the container starts, it works"; ~= manual wiring perf | FastAPI, Django, Flask, Starlette, Celery, Click, AIOHTTP |
| **linkd / Alluka** | `@linkd.inject`, `Contexts`; `arc.inject()` type-keyed | `Contexts` (linkd); none (Alluka) | contextual async | — | type-keyed | lightbulb v3 / arc |
| **Litestar built-in** | `Provide(fn, use_cache, sync_to_thread)`, `dependencies={}` per app/router/controller/handler | layered override | yield cleanup before response | lower layer overrides key | `NamedDependency[T]` marker (2.24) | Litestar |

## Comparison table

| | aiogram 3 | discord.py 2 | hikari (+arc/lightbulb) | Bolt Python | PTB 20+ |
|---|---|---|---|---|---|
| API shape | `Dispatcher` root `Router`, nested `include_router`, first-match DFS | `Bot` + `Cog` classes, `CogMeta` | `GatewayBot` + type-driven `listen`; class commands | `App`/`AsyncApp`, flat listener list | `Application.builder()`, handler groups |
| Filters | callables/`MagicFilter` returning `bool|dict`, `&|~` | converters/`Transformer` from annotations, checks | `Annotated` options, hooks | `matchers=[...]`, str/regex constraints | `filters.TEXT & ~filters.COMMAND` |
| DI | kwargs by name (+dishka) | `Context` only | Alluka/linkd type-keyed | kwargs by name, fail-open `None` | `CallbackContext` |
| FSM | `StorageKey`+`FSMStrategy`+`EventIsolation`, Scenes | none | none | none | `ConversationHandler` returns states |
| Middleware | outer/inner `BaseMiddleware.__call__(handler, event, data)` | hooks only | hooks only | global + per-listener `next()` | none (handler `block`) |
| Testing | internal `MockedBot` only | 3rd-party dpytest | — | none (issue #380) | none |
| Codegen | butcher, `.butcher/**` inputs | hand `TypedDict` | attrs + `EntityFactory` | dicts (`Dict[str, Any]` payloads) | hand-written |
| Handler typing | `Callable[..., Any]` | `ParamSpec`/`Concatenate` | `Callable[[EventT], Coroutine]` | `Callable[..., Awaitable]` | `HandlerCallback[UpdateT, CCT, RT]` |

## Patterns to adopt

1. **Router tree with explicit ordering and cycle checks** (aiogram `parent_router` setter; `_propagate_event` DFS). Keep `UNHANDLED`/`REJECTED` sentinels and `SkipHandler`.
2. **Filters that return typed data** — but make the return a typed object, not `dict[str, Any]`. Combine aiogram's `Command → CommandObject` idea with discord.py's `ParamSpec`/`Transformer` typing so `def h(msg: Post, cmd: CommandObject)` is checkable.
3. **Handler-flag metadata** (`aiogram.dispatcher.flags`) for rate-limit/`chat_action`-style cross-cutting concerns instead of baking throttling into core (aiogram removed `dp.throttle()`).
4. **Outer/inner middleware with `(handler, event, data)`** semantics and a built-in `update` observer so middleware placement is predictable; document "outer runs before filters" verbatim.
5. **Per-key event isolation lock + FSM strategy** (`StorageKey`, `FSMStrategy`, `BaseEventIsolation.lock`); for Mattermost the key is `(bot_id, channel_id, user_id, root_id/thread, destiny)`; ship `Memory`, `Redis`, `Mongo` storages and a Redis isolation for multi-replica. Add the lock-cleaner aiogram's TODO lacks.
6. **Declarative multi-step flows** à la Scenes (`@on.message.enter()`, `After.goto`, `HistoryManager`) — but design them typed from day one rather than "experimental".
7. **Multibot-safe root**: root object doesn't own the client; `feed_event(bot, event)`; `DefaultBotProperties`-style resolved defaults; awaitable method objects generic in return type (`TelegramMethod[T]`, `__returning__`).
8. **Startup-validated, scoped DI** (dishka `Scope.REQUEST` per event, `from_context(Event)`, `auto_inject` at startup not per-call; wireup's "if the container starts, it works"). Prefer a first-party dishka integration over kwargs magic; fail closed on unknown parameters (Bolt logs a warning and injects `None`).
9. **Type-driven event subscription** (hikari `listen()` inferring `EventT` from the annotation; `wait_for`/`stream` for tests and flows).
10. **First-party test toolkit** modelled on Zulip's `verify_dialog` + aiogram's `MockedSession` request/response queues + dpytest's `verify().message()` chain: `TestClient.feed(post_event(...))`, recorded API calls, storage inspection, no network.
11. **Codegen with in-repo override inputs** (`.butcher/methods/X/{entity.json,default.yml}`, "edit generator inputs, not generated code"). Mattermost's OpenAPI 3.0.0 (`api/v4/source/*.yaml` → `mattermost-openapi-v4.yaml`, 45 tags, ~80 schemas) is usable for REST codegen **only with an override layer**: `Post.props`/`data`/`payload` are bare `type: object`, enums are sparse, `required` arrays sparse, and the WebSocket API (45 events: `posted`, `post_edited`, `typing`, `status_change`, `hello`, ...) is prose-only in `introduction.yaml` — WS event models must be hand-written attrs/pydantic classes with an `EntityFactory`-style seam and `UNDEFINED`-aware serialisation.
12. **Immutable incoming models** (aiogram frozen pydantic, discord.py "no in-place edit", PTB tuples) and keyword-only constructors.
13. **Agent-facing docs**: `AGENTS.md` (aiogram, Bolt), `llms.txt`/`.md` mirrors (Slack), `CHANGES/` fragments (towncrier).

## Patterns to avoid

- **Implicit default filters** (aiogram v2 `state=None`, `content_types=TEXT`) — removed in v3 as a silent-behaviour trap.
- **Global context singletons** (`Bot.get_current()`) — removed in v3; pass `bot` explicitly / via DI.
- **Fail-open kwargs injection** (Bolt: unknown arg → `None` + warning).
- **Untyped `Callable[..., Any]` handler contracts** (aiogram, Bolt) when `ParamSpec`/`Protocol` are available (discord.py shows it is feasible).
- **Positional API-method params** (aiogram: new params inserted mid-signature misbind).
- **Sync/async duplicated packages** (Bolt must mirror every change) — go async-only.
- **Threading for I/O** (PTB pre-v20).
- **FSM without isolation** and locks that never get cleaned (aiogram TODO).
- **Returning state ints from callbacks with `per_*` key flags** (PTB `ConversationHandler` footguns).
- **Shipping test doubles only in `tests/`** (aiogram) or not at all (Bolt, PTB).

## Sources

- aiogram: `aiogram/dispatcher/router.py`, `dispatcher/dispatcher.py`, `dispatcher/event/telegram.py`, `dispatcher/event/handler.py`, `dispatcher/middlewares/base.py`, `dispatcher/flags.py`, `filters/command.py`, `utils/magic_filter.py`, `fsm/storage/base.py`, `fsm/storage/memory.py`, `fsm/strategy.py`, `fsm/middleware.py`, `fsm/scene.py`, `methods/base.py`, `client/default.py`, `tests/mocked_bot.py`, `AGENTS.md`, `.butcher/` (branch dev-3.x, https://github.com/aiogram/aiogram); docs https://docs.aiogram.dev/en/latest/migration_2_to_3.html, /dispatcher/middlewares.html, /dispatcher/finite_state_machine/scene.html; generator https://github.com/aiogram/tg-codegen.
- discord.py: `discord/ext/commands/core.py`, `cog.py`, `discord/app_commands/transformers.py`, `discord/types/message.py`; https://discordpy.readthedocs.io/en/stable/migrating.html; dpytest https://github.com/CraftSpider/dpytest.
- hikari: `hikari/api/entity_factory.py`, `api/event_manager.py`, `impl/gateway_bot.py`, `messages.py`, `internal/data_binding.py`; lightbulb https://github.com/tandemdude/hikari-lightbulb, linkd https://github.com/tandemdude/linkd; arc https://github.com/hypergonial/hikari-arc, https://arc.hypergonial.com/guides/dependency_injection/.
- Bolt Python: `slack_bolt/app/app.py`, `app/async_app.py`, `kwargs_injection/args.py`, `kwargs_injection/utils.py`, `listener_matcher/builtins.py`, `slack_bolt/adapter/`, `AGENTS.md`; https://docs.slack.dev/tools/bolt-python/concepts/global-middleware, https://docs.slack.dev/llms.txt; issues #380, #157; https://docs.slack.dev/ai/slack-mcp-server/.
- PTB: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Transition-guide-to-Version-20.0, https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html.
- DI: https://dishka.readthedocs.io, `src/dishka/integrations/aiogram.py`; https://github.com/Lancetnik/FastDepends; https://faststream.ag2.ai/latest/getting-started/dependencies/; https://github.com/modern-python/that-depends; https://github.com/maldoinc/wireup; https://docs.litestar.dev/latest/usage/dependency-injection.html.
- Zulip: `zulip_bots/README.md`, `zulip_bots/zulip_bots/test_lib.py` (https://github.com/zulip/python-zulip-api). Rocket.Chat: https://github.com/hynek-urban/rocketchat-async, https://github.com/jadolg/rocketchat_API, https://pypi.org/project/rocketbotte/.
- Mattermost API: https://github.com/mattermost/mattermost-api-reference (archived 2023-06-29), https://github.com/mattermost/mattermost/tree/master/api (`api/README.md`, `v4/source/introduction.yaml`, `v4/source/definitions.yaml`).
