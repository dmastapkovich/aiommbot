# Mattermost WebSocket protocol — facts for a fault-tolerant client

Status: complete (2026-09-02). Sources are `master` of github.com/mattermost/mattermost unless noted; constants are quoted verbatim from source. "unverified" marks anything I could not confirm from a primary source.

## 1. Connection, auth, envelope, request/response

**Endpoint.** Route is registered under the API root as `"/{websocket:websocket(?:\\/)?}"`, i.e. `GET /api/v4/websocket` (trailing slash tolerated). Upgrader uses `ReadBufferSize`/`WriteBufferSize = model.SocketMaxMessageSizeKb` and `CheckOrigin = c.App.OriginChecker()` — so `Origin` must pass `ServiceSettings.AllowCorsFrom` rules (a bot should simply not send an `Origin` header). If the handshake arrives as HTTP/1.0 the server logs a proxy-misconfiguration warning. [`server/channels/api4/websocket.go`]

**Authentication — two options** (docs: "authenticated using the standard API authentication methods (by a cookie or with an explicit Authorization header) or through an authentication challenge" [`api/v4/source/introduction.yaml`]):

1. **Header on the handshake.** `ParseAuthTokenFromRequest` accepts cookie `MMAUTHTOKEN`, `Authorization: Bearer <tok>` or `Authorization: token <tok>` (case-insensitive prefixes), query `access_token=`, plus cloud/remote-cluster headers. [`server/channels/app/authentication.go`] If a session exists, the connection is registered in the hub immediately; the hub sends `hello` on registration when `IsBasicAuthenticated() && reuseCount == 0`. [`server/channels/app/platform/web_hub.go`]
2. **`authentication_challenge` message** after upgrade: `{"seq":1,"action":"authentication_challenge","data":{"token":"..."}}` → reply `{"status":"OK","seq_reply":1}`, then `HubRegister(conn)`, `SetStatusOnline`, and `hello` follows. An unauthenticated socket that has not set a token within `authCheckInterval = 5 * time.Second` is closed (`websocket.authTicker: did not authenticate`). Non-auth actions before auth get `api.web_socket_router.not_authenticated.app_error` (401). Binary frames from an unauthenticated connection close the socket ("binary frames require authentication", MM-68222). [`server/channels/app/platform/websocket_router.go`, `web_conn.go`]

The Go reference client uses option 2 for `NewWebSocketClient*` and option 1 (`Authorization: Bearer`) for `NewReliableWebSocketClientWithDialer`. [`server/public/model/websocket_client.go`]

**`hello` event.** Built by `createHelloMessage()`; `data` fields: `server_version` = `fmt.Sprintf("%v.%v.%v.%v", model.CurrentVersion, model.BuildNumber, ClientConfigHash(), ee)` (4 dot-separated parts; last is enterprise bool), `connection_id`, `server_hostname` (omitted if `os.Hostname()` fails). [`web_conn.go`]

**Request envelope** (`WebSocketRequest`): `seq int64` ("A counter which is incremented for every request made"), `action string`, `data map[string]any`. Server validation: empty action → `api.web_socket_router.no_action.app_error`; `seq <= 0` → `api.web_socket_router.bad_seq.app_error`; unknown action → `api.web_socket_router.bad_action.app_error`. [`server/public/model/websocket_request.go`, `websocket_router.go`]

**Response envelope** (`WebSocketResponse`): `status` (`"OK"` / `"FAIL"`), `seq_reply` (omitempty), `data` (omitempty), `error *AppError` (omitempty, detailed part wiped with `WipeDetailed()`). Responses carry no `event` key — clients distinguish them by presence of `seq_reply`. [`server/public/model/websocket_message.go`]

**Registered actions** (server `wsapi` + router):

| action | data | returns |
|---|---|---|
| `authentication_challenge` | `token` | OK |
| `ping` | – | `{"text":"pong","version":CurrentVersion,"server_time":ms,"node_id":""}` |
| `user_typing` | `channel_id`, `parent_id` | requires `PermissionCreatePost`; can fail `api.websocket_handler.server_busy.app_error` |
| `get_statuses` | – | `{user_id: status}` for all users |
| `get_statuses_by_ids` | `user_ids []` | `{user_id: status}`; missing ids → error `user_ids` |
| `user_update_active_status` | `user_is_active`, `manual` | sets online/away |
| `presence` | `channel_id` / `team_id` / `thread_channel_id`+`is_thread_view` | OK; sets the connection's active channel/team (affects typing/reaction filtering) |
| `posted_notify_ack` | `post_id`, `user_agent`, `status`, `reason`, `data` | metrics only |

[`server/channels/wsapi/system.go`, `status.go`, `user.go`, `websocket_router.go`; TS names in `webapp/platform/client/src/websocket.ts`]. Note the Go client still labels presence `"presence_indicator"` while the model constant is `WebsocketPresenceIndicator = "presence"` — use `presence`.

## 2. Reliable WebSocket / resume

**Query params.** Client reconnects with `?connection_id=<id>&sequence_number=<n>` (TS client also adds `posted_ack=true` and `disconnect_err_code=<code>`; valid codes 1000–1016, 4000, 4001). `PopulateWebConnConfig`: `connection_id` must satisfy `model.IsValidId` (26-char id) else error `invalid connection id`; `sequence_number` is required and parsed with `strconv.ParseInt(seqVal, 10, 0)`. Then `CheckWebConn(userId, connID, seqNum)`; if nothing is found a fresh `model.NewId()` connection id is issued. [`web_conn.go`, `api4/websocket.go`]

**Server buffers.** Per connection: `sendQueueSize = 256` (active queue channel) and `deadQueueSize = 128` (ring buffer of already-sent events, indexed by `seq`). On disconnect the hub marks the `WebConn` inactive but keeps it; `RemoveInactiveConnections` deletes it once `!Active && now-lastUserActivityAt > staleThreshold`, where `staleThreshold = inactiveConnReaperInterval = 5 * time.Minute`. So the resume window is roughly **5 minutes and ≤128 missed events** (plus whatever is still in the 256-slot active queue). [`web_hub.go`, `web_conn.go`]

**Resume algorithm** (start of `writePump`, when `wc.Sequence != 0`):
- `isInDeadQueue(seq)` → `drainDeadQueue(index)` replays from that seq; metric `reconnectFound`.
- else if `hasMsgLoss()` (gap not recoverable) → `clearDeadQueue()`, `SetConnectionID(model.NewId())`, `Sequence = 0`, a new `hello` is sent (and put in the dead queue); metric `reconnectNotFound`. **The client detects this by `hello.data.connection_id != previous id` and must do a full state resync.**
- else (no loss) → metric `reconnectLossless`, no hello.
`hello` is not re-sent on a successful resume (`reuseCount > 0`). [`web_conn.go`, `web_hub.go`]

**HA.** Since PR #29489 (MM-61904, v10.x) the node checks other cluster nodes' active/dead queues for the connection id; edge case of queues spread over several nodes is explicitly not handled. [github.com/mattermost/mattermost/pull/29489]

**Config flag.** `ServiceSettings.EnableReliableWebSockets` no longer exists in `model/config.go` (checked master). Docs: "deprecated, and the ability to buffer messages during a connection loss has been promoted to general availability from Mattermost v6.3." Treat as always-on for ≥6.3. [docs.mattermost.com deprecated-configuration-settings]

## 3. Heartbeat, deadlines, official client reconnect behaviour

**Server side** (`web_conn.go`):
```
writeWaitTime = 30 * time.Second
pongWaitTime  = 100 * time.Second
pingInterval  = (pongWaitTime * 6) / 10      // 60s
```
The server **sends WS ping frames every 60 s**, sets `SetReadDeadline(pongWaitTime)` and refreshes it in `SetPongHandler` (which also triggers `SetStatusAwayIfNeeded`). A client that does not answer pongs for 100 s is dropped with `websocket.NextReader: closing websocket ... i/o timeout`. Writes have a 30 s deadline. `SetReadLimit(model.SocketMaxMessageSizeKb)` where `SocketMaxMessageSizeKb = 8 * 1024` → **client→server frames are capped at 8192 bytes** (name is misleading). Client ping frames are answered by gorilla's default handler (implicit; issue #17197 reported drops on 5.33 — resolution unverified).

**Go client** (`websocket_client.go`): passive. `SetPingHandler` resets a watchdog of `time.Second * (60 + PingTimeoutBufferSeconds)` = 65 s (`PingTimeoutBufferSeconds = 5`); expiry signals `PingTimeoutChannel`. No reconnect: "a closed client should not be reused again. Rather a new client should be created anew." `Sequence` starts at 1 and `wsc.Sequence++` after each send.

**TS client** (`webapp/platform/client/src/websocket.ts`) — the de-facto reference for a resilient client:
```
maxWebSocketFails: 7, minWebSocketRetryTime: 3000, maxWebSocketRetryTime: 300000,
reconnectJitterRange: 2000, clientPingInterval: 30000
clientPingTimeoutErrCode = 4000, clientSequenceMismatchErrCode = 4001
```
- **Backoff** (onclose): `retryTime = minWebSocketRetryTime`; if `connectFailCount > maxWebSocketFails` then `min * connectFailCount²`, capped at `max`, plus `random(0..jitter)`. `closeCallback`/listeners fire on every close.
- **Application-level ping**: sends `{"action":"ping"}` immediately on open and every 30 s; `waitingForPong` cleared by the `seq_reply` callback; if still waiting at the next tick → close with 4000 and reconnect. (This is in addition to the server's frame pings.)
- **Sequence check**: constructor `serverSequence = 0`, `responseSequence = 1`. For each event: `if (msg.seq !== this.serverSequence)` → log `missed websocket event, act_seq=… exp_seq=…`, close with 4001 and reconnect (server will replay from the dead queue); otherwise `serverSequence = msg.seq + 1`.
- **hello**: if stored `connectionId !== '' && !== msg.data.connection_id` → `missedEventCallback` + `missedMessageListeners`, `serverSequence = 0`; then store `connection_id`, `server_hostname`. Gotcha (issue #30388): the reset only runs when a missed-message listener is registered — otherwise infinite reconnect loops.
- `onopen`: `connectFailCount > 0` → `reconnectCallback`, else `firstConnectCallback`.
- `sendMessage` silently drops if socket not `OPEN`; callbacks keyed by `seq`.
- **Post ordering**: the client does no ordering; the webapp (`webapp/channels/src/actions/websocket_actions.ts`) on reconnect runs `syncPostsInChannel(channelId, mostRecentPost.create_at)` (falls back to `getPosts`), re-fetches channels/members, threads since, and debounces bursts of `posted` (queue after 4 posts within 100 ms).

## 4. Event catalog and envelope

**Wire shape** (`webSocketEventJSON`, `server/public/model/websocket_message.go`):
```json
{"event": "<name>", "data": {...}, "broadcast": {...}, "seq": <int64>}
```
`seq` is the per-connection server counter (starts at 0 for a fresh connection; the hello is seq 0). `broadcast` (`WebsocketBroadcast`):
```
omit_users map[string]bool | user_id | channel_id | team_id | connection_id | omit_connection_id
contains_sanitized_data, contains_sensitive_data, required_permissions, broadcast_hooks, broadcast_hook_args (all omitempty)
```
`ReliableClusterSend` is `json:"-"` (server-internal). The server already applies these filters in `ShouldSendEvent` before sending (`connection_id` → only that connection; `omit_connection_id`; `user_id`; `omit_users`; `channel_id` membership; `team_id`; guest rules), so a client sees them only as metadata. For a bot they are useful for: `broadcast.channel_id` (cheap routing without parsing `post`), `broadcast.user_id` (event targeted at the bot itself — e.g. `ephemeral_message`), and `broadcast.omit_users` (contains the actor's id for `typing`). They are **not** a dedup key — dedup on `(event, post.id/…)` or on `seq` within a connection id.

**Event names** (complete `WebsocketEvent*` block on master, 2026-09): `typing, posted, post_edited, post_deleted, post_unread, channel_converted, channel_created, channel_deleted, channel_restored, channel_updated, channel_member_updated, channel_scheme_updated, direct_added, group_added, new_user, added_to_team, leave_team, update_team, delete_team, restore_team, update_team_scheme, user_added, user_updated, user_role_updated, memberrole_updated, user_removed, preference_changed, preferences_changed, preferences_deleted, ephemeral_message, status_change, hello, authentication_challenge, reaction_added, reaction_removed, response, emoji_added, multiple_channels_viewed, plugin_statuses_changed, plugin_enabled, plugin_disabled, role_updated, license_changed, config_changed, open_dialog, guests_deactivated, user_activation_status_change, received_group, received_group_associated_to_team, received_group_not_associated_to_team, received_group_associated_to_channel, received_group_not_associated_to_channel, group_member_deleted, group_member_add, sidebar_category_created, sidebar_category_updated, sidebar_category_deleted, sidebar_category_order_updated, cloud_subscription_changed, thread_updated, thread_follow_changed, thread_read_changed, first_admin_visit_marketplace_status_received, draft_created, draft_updated, draft_deleted, post_acknowledgement_added, post_acknowledgement_removed, persistent_notification_triggered, hosted_customer_signup_progress_updated, channel_bookmark_created, channel_bookmark_updated, channel_bookmark_deleted, channel_bookmark_sorted, channel_access_control_updated, permission_policy_updated, team_access_control_updated, presence, posted_notify_ack, scheduled_post_created, scheduled_post_updated, scheduled_post_deleted, custom_profile_attributes_field_created, custom_profile_attributes_field_updated, custom_profile_attributes_field_deleted, custom_profile_attributes_values_updated, content_flagging_report_value_updated, job_updated, recap_updated, post_translation_updated, post_revealed, post_burned, burn_on_read_all_revealed, board_created, view_created, view_updated, view_deleted, view_sorted, property_field_created, property_field_updated, property_field_deleted, property_values_updated, file_download_rejected, file_upload_rejected, show_toast, shared_channel_remote_updated, channel_join_request_created, channel_join_request_updated`. Note: there is **no** `channel_viewed` any more — it is `multiple_channels_viewed`. Plugins add `custom_<pluginid>_<name>` via `PublishWebSocketEvent`. Version note: many of the tail entries (boards/views, burn-on-read, recap, translation, join requests) are 2025–2026 additions; the reference list must be treated as open-ended.

**`posted` payload** (`server/channels/app/notification.go` `SendNotifications` + broadcast hooks): `channel_type`, `channel_display_name`, `channel_name`, `sender_name` (`@username` via `GetSenderName(model.ShowUsername, EnablePostUsernameOverride)`; webhook override applied only if the setting is on), `team_id` (empty string for DMs/GMs), `set_online` (bool — hint to mark the sender online), optional `otherFile: "true"`, `image: "true"`, `mentions` (JSON string array, hook `broadcastAddMentions`), `followers` (hook), `should_ack: true` (hook, only when the client connected with `posted_ack=true`), and `post`. **`data.post` is a JSON string, not an object** — the server does `post.ToJSON()` and `msg.Add("post", updatedPostJSON)` (`server/channels/app/web_broadcast_hooks.go`, `post.go` for `post_edited`/`ephemeral_message`); the webapp reads it with `JSON.parse(msg.data.post)` for `posted`, `post_edited`, `post_deleted`. The exact line adding the initial `post` in `SendNotifications` was not surfaced by my fetch (the file was truncated) — format is confirmed by the hook/edit paths and the webapp consumer. Same double encoding applies to `mentions`. Hooks run per recipient connection (permalink previews, channel mentions, burn-on-read sanitization), so two bots may receive slightly different `post` JSON for the same event.

## 5. Rate limits / backpressure

- **Per-connection send queue**: `sendQueueSize = 256`. Broadcast is non-blocking: if the channel is full the hub logs `webhub.broadcast: cannot send, closing websocket for user` and `closeAndRemoveConn` — the connection is **removed outright (not kept as inactive)**, so a slow reader loses the resume window too. [`web_hub.go`]
- Soft thresholds: at `sendSlowWarn = 50%` of the queue, `typing`, `status_change`, `multiple_channels_viewed` events are **dropped** (`websocket.slow: dropping message`); at `sendFullWarn = 95%` a `websocket.full` warning is logged (rate-limited to once per `websocketSuppressWarnThreshold = time.Minute`). [`web_conn.go`]
- Hub broadcast queue `broadcastQueueSize = 4096` (server-wide per hub). [`web_hub.go`]
- Frame size: inbound ≤ 8192 bytes (`SetReadLimit(SocketMaxMessageSizeKb)`); outbound events are not size-limited by the socket layer, but REST `ServiceSettings.MaximumPayloadSizeBytes` default `300000` bounds request bodies. [`web_conn.go`, `model/config.go`]
- **REST rate limiting** (`RateLimitSettings`): `Enable=false` (default), `PerSec=10`, `MaxBurst=100`, `MemoryStoreSize=10000`, `VaryByRemoteAddr=true`, `VaryByUser=false`, `VaryByHeader=""`. The WS handshake is an HTTP request and counts when enabled; a reconnect storm from one IP (`VaryByRemoteAddr`) can be throttled with 429. [`model/config.go`]
- `user_typing` can return `api.websocket_handler.server_busy.app_error` when the server is in busy mode.

## 6. Multi-instance caveats

- Broadcast semantics are **per connection, not per user**: the hub iterates every active `WebConn` and `ShouldSendEvent` filters only by user/channel/team/permissions. Two sockets for the same bot account (two replicas, or one replica mid-reconnect with a stale resumable connection) **both receive every event**. There is no per-user connection cap in the hub. [`web_hub.go`, `web_conn.go`]
- In an HA cluster each node broadcasts to its own connections; `connection_id` resume across nodes works since PR #29489 (v10.x) with the noted edge case.
- Official guidance for horizontally scaled processing is the plugin surface: `MessageHasBeenPosted(c, post)`, `MessageWillBePosted`, `MessageHasBeenUpdated`, `OnWebSocketConnect/Disconnect(webConnID, userID)`, `WebSocketMessageHasBeenPosted(webConnID, userID, req)`, all invoked on the node handling the request; plugins publish via `PublishWebSocketEvent`. There is no documented server-side consumer-group/ack mechanism for WS clients — dedup and leader election are the client's job. [developers.mattermost.com server reference]

## 7. Known gotchas

- **Idle drops behind proxies.** Official nginx block uses `proxy_read_timeout 90s` (older configs `600s`) for `location ~ /api/v[0-9]+/(users/)?websocket$` and requires `proxy_http_version 1.1` + `Upgrade`/`Connection "upgrade"`. Because the server pings only every 60 s, any hop with an idle timeout ≤ 60 s (AWS ALB default 60 s, docs issue #8930) races the ping and drops the socket. `websocket.NextReader: closing websocket … i/o timeout` in server logs is considered benign by Mattermost staff (forum #14335, GH #21515). [docs.mattermost.com setup-nginx-proxy]
- **Session expiry is silent.** `IsBasicAuthenticated` re-fetches the session when `ExpiresAt` passes; if `GetSession(token)` fails it clears the token and returns false, and `ShouldSendEvent` then returns false — the socket **stays open but receives nothing**. Bot/personal access tokens don't expire, but a revoked token or a login-session token (`SessionLengthWebInHours`, `SessionIdleTimeoutInMinutes` default 43200) degrades into a silent connection. Because `ping` also requires auth, a `not_authenticated` error on the periodic `ping` is the practical detector. [`web_conn.go`]
- **Own posts arrive as `posted`.** The event is channel-broadcast; `broadcast.omit_users` is not set for posts. Filter on `post.user_id == bot_id` (after `JSON.parse`) and/or `post.props.from_bot`/`from_webhook`; never on `sender_name` (display handle, override-able).
- **`sender_name`** is `@username` unless `EnablePostUsernameOverride` and webhook override props apply; **`set_online`** only carries the sender's presence hint (false for e.g. auto-responder/API posts with `set_online=false`).
- `hello.server_version` has four dot-separated parts (version.build.confighash.enterprise) — do not parse as semver.
- `presence`/`user_typing`/reactions filtering: `typing`, `reaction_added/removed` are delivered only if the connection's active channel/thread (set via `presence`) matches or the user is in the channel (`notInChannel && notInThread` check) — bots that never send `presence` still receive them for channels they belong to.
- Client-initiated WS ping frames: issue #17197 (5.33) reported silent drops; status unverified — prefer the JSON `ping` action.
- `sendMessage` before `OPEN` is dropped silently in the TS client; the Go client surfaces write errors on `ListenError` — a new client must queue or fail explicitly.

## Design implications for a client

- Authenticate on the handshake (`Authorization: Bearer`) so `hello` arrives immediately and the 5 s `authTicker` cannot bite; keep `authentication_challenge` only as a fallback for proxies that strip headers.
- Persist `connection_id` and `last_seq` in memory per connection; reconnect with `?connection_id=&sequence_number=<last_seq+1>` (TS semantics: expected next seq). Treat a `hello` whose `connection_id` differs as "state lost → full resync" (re-list channels, fetch posts since last processed `create_at`). Always reset the sequence on id change regardless of listeners (avoid issue #30388).
- Resume budget is ~5 min / 128 events; anything longer or burstier must go through REST backfill, so make the resync path first-class, not an edge case.
- Enforce `seq` continuity: on gap, close with 4001 and reconnect (server replays); do not skip.
- Answer server ping frames (library default) **and** send the JSON `ping` action every ~30 s with a pong deadline (TS uses the next 30 s tick); server pongs carry `server_time` — usable for clock skew. Assume a 100 s server read deadline and ≤60 s proxy idle timeouts.
- Reconnect backoff: 3 s flat for the first 7 failures, then `3s·n²` capped at 300 s, plus 0–2 s jitter; count "no hello within N s" as a failure.
- Parse `data.post` (and `mentions`) as JSON strings; route on `broadcast.channel_id`/`data.team_id` before parsing when possible; drop own posts by `post.user_id`, never by `sender_name`.
- Dedup key: `(connection_id, seq)` for exact-once within a connection, plus `(event, post.id, post.update_at|edit_at)` across reconnects — a resumed dead queue never duplicates, but a full resync can.
- Multiple replicas → every replica gets every event; add an idempotency store (e.g. Mongo compare-and-set on `post.id`) or single-active-consumer leasing.
- Drain the socket fast: put events into an internal bounded queue and process asynchronously; a full 256-slot server queue is a hard disconnect with loss of the resume window.
- Watch for the "silent" state: if no event and no `pong` for > pong deadline, or `ping` returns `api.web_socket_router.not_authenticated.app_error`, tear down and re-authenticate (token may have been revoked).
- Cap outbound frames at 8 KiB; the only outbound actions a bot needs are `ping`, `user_typing`, `get_statuses_by_ids`, optionally `presence`.
- Keep the event-name set open (`str` subtype / enum with fallback), map unknown events to a generic handler; the catalog grows every release.
- Log `connection_id`, `seq`, event name, `post.id` — never the token, `data.post` body, or `server_hostname` at INFO in multi-tenant logs.

## Sources

Server (github.com/mattermost/mattermost, master):
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/web_conn.go — constants, ping/pong, dead queue, `ShouldSendEvent`, auth checks, `PopulateWebConnConfig`, `createHelloMessage`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/web_hub.go — `broadcastQueueSize`, `inactiveConnReaperInterval`, register/hello, full-queue close, `CheckConnResult`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/websocket_router.go — request validation, `authentication_challenge`, `presence`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/api4/websocket.go — route, upgrader, query params
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/wsapi/system.go, status.go, user.go — `ping`, `get_statuses*`, `user_typing`, `user_update_active_status`, `posted_notify_ack`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/notification.go — `posted` data fields
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/web_broadcast_hooks.go — hooks, `msg.Add("post", updatedPostJSON)`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/post.go — `post_edited`/`ephemeral_message` payloads
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/authentication.go — `ParseAuthTokenFromRequest`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/websocket_message.go — event catalog, `WebsocketBroadcast`, `WebSocketResponse`, `webSocketEventJSON`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/websocket_request.go
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/websocket_client.go — Go client, `SocketMaxMessageSizeKb`, `PingTimeoutBufferSeconds`
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/public/model/config.go — `RateLimitSettings`, `MaximumPayloadSizeBytes`, session settings, absence of `EnableReliableWebSockets`
- https://raw.githubusercontent.com/mattermost/mattermost/master/api/v4/source/introduction.yaml — documented WebSocket API text
- https://github.com/mattermost/mattermost/pull/29489 — reliable websockets in HA

Clients:
- https://raw.githubusercontent.com/mattermost/mattermost/master/webapp/platform/client/src/websocket.ts — TS client constants, backoff, ping, sequence/hello handling
- https://raw.githubusercontent.com/mattermost/mattermost/master/webapp/channels/src/actions/websocket_actions.ts — `JSON.parse(msg.data.post)`, reconnect resync

Docs / issues:
- https://docs.mattermost.com/administration-guide/configure/deprecated-configuration-settings.html — `EnableReliableWebSockets` deprecated, GA since v6.3
- https://docs.mattermost.com/deployment-guide/server/setup-nginx-proxy.html — nginx websocket block (`proxy_read_timeout 90s`)
- https://developers.mattermost.com/integrate/reference/server/server-reference/ — plugin hooks
- https://github.com/mattermost/mattermost/issues/30388 — hello/connection-id reset gotcha
- https://github.com/mattermost/mattermost/issues/17197 — client ping frames (resolution unverified)
- https://github.com/mattermost/mattermost/issues/23332 — raw `posted` event dump (`post` as string, `sender_name`, `set_online`)
- https://github.com/mattermost/docs/issues/8930 — ALB 60 s idle timeout vs 60 s server ping
- https://forum.mattermost.com/t/many-errors-in-logs-websocket-nextreader-closing-websocket/14335 and https://github.com/mattermost/mattermost-server/issues/21515 — benign `i/o timeout` logs
