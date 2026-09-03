---
status: accepted
date: 2026-09-03
ticket: "#21"
---

# API failures are exceptions in a typed hierarchy that carries Mattermost's `AppError` fields and a retryable classification; expected outcomes stay values where earlier decisions put them

0.4.8 raised bare `aiohttp.ClientResponseError`s with `raise_for_status=True` and never read the
server's error body, so no bot could tell a revoked token from a missing channel (#21 resolution).
Mattermost returns `AppError` JSON — `id`, `message`, `detailed_error`, `request_id`,
`status_code`, `props` — for every application error, plain text for 429, and `X-Request-ID` and
`X-Version-ID` on every response (`server/public/model/utils.go`, `client4.go`). We decided:

- **Exceptions, not result unions, for API calls.** Values remain where ADR-0014, ADR-0020 and
  ADR-0022 placed them — extractor results, dispatch `Outcome`, `StateContext` — because there the
  handler must decide; a failed REST call is exceptional for the caller and every mature client
  raises. Read operations raise `NotFound`; there are no `find_*` variants returning `None`.
- **Hierarchy.** Core: `AiommbotError` (root), `FatalError(AiommbotError)` (ADR-0021). Adapter,
  transport level: `TransportError` → `ConnectError`, `NetworkError`, `TimeoutError`,
  `ProtocolError` — the same four kinds as the WebSocket connection (ADR-0023). Adapter, API
  level: `ApiError(status, error_id, message, detailed_error, request_id, server_version)` with
  one subclass per HTTP class a caller acts on: `BadRequest` (400), `Unauthorized` (401),
  `Forbidden` (403), `NotFound` (404), `Conflict` (409), `PayloadTooLarge` (413),
  `RateLimited` (429, with `retry_after`), `ServerError` (5xx). `DecodeError` is raised when a
  2xx body does not match the model — contract drift, not a network fault — and carries the
  operation id and the decoder's message, never the body.
- **Retryable is a property, not a class tree.** Every exception exposes `retryable: bool`
  (network, timeout, 408, 429, 5xx → true; other 4xx, decode → false) so `RetryPolicy`, a plugin or
  `stamina` classifies without `isinstance` ladders.
- **Authentication loss is escalated outside the client.** The API client raises `Unauthorized`
  for 401 `api.context.session_expired.app_error`. In a Bot, the shared `AuthLossDetector`
  (ADR-0023) retries once with a refreshed token and then raises `FatalError(AuthRevoked)`; a
  standalone script sees `Unauthorized` and decides itself.
- **No payload in any exception.** Exceptions carry `request_id`, `error_id`, `status`, the
  operation id and the path template; never the request body, the response body, headers, query
  strings or the token.

## Considered options

- *`Ok[T] | ApiFailure` from every call* — rejected: every `await runtime.answer(...)` becomes a
  union match for a case the handler cannot act on.
- *`find_*` helpers returning `None` beside raising getters* — rejected: two contracts for one
  question; a caller that wants `None` writes one `except NotFound`.
- *Retryable as a mixin class* — rejected: the property composes with any subclass and with
  transport errors alike.
