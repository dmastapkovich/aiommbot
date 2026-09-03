---
status: accepted
date: 2026-09-03
ticket: "#19"
---

# The WebSocket gateway is one supervised reconnect loop with heartbeat, resume, seq continuity, a never-stalling reader and a graceful drain

A bot lives on one WebSocket for weeks. The Mattermost protocol facts (`docs/research/01`) and
the mechanics of mature real-time clients (`docs/research/02`) fix the design of the
`WebSocketTransport` plugin:

- **Structure.** One outer reconnect loop owns the connection state (`connection_id`, `last_seq`,
  backoff) and starts a `TaskGroup` per connection — reader, heartbeat, liveness monitor. Any
  task failing cancels its siblings; the loop classifies the exit against an explicit table:
  *transient* (network error, 1006, our own 4000) → backoff and resume; *resumable* (4001 sequence
  gap) → immediate resume; *fatal* (401/403 on the handshake, invalid URL, `not_authenticated`
  after a token refresh) → `FatalError` (ADR-0021).
- **Heartbeat, configurable.** The library answers server ping frames; the gateway also sends the
  JSON `ping` action every 30 s, as the official TS client does — it keeps proxies alive and
  verifies the session. A separate monitor treats **60 s without data of any kind** (2×
  interval) as a dead link: close with private code 4000 and reconnect with resume. Ping RTT and
  the pong's `server_time` feed observability. Interval, deadline and codes are settings with
  these defaults.
- **Backoff.** Full-jitter exponential: `uniform(0, min(300 s, 1 s · 2^n))`, the first delay
  randomised too, reset after 30 s of stable connection. Attempts are unbounded — the bot does
  not give up — but after a configurable count or duration the `Degraded` Signal fires for
  alerting. "No `hello` within 10 s" counts as a failure.
- **Resume and continuity.** Reconnect with `?connection_id=&sequence_number=`; enforce `seq`
  continuity — a gap closes with 4001 and resumes, never skips; replayed duplicates are deduped
  by `(connection_id, seq)` in memory. A `hello` carrying a new `connection_id` means state was
  lost: the sequence resets and the `Resynced(since=…)` Signal fires with the loss window;
  backfilling posts over REST is a first-party plugin or recipe on that Signal, because only the
  application knows what matters. Cross-resync dedup by `post.id` is an optional Inbound
  middleware on `KeyValueStore`.
- **The reader never stalls.** A full server send queue (256) drops the connection and the resume
  window, so the reader always drains the socket into a bounded queue served by N workers (a thin
  concurrency cap). Overflow is a typed `OverflowPolicy` per event kind: low-value kinds
  (`typing`, `status_change`, `presence`) drop the oldest with a `Dropped` Signal; posts and
  callbacks grow to a hard ceiling and only then drop with a Signal. Queue depth, drops and worker
  saturation are metrics; sizes, N and policies are settings.
- **Graceful drain.** On stop: close the socket first (1000/1001) so the server stops queueing
  for us, drain the queue and in-flight handlers within a grace period (default 25 s inside the
  30 s Kubernetes budget), then cancel the rest with `DrainTimedOut(count)`. Plugins stop in
  reverse topological order (ADR-0015).
- **Single consumer.** The transport requires `ProcessProfile.websocket_consumer=True` (a check
  error otherwise — `aiommbot run` can no longer raise a socket in a worker by accident). With a
  distributed `LockProvider` configured it takes a renewed single-consumer lease; a second replica
  waits in standby and takes over when the lease lapses — failover for free. Without a
  distributed lock, the declaration alone applies.
- **Authentication.** Bearer token on the handshake so `hello` arrives at once;
  `authentication_challenge` only as an option for header-stripping proxies. The token comes from
  the `TokenProvider` Protocol on every connection (static token trivial, vault rotation the
  application's). On `not_authenticated` from `ping` or 401 on the handshake: one retry with a
  refreshed token, then `FatalError` — a configuration error, not a network one. The token is
  never logged and never placed in the URL.
- **Loss of authentication is detected, not assumed.** The Mattermost server never closes a
  socket whose session was revoked or expired and sends no event: it silently drops every event
  and answers every JSON request, `ping` included, with
  `api.web_socket_router.not_authenticated.app_error` (`docs/research/15`). Bot tokens are
  personal access tokens whose session the server recreates on demand, so only deleting or
  disabling the token, disabling the bot or deactivating the user can kill a bot — always a
  configuration event, never a network one. Therefore the gateway **parses the reply to every
  JSON `ping`**; on `not_authenticated`, a close, or a pong timeout it runs a REST probe
  (`GET /api/v4/users/me`) through a shared `AuthLossDetector`: 200 → network trouble, reconnect
  with the same token; 401 `session_expired` → one retry with a token from `TokenProvider`, else
  `FatalError(AuthRevoked)` carrying `error.id`, `request_id` and `token_sha256`, never the
  token; 403 → fatal; 5xx/429 → backoff. Detection is bounded by one ping interval plus RTT. The
  0.4.x behaviour — treating a mute socket as a network cut and reconnecting forever — is exactly
  the silent-bot failure this rules out.
- **Library.** The gateway logic depends only on the Core-owned `WebSocketConnection` Protocol —
  connect with headers/query/TLS/proxy, `receive(timeout)` returning `Text | Binary | Closed`,
  `send_text`, `ping`, `close(code)`, four typed error kinds — so the library is replaceable.
  **`websockets` 17.x is the primary implementation**: zero dependencies, proxy support including
  TLS to the proxy and environment discovery, free-threaded, a five-year compatibility policy.
  **`picows` is an optional extra** behind the same Protocol for deployments that want its
  Cython data path; it has a single maintainer, a hard dependency on `aiofastnet` on the TLS path
  and no `https://` proxy support, so it is not the default. Both run the same contract test
  suite in CI; an in-memory connector is the test double. Mattermost never negotiates
  permessage-deflate, so compression is not a criterion (`docs/research/14`). The REST client
  candidate from the same research is `httpx2` behind an `HTTPTransport` Protocol; that decision
  is #21's.
- **Signals**: `Connected`, `Disconnected(reason)`, `Resumed`, `Resynced(since)`, `Degraded`,
  `Dropped(kind, count)`, `DrainTimedOut(count)`.

## Considered options

- *TS-client backoff (3 s × 7, then 3·n² to 300 s)* — rejected: little jitter, thundering herd on
  mass disconnects.
- *Finite attempts then process exit* — rejected: the restart burden moves to the orchestrator
  and contradicts ADR-0021.
- *Blocking the reader on a full queue* — rejected: against this server it becomes a disconnect
  and a lost resume window.
- *Unbounded queue (Slack SDK)* — rejected: memory grows silently under slow handlers.
- *Automatic post backfill inside the gateway* — rejected: the gateway cannot know what matters
  and would duplicate events.
- *Passive heartbeat (Go client)* — rejected: a mute expired session or a proxy cut is noticed
  after 100 s or never.
