# Webhook and callback ingress patterns in peer frameworks: how HTTP callbacks join an event-driven core

Research date: 2026-09-03. Ticket #44, input to #20 (webhook callbacks: same event model or separate
request/response model; plugin boundary). Sources are primary (official docs, framework source on
GitHub, the Mattermost server). Claims I could not confirm from a primary source are marked
**[unverified]**.

## 0. The question and the constraint set by ADR-0012/0013

ADR-0012 already reserves a seat for callbacks: `Event[P].meta` carries "an optional typed **reply
channel** with a deadline so request/response transports (webhook callbacks) can join the same
model if #20 decides so", and `InteractiveAction` / `DialogSubmission` are listed as first-class
payloads "from the webhook path". ADR-0013 makes dispatch first-match with a typed
`Handled | Unhandled` outcome. ADR-0005 makes the webhook ingress the *horizontally replicable*
half of the deployment. So the question is not "can a callback be an event" but: what does the
peer field do about the **HTTP answer** (who produces it, by when, with what shape), where
**verification** sits, whether the HTTP side is a **separate package**, and how it is **tested**.

## 1. aiogram 3: one `feed_update` path, two transports, and "reply into webhook response"

**Same model.** Both transports end in `Dispatcher.feed_update(bot, update) -> Any`
(`dispatcher/dispatcher.py`). Polling calls `_process_update(bot, update, call_answer=True)`; the
webhook calls `feed_webhook_update(bot, update, _timeout=55) -> TelegramMethod | None`, a thin
wrapper that awaits `feed_update` under a timeout. There is no second dispatch model and no
"request" type — handlers see `Message`/`CallbackQuery` regardless of transport.

**The immediate answer is the handler's return value.** A handler may `return SendMessage(...)`.
In polling, `_process_update` executes it through `silent_call_request` (errors logged, never
raised); in webhook mode the same object becomes the HTTP body: `_build_response_writer(bot,
result)` serialises `result.model_dump()` as multipart form-data with an extra `method` field
(`result.__api_method__`), or `JsonPayload({})` when nothing was returned
(`webhook/aiohttp_server.py`). The docs tell a non-aiohttp host to "check that result of the
`feed_update` methods is an instance of API method and build multipart/form-data or
application/json response body manually". The reply channel is thus **implicit**: return value,
one method, no typing of *which* methods are legal for which event.

**Deadline handling is explicit.** `feed_webhook_update` waits up to 55 s, then logs "Detected
slow response into webhook. Telegram is waiting for response only first 60 seconds and then re-send
update ... handler is moved to background", returns `None` (empty 200) and lets the task finish
detached. `SimpleRequestHandler(dispatcher, bot, handle_in_background=True, secret_token=None)`
goes further: it spawns `asyncio.create_task(_background_feed_update)` → `feed_raw_update`, tracks
it in `_background_feed_update_tasks`, and returns `web.json_response({})` at once — so "reply into
webhook" is silently unavailable in that mode.

**Verification lives in the transport handler, not in middleware.** `handle()` compares the
`X-Telegram-Bot-Api-Secret-Token` header with `secrets.compare_digest` and answers
`web.Response(body="Unauthorized", status=401)`; `TokenBasedRequestHandler.verify_secret` always
returns `True` (the bot token in the path is the secret). No replay window — Telegram's protocol
has none. `ip_filter_middleware` is separate, warning that `X-Forwarded-For` "is trustworthy only
if all webhook traffic goes through a trusted reverse proxy".

**Packaging and tests.** `aiogram.webhook.aiohttp_server` ships in the main package; `aiohttp` is
a core dependency, so no extra exists. `tests/test_webhook/test_aiohttp_server.py` uses
pytest-aiohttp's `aiohttp_client(app)` (in-process), posts a raw `Update` to `/webhook`, asserts
`resp.status == 401` for a bad secret, reads the multipart reply with `MultipartReader` and asserts
`result["method"] == "sendDocument"`; the background mode is asserted by patching
`Dispatcher.silent_call_request`.

## 2. Slack Bolt (Python): `ack()` deadline, lazy listeners, request verification as middleware

**Same model, one dispatch entry.** `App.dispatch(req: BoltRequest) -> BoltResponse` is the only
entry for every HTTP adapter *and* Socket Mode. A `BoltRequest` is transport-neutral (`body`,
`headers`, `mode="http" | "socket_mode"`); listeners (`@app.action`, `@app.view`, `@app.event`)
never see the transport.

**Verification is global middleware.** Default chain (`_init_middleware_list`): `SslCheck`,
`RequestVerification`, `before_authorize`, `SingleTeamAuthorization`/`MultiTeamsAuthorization`,
`IgnoringSelfEvents`, `UrlVerification`, `AttachingFunctionToken`. `RequestVerification` wraps
`slack_sdk.signature.SignatureVerifier`: reject when `abs(now - int(timestamp)) > 60 * 5`, hash
`f"v0:{timestamp}:{body}"` with HMAC-SHA256, compare with `hmac.compare_digest`, on failure return
`BoltResponse(status=401, body={"error": "invalid request"})`. Its `_can_skip` returns true when
`mode == "socket_mode"` — one middleware stack serves both transports and the verification step
switches itself off where the transport is already authenticated. If no listener matches,
`_handle_unmatched_requests` logs a warning and returns **404**.

**`ack()` is a reply channel with a deadline and a request-type-dependent shape.** Docs: "you only
have 3 seconds to respond before Slack registers a timeout error". `ack()` is injected into the
listener and builds the body through `_set_response(text_or_whole_response="", blocks=...,
options=..., response_action=..., errors=..., view=...) -> BoltResponse`: options →
`{"options": ...}`; view submissions → `{"response_action": "update"|"push"|"clear", "view": ...}`
or `{"response_action": "errors", "errors": {...}}` (`ValueError("errors field is required for
response_action: errors")` otherwise); text/blocks for slash commands; empty → `200 ""`. Bolt
validates the shape at call time, not at type-check time.

**Deadline mechanics.** `ThreadListenerRunner.run` (default) submits the listener to a
`ThreadPoolExecutor` (5 workers) and blocks the HTTP thread only until `ack()` is called or
`listener.ack_timeout` elapses (logging `warning_did_not_call_ack`); the listener keeps running
after the response is written. `process_before_response=True` (FaaS) runs the whole listener
before responding, auto-acks if it forgot, and moves long work to `lazy=[...]` functions that "do
not have access to `ack()`" and are re-invoked out of band.

**Packaging and tests.** Adapters live *inside* `slack_bolt/adapter/` (`aiohttp`, `asgi`,
`aws_lambda`, `django`, `falcon`, `fastapi`, `flask`, `sanic`, `socket_mode`, `starlette`,
`tornado`, `wsgi`, ...), yet `pyproject.toml` declares one dependency, `slack_sdk>=3.38.0,<4`, and
**no extras**: each adapter imports the host framework the application already installed, and Bolt
never runs its own server. `tests/scenario_tests/test_block_actions.py` builds
`BoltRequest(body=raw_body, headers={"x-slack-signature": [signature_verifier.generate_signature(body,
ts)], "x-slack-request-timestamp": [ts]})`, calls `app.dispatch(request)` and asserts
`response.status == 200` (or **404** for an unmatched `block_id`); only the Slack Web API is mocked.

## 3. Discord: interaction endpoint (Ed25519), deferred responses, gateway vs HTTP sharing one model

**Platform contract.** Interactions arrive either as the gateway event `INTERACTION_CREATE` or,
"if you want to receive interactions via HTTP-based outgoing webhooks", at an Interactions
Endpoint URL — mutually exclusive per app. HTTP delivery requires validating every request with the
app public key over `X-Signature-Ed25519` / `X-Signature-Timestamp` ("your app should respond
with a `401` error code"), a `PING`→`PONG` handshake, and Discord "will also perform automated,
routine security checks against your endpoint, including purposefully sending you invalid
signatures" — failing them removes the URL. "You must send an initial response within 3 seconds of
receiving the event. If the 3 second deadline is exceeded, the token will be invalidated." Callback
types: `CHANNEL_MESSAGE_WITH_SOURCE` (4), `DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE` (5),
`DEFERRED_UPDATE_MESSAGE` (6), `UPDATE_MESSAGE` (7), `MODAL` (9). "Interaction tokens are valid for
15 minutes and can be used to send followup messages." An HTTP-delivered interaction may be
answered either in the HTTP response body **or** via `POST /interactions/{id}/{token}/callback` —
the same endpoint the gateway flow uses.

**hikari: shared model classes, two dispatch and reply styles.** `GatewayBot` publishes
`InteractionCreateEvent` to all subscribers; handlers answer over REST (`create_initial_response`,
`NotFoundError` if already answered). `RESTBot` ("Basic implementation of an interaction based
REST-only bot") composes an `InteractionServer`; `set_listener(interaction_type, listener, /, *,
replace=False)` takes **one listener per type** (`CommandInteraction`, `ComponentInteraction`,
`AutocompleteInteraction`, `ModalInteraction`) and the listener **returns a response builder** —
`build_response()`, `build_deferred_response()`, `build_modal_response()`, each documented "for
use in the REST server flow". `InteractionServer.on_interaction(body: bytes, signature: bytes,
timestamp: bytes) -> Response` verifies with PyNaCl `VerifyKey.verify(timestamp + body,
signature)` (answering **400**, not the 401 Discord asks for), answers `PING` with `{"type": 1}`,
requires `Content-Type: application/json` (415 otherwise), and is public so the bot can be embedded
in an existing aiohttp app instead of the built-in one-route server. Verdict: payload and REST
layers are shared; **dispatch is not** (pub/sub vs one-listener-per-type), and the reply channel
differs (call REST vs return a builder).

**discord.py** receives interactions over the gateway only (`InteractionResponse.defer()`,
`is_done()` — "An interaction can only be responded to once" — `Interaction.followup`,
`expires_at`); nothing about an Interactions Endpoint URL appears in its API reference.

## 4. Microsoft Bot Framework (botbuilder-python): `process_activity`, turn context, response vs proactive

**One activity model, one pipeline.** `BotFrameworkAdapter.process_activity(req, auth_header,
logic)` runs `JwtTokenValidation.authenticate_request` (`PermissionError` when unauthenticated),
builds `TurnContext(self, activity)`, stores identity/callback/connector client in `turn_state`,
and calls `run_pipeline(context, logic)` — the middleware onion ending in the bot's turn handler.
Proactive messaging reuses the same pipeline: `continue_conversation(reference:
ConversationReference, callback)` fabricates a `TurnContext` from a stored reference and calls
`run_pipeline` again.

**The HTTP response is normally empty; replies are separate requests.** Docs: "The bot responds to
the inbound POST request with a 200 HTTP status code. Activities sent from the bot to the channel
are sent on a separate HTTP POST to the Bot Framework Service", typically "nested" inside the
inbound request; "The bot has 15 seconds to acknowledge the call with a status 200 on most
channels ... an HTTP GatewayTimeout error (504) occurs" otherwise. `send_activities` calls
`send_to_conversation()` / `reply_to_activity()` rather than writing to the response. Two cases put
content **into** the body: (a) `ActivityTypes.invoke` — the bot stores an `InvokeResponse` in
`turn_state[_INVOKE_RESPONSE_KEY]`, the adapter returns `InvokeResponse(status, body)`, a missing
one becomes **501 Not Implemented**; (b) `delivery_mode == expect_replies` — activities are
buffered in `context.buffered_reply_activities` and returned as `ExpectedReplies(activities=...)`.
The aiohttp `CloudAdapter.process(request, bot)` maps this to `json_response(body,
status=invoke_response.status)` or `Response(status=201)` when there is nothing to say, and
415/400/405/401 for content type, missing `type`, method and auth failures. The SDK is archived
(support ended 2025-12-31), but "default ack; typed invoke response keyed in turn state; proactive
path through the same pipeline" is the clearest *reply-channel-in-context* precedent.

## 5. FastStream, Litestar, FastAPI: exposing an ASGI app instead of running a server; testing without one

**FastStream** does not own a server. `AsgiFastStream(broker, asgi_routes=[("/path", handler)])`
implements `async def __call__(self, scope, receive, send)`: `lifespan` scope starts/stops the
broker, `http` scope is matched by **path equality** over `self.routes`, anything else is 404;
`mount(path, route)` appends a route later and `from_app(app, asgi_routes)` wraps an existing
`FastStream` app. The docs run it with `uvicorn main:app` and say the helpers "can be used as
ready-to-use endpoints for other ASGI frameworks", e.g. `app.mount("/health", make_ping_asgi(broker))`
inside FastAPI. Tests use `TestBroker`/`TestApp` (in-memory broker, lifespan hooks fire); ASGI route
testing is not documented — but since the object is a plain ASGI callable, Starlette's
`TestClient` applies unchanged.

**Litestar** mounts foreign ASGI apps with `@asgi(path="/x", is_mount=True, copy_scope=True)`:
"Mount path accept any arbitrary paths that begin with the defined prefixed path"; `copy_scope`
"should be set to 'True' unless side effects via scope mutations by the mounted ASGI application
are intentional". **FastAPI** does the same with `app.mount("/subapi", subapi)` and forwards the
prefix as ASGI `root_path`. **Starlette `TestClient`** "allows you to make requests against your
ASGI application, using the `httpx2` library" — the documented example is a bare
`async def app(scope, receive, send)`, so any ASGI callable is testable with synchronous calls and
no socket. The 0.4.x repo already depends on `httpx2` for exactly this ("ASGI test transport for
the webhook surface; the framework itself runs on aiohttp", `pyproject.toml`).

The shared lesson: an event framework exposes an **ASGI callable** (or a function `bytes,
headers -> response`, like hikari's `on_interaction`) and leaves server, TLS, port, and process
model to the host; that is also what makes it testable in-process.

## 6. Mattermost specifics: action and dialog callback contracts, `trigger_id`, how existing code handles them

**Action callback** (`server/channels/app/integration_action.go`, `DoPostActionWithCookie`). The
server signs a `trigger_id` (`GenerateTriggerId`: ECDSA-SHA256 over
`clientTriggerId:userId:millis`), marshals `PostActionIntegrationRequest{UserId, UserName,
ChannelId, ChannelName, TeamId, TeamDomain, PostId, TriggerId, Type, DataSource, Context}` — for
selects `Context["selected_option"]` is injected — and POSTs it. Routing is by URL: paths under
`/plugins/` go in-process (`DoLocalRequest` → `doPluginRequest`, which sets `Mattermost-User-Id`
and `Authorization: Bearer <session token>`); everything else is a real HTTP request with **only**
`Content-Type: application/json` and `Accept: application/json` — no signature, no user header, no
timestamp. The request context is `context.WithTimeout(...,
ServiceSettings.OutgoingIntegrationRequestsTimeout)` (default **30 s**, `model/config.go`). The
response is read up to `MaxIntegrationResponseSize`; any status other than 200 is an error
(429/503 preserved, other 5xx → 502, everything else → 400). On success `response.Update` is
applied through `applyPostActionUpdate` and `response.EphemeralText` becomes an ephemeral post;
`GotoLocation` is returned to the client. Response type
`PostActionIntegrationResponse{Update *Post, EphemeralText, SkipSlackParsing, GotoLocation}`.
The docs stress that `context` "is kept confidential ... add a token to your context without users
ever being able to see it": the **only** authentication primitive for an external URL is a secret
the bot itself placed in `context`.

**Dialog callback** (`SubmitInteractiveDialog`). Opening requires the signed `trigger_id`;
`OpenInteractiveDialog` verifies it with `DecodeAndVerifyTriggerId(key, timeout)` where `timeout`
is the **same `OutgoingIntegrationRequestsTimeout`** — so a trigger id lives 30 s by default, a
fact the docs never state. The dialog is pushed to the user's client over WebSocket
(`WebsocketEventOpenDialog = "open_dialog"`), but the submission comes back to the integration
over HTTP: `SubmitDialogRequest{Type: "dialog_submission", URL, CallbackId, State, UserId,
ChannelId, TeamId, Submission map[string]any, Cancelled, FileIds}` (file ids are validated for
ownership first). The response is `SubmitDialogResponse{Error, Errors map[string]string, Type,
Form *Dialog}`: an **empty body is accepted** ("an empty response is acceptable"), `errors` keeps
the dialog open with per-field text, `error` shows a general message, `type: "form"` continues to a
next dialog; `response.IsValid()` is enforced. Field validation errors are therefore **only**
expressible through the HTTP response body — there is no REST call that re-opens a dialog with
errors after the fact.

**Plugin SDK.** Plugins receive the same callbacks through `Hooks.ServeHTTP` — "This can be used
to receive post action requests when Interactive Messages Buttons and Menus are triggered" — and
"the Mattermost Server sets the HTTP header `Mattermost-User-Id` when the request is made by an
authenticated client ... if the `Mattermost-User-Id` is blank, it's the plugin's responsibility to
reject the request" (the starter template's `MattermostAuthorizationRequired` middleware does
exactly that). Since v9.4 an external `Authorization` header is passed through to plugins. None of
this exists for non-plugin bots.

**Community Python: mmpy_bot.** `webhook_server.py` runs its own `aiohttp.web.Application` with
`POST /hooks/{webhook_id}`; the body becomes an `ActionEvent` (if `trigger_id` is present) or a
`WebHookEvent`, goes on `event_queue`, and the route awaits a `Future` in
`response_handlers[request_id]` **with no timeout**; `_obtain_responses_loop` polls
`response_queue` every 0.5 s; `NoResponse` → empty `200`, otherwise `web.json_response(result)`.
Handlers reply with `driver.respond_to_web(event, response)`. This is "callback as event + reply
channel keyed by request id" in its rawest form, failure mode included: a handler that never
replies hangs the request until Mattermost's 30 s timeout.

**aiommbot 0.4.x** (`aiommbot/channels/webhook.py`, `aiommbot/webhook/*`). A FastAPI
`WebhookChannel` decodes a Fernet-encrypted hook path segment, verifies signed tokens carried in
`context`/`state` with a max age and `strict | warn | ignore` enforcement, redacts before logging,
masks every failure as an empty **404**, awaits `dispatch_event(EventType.ACTION | DIALOG |
EXTERNAL, data)` inline and then **always** returns `JSONResponse({"status": "Ok"})`. The body is
never derived from the handler: 0.4.x cannot express `update`, `ephemeral_text` or dialog
`errors` — consistent with research 09, where all 11 bots reach for `update_post` and manual
`submission[...]` parsing instead — and it holds the request open with no deadline of its own.

## 7. "Queue reading": Slack Socket Mode as the analogue, and what Mattermost offers (nothing)

**Slack Socket Mode** is a callback queue over WebSocket. The app calls `apps.connections.open`
with an app-level token, receives a WebSocket URL, and gets envelopes `{envelope_id, type,
payload, accepts_response_payload, retry_attempt, retry_reason}`; it must ack each with
`{"envelope_id": ...}` and "when `accepts_response_payload` is true" may add a `payload` — the
same body it would have written to an HTTP response. Up to **10** concurrent connections; the
server sends `disconnect` (`refresh_requested`, ...) and the client reconnects. In
`python-slack-sdk`, `SocketModeClient.receive_messages()` enqueues TEXT frames on an
`asyncio.Queue` (`message_queue`), `process_messages()` pops and fans out to
`socket_mode_request_listeners`, and `send_socket_mode_response(SocketModeResponse(envelope_id,
payload))` writes the ack. Bolt's adapter (`adapter/socket_mode/internals.py`) is 20 lines:
`BoltRequest(mode="socket_mode", body=req.payload, headers=build_headers(req))` → `app.dispatch`
→ if `bolt_resp.status == 200` send `SocketModeResponse(envelope_id=req.envelope_id[,
payload=dict_body])`. The reply channel is identical to HTTP; only the carrier changed.

**Mattermost has no equivalent.** `server/public/model/websocket_message.go` lists no event for
interactive actions or dialog submissions — the only dialog-related event is the outbound
`open_dialog` push to the *user's* client. Callbacks reach an integration exclusively by the
server POSTing to the registered URL (in-process for plugins, HTTP otherwise). Confirmed by
absence in the constant list and by `DoActionRequest`'s two code paths.

**What a broker-backed callback queue would look like.** Because the answer must be in the HTTP
response, a queue can only sit *behind* the ingress: the replicable webhook process verifies,
decodes to `Event[InteractiveAction | DialogSubmission]`, publishes it with a reply address
(correlation id + reply topic), **waits** for the reply under a deadline < 30 s, then writes the
body — mmpy_bot's `response_handlers` future over a broker. It buys nothing for the HTTP response
(latency, a hop, a hard failure when no worker answers) and only helps for *post-ack* work, which
ADR-0005 already routes to workers. Slack's design works because Slack, not the app, owns the
queue. A recipe at most, not a Core feature.

## 8. Comparison table

| Framework | Callback = same event model? | Immediate HTTP answer | Deadline | Verification / replay | Webhook side packaging | Test without server |
|---|---|---|---|---|---|---|
| aiogram 3 | Yes — `feed_update` for polling and webhook | Handler **return value** (`TelegramMethod`) serialised to multipart/JSON; `{}` default; lost when `handle_in_background` | 55 s internal, then detach and answer `{}` (Telegram waits 60 s) | Secret-token header, constant-time compare, 401; in the aiohttp handler, no replay window | Same package; aiohttp is a core dep; other hosts DIY | pytest-aiohttp `aiohttp_client`, asserts 401 and `method` field |
| Slack Bolt | Yes — `App.dispatch(BoltRequest)` for HTTP and Socket Mode | Injected **`ack(...)`** whose accepted shape depends on request type; auto-ack in FaaS mode; 404 when unmatched | 3 s (platform); thread waits for `ack` up to `ack_timeout`, rest continues | Global middleware: HMAC v0, ±300 s, `compare_digest`, 401; skipped for socket mode | Adapters inside `slack_bolt.adapter`, host framework not a dependency, no extras | `app.dispatch(BoltRequest(...))` with generated signature; only Web API mocked |
| hikari (REST) | Partly — same payload/REST classes; **separate** one-listener-per-type dispatch | Listener **returns a response builder**; PING answered internally | 3 s (platform), 15 min follow-up token | In `InteractionServer`: Ed25519 over `timestamp+body`, 400 on failure | Same package; own aiohttp server or `on_interaction(body, sig, ts)` for embedding | Call `on_interaction` directly [test file not checked — unverified] |
| discord.py | N/A — gateway only | `InteractionResponse.*` over REST; `defer()` | 3 s / 15 min | — | — | — |
| Bot Framework | Yes — one `TurnContext` pipeline for inbound and proactive | Default empty 200/201; `invoke` → `InvokeResponse` from `turn_state` (501 if missing); `expect_replies` buffers activities into the body | 15 s (504 otherwise) | JWT in adapter (`authenticate_request`), 401 | Core + `botbuilder-integration-aiohttp` as a **separate distribution** | Not examined [unverified] |
| FastStream | n/a (HTTP is auxiliary) | `AsgiResponse` from route | — | — | ASGI callable, mountable in any host | Any ASGI `TestClient` |
| mmpy_bot | Yes — `ActionEvent`/`WebHookEvent` on the same queue | Future keyed by `request_id`; `NoResponse` → empty 200 | **None** (hangs until MM's 30 s) | Fixed path only [no signature check seen — unverified beyond the file read] | Own aiohttp server in the bot process | Not examined |
| aiommbot 0.4.x | Yes — same dispatchers | **Fixed** `{"status": "Ok"}`; `update`/`ephemeral_text`/`errors` impossible | None of its own | Fernet hook segment + signed tokens in `context`, max age, strict/warn/ignore, masked 404 | FastAPI in core extras | httpx2 ASGI transport |

## 9. Recommendation for the Mattermost adapter

**1. Callbacks are events in the same model — with a reply channel, not a second dispatcher.**
Every mature peer that has both a push transport and a callback transport (aiogram, Bolt, Bot
Framework) funnels them into one dispatch entry; hikari is the outlier and pays with two
programming models. Keep `Event[InteractiveAction]` and `Event[DialogSubmission]` routable by
`@router.on` exactly like `Event[Posted]` (ADR-0012/0013). The transport difference is confined to
`meta.reply`: present and typed for webhook-delivered events, absent (`None`) for WebSocket ones.

**2. Reply channel: typed per payload, single write, default ack, deadline-aware.** Neither
aiogram's untyped return value nor Bolt's one-`ack`-fits-all survives ADR-0006's typing bar. Bind
the reply type to the payload: `InteractiveAction` → `ActionReply` (`update: Post | None`,
`ephemeral_text: str | None`, `skip_slack_parsing`, `goto_location`); `DialogSubmission` →
`DialogReply` (`errors: Mapping[str, str]`, `error: str | None`, `form: Dialog | None`). One
`await event.meta.reply.send(...)` per event — Bolt, Discord and hikari all enforce a single
response (`is_done`, `NotFoundError`); a second call is a programming error. **Default ack**: a
handler that returns without replying, or an `Unhandled` outcome, produces an empty `200`
(Mattermost accepts an empty body for both callbacks; Bot Framework's 201 and Bolt's auto-ack are
the precedents). `Unhandled` must **not** become 404 as in Bolt: Mattermost turns any non-200 into a
visible client error, and the masked 404 is reserved for unauthenticated callers. **Deadline**:
`meta.reply.deadline` comes from a configured budget well under `OutgoingIntegrationRequestsTimeout`
(default 30 s; propose 10 s). As in aiogram, when it passes the transport writes the default ack and
lets the handler continue, its later `reply.send` raising `ReplyClosed` so the bug is observable; as
in Bolt, long work acks first and continues through the Runtime/workers (ADR-0005). Dialog field
validation is the one case where the body *must* carry content, so `DialogReply.errors` is the
load-bearing type.

**3. Verification is the transport's job; replay protection is a payload-level claim.** Mattermost
sends no signature and no timestamp to external URLs, so a generic middleware has nothing to check;
the credential is what *we* put in `context`/`state` when creating the button or dialog, as 0.4.x
already does (signed token with max age). Keep it inside the webhook transport, fail closed with the
masked empty 404 *before* decoding to an event, never log the body, and expose one policy setting
(`strict | warn`) owned by the Adapter — research 09 counts seven differently named settings for
this concept today. The Core never sees `trigger_id`; the Adapter documents its 30 s default
lifetime for handlers that open dialogs. Bolt's "skip verification when `mode == socket_mode`"
states the general rule: the transport that authenticated the carrier decides, not the router.

**4. Plugin boundary: an ASGI callable in the Mattermost adapter, no server in the Core.** Follow
Bolt/FastStream/hikari, not mmpy_bot: the adapter exposes `webhook_app(bot) -> ASGIApp` plus a
lower-level `handle_callback(body: bytes, headers) -> CallbackResponse` for non-ASGI hosts; the
application mounts it (`app.mount("/mm", ...)`, Litestar `@asgi(is_mount=True)`) or hands it to
uvicorn. The Core stays free of HTTP vocabulary (ADR-0002/0006), the ingress stays replicable
(ADR-0005), and the host framework is the application's choice. A hand-written ASGI callable adds
zero dependencies (Bolt's precedent), so a separate distribution or `aiommbot[webhook]` extra is
warranted only if we pull in Starlette/FastAPI for routing — I recommend not doing so.

**5. Testing: dispatch-level first, ASGI-level second, no sockets.** Mirror Bolt's scenario tests:
`aiommbot.testing` builds an `Event[InteractiveAction]` with a **recording reply channel** and
asserts the typed reply (`assert_replied(ActionReply(...))`, `assert_default_ack()`); the ASGI
layer is exercised separately with Starlette's `TestClient` (already present via `httpx2`) for
verification failures (masked 404), malformed JSON, deadline fallback and the exact body written.
Property tests on `ActionReply`/`DialogReply` serialisation against `PostActionIntegrationResponse`
/ `SubmitDialogResponse` cover the wire contract the server enforces with `IsValid()`.

## Sources

- aiogram: [`aiogram/webhook/aiohttp_server.py`](https://raw.githubusercontent.com/aiogram/aiogram/dev-3.x/aiogram/webhook/aiohttp_server.py), [`aiogram/dispatcher/dispatcher.py`](https://raw.githubusercontent.com/aiogram/aiogram/dev-3.x/aiogram/dispatcher/dispatcher.py), [Webhook guide](https://docs.aiogram.dev/en/latest/dispatcher/webhook.html), [`pyproject.toml`](https://raw.githubusercontent.com/aiogram/aiogram/dev-3.x/pyproject.toml), [`tests/test_webhook/test_aiohttp_server.py`](https://raw.githubusercontent.com/aiogram/aiogram/dev-3.x/tests/test_webhook/test_aiohttp_server.py)
- Slack Bolt: [`slack_bolt/app/app.py`](https://raw.githubusercontent.com/slackapi/bolt-python/main/slack_bolt/app/app.py), [`middleware/request_verification/request_verification.py`](https://raw.githubusercontent.com/slackapi/bolt-python/main/slack_bolt/middleware/request_verification/request_verification.py), [`slack_sdk/signature/__init__.py`](https://raw.githubusercontent.com/slackapi/python-slack-sdk/main/slack_sdk/signature/__init__.py), [`listener/thread_runner.py`](https://raw.githubusercontent.com/slackapi/bolt-python/main/slack_bolt/listener/thread_runner.py), [`context/ack/internals.py`](https://raw.githubusercontent.com/slackapi/bolt-python/main/slack_bolt/context/ack/internals.py), [`adapter/socket_mode/internals.py`](https://raw.githubusercontent.com/slackapi/bolt-python/main/slack_bolt/adapter/socket_mode/internals.py), [`slack_bolt/adapter/` listing](https://api.github.com/repos/slackapi/bolt-python/contents/slack_bolt/adapter), [`pyproject.toml`](https://raw.githubusercontent.com/slackapi/bolt-python/main/pyproject.toml), [`tests/scenario_tests/test_block_actions.py`](https://raw.githubusercontent.com/slackapi/bolt-python/main/tests/scenario_tests/test_block_actions.py), docs: [Acknowledging requests](https://docs.slack.dev/tools/bolt-python/concepts/acknowledge), [Lazy listeners](https://docs.slack.dev/tools/bolt-python/concepts/lazy-listeners), [Using Socket Mode](https://docs.slack.dev/apis/events-api/using-socket-mode), [`slack_sdk/socket_mode/aiohttp/__init__.py`](https://raw.githubusercontent.com/slackapi/python-slack-sdk/main/slack_sdk/socket_mode/aiohttp/__init__.py)
- Discord: [Receiving and Responding](https://docs.discord.com/developers/interactions/receiving-and-responding), [Interactions overview / security](https://docs.discord.com/developers/interactions/overview); hikari: [`hikari/impl/interaction_server.py`](https://raw.githubusercontent.com/hikari-py/hikari/master/hikari/impl/interaction_server.py), [`hikari/impl/rest_bot.py`](https://raw.githubusercontent.com/hikari-py/hikari/master/hikari/impl/rest_bot.py), [`hikari/interactions/command_interactions.py`](https://raw.githubusercontent.com/hikari-py/hikari/master/hikari/interactions/command_interactions.py), [`hikari/interactions/base_interactions.py`](https://raw.githubusercontent.com/hikari-py/hikari/master/hikari/interactions/base_interactions.py); discord.py: [Interactions API reference](https://discordpy.readthedocs.io/en/stable/interactions/api.html)
- Bot Framework: [`botbuilder/core/bot_framework_adapter.py`](https://raw.githubusercontent.com/microsoft/botbuilder-python/main/libraries/botbuilder-core/botbuilder/core/bot_framework_adapter.py), [`botbuilder/core/cloud_adapter_base.py`](https://raw.githubusercontent.com/microsoft/botbuilder-python/main/libraries/botbuilder-core/botbuilder/core/cloud_adapter_base.py), [`botbuilder/integration/aiohttp/cloud_adapter.py`](https://raw.githubusercontent.com/microsoft/botbuilder-python/main/libraries/botbuilder-integration-aiohttp/botbuilder/integration/aiohttp/cloud_adapter.py), [Basics of the Bot Framework](https://learn.microsoft.com/en-us/azure/bot-service/bot-builder-basics?view=azure-bot-service-4.0)
- ASGI hosting: FastStream [ASGI](https://faststream.ag2.ai/latest/getting-started/asgi/), [`faststream/asgi/app.py`](https://raw.githubusercontent.com/ag2ai/faststream/main/faststream/asgi/app.py), [Testing lifespan](https://faststream.ag2.ai/latest/getting-started/lifespan/test/); Litestar [handlers reference (`asgi`, `is_mount`, `copy_scope`)](https://docs.litestar.dev/latest/reference/handlers.html); FastAPI [Sub Applications - Mounts](https://fastapi.tiangolo.com/advanced/sub-applications/); Starlette [`docs/testclient.md`](https://raw.githubusercontent.com/encode/starlette/master/docs/testclient.md)
- Mattermost: [`server/channels/app/integration_action.go`](https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/integration_action.go), [`server/public/model/integration_action.go`](https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/integration_action.go), [`server/public/model/config.go`](https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/config.go) (`OutgoingIntegrationRequestsDefaultTimeout = 30`), [`server/public/model/websocket_message.go`](https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/websocket_message.go), docs: [Interactive messages](https://developers.mattermost.com/integrate/plugins/interactive-messages/), [Interactive dialogs](https://developers.mattermost.com/integrate/plugins/interactive-dialogs/), [Plugin server best practices (authentic HTTP requests)](https://developers.mattermost.com/integrate/plugins/components/server/best-practices/), [mattermost-plugin-starter-template `server/api.go`](https://raw.githubusercontent.com/mattermost/mattermost-plugin-starter-template/master/server/api.go)
- mmpy_bot: [`mmpy_bot/webhook_server.py`](https://raw.githubusercontent.com/attzonko/mmpy_bot/main/mmpy_bot/webhook_server.py), [`mmpy_bot/event_handler.py`](https://raw.githubusercontent.com/attzonko/mmpy_bot/main/mmpy_bot/event_handler.py)
- aiommbot 0.4.x (local checkout): `aiommbot/channels/webhook.py`, `aiommbot/webhook/{config,verifier,security,runtime}.py`, `pyproject.toml`; this repo: `docs/adr/0005`, `0012`, `0013`, `docs/research/09-usage-mining-0.4.x-bots.md`

**Not independently verified in this pass:** hikari's and botbuilder's own test harnesses for the
HTTP surface; whether mmpy_bot performs any authenticity check on `/hooks/{webhook_id}` beyond the
path; matterbridge (not examined — it bridges messages over the WebSocket/REST API and, as far as
this pass could tell, has no interactive-callback surface); Mattermost Apps framework call
semantics.
