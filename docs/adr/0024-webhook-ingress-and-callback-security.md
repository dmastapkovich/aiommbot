---
status: accepted
date: 2026-09-03
ticket: "#20"
---

# Interactive callbacks are events with a payload-bound reply channel; the webhook plugin is a bare ASGI callable; authenticity is a default-on self-issued HMAC token with no expiry unless configured

Mattermost delivers button clicks and dialog submissions as one HTTP POST per interaction with
no signature, no retry, a 30 s timeout shared with `trigger_id`, a 1 MiB reply cap, and turns any
non-200 into a user-visible error; field errors of a dialog are expressible only in the reply body
(`docs/research/11`, `16`). 0.4.x always answered `{"status":"Ok"}`, so `update`, `ephemeral_text`
and dialog `errors` were impossible, and it carried 2,158 lines of bespoke cryptography. We
decided:

- **Same event model.** Callbacks are `Event[InteractiveAction]` and `Event[DialogSubmission]`
  dispatched through the same routers, filters, DI and middleware as WebSocket events
  (ADR-0012). The only difference is `meta.reply`: present and typed for webhook-delivered
  events, absent otherwise. Every mature peer with two transports funnels callbacks into one
  dispatch entry; hikari's split pays with two programming models.
- **Reply channel.** The reply type is bound to the payload — `ActionReply(update,
  ephemeral_text, skip_slack_parsing, goto_location)`, `DialogReply(errors, error, form)` — and is
  sent at most once. A handler that does not reply, an `Unhandled` walk or a `Failed` outcome all
  produce an **empty 200**; never 404, 202 or 5xx. The reply **deadline defaults to 10 s**
  (strictly under the server's 30 s with two thirds of margin; GitHub's hard limit; Slack's and
  Discord's 3 s is unnecessary because Mattermost has no follow-up URL and accepts UI in the
  reply). At the deadline the transport writes the default reply and the handler continues; a
  later `reply.send` returns the typed outcome `ReplyAlreadySent` and later effects go through
  the Runtime. Dialog field errors are therefore deliverable only before the deadline, which the
  documentation states plainly. Reply bodies are checked against the 1 MiB cap.
- **Bare ASGI callable.** The webhook plugin exposes `webhook_app(bot) -> ASGIApp` — one POST
  route written as an ASGI function with no framework and no added dependency (Bolt and hikari
  precedent) — plus `handle_callback(body, headers) -> CallbackResponse` for non-ASGI hosts and
  tests, and a tiny health route. The application hands it to uvicorn or hypercorn or mounts it in
  its FastAPI or Litestar app; starting a server from the CLI is the CLI extra's business (#30),
  never the plugin's or the Core's (ADR-0002).
- **Authenticity is default-on.** The server signs nothing towards an external URL, so RFC 9421
  and Standard Webhooks do not apply as transport schemes; the only credential is what the bot
  places in button `context` and dialog `state`, which the server keeps from clients. Following
  CISA's and OWASP's "secure by default", verification is **on whenever the webhook plugin is
  enabled**: a missing key is a check error unless `authenticity="off"` is written explicitly;
  `strict | warn` remains for migration and `warn` is a check warning outside development. The
  codec sits behind the `CallbackTokenCodec` Protocol. The bundled codec is a **stdlib HMAC-SHA256
  compact token** modelled on Standard Webhooks and RFC 8725: `v1.<base64url(payload)>.
  <base64url(mac)>`, MAC over version and payload, no `alg` field, claims `{kid, iat, exp?, aud =
  bot id, act = action or callback id, sub? = intended user, jti?}`, `hmac.compare_digest`, key
  rotation through `signing_keys` plus `active_kid`, about 150 bytes. `pyseto` (PASETO v4.local)
  ships as the `aiommbot[paseto]` extra behind the same Protocol for teams that want a
  standardised format. Verification runs in the transport **before** an Event exists; `Missing` or
  `Invalid` under `strict` ends the request with an empty 404 without invoking handlers, and the
  body is never logged. itsdangerous (SHA-1 default, no key id, still needs a claims wrapper) and
  Fernet/Branca (encryption adds nothing and pulls `cryptography`/libsodium) were rejected.
- **No expiry by default.** Posts with actions routinely live for weeks, so the default token has
  no `exp`; `default_ttl` is a plugin setting and any button or dialog may set its own. When a TTL
  is set, `clock_leeway` (120 s) applies. A `NonceStore` on `KeyValueStore` is **opt-in** for
  single-use buttons and dialogs (`jti`). Verification yields a typed union — `Verified(claims)`,
  `Missing`, `Invalid(reason)`, `Expired`, `Replayed`, `ActorMismatch` — and `Expired`/`Replayed`
  are routable `StaleAction` events whose default handler answers an ephemeral "this action has
  expired" and an `update` that disables the buttons. Actor binding (`sub`) is per button; a
  mismatch with the callback's `user_id` is `ActorMismatch`. Idempotency of the business effect
  stays in application services through compare-and-set, as at Stripe.
- **Logging.** At INFO: outcome class, `kid`, `act`, `post_id`, `channel_id`, `user_id`, token age,
  reply latency, whether the deadline fired. Never the token, `context`/`state`, `trigger_id` or
  the dialog `submission`. Metrics per outcome class.

## Considered options

- *Separate request/response model for webhook* — rejected: two programming models.
- *Immediate 200 always, replies only via REST (0.4.x)* — rejected: dialog field errors become
  impossible.
- *Deadline 3 s (Slack/Discord)* — rejected: one external call would already miss it, and
  Mattermost allows UI in the reply.
- *Starlette app in an extra* — rejected: a dependency and a host framework for one route.
- *Authenticity as an optional plugin, off by default* — rejected after research: it repeats the
  0.4.x audit finding and violates secure-by-default; the explicit `off` switch preserves the
  choice.
- *itsdangerous / Fernet / PASETO as the only codec* — rejected as above; PASETO stays optional.
- *Mandatory nonce store* — rejected: a distributed backend for every bot and broken long-lived
  buttons.
