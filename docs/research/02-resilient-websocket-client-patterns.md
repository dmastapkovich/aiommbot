# Resilient long-lived WebSocket consumer patterns (chat-bot gateway)

Research date: 2026-09-02. Sources are primary (library source at pinned URLs, vendor docs, RFCs).
Values quoted from source are marked with backticks; anything I could not open is marked **[unverified]**.

---

## 1. Slack Socket Mode (`slack_sdk.socket_mode`)

**Protocol (docs.slack.dev, "Using Socket Mode")**
- The client obtains a WS URL by calling `apps.connections.open` with an *app-level* token in the `Authorization`
  header; the response is `{"ok": true, "url": "wss://wss.slack.com/link/?ticket=..."}`. "The WebSocket URL you
  listen to is not static. The URL is created at runtime" and "refreshes regularly". Method rate tier: "Tier 3: 50+ per minute".
- First frame is `hello` with `num_connections`, `connection_info.app_id` and `debug_info`
  (`host`, `started`, `build_number`, `approximate_connection_time` — seconds until the next forced refresh, example `3600`).
- Server-initiated `disconnect` frames carry `reason`: `"warning"` (sent ~10 s before disconnect),
  `"refresh_requested"`, `"link_disabled"` (Socket Mode toggled off), plus `debug_info`. The Node SDK maintainers
  concluded the client should reconnect for **all** `type:disconnect` messages (incl. `too_many_websockets`).
- "Socket Mode allows your app to maintain *up to 10* open WebSocket connections at the same time" — the docs recommend
  multiple connections for graceful restarts.
- Envelope: `type`, `envelope_id`, `payload`, `accepts_response_payload`, `retry_attempt`, `retry_reason`
  (`slack_sdk/socket_mode/request.py::SocketModeRequest`). Ack = send `{"envelope_id": ...}` back; the SDK example acks
  *before* doing Web API work. The 3-second window and retry schedule come from the Events API docs ("respond ... *within
  three seconds*"; "we'll retry three times, backing off exponentially" — nearly immediately, after 1 min, after 5 min;
  `retry_reason` ∈ {`http_timeout`, `http_error`}). Dedup key is the payload `event_id` ("globally unique across all
  workspaces"), not the retry counter. Socket-Mode-specific statement of the 3 s limit: **[unverified — only stated for HTTP Events API]**.

**Client mechanics (`slack_sdk/socket_mode/client.py`, `aiohttp/__init__.py`, `builtin/client.py`)**
- Base class: `message_queue` + `message_listeners` (raw `(client, message_dict, raw_message)`) vs
  `socket_mode_request_listeners` (`(client, SocketModeRequest)`); `process_message()` runs
  `if message.get("type") == "disconnect": connect_to_new_endpoint(force=True)`; listeners run via
  `self.message_workers.submit(_run_message_listeners)` (ThreadPoolExecutor).
- `connect_to_new_endpoint(force)`: `connect_operation_lock.acquire(blocking=True, timeout=5)`, then
  `self.wss_uri = self.issue_new_wss_url()` + connect. `issue_new_wss_url()` on `ratelimited` sleeps
  `int(e.response.headers.get("Retry-After", "30"))` and retries.
- aiohttp flavour defaults: `ping_interval: float = 5`, `auto_reconnect_enabled: bool = True`, `trace_enabled: bool = False`.
  `ws_connect(..., autoping=False, heartbeat=self.ping_interval)`; it sends its **own** payload pings
  `"sdk-ping-pong:{t}"` and records `last_ping_pong_time` on PONG. `monitor_current_session` runs every `ping_interval`
  and declares the link stale when `disconnected_seconds >= (self.ping_interval * 4)` (20 s), then
  `connect_to_new_endpoint()`. `receive_messages` reconnects on `WSMsgType.CLOSE`, sleeps `consecutive_error_count`
  seconds on repeated errors, and the `connect()` retry loop sleeps `ping_interval` between attempts. Session identity:
  `"s_" + str(hash(session))` — stale tasks compare `session != self.current_session` and exit.
- builtin flavour defaults: `ping_interval=5`, `receive_buffer_size=1024`, `concurrency=10`, monitor thread
  `_monitor_current_session` at `ping_interval`, message processor `IntervalRunner` at `0.001` s; reconnect is immediate
  (no backoff).

Take-away: Slack pushes the reconnect burden to the server (`disconnect` with warning + fresh URL per connect), uses an
**app-level ack with redelivery**, and the SDK uses a separate *monitor* loop rather than trusting the transport's ping.

## 2. Discord Gateway (discord.py `gateway.py`/`client.py`/`backoff.py`, hikari `impl/shard.py`)

**Protocol (docs.discord.com)**
- HELLO carries `heartbeat_interval` (ms). "Wait `heartbeat_interval * jitter` where `jitter` is any random value between
  0 and 1, then send its first Heartbeat" (spreads heartbeats across shards).
- "If a client does not receive a heartbeat ACK between its attempts at sending heartbeats ... immediately terminate the
  connection with any close code besides `1000` or `1001`, then reconnect and attempt to Resume."
- Send-side limit: "120 gateway events per connection every 60 seconds ... Apps that surpass the limit are immediately disconnected."
- RESUME needs `session_id` + `resume_gateway_url` (from READY) + last `s`; server replays missed events then `Resumed`.
  `Invalid Session` (op 9) with `d=false` → disconnect and re-IDENTIFY; `Reconnect` (op 7) → resume.
- IDENTIFY concurrency: "limit of 1 per 5 seconds per shard bucket", `rate_limit_key = shard_id % max_concurrency`,
  daily `session_start_limit {total, remaining, reset_after}`.
- Close codes (reconnect column): 4000, 4001, 4002, 4003, 4005, 4007, 4008, 4009 → `true`;
  **4004 auth failed, 4010, 4011, 4012, 4013, 4014 → `false`** (fatal).

**discord.py**
- `KeepAliveHandler` (thread): `heartbeat_timeout = ws._max_heartbeat_timeout` ← `ConnectionState.heartbeat_timeout =
  options.get('heartbeat_timeout', 60.0)`. Loop: `if self._last_recv + self.heartbeat_timeout < time.perf_counter()` →
  log "Shard ID %s has stopped responding to the gateway. Closing and restarting." → `self.ws.close(4000)` via
  `run_coroutine_threadsafe`. `ack()` computes `latency = ack_time - _last_send`; warns `"Can't keep up ... %.1fs behind"`
  when > 10 s; also warns when the heartbeat send itself is blocked > 10 s (event-loop starvation detector).
- `poll_event()` = `socket.receive(timeout=self._max_heartbeat_timeout)`; timeout → `ReconnectWebSocket`.
  `INVALIDATE_SESSION`: resumable → close+resume; not resumable → `sleep(5.0)`, reset `sequence`/`session_id`, IDENTIFY.
- `_can_handle_close()`: not resumable for `1000, 4004, 4010, 4011, 4012, 4013, 4014`; everything else reconnects.
- `GatewayRatelimiter(count=110, per=60.0)` — client keeps a 10-event margin under Discord's 120 for heartbeats.
- `client.connect()`: `backoff = ExponentialBackoff()`; `ws_params = {initial, shard_id, sequence, resume, session, gateway}`;
  catches `OSError, HTTPException, GatewayNotFound, ConnectionClosed, aiohttp.ClientError, asyncio.TimeoutError`;
  comment "Always try to RESUME the connection / If the connection is not RESUME-able then the gateway will invalidate the
  session"; `4014 → PrivilegedIntentsRequired`; `if exc.code != 1000: await self.close(); raise`; comment "sometimes,
  discord sends us 1000 for unknown reasons so we should reconnect regardless and rely on is_closed instead";
  `retry = backoff.delay(); await asyncio.sleep(retry)`.
- `ExponentialBackoff(base=1, integral=False)`: delay ∈ `[0, base * 2**exp]` (full jitter via `random.uniform`),
  `_exp` capped at `_max = 10` (max 1024 s), `_reset_time = base * 2**11` — exponent resets to 1 if no retry in 2048 s.

**hikari `impl/shard.py`**
- `_BACKOFF_WINDOW: 30.0`, `_BACKOFF_BASE: 1.85`, `_BACKOFF_CAP: 60.0`; backoff only applies when
  `time.time() - last_started_at < _BACKOFF_WINDOW` (a connection that lived > 30 s resets the counter).
- `_RESUME_CLOSE_CODE: 3_000` — comment: "Discord seems to invalidate sessions if I send a 1xxx."
- `_RECONNECTABLE_CLOSE_CODES = {UNKNOWN_ERROR, DECODE_ERROR, INVALID_SEQ, SESSION_TIMEOUT, RATE_LIMITED}`; others raise
  `GatewayServerClosedConnectionError(can_reconnect=False)`.
- Zombie test in heartbeat loop: `if self._last_heartbeat_ack_received <= self._last_heartbeat_sent` → disconnect.
- Two token buckets: `_TOTAL_RATELIMIT: (60.0, 120)` and `_NON_PRIORITY_RATELIMIT: (60.0, 117)` — 3 slots reserved for heartbeats.
- Resume iff `self._seq is not None` and `_session_id`/`_resume_gateway_url` exist; else IDENTIFY.

## 3. aiogram (long polling) — borrowed backoff shape only

- `aiogram/utils/backoff.py`: `BackoffConfig(min_delay, max_delay, factor, jitter)`; `__post_init__` enforces
  `max_delay > min_delay` and `factor > 1`. `Backoff._calculate_next(value) = normalvariate(min(value * factor, max_delay), jitter)`
  (Gaussian jitter around the capped geometric value); `reset()` → `_next_delay = min_delay`; `asleep()`.
- `Dispatcher.DEFAULT_BACKOFF_CONFIG = BackoffConfig(min_delay=1.0, max_delay=5.0, factor=1.3, jitter=0.1)`.
  `_listen_updates`: catches broad `Exception`, logs "Sleep for %f seconds and try again... (tryings = %d, bot id = %d)",
  `backoff.reset()` on success. `handle_as_tasks: bool = True` → `asyncio.create_task(...)` stored in
  `_handle_update_tasks` with `add_done_callback(discard)`; optional `tasks_concurrency_limit` (`asyncio.Semaphore`).
  Shutdown: `_running_lock`, `_stop_signal`/`_stopped_signal` events, `_signal_stop_polling` on SIGINT/SIGTERM.
  `polling_timeout` default `10` (`30` inside `_listen_updates`).

## 4. Home Assistant — skipped (optional, not researched).

## 5. Message brokers: NATS, Centrifugo, Redis

**nats.py (`nats/aio/client.py` @ v2.9.0; docs signature matches)**
- `DEFAULT_PENDING_SIZE = 2 * 1024 * 1024`, `DEFAULT_MAX_PAYLOAD_SIZE = 1048576`, `DEFAULT_RECONNECT_TIME_WAIT = 2`,
  `DEFAULT_MAX_RECONNECT_ATTEMPTS = 60`, `DEFAULT_PING_INTERVAL = 120`, `DEFAULT_MAX_OUTSTANDING_PINGS = 2`,
  `DEFAULT_MAX_FLUSHER_QUEUE_SIZE = 1024`, `DEFAULT_CONNECT_TIMEOUT = 2`, `DEFAULT_DRAIN_TIMEOUT = 30`.
- `connect(..., error_cb, disconnected_cb, closed_cb, discovered_server_cb, reconnected_cb, allow_reconnect=True,
  dont_randomize=False, flusher_queue_size=1024, pending_size=2097152, flush_timeout=None, drain_timeout=30)`.
- `_ping_interval()` increments `_pings_outstanding`; above `max_outstanding_pings` → `_process_op_err(ErrStaleConnection())`
  (dead-link detection = `ping_interval * (max_outstanding_pings+1)` ≈ 6 min by default).
- `_process_op_err()`: if `allow_reconnect` → status `RECONNECTING`, spawn `_attempt_reconnect()`; that shuffles the server
  pool (unless `dont_randomize`), sleeps `reconnect_time_wait` per server, `max_reconnect_attempts == -1` = infinite,
  replays subscriptions, flushes `_pending`, fires `reconnected_cb`.
- Outbound buffering: `publish()` appends to `_pending` via `_send_command`; while disconnected, if
  `pending_data_size > _max_pending_size` → `OutboundBufferLimitError`; oversize → `MaxPayloadError`. A dedicated
  `_flusher` coroutine drains a bounded `flush_queue` (`flusher_queue_size`) — write-side backpressure decoupled from callers.
- `drain()` = stop new subs, let in-flight complete within `drain_timeout`, then close (graceful shutdown primitive).

**centrifuge-python (`centrifuge/client.py`, `utils.py`)**
- Defaults: `timeout=5.0`, `max_server_ping_delay=10.0`, `min_reconnect_delay=0.1`, `max_reconnect_delay=20.0`.
- Server→client ping = empty `{}`; client optionally answers `{}`; `_restart_ping_wait()` arms a timer for
  `ping_interval + max_server_ping_delay`; expiry → `_no_ping()` → disconnect with reconnect.
- `_backoff(step, min, max) = random.uniform(0, min(max_value, min_value * 2**step))` — AWS "full jitter", `MAX_STEP = 31`.
- Terminal close codes: `if (3500 <= ws_code < 4000) or (4500 <= ws_code < 5000): reconnect = False`; all else reconnects.
  `_is_token_expired(code)` → clear token, call `get_token()` on next connect (auth refresh inside the reconnect loop).
- Resume-like recovery: `subscribe["recover"]=True, ["epoch"], ["offset"]`; RPC correlation by `cmd_id` with
  `_register_future(cmd_id, timeout)` → `OperationTimeoutError`.

**redis-py asyncio `PubSub`**: `on_connect` "Re-subscribe to any channels and patterns previously subscribed to";
`check_health()` sends `PING` with `HEALTH_CHECK_MESSAGE` sentinel when `health_check_interval` (default `0` = off) elapsed
and raises `ConnectionError("Bad response from PING health check")`; `run(exception_handler, poll_timeout)`.

## 6. Transport libraries and structured concurrency

**websockets (`src/websockets/client.py`, `asyncio/client.py`, keepalive doc)**
- `connect()` defaults: `ping_interval=20`, `ping_timeout=20`, `close_timeout=10`, `open_timeout=10`,
  `max_size=2**20`, `max_queue=16` (high-water; low-water `max_queue // 4`), `write_limit=2**15`, `compression="deflate"`.
- Auto-reconnect: `async for websocket in connect(uri):` — "If the connection fails with a transient error, it is retried
  with exponential backoff. If it fails with a fatal error, the exception is raised ... The connection is closed
  automatically after each iteration." Backoff constants (env-overridable): `BACKOFF_INITIAL_DELAY = 5`,
  `BACKOFF_MIN_DELAY = 3.1`, `BACKOFF_MAX_DELAY = 90.0`, `BACKOFF_FACTOR = 1.618`; `backoff()` first yields
  `random.random() * initial_delay`, then multiplies by the factor up to the cap. After a successful connection
  `delays = None` (reset). Default `process_exception()`: transient = `OSError`, `asyncio.TimeoutError`,
  `InvalidMessage` from `EOFError`, `InvalidStatus` with `500, 502, 503, 504`; everything else fatal.
- Keepalive doc: "Proxies may terminate WebSocket connections prematurely when no message was exchanged in 30 seconds";
  worst-case dead-link detection = `ping_interval + ping_timeout` (40 s); `latency` attribute from Ping/Pong RTT.

**aiohttp `ClientWebSocketResponse` (`client_ws.py`)**: `heartbeat=` sends PING every N s with pong deadline
`_pong_heartbeat = heartbeat / 2.0`; missing pong → `_pong_not_received()` sets `_exception = ServerTimeoutError` and
`_close_code = WSCloseCode.ABNORMAL_CLOSURE` (1006) — the caller only sees it on the next `receive()`, which returns
`WSMsgType.ERROR`/`CLOSED`. Any received data resets the timer. `autoping=True`, `autoclose=True`,
`ClientWSTimeout(ws_receive=None, ws_close=10.0)`, `max_msg_size` 4 MB, `compress=0`. No reconnect.

**trio-websocket**: `open_websocket(connect_timeout=60, disconnect_timeout=60, message_queue_size=1,
max_message_size=1048576, receive_buffer_size=4096)`; `connect_websocket(nursery, ...)` for a caller-owned nursery. A
queue of size 1 means the reader task stops reading the socket until the consumer calls `get_message()` — true
backpressure by construction. `ping()` blocks until the matching pong.

**httpx-ws**: built on httpx + wsproto (sans-io); `keepalive_ping_interval_seconds=20`, `keepalive_ping_timeout_seconds=20`,
`queue_size=512`, `max_message_size_bytes=65536`; `WebSocketDisconnect` vs `WebSocketNetworkError`; asyncio and Trio via AnyIO.

**wsproto**: "pure Python and performs no I/O of its own", RFC 6455 + RFC 7692 permessage-deflate; version 1.3.2.

**picows**: Cython, transport/protocol callbacks (`on_ws_connected`, `on_ws_frame`), "up to 2x" faster than websockets,
zero-copy frames, auto ping-pong with `enable_auto_ping`, `auto_ping_idle_timeout`, `auto_ping_reply_timeout`,
`WSAutoPingStrategy.PING_WHEN_IDLE`; Core API deliberately lacks permessage-deflate and async iteration. Exact
`ws_connect` defaults **[unverified — stub file did not include the function]**.

**Structured concurrency (anyio)**: "If a child task, or the code in the enclosed context block raises an exception, all
child tasks are cancelled"; multiple failures surface as `ExceptionGroup`; `start()` blocks until `task_status.started()`
— ideal for "connect, then hand over a live socket" handshakes. The idiom that follows: one outer reconnect loop; per
connection one TaskGroup with {reader, heartbeat, writer}; any member raising cancels the siblings, the group exits, the
loop decides resume/identify/backoff.

### Comparison table

| Library | Reconnect built-in | Ping/pong | Dead-link detect | Backpressure | Compression | Sans-io | Perf / maintenance |
|---|---|---|---|---|---|---|---|
| websockets (asyncio) | yes, `async for` + `process_exception`; 5s jitter start, ×1.618, cap 90s | `ping_interval=20`, `ping_timeout=20` | `ping_interval+ping_timeout` | `max_queue=16` high / 4 low, `write_limit=32KiB`, `max_size=1MiB` | deflate default | core is sans-io | pure Python; active |
| aiohttp ws client | no | `heartbeat=N`, pong within N/2 | `ServerTimeoutError` → close 1006, seen on next `receive()` | `max_msg_size=4MB` only | opt-in `compress` | no | C parser optional; active |
| trio-websocket | no | manual `ping()` awaits pong | manual | `message_queue_size=1` (hard) | no [unverified] | wsproto | trio-only |
| httpx-ws | no | 20s / 20s keepalive | `WebSocketNetworkError` | `queue_size=512`, `max_message_size_bytes=64KiB` | via wsproto | wsproto | anyio; active |
| picows | no | auto-ping idle/reply timeouts | `auto_ping_reply_timeout` | protocol `pause_writing`/`resume_writing` [unverified] | none (by design) | no | fastest (~2× websockets) |
| wsproto | n/a | events only | n/a | n/a | RFC 7692 | yes | 1.3.2 |
| Slack SDK (aiohttp) | yes, immediate + `ping_interval` sleep | own `sdk-ping-pong` every 5s | `4 × ping_interval` = 20s | thread pool `concurrency=10`, unbounded queue | n/a | n/a | app-level `envelope_id` ack |
| discord.py | yes, full-jitter 2^n, cap 1024s, reset 2048s | server interval from HELLO | `heartbeat_timeout=60` | client 110/60s send limiter | zlib stream | n/a | RESUME with `seq` |
| hikari | yes, base 1.85, cap 60s, window 30s | HELLO interval | ack ≤ sent → zombie | 120/60s + 117 non-priority | zlib | n/a | close 3000 to resume |
| nats.py | yes, `reconnect_time_wait=2`, `max_reconnect_attempts=60` (-1 ∞), randomized pool | `ping_interval=120`, `max_outstanding_pings=2` | stale after 3 unanswered pings | `pending_size=2MiB` + `flusher_queue_size=1024` | n/a | n/a | callbacks: disconnected/reconnected/error/closed |
| centrifuge-python | yes, full jitter 0.1s→20s | server ping, `max_server_ping_delay=10` | `ping_interval+10s` | n/a | n/a | n/a | terminal codes 3500–3999, 4500–4999 |

## 7. RFC / SRE principles

- RFC 6455 §7.4.1: `1000` normal, `1001` going away, `1002` protocol error, `1003` unsupported data, `1006` abnormal (no
  close frame — what you see on a dead TCP link), `1008` policy, `1009` too big, `1011` internal error, `1012–1014`
  reserved, `4000–4999` private use. §5.5.2/5.5.3: a Pong "must have identical 'Application data'" to its Ping; "A Pong
  frame MAY be sent unsolicited. This serves as a unidirectional heartbeat." §5.4: control frames may be interleaved in a
  fragmented message and "MUST NOT be fragmented". §7.1.1: server closes TCP first; client SHOULD wait.
- AWS "Exponential Backoff And Jitter": `sleep = min(cap, base * 2**attempt)`; Full Jitter
  `sleep = random_between(0, min(cap, base * 2**attempt))`; Decorrelated `sleep = min(cap, random_between(base, sleep*3))`.
  Jittered variants give "a substantial decrease in client work and server load"; Full Jitter "uses less work, but slightly more time".
- Fowler, Circuit Breaker: closed → open after failure threshold; "all further calls ... return with an error, without the
  protected call being made"; half-open trial "after a suitable interval". Use it around `apps.connections.open`-style
  URL/token fetches so a dead control plane does not trigger a reconnect storm.
- Idle timeouts that kill silent WebSockets: nginx "By default, the connection will be closed if the proxied server does
  not transmit any data within 60 seconds" (`proxy_read_timeout`; docs suggest periodic ping frames); AWS ALB
  `idle_timeout.timeout_seconds` "The default is 60 seconds". TCP keepalive (kernel, often hours) does not help here —
  only application-level frames reset L7 idle timers.
- Kubernetes: SIGTERM, then SIGKILL after `terminationGracePeriodSeconds` (default 30 s); endpoint removal runs in parallel
  with SIGTERM — a bot should stop pulling new events, finish/ack in-flight ones, and close with `1000/1001` inside that window.

## Distilled design rules for our gateway

1. **One outer reconnect loop, one TaskGroup per connection** ({reader, heartbeat, writer}); any task failing cancels the
   siblings and the loop decides what next (anyio TaskGroup; `websockets` `async for` iterator).
2. **Classify every exit** into *transient* (retry), *resumable* (retry keeping session), *fatal* (raise) using a
   `process_exception`-style hook and an explicit close-code table (websockets; Discord 4004/4010–4014 fatal; Centrifugo
   3500–3999/4500–4999 terminal; discord.py "1000 is not trustworthy — rely on `is_closed`").
3. **Full-jitter exponential backoff with cap and window reset**: `random.uniform(0, min(cap, base*2**n))`, cap 60–90 s,
   randomized *first* delay, reset after a connection that survived > 30 s (AWS; centrifuge; websockets 5/3.1/90/1.618;
   hikari `_BACKOFF_WINDOW=30`; discord.py `_reset_time`).
4. **Application heartbeat every ≤ 20–30 s, dead-link deadline ≈ 2× interval**: proxies/LBs default to 60 s idle
   (nginx, ALB); websockets 20/20; Slack `4×5 s`; aiohttp pong window `heartbeat/2`. Treat "no data of any kind for the
   deadline" as dead (discord.py `_last_recv`), not just "no pong".
5. **Own the liveness timer; do not trust the transport's silent close**: aiohttp surfaces a missed pong only on the next
   `receive()`; Slack runs a separate `monitor_current_session` task — run a monitor task with `receive(timeout=deadline)`.
6. **Resume before identify**: keep `session_id`/`seq`/`resume_url` and try RESUME first; fall back to a fresh session
   only when the server says the session is invalid (Discord; Centrifugo `recover/epoch/offset`).
7. **At-least-once + idempotent consumer**: ack immediately by `envelope_id` (Slack, 3 s window), then process; dedup by
   the payload's stable `event_id`, never by `retry_attempt` (Slack Events API docs).
8. **Bounded inbound queue with real backpressure**: stop reading when the consumer lags (websockets `max_queue=16`
   high/low water; trio-websocket `message_queue_size=1`; httpx-ws 512) instead of an unbounded Slack-style queue.
9. **Bounded outbound buffer + dedicated flusher**: cap pending bytes (`nats.py pending_size=2MiB`, `flusher_queue_size=1024`)
   and fail fast with a typed error when exceeded while disconnected.
10. **Send-side rate limiter that reserves heartbeat capacity** (hikari 120 total / 117 non-priority; discord.py 110 of 120).
11. **Fresh connection URL/token per attempt, behind a circuit breaker and `Retry-After`**: Slack `apps.connections.open`
    with `Retry-After` default 30 s; Centrifugo clears the token on `TOKEN_EXPIRED` and calls `get_token()` in-loop;
    Fowler's breaker stops reconnect storms when the control plane itself is down.
12. **Honour server-initiated disconnect hints**: on `disconnect{reason: warning|refresh_requested}` open the new
    connection *before* closing the old one; keep >1 connection for zero-downtime restarts (Slack up to 10).
13. **Stagger identify/first heartbeat with jitter and serialize session starts** (Discord `heartbeat_interval * jitter`,
    1 identify / 5 s per bucket) to avoid thundering herd after a mass disconnect.
14. **Resumable close code ≠ 1000/1001**: close with a private 4xxx/3xxx code when you intend to resume (Discord docs;
    hikari `_RESUME_CLOSE_CODE=3000`; discord.py `close(4000)`).
15. **Graceful drain on SIGTERM**: stop accepting, finish in-flight handlers with a bounded `drain_timeout` (nats.py 30 s),
    close `1000/1001`, all inside the Kubernetes 30 s grace period (aiogram `_stop_signal`/`_stopped_signal` pattern).
16. **Fire lifecycle callbacks/metrics**: `disconnected_cb`, `reconnected_cb`, `error_cb`, `closed_cb` (nats.py),
    plus latency from ping RTT (websockets `latency`, discord.py `ack()`), and an event-loop-blocked warning (> 10 s).
17. **Run handlers as tasks with a concurrency limit and tracked set** (aiogram `handle_as_tasks` + `tasks_concurrency_limit`)
    so a slow handler never blocks the read loop or the heartbeat.
18. **Pick the transport by need**: `websockets` (reconnect iterator, flow control, deflate) or `picows` (raw speed, no
    deflate); wrap it behind a Protocol so the gateway logic is transport-agnostic (sans-io mindset of wsproto).

## Sources

- Slack: https://docs.slack.dev/apis/events-api/using-socket-mode ; https://docs.slack.dev/reference/methods/apps.connections.open ;
  https://docs.slack.dev/apis/events-api/ ; https://raw.githubusercontent.com/slackapi/python-slack-sdk/main/slack_sdk/socket_mode/client.py ;
  .../slack_sdk/socket_mode/aiohttp/__init__.py ; .../slack_sdk/socket_mode/builtin/client.py ; .../slack_sdk/socket_mode/request.py ;
  https://github.com/slackapi/node-slack-sdk/pull/1762
- Discord: https://docs.discord.com/developers/events/gateway ; https://docs.discord.com/developers/topics/opcodes-and-status-codes ;
  https://raw.githubusercontent.com/Rapptz/discord.py/master/discord/gateway.py ; .../discord/client.py ; .../discord/backoff.py ; .../discord/state.py ;
  https://raw.githubusercontent.com/hikari-py/hikari/master/hikari/impl/shard.py
- aiogram: https://raw.githubusercontent.com/aiogram/aiogram/dev-3.x/aiogram/utils/backoff.py ; .../aiogram/dispatcher/dispatcher.py
- NATS: https://raw.githubusercontent.com/nats-io/nats.py/v2.9.0/nats/aio/client.py ; https://nats-io.github.io/nats.py/modules.html
  (main-branch raw URL returned 404; docs.nats.io reconnect/pingpong pages have moved — not quoted)
- Centrifugo: https://raw.githubusercontent.com/centrifugal/centrifuge-python/master/centrifuge/client.py ; .../centrifuge/utils.py
- redis-py: https://raw.githubusercontent.com/redis/redis-py/master/redis/asyncio/client.py ; .../redis/asyncio/connection.py
- websockets: https://raw.githubusercontent.com/python-websockets/websockets/main/src/websockets/client.py ;
  .../src/websockets/asyncio/client.py ; https://websockets.readthedocs.io/en/stable/topics/keepalive.html ;
  https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html
- aiohttp: https://docs.aiohttp.org/en/stable/client_reference.html ; https://raw.githubusercontent.com/aio-libs/aiohttp/master/aiohttp/client_ws.py
- trio-websocket: https://trio-websocket.readthedocs.io/en/stable/clients.html ; https://trio-websocket.readthedocs.io/en/stable/api.html
- httpx-ws: https://frankie567.github.io/httpx-ws/reference/httpx_ws/ ; wsproto: https://python-hyper.org/projects/wsproto/en/stable/
- picows: https://github.com/tarasko/picows ; https://picows.readthedocs.io/en/stable/ ; https://raw.githubusercontent.com/tarasko/picows/master/picows/picows.pyi
- anyio: https://anyio.readthedocs.io/en/stable/tasks.html
- RFC 6455: https://www.rfc-editor.org/rfc/rfc6455.html
- AWS: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
- Fowler: https://martinfowler.com/bliki/CircuitBreaker.html
- nginx: https://nginx.org/en/docs/http/websocket.html ; AWS ALB: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/application-load-balancers.html
- Kubernetes: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
