---
status: accepted
date: 2026-09-03
ticket: "#21"
---

# The Mattermost REST client is a standalone typed API client: httpx2 behind an `HTTPTransport` Protocol, generated `Operation` descriptors under resource methods, pagination iterators, a narrow built-in retry policy, async first with a generated `Sync` face

0.4.8's `ApiManager` was ~930 lines over aiohttp that only a Bot could construct, parsed no error
body, handled no 429, and left one bot calling raw paths (`docs/research/09`, #21 resolution). The
maintainer's requirement is a client good enough to use **without a bot**. The dual-face rule
(ADR-0004) needs an HTTP library with a synchronous twin generated from one codebase; `httpx2`
mirrors `Client`/`AsyncClient` token for token, aiohttp has no sync face and niquests rewrites the
host application's `urllib3` (`docs/research/14`). We decided:

- **A standalone API client.** `MattermostClient(base_url, token, *, transport=None, timeout=...,
  retry=..., codec=..., observers=())` is an async context manager that knows nothing of Bot or
  Event; `token` is a `str` or a `TokenProvider` (ADR-0023), sent as `Authorization: Bearer` on
  every request, never in the URL or a log. `base_url` is the server URL; the client appends
  `/api/v4` and supports sub-path installations. The Adapter composes one per Bot; a script
  constructs one directly.
- **Three layers, two public.** `HTTPTransport` is a Core-owned Protocol at the level of raw HTTP —
  method, URL, headers, body or byte stream, multipart → status, headers, body or stream — with an
  in-memory implementation in `aiommbot.testing` and **`httpx2 >=2.12,<3` as the sole shipped
  implementation**, mirroring `WebSocketConnection` (ADR-0023); the fork risk of httpx2 is real and
  the Protocol is the insurance. The **API client** and the **Runtime** (ADR-0028) are public.
- **Naming.** The bare name is the asynchronous face — `MattermostClient`, `Runtime` — and the
  synchronous face carries the `Sync` prefix (`SyncMattermostClient`, `SyncRuntime`), generated
  under #22's mechanism with an explicit token map. Handlers are asynchronous by default and read
  `Runtime` without a prefix.
- **Operations are data.** The generator emits one frozen `Operation[Req, Resp]` descriptor per
  spec operation — method, path template, parameter names, request and response types, flags from
  the overlay — and resource groups by spec tag with `operationId` in snake case:
  `client.posts.create(...)`, `client.users.get(user_id)`. Every method is one line over its
  descriptor executed by a single hand-written executor. `Operation` is public and
  user-constructible: a server-plugin endpoint (`/plugins/<id>/...`) is declared as a typed
  `Operation` and run through `client.execute(op, ...)`, gaining auth, retries, observers and the
  error taxonomy. There is no raw `request(method, url)`.
- **Pagination.** Operations flagged `x-aiommbot-paginated` get both the page method and an
  `iter_<name>()` iterator over items that stops on a short page, with `per_page` at the server's
  maximum of 200; the generated sync face yields a plain iterator. Cursor-style endpoints
  (`since`/`before`/`after`) stay page methods in 0.5.0.
- **Retries are narrow, built in, and off by one setting.** `RetryPolicy` (stdlib): 2 retries,
  full-jitter backoff, only on network errors, 408, 429 and 5xx, honouring `Retry-After` and
  `X-RateLimit-Reset`; only for `GET`/`HEAD`/`PUT`/`DELETE` and for operations flagged
  `x-aiommbot-idempotency-key`. `create_post` is such an operation: the server deduplicates by
  `pending_post_id` for 30 s (`server/channels/app/post.go`, `deduplicateCreatePost`), so the
  client fills `pending_post_id` when absent and may retry a timed-out post without duplicating it.
  Other `POST`s never retry. `retries=0` disables; anything larger is a recipe over `stamina`.
  Mattermost's rate limiter is off by default and answers 429 as plain text, so `RateLimited`
  is derived from the status and headers, not from an `AppError` body.
- **Observability is optional, replaceable and never mandatory.** The client accepts
  `observers: Sequence[RequestObserver]` — a Protocol with `on_request`, `on_response`, `on_error`
  receiving a typed record: operation id, method, path template, status, duration, attempt,
  `X-Request-ID`, `error_id`, byte sizes. It **never** exposes bodies, headers, query strings or the
  token, and no switch turns that on; the built-in `DEBUG` log carries the same fields. The default
  is no observer at all, so an unconfigured client costs nothing. Three levels of adoption are
  supported deliberately:
  1. **Ours out of the box** — a first-party observer shipped as an extra emits spans and metrics
     under recognised conventions, ready to register in one line.
  2. **Yours by convention** — an application implements `RequestObserver` itself and emits whatever
     names, labels, log format or tracer it already uses. Several observers compose; each is
     isolated, so a failing observer is caught and logged and never breaks the call. Observers
     observe: they cannot alter the request, the response or the retry decision.
  3. **Yours by wrapping** — an application that must *change* behaviour decorates the
     `HTTPTransport` Protocol (headers, caching, its own retry or breaker) or adds Middleware over
     the dispatch layers (ADR-0020) for event-level instrumentation. Observation and modification
     are separate seams on purpose.
  The record shape, the first-party observer's conventions and whether `opentelemetry-api` is a
  dependency at all are confirmed by `docs/research/17` and finalised with the observability
  boundary in #29; the pluggability above is not up for renegotiation there.
- **Defaults are settings, not decisions**: timeouts (connect 5 s, read and write 30 s, pool 5 s;
  300 s for file operations), pool limits (httpx2's 100/20), HTTP/2 off (`http2` extra available).
  They live in the client's component document.

## Considered options

- *aiohttp behind a Protocol (`docs/research/04`)* — rejected after ADR-0004: no synchronous face,
  so the generated sync client would need a second HTTP stack.
- *niquests* — rejected: shadows `urllib3` in the host application.
- *httpx2 directly, no Protocol* — rejected: a young fork without insurance or an in-memory double.
- *Publish only the Runtime* — rejected: every new need becomes a new helper, and the raw
  escape hatch returns.
- *Allowlist of bot-relevant operations* — rejected: the client is meant to stand alone; 0.4.8
  already had one bot outside the allowlist.
- *Request objects as the only API* — rejected: unfamiliar for a standalone client and without
  resource-level completion; descriptors keep the sans-I/O core anyway.
- *No retries, `RateLimited` plus a stamina recipe* — rejected: a standalone client that gives up
  on the first connection reset reads as unfinished.
- *A built-in token-bucket rate limiter* — rejected: client-side state, useless across replicas, no
  peer does it.
- *Raw `request(method, path)` beside `execute`* — rejected: a second, untyped contract.
- *The client emitting metrics and spans itself under our own names* — rejected: it forces our
  conventions on every application and drags an observability dependency into the Adapter; a typed
  observer plus a first-party extra gives the same convenience without the lock-in.
- *Observers allowed to modify the request* — rejected: one seam doing two jobs; modification
  belongs to a transport decorator or Middleware.
