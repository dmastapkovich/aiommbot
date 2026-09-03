# WebSocket client libraries for the Mattermost gateway — what goes behind `WebSocketConnection`

Status: complete (2026-09-03). Primary sources only (library source on GitHub, official docs, PyPI
release history); versions and dates are as observed on 2026-09-03. **[unverified]** marks anything I
could not confirm from a primary source. Builds on `01-mattermost-websocket-protocol.md` (server
constants) and `02-resilient-websocket-client-patterns.md` (reconnect/heartbeat patterns, first-pass
library table) — nothing from those two is repeated here.

Question: which WebSocket client stack goes behind the Core-owned `WebSocketConnection` Protocol, and
what HTTP client should the REST side (#21) use?

**One fact that reshapes the comparison.** Mattermost's upgrader in `server/channels/api4/websocket.go`
sets only `ReadBufferSize`, `WriteBufferSize` and `CheckOrigin`; it never sets `EnableCompression`, and
gorilla's zero value means "do not attempt to negotiate per message compression (RFC 7692)". No
`EnableWriteCompression` call exists in `web_conn.go` either. So permessage-deflate is never negotiated on
`/api/v4/websocket`, and a client without deflate support loses nothing.

## 1. picows

**Release state.** 2.1.3 (2026-08-04), MIT, `requires_python >=3.9` (classifiers 3.10–3.14), 63 wheels
per release including `cp313t`/`cp314t` free-threaded builds. Cadence in 2026 is roughly one release every
two to three weeks (1.10.2 Jan → 2.1.3 Aug: 14 releases). Repository: 290 stars, 3 open issues, last push
2026-08-31. **Single maintainer**: `tarasko` has 125 of ~132 commits; the next contributor has 4. No
verifiable list of notable users exists (GitHub "used by" is not exposed via API) — **[unverified]**.
Security responsiveness is visible: GHSA-583m-hcmv-qpq9 (server crash on an invalid 64-bit payload
length) was fixed in 2.1.2 (2026-07-30).

**Architecture.** A Cython `WSProtocol` (asyncio `BufferedProtocol` since 1.15.0, previously only under
uvloop) parses frames in C and calls back into a user `WSListener` *synchronously* — there is no
async data path by design ("async interface introduces an extra hop through the event loop"). The
listener callbacks are `on_ws_connected(transport)`, `on_ws_frame(transport, frame)`,
`on_ws_disconnected(transport)`, `send_user_specific_ping(transport)`, `is_user_specific_pong(frame)`,
`pause_writing()`, `resume_writing()`. Frames, not messages: `WSFrame` exposes `msg_type`, `fin`,
`payload_size`, `get_payload_as_bytes/utf8_text/ascii_text/memoryview()`, `get_close_code()`,
`get_close_message()`; fragment reassembly is the caller's job (`CONTINUATION` + `fin`).

`ws_connect` (from `picows/api.py`, pure Python since 1.12.0):

```python
async def ws_connect(ws_listener_factory, url, *, ssl_context=None, disconnect_on_exception=True,
    websocket_handshake_timeout=5, logger_name=None, enable_auto_ping=False,
    auto_ping_idle_timeout=10, auto_ping_reply_timeout=10,
    auto_ping_strategy=WSAutoPingStrategy.PING_WHEN_IDLE, enable_auto_pong=True,
    max_frame_size=10 * 1024 * 1024, extra_headers=None, max_redirects=5, proxy=None,
    read_buffer_init_size=16 * 1024, socket_factory=None, use_aiofastnet=None, **kwargs
) -> tuple[WSTransport, WSListener]
```

`**kwargs` go to `loop.create_connection`; `ssl`, `sock` and `all_errors` are asserted out. There is no
query-string helper — the URL is passed whole, which suits `?connection_id=&sequence_number=`.
`WSTransport`: `send(msg_type, message, fin=True, rsv1..3)`, `send_ping()`, `send_pong()`,
`send_close(close_code, close_message)`, `disconnect(graceful=True)`, `await wait_disconnected()`,
`await measure_roundtrip_time(rounds) -> list[float]`, properties `close_handshake`,
`is_close_frame_sent`, `is_disconnected`, `underlying_transport`, `request`, `response`.

**Auto-ping/pong.** `enable_auto_pong=True` answers server PING frames (what Mattermost sends every
60 s). `enable_auto_ping` is a *stale-link detector*: `PING_WHEN_IDLE` pings after
`auto_ping_idle_timeout` s of silence, `PING_PERIODICALLY` every N s; no PONG within
`auto_ping_reply_timeout` → disconnect. `send_user_specific_ping`/`is_user_specific_pong` let the
application substitute its own probe — this is exactly the hook for Mattermost's JSON `{"action":"ping"}`
instead of a frame ping, so the gateway's 30 s heartbeat can be delegated to the library timer if we want.

**Backpressure.** Write side: `pause_writing`/`resume_writing` are the asyncio flow-control callbacks
forwarded to the listener (1.19.0 stopped logging them when overridden). Read side: nothing built in —
frames are pushed synchronously; to stop reading, the adapter must call
`transport.underlying_transport.pause_reading()`/`resume_reading()` when its own bounded queue fills.
Whether the `aiofastnet` transport implements `pause_reading` identically to asyncio's — **[unverified]**.

**Close codes.** A CLOSE frame arrives at `on_ws_frame` (`WSMsgType.CLOSE`, `get_close_code()`,
`get_close_message()`); `WSTransport.close_handshake` retains it (2.0.0 fixed cases where it "wasn't
properly filled"). `wait_disconnected()` raises `WSError` when the disconnect was caused by a protocol
parsing error and re-raises user exceptions thrown in `on_ws_disconnected` (1.14.0). Exception hierarchy
(1.16.0/1.20.0): `WSError` → `WSHandshakeError`, `WSInvalidMessageError`, `WSInvalidStatusError`,
`WSInvalidHeaderError`, `WSInvalidUpgradeError`, `WSProtocolError`; `WSError` carries `raw_header`,
`raw_body`, `response` (1.12.0) — useful to surface a 401/429 handshake.

**TLS / proxy.** `ssl_context` overrides the default context for `wss://`; there is no fingerprint helper
(pin via a custom context). Proxy since 1.13.0: `proxy=` URL with `http://`, `socks4://`, `socks5://`
(authenticated variants included); "HTTPS proxy scheme (`https://`) is currently not supported". No
environment-variable discovery — the caller must read `HTTPS_PROXY` and pass it.

**Dependencies.** `multidict`, `python-socks[asyncio]`, `aiofastnet>=1.0.3`. `aiofastnet` replaces
`loop.create_connection` by default (1.18.0); 2.1.1 bumped it to fix "python distributions that are
statically linked with openssl" — i.e. it touches the TLS path. `use_aiofastnet=False` falls back to
the stdlib. Who maintains `aiofastnet` — **[unverified]**; treat it as part of the picows trust surface.

**uvloop / free-threading.** uvloop 0.22.1 (2025-10-16) is the last release; the picows author's own
benchmark notes say uvloop "is not very well maintained anymore … but it is still a little faster than
vanilla asyncio from Python-3.13". picows itself: "fully compatible with free-threaded Python.
**picows** transports do not require the GIL and can run in parallel in different threads"; 1.18.0 raises
if `WSTransport` methods are called from the wrong thread.

**Benchmarks.** `tarasko/websocket-benchmark` (pushed 2026-06-28): request–response echo loop against
one C++ server over loopback, RPS at 256 B / 8 KiB / 100 KB / 2 MB, Linux and Windows; results are PNG
charts only, no numbers in the README. Qualitative claims: websockets "significantly slower than
aiohttp" (pure-Python frame parsing); aiohttp loses "due to high level features like async interface,
message assembling and corresponding copying"; "picows + uvloop can be even faster than Beast" above
~2 KB. The README's "up to 2x" versus websockets is the maintainer's figure — **[unverified]**.
2.0.0 added `picows.websockets`, a drop-in compatibility shim for the `websockets` API; irrelevant for us,
we would use the Core API.

## 2. websockets

**Release state.** 17.1 (2026-08-26), BSD, `requires_python >=3.11` (17.0 dropped 3.10), 147 wheels
including `cp314t`; pure Python with an optional C speedups module (masking). Cadence: 14.0 Nov 2024,
15.0 Feb 2025, 16.0 Jan 2026, 16.1 Jul 2026, 17.0 Jul 29 2026, 17.1 Aug 26 2026. Policy: "preserve
backwards-compatibility for five years after the release that introduced the change." Single principal
author (Aymeric Augustin), Tidelift-funded.

**asyncio vs sans-I/O.** `websockets.asyncio.client.connect` is the default since 14.0 (legacy
implementation deprecated); a threading implementation exists since 14.0 and a trio one since 17.0. All
three sit on the sans-I/O `websockets.protocol`/`ClientProtocol`, which is a second sans-I/O core
alongside wsproto — with C-accelerated masking and permessage-deflate — should we ever write our own
driver (section 4).

`connect(uri, *, origin, extensions, subprotocols, compression="deflate", additional_headers,
user_agent_header, proxy=True, process_exception, open_timeout=10, ping_interval=20, ping_timeout=20,
close_timeout=10, reconnect_delays=backoff, max_size=2**20, max_queue=16, write_limit=2**15, logger,
create_connection, **kwargs)`. `max_queue` is the receive high-water mark in frames (low-water
`max_queue // 4`, tuple allowed; 16.0 split `max_size` into message/fragment limits); `write_limit` is
passed to `set_write_buffer_limits`. `recv(decode=False)` returns bytes for text frames without the
UTF-8 pass. `ping()` returns a future resolved by the matching pong (its result is the RTT); `latency`
holds the last keepalive RTT. `close_code`/`close_reason` exist on the connection (14.1) but the docs
recommend reading them from `ConnectionClosed.rcvd/sent` (`ConnectionClosedOK` vs
`ConnectionClosedError`). `process_exception` classifies transient vs fatal for the
`async for ws in connect(...)` iterator; 17.0 added `reconnect_delays`, 17.1 a standalone `reconnect()`
iterator. Free-threaded Python support landed in 16.0.

## 3. aiohttp client WebSocket

**Release state.** 3.14.3 (2026-07-23), Apache-2.0, `requires_python >=3.10`, `cp314t` wheels; team
maintained (`aiohttp team`). Cadence: 3.13.0 Oct 2025, 3.14.0 Jun 2026, patch releases monthly.
Free-threading support was added in 3.13.0 (Python 3.14t). The C HTTP parser is llhttp 9.4.2 (optional,
`AIOHTTP_NO_EXTENSIONS`); the WebSocket frame reader is Cython. Seven runtime dependencies
(`aiohappyeyeballs`, `aiosignal`, `attrs`, `frozenlist`, `multidict`, `propcache`, `yarl`).

`ClientSession.ws_connect(url, *, method="GET", protocols=(), timeout=ClientWSTimeout(ws_receive=None,
ws_close=10.0), autoclose=True, autoping=True, heartbeat=None, origin, params, headers, proxy,
proxy_auth, ssl=True, fingerprint, ssl_context, proxy_headers, compress=0, max_msg_size=4194304)`.
`receive(timeout)` uses `timeout or self._timeout.ws_receive` and returns `WSMessage`; a missed pong
(`_pong_not_received`) stores `ServerTimeoutError` and sets `close_code = 1006`, which the caller only sees
as `WSMsgType.ERROR`/`CLOSED` on the next `receive()` — the error itself via `exception()`. 3.14.0
finally resets the heartbeat timer on inbound data; 3.14.2 fixed decompressing frames when deflate was not
negotiated and control frames breaking fragmented messages — bug classes that matter for a long-lived
gateway and that were still being found in 2026. Proxies: "plain HTTP proxies and HTTP proxies that can
be upgraded to HTTPS via the HTTP CONNECT method", `trust_env=True` reads `HTTP_PROXY`/`HTTPS_PROXY`/
`WS_PROXY`/`WSS_PROXY`/`no_proxy` via `getproxies()`; HTTPS (TLS-to-proxy) proxies are described as
limited by asyncio TLS-in-TLS. Pinning: `ssl=aiohttp.Fingerprint(sha256_der)`. aiohttp 4.0 remains a
deprecation target with no date.

## 4. wsproto + our own transport

wsproto 1.3.2 (2025-11-20), MIT, `requires_python >=3.10`, python-hyper, maintainer Thomas Kriechbaumer.
Release gap 1.2.0 (2022-08) → 1.3.0 (2025-11): three years, then three releases in nine days — a
"finished" library, not an abandoned one. Source is ~75 KB: `frame_protocol.py` 24 KB, `handshake.py`
18.6 KB, `extensions.py` 11 KB (RFC 7692), `connection.py` 7.8 KB, `events.py` 7.9 KB. Masking is pure
Python.

**What we would write.** An asyncio `Protocol` (or `BufferedProtocol`) that (a) opens the socket with
`loop.create_connection(ssl=ctx, server_hostname=host)`, (b) sends
`connection.send(Request(host, target, extra_headers))`, (c) feeds `data_received` bytes into
`connection.receive_data()` and iterates `connection.events()`: `AcceptConnection`/`RejectConnection`
(map 401/429 to typed errors), `TextMessage`/`BytesMessage` with `message_finished` (reassemble),
`Ping` (answer with `Pong` immediately), `Pong`, `CloseConnection(code, reason)` (echo the close, then
close TCP after the server does — RFC 6455 §7.1.1), (d) `send_text` = `transport.write(connection.send(
TextMessage(...)))`, (e) `pause_writing`/`resume_writing` → an `asyncio.Event` the writer awaits, (f)
open/close timeouts via `asyncio.timeout`, (g) HTTP proxy = manual `CONNECT host:443` on a plain
connection, then `loop.start_tls()` (3.11+), SOCKS via `python-socks`. Precedents for the size:
httpcore's `_async/http11.py` drives h11 over `AsyncNetworkStream` in 13.9 KB with backends of 5–8 KB
each (`anyio.py` 5.3 KB, `trio.py` 6 KB, `sync.py` 8 KB, `mock.py` 4 KB); httpx-ws's `_api.py` is 57 KB
because it ships sync *and* async sessions, keepalive, JSON helpers and a queue. An asyncio-only driver
for our narrow Protocol is realistically 400–600 lines plus ~150 for proxy CONNECT, plus a test suite
that has to re-cover what the Autobahn suite already covers for the libraries.

**Is it worth it?** Maximal control is real (no hidden reader task, no hidden ping timer, exceptions
exactly where we want them), and wsproto's I/O-free core is the most testable piece in this whole list.
But it buys nothing the picows Core API does not already give us — picows is likewise "framing + TLS +
ping/pong + close", just in C with a sync callback instead of an event generator — and it would make us
the maintainers of masking performance, proxy handshakes and RFC edge cases (the picows GHSA above is
exactly the class of bug we would own). Verdict: not as a shipped implementation; keep it as the shape of
the Protocol (section 7) so that a wsproto driver stays a one-file contribution if ever needed.

## 5. httpx-ws, httpx2, niquests

**httpx2** is not "httpx v2 by encode". PyPI: maintainer `"Pydantic Services Inc."
<engineering@pydantic.dev>`, repo `github.com/pydantic/httpx2`; changelog 2.0.0b1: "a fork of httpx
maintained by Pydantic. Forked from httpx 0.28.1"; README: HTTPX "seeing limited activity recently",
"Pydantic is picking up stewardship". Import name `httpx2`; `httpcore` renamed to the vendored
`httpcore2`; `alias_httpx()` (2.9.0) aliases `httpx` process-wide for third-party code. 2.12.0
(2026-08-18); twelve releases between 2026-05-17 and 2026-08-18; `requires_python >=3.10`, classifiers to
3.15; runtime deps `anyio>=4.10`, `httpcore2`, `idna`, `truststore>=0.10` (2.3.0 switched SSL
verification to the OS trust store), extras `http2` (h2), `socks` (socksio), `ws` (wsproto), `brotli`,
`zstd`. Upstream `httpx` meanwhile: last stable 0.28.1 (2024-12-06); `1.0.dev4–dev6` appeared
2026-08-19…31, so encode is stirring again but has shipped no stable release in 21 months. The 0.4.x
stack's `httpx2>=2.5` therefore pointed at this Pydantic fork.

**WebSocket in httpx2.** 2.6.0 (2026-07-14): "Native WebSocket support by vendoring `httpx-ws`",
`httpx2[ws]`; 2.7.0 synced to httpx-ws 0.9.0; 2.10.0 fixed max-message-size enforcement across fragments
and ignores unsolicited/duplicate pongs. API: `client.websocket(url)` / `AsyncClient.websocket(url)` /
`httpx2.websocket()`; `send_text/bytes/json`, `receive_text/bytes/json(timeout=)`, `ping()` returns an
event set on pong; defaults `max_message_size_bytes=65536`, `queue_size=512`,
`keepalive_ping_interval_seconds=20.0`, `keepalive_ping_timeout_seconds=20.0`; exceptions in
`httpx2.websockets`: `HTTPXWSException` → `WebSocketUpgradeError`, `WebSocketDisconnect(code, reason)`,
`WebSocketNetworkError`, `WebSocketInvalidTypeReceived`. Mechanics (from httpx-ws): the session "uses an
anyio task group to manage background tasks" reading the network stream into a queue. Standalone
**httpx-ws** 0.9.0 (2026-03-28) still depends on `httpx>=0.23.1` — the encode package, not `httpx2` —
so it is not usable together with httpx2 without the vendored copy. Whether the WebSocket path works
through an HTTP CONNECT proxy (httpcore tunnel → `network_stream`) is plausible but **[unverified]**.

**niquests** 3.21.1 (2026-08-28), maintainer Ahmed Tahri (jawah), monthly releases, classifier
`Free Threading :: 4 - Resilient`. WebSocket confirmed: `niquests[ws]`, `ws://`/`wss://` over HTTP/1.1,
`wss+rfc8441://` for extended CONNECT over HTTP/2 (RFC 8441) or HTTP/3, API
`resp.extension.next_payload()/send_payload()/ping()/close()`, works in the async session. The blocker is
its dependency `urllib3-future`, "an independently maintained, compatibility-first fork of urllib3" that,
installed as the standard wheel, "shadows the urllib3 import namespace environment-wide" and re-creates
the `urllib3` directory from its own copy if files are mixed. A framework must not impose that on host
applications that also carry `requests`/`boto3`/`kubernetes` (all urllib3 consumers).

## 6. Proxy and TLS reality

Corporate deployments mean an HTTPS-terminating egress proxy (`HTTPS_PROXY=http://proxy:3128`), a
private CA in the OS store or a `SSL_CERT_FILE` bundle, and occasionally a TLS-to-proxy (`https://`)
scheme. Per library, as of the versions above:

| | picows 2.1.3 | websockets 17.1 | aiohttp 3.14.3 | httpx2 2.12 (WS) |
|---|---|---|---|---|
| Env discovery | none — pass `proxy=` | `getproxies()`: `wss_proxy`/`ws_proxy`, then `https_proxy`, `http_proxy` (ws only), `no_proxy`; `proxy=True` default | `trust_env=True`: `HTTP_PROXY`/`HTTPS_PROXY`/`WS_PROXY`/`WSS_PROXY`/`no_proxy` | httpx env handling (`HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY`/`NO_PROXY`, `trust_env`); WS via proxy **[unverified]** |
| HTTP CONNECT proxy | yes (`http://`, auth) | yes, Basic auth | yes | yes for HTTP; WS **[unverified]** |
| TLS-to-proxy (`https://`) | no ("currently not supported") | yes ("TLS-in-TLS is supported") | limited (asyncio TLS-in-TLS caveat) | inherits httpcore |
| SOCKS | `socks4://`, `socks5://` (python-socks is a hard dep) | SOCKS4/4a/5/5h via optional `python-socks[asyncio]` | third-party only | `socks` extra (socksio) |
| Custom CA | `ssl_context=` | `ssl=` context | `ssl=` context / connector | `truststore` OS store by default; `verify=` context |
| Pinning | own context/verify callback | own context | `aiohttp.Fingerprint(sha256)` | own context |
| SNI | from URL host (default context) | `server_hostname=` override | automatic | automatic |

Every library that builds `ssl.create_default_context()` inherits OpenSSL's `SSL_CERT_FILE`/`SSL_CERT_DIR`
env handling from the stdlib; httpx2 with `truststore` reads the OS store instead — whether it still
honours `SSL_CERT_FILE` after 2.3.0 is **[unverified]**. Practical consequence: env-var discovery and CA
policy must live in *our* connector (one place, tested once), and be passed down explicitly; then the
only real per-library gap is picows' missing `https://` proxy scheme, which no company bot has needed so
far (0.4.x used httpx2 with plain `HTTPS_PROXY=http://…`) — **[unverified for all eleven bots]**.

## 7. The Protocol surface the gateway needs

Everything reconnect-, heartbeat-, resume- and queue-related is ours (doc 01/02); the Protocol is only
"one open socket". Minimal surface, expressed as two Protocols plus a frozen event union:

```python
class WebSocketConnector(Protocol):
    async def connect(self, url: str, *, headers: Mapping[str, str], timeout: float,
                      tls: TLSConfig, proxy: ProxyConfig | None) -> WebSocketConnection: ...
        # raises WebSocketConnectError(kind: dns|tcp|tls|proxy|handshake, status: int | None)

class WebSocketConnection(Protocol):
    async def receive(self, timeout: float | None) -> Text | Binary | Closed: ...
        # Closed(code: int, reason: str, clean: bool); raises WebSocketTimeout, WebSocketProtocolError,
        # WebSocketNetworkError (TCP reset / EOF without close frame → code 1006)
    async def send_text(self, payload: str) -> None: ...      # raises WebSocketClosed | WebSocketNetworkError
    async def ping(self) -> Awaitable[float]: ...              # frame ping; result = RTT
    async def close(self, code: int = 1000, reason: str = "") -> None:  # idempotent, bounded by close timeout
    @property
    def close_code(self) -> int | None: ...
```

Design notes: `receive` returns whole messages (the adapter reassembles fragments — gorilla's
`WriteMessage`/`WriteJSON` normally emit one unfragmented frame, but nothing guarantees it); query
parameters are part of `url` (built by the gateway); `ping()` returns an awaitable so the gateway can
measure RTT without owning pong matching; the exception taxonomy is *ours* and every adapter translates.

How each library maps:

- **picows**: `on_ws_frame` → reassemble → `asyncio.Queue(maxsize=N)`; on full queue call
  `underlying_transport.pause_reading()`, resume when drained (read backpressure by hand); `CLOSE` frame
  → put `Closed(get_close_code(), get_close_message())`; `on_ws_disconnected` without a prior CLOSE →
  `Closed(1006)`; `send_text` = `transport.send(WSMsgType.TEXT, str)` after checking `pause_writing`
  state; `ping` = `send_user_specific_ping` + a future resolved in `is_user_specific_pong` (or
  `measure_roundtrip_time(1)`); `close` = `send_close(code)` then `await wait_disconnected()` under a
  timeout; `WSHandshakeError`/`WSInvalidStatusError` → `WebSocketConnectError(handshake, status)`.
  Adapter estimate: ~150–200 lines.
- **websockets**: `recv(decode=False)` with `asyncio.timeout`; `ConnectionClosedOK/Error` →
  `Closed(exc.rcvd.code if exc.rcvd else 1006, ...)`; `ping()` already returns the pong future;
  `max_queue`/`write_limit` give backpressure for free; `InvalidStatus` → `WebSocketConnectError`;
  `ping_interval=None` (we own liveness). ~100 lines.
- **aiohttp**: `receive(timeout)` → `WSMsgType.TEXT/BINARY/CLOSE/CLOSED/ERROR` switch, `exception()`
  for the error, `close_code` for the code; `heartbeat=None`, `autoping=True`; needs a `ClientSession`
  lifecycle. ~120 lines.
- **httpx2 WS**: `receive_text(timeout)`; `WebSocketDisconnect(code, reason)` → `Closed`;
  `WebSocketNetworkError` → network; `ping()` event → wrap in awaitable; note its own keepalive must be
  disabled (`keepalive_ping_interval_seconds=None`) and `max_message_size_bytes` raised from 64 KiB.
  ~100 lines.

**In-memory test double.** `FakeConnection(script: list[Text | Binary | Closed | Exception | Sleep])`
that `receive()` pops from (an `Exception` entry is raised, `Sleep(s)` delays to exercise `timeout`),
records `sent: list[str]`, `pings: int`, `closed_with: (code, reason) | None`; plus `FakeConnector`
holding a queue of connections-or-exceptions per attempt so reconnect, resume-URL construction and
backoff are tested without sockets. Both implementations then run the same contract test module
(parametrised over `picows`, `websockets`, the fake) against a local `websockets.serve`/picows server
fixture that scripts handshake 401, slow pongs, close 1001, TCP reset, oversized frames — that contract
suite, not the adapters, is what makes the library swappable in practice.

## 8. HTTP client for the REST side (#21)

| | aiohttp 3.14.3 | httpx2 2.12.0 | niquests 3.21.1 | urllib3 2.7.0 |
|---|---|---|---|---|
| Maintenance 2026 | team; monthly patches; 4.0 open-ended | Pydantic Services; 12 releases in 4 months (young fork, `HTTPXDeprecationWarning` in use) | one maintainer; monthly | core team (3 maintainers); 2.7.0 May 2026 |
| HTTP/2 | no (client) | `http2` extra (h2) | yes, plus HTTP/3, multiplexing | no — docs banner "fundraising for HTTP/2" |
| Async | asyncio only | asyncio + trio via anyio | yes (urllib3-future `AsyncPoolManager`) | none in 2.x docs |
| Sync face | none | `Client` mirrors `AsyncClient` | `Session`/`AsyncSession` | sync only |
| Pooling / limits | `TCPConnector(limit, limit_per_host)` | `Limits(max_connections, max_keepalive_connections, keepalive_expiry)` (httpx defaults **[unverified for httpx2]**) | urllib3-future pools | `PoolManager` |
| Typing | `py.typed`, deep generics | "Fully type annotated", `Headers.get -> str \| None` (2.10.0) | typed | typed |
| Free-threading | 3.13.0+, `cp314t` wheels | pure Python; relies on anyio (`Free Threading :: 2 - Beta`) | classifier `4 - Resilient` | `2 - Beta` |
| Multipart upload | `FormData` streaming | `files=` mapping | requests-style `files=` | `encode_multipart_formdata` |
| Deal-breaker for us | no sync face → ADR-0004 needs a second implementation | fork risk (mitigated by pinning and a transport Protocol) | shadows `urllib3` namespace in host apps | no async |

## 9. Comparison table (WebSocket implementations)

| | picows 2.1.3 | websockets 17.1 | aiohttp 3.14.3 | httpx2[ws] 2.12 | wsproto driver |
|---|---|---|---|---|---|
| Level | frames, sync callbacks | messages, async | messages, async | messages, async (anyio) | events, ours |
| Framing impl | C/Cython, SIMD masking | Python + C masking | Cython reader | Python (wsproto) | Python (wsproto) |
| Deflate | no (not needed) | default on | opt-in | via wsproto | via wsproto |
| Read backpressure | manual `pause_reading` | `max_queue` hi/lo | `max_msg_size` only | `queue_size=512` | ours |
| Write backpressure | `pause_writing` callbacks | `write_limit` | asyncio default | anyio stream | ours |
| Close-code surfacing | CLOSE frame + `close_handshake` | `ConnectionClosed.rcvd/sent` | `close_code` after `receive()` | `WebSocketDisconnect(code)` | `CloseConnection` event |
| Proxy | http/socks, no `https://`, no env | http/https/socks, env | http, env; https limited | inherits httpx | ours |
| Free-threaded | yes (GIL-free transports) | 16.0+ | 3.13.0+ | anyio-dependent | n/a |
| Python | ≥3.10 effective | ≥3.11 | ≥3.10 | ≥3.10 | ≥3.10 |
| Runtime deps | 3 (+aiofastnet TLS path) | 0 | 7 | 4 + wsproto | 1 |
| Bus factor | 1 | 1 (5-year policy, Tidelift) | team | Pydantic | us |
| Compat policy | none stated (2.0 was non-breaking) | 5 years | deprecations toward 4.0 | new | n/a |

## 10. Recommendation

**Primary WebSocket implementation: picows (Core API), pinned `picows>=2.1,<3`.** It is the only
candidate that does exactly what the maintainer asked the library to do and nothing more — framing,
TLS, ping/pong frames, close handshake — with a synchronous, zero-copy data path that feeds our bounded
queue without a second event-loop hop, explicit close frames and codes, a formal exception hierarchy,
free-threaded transports, and `send_user_specific_ping` as a native hook for the JSON `ping`. Its two
shortcomings (no read backpressure primitive, no `https://` proxy or env discovery) are 20 lines in the
adapter and the connector respectively; its lack of deflate is irrelevant because Mattermost never
negotiates it. Its real risk is a bus factor of one plus the `aiofastnet` dependency on the TLS path —
which is precisely what the Protocol and the contract suite exist to absorb.

**Second implementation behind the same Protocol: websockets (asyncio) 17.x.** The most conservative
choice in the field: zero dependencies, a stated five-year compatibility policy, free-threaded since 16.0,
the only client with full proxy coverage including TLS-to-proxy, and built-in receive/write flow control.
Ship it as the fallback that the contract suite runs in CI on every commit, and make the selection a
config/extra (`aiommbot[picows]`), so swapping is a one-line change for a bot, not a release of the
framework. Do not add aiohttp as a third: it brings seven dependencies and a REST client we are not going
to use, and its WebSocket layer was still fixing fragmentation and heartbeat bugs in mid-2026. Keep
httpx2's bundled WebSocket as a *zero-cost* third candidate to revisit once it has a year of releases
behind it — it comes free with the REST dependency but is two months old as a vendored module.

**Minimal Protocol surface:** section 7 — `connect(url, headers, timeout, tls, proxy)`;
`receive(timeout) -> Text | Binary | Closed(code, reason, clean)`; `send_text`; `ping() -> Awaitable[float]`;
`close(code, reason)`; `close_code`; four exception kinds (`ConnectError` with `kind`/`status`,
`NetworkError`, `ProtocolError`, `Timeout`), plus `Closed` as a value, not an exception, so the gateway's
resume/backoff decision reads the code without `except` ladders.

**HTTP client for REST: httpx2, pinned `httpx2>=2.12,<3`, behind our own thin transport Protocol.**
It is the only candidate that satisfies ADR-0004's dual sync/async face from one codebase, is fully
typed, uses the OS trust store by default (the corporate-CA problem disappears), offers HTTP/2 as an
extra, and is where the 0.4.x bots already are. aiohttp is async-only (the generated sync face would need
a second HTTP stack), niquests would rewrite the host application's `urllib3`, and urllib3 has no async
API. The fork risk of httpx2 is real — twelve minor versions in four months, deprecations already in
flight — so the REST layer should depend on a `HTTPTransport` Protocol of our own (send request model →
response model, streaming body, multipart) with httpx2 as the sole shipped implementation, exactly
mirroring the WebSocket decision.

## Sources

Mattermost / gorilla:
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/api4/websocket.go — upgrader fields (no `EnableCompression`)
- https://raw.githubusercontent.com/mattermost/mattermost/master/server/channels/app/platform/web_conn.go — no `EnableWriteCompression`
- https://pkg.go.dev/github.com/gorilla/websocket#Upgrader — `EnableCompression` semantics

picows:
- https://pypi.org/pypi/picows/json — 2.1.3, release dates, wheels, deps
- https://github.com/tarasko/picows (repo metadata, releases via `gh api repos/tarasko/picows/releases`, contributors)
- https://github.com/tarasko/picows/blob/master/picows/api.py — `ws_connect` signature and docstrings
- https://github.com/tarasko/picows/blob/master/picows/picows.pyi — `WSListener`, `WSTransport`, `WSFrame`, enums
- https://github.com/tarasko/picows/blob/master/picows/__init__.py — exception exports
- https://github.com/tarasko/picows/blob/master/docs/source/guides.rst — free-threaded Python guide
- https://github.com/tarasko/picows/blob/master/README.md — features, benchmark link
- https://github.com/tarasko/websocket-benchmark — benchmark method and commentary

websockets:
- https://pypi.org/pypi/websockets/json — 17.1, release dates
- https://raw.githubusercontent.com/python-websockets/websockets/main/src/websockets/asyncio/client.py — `connect` signature, proxy code
- https://websockets.readthedocs.io/en/stable/project/changelog.html — 14.0–17.1, compatibility policy
- https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html — `latency`, `ping`, close codes
- https://websockets.readthedocs.io/en/stable/topics/proxies.html — proxy discovery, TLS-in-TLS

aiohttp:
- https://pypi.org/pypi/aiohttp/json — 3.14.3, deps
- https://docs.aiohttp.org/en/stable/client_reference.html — `ws_connect`, `ClientWebSocketResponse`
- https://docs.aiohttp.org/en/stable/client_advanced.html — proxies, SSL, fingerprint
- https://docs.aiohttp.org/en/stable/changes.html — 3.13.0 free-threading, 3.14.x WebSocket fixes
- https://github.com/aio-libs/aiohttp/blob/master/aiohttp/client_ws.py — `ClientWSTimeout`, `_pong_not_received`, `receive(timeout)`

wsproto / precedents:
- https://pypi.org/pypi/wsproto/json — 1.3.2 release history
- https://github.com/python-hyper/wsproto/tree/main/src/wsproto — file sizes
- https://github.com/encode/httpcore/tree/master/httpcore/_async and `_backends` — h11 driver sizes
- https://github.com/frankie567/httpx-ws/tree/main/httpx_ws — `_api.py` size

httpx2 / httpx-ws / niquests / urllib3:
- https://pypi.org/pypi/httpx2/json, https://pypi.org/pypi/httpx/json, https://pypi.org/pypi/httpx-ws/json, https://pypi.org/pypi/niquests/json, https://pypi.org/pypi/urllib3/json, https://pypi.org/pypi/anyio/json, https://pypi.org/pypi/uvloop/json
- https://github.com/pydantic/httpx2/blob/main/README.md — stewardship statement, truststore
- https://github.com/pydantic/httpx2/blob/main/src/httpx2/CHANGELOG.md — fork point, 2.6.0 WebSocket, 2.10.0 fixes
- https://github.com/pydantic/httpx2/blob/main/docs/websockets.md — `client.websocket()` API, defaults, exceptions
- https://frankie567.github.io/httpx-ws/reference/httpx_ws/ — `aconnect_ws`, exceptions, task group
- https://niquests.readthedocs.io/en/latest/user/quickstart.html — WebSocket over HTTP/1.1, `wss+rfc8441://`
- https://github.com/jawah/urllib3.future/blob/main/README.md — namespace shadowing, async, WS
- https://urllib3.readthedocs.io/en/stable/v2-migration-guide.html — no async API, HTTP/2 fundraising banner
