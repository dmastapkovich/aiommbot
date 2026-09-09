---
status: accepted
date: 2026-09-09
ticket: "#29"
---

# `REDACTED_FIELDS` is forty field names that may never appear in a log record or an observability record, matched exactly on the normalised name; an exception's contents stay `ST-ERR-08`'s

`ST-LOG-04` requires one named list and left its membership to this ticket, declaring its scope as
"a log record, an exception or an observer" — which cannot hold, because `ST-ERR-08` and
[ADR-0034](0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md) deliberately
allow the short server `message` on an `ApiError` while
[`docs/research/17`](../research/17-http-client-observability.md) §7 forbids `message` in a record.
Nor can one flat set express "loggable but never a metric label", which is what
[ADR-0024](0024-webhook-ingress-and-callback-security.md) asks for with `user_id`, `channel_id` and
`post_id`. We decided:

- **Two sinks, not three.** The list governs what leaves the process past its caller: the fields of
  a **log record** and of an **observability record**. What an exception may carry stays
  `ST-ERR-08`'s own allow-list — `status`, `error_id`, the short `message`, `request_id` — because a
  caller catches an exception and inspects it in process and needs that text to decide, whereas a
  record is published. So `message` is on the list and our own log line records `error_id` instead.
- **The list bans names, not values, and wins every collision.** Where a safe fact collides with a
  banned name, the fact is recorded under a different key: the FSM state name is `flow_state`, never
  `state`; a `StateContext` draft is summarised as `flow`, never `data`; an exception is
  `error_type`, never `error`. That last one is why `error` is on the list at all — banning it
  mechanically enforces the rule of
  [`docs/research/12`](../research/12-error-boundary-conventions.md), never `str(exc)` of an
  exception that might wrap a payload.
- **Matching is exact on the whole normalised name** — lower-cased, `-` mapped to `_` — never a
  substring, which is what lets `token_sha256`, `post_id` and `server_address` stay legal beside
  `token`, `post` and the banned `url`. One set covers all three namespaces a key can come from — a
  Python attribute, a JSON key, an HTTP header name — because they all end in the same place.
- **The membership, grouped by the reason each name is on it.** The list may only grow.

| Reason | Names |
|---|---|
| Credentials and secrets | `access_token`, `authorization`, `cookie`, `password`, `proxy_authorization`, `secret`, `signing_keys`, `token` |
| Content of a message or an event | `body`, `data`, `followers`, `mentions`, `message`, `payload`, `post`, `props`, `raw`, `text` |
| Interactive-action and reply fields | `context`, `ephemeral_text`, `errors`, `form`, `state`, `submission`, `trigger_id`, `update` |
| HTTP-level fields | `detailed_error`, `headers`, `multipart`, `query`, `url` |
| Names of people and places | `channel_display_name`, `channel_name`, `email`, `full_name`, `nickname`, `sender_name`, `team_domain`, `username` |
| Free text from an exception | `error` |

The counterparts that stay legal are named beside it so a reader sees the line: `attempt`, `act`,
`channel_id`, `connection_id`, `correlation_id`, `duration_ms`, `error_id`, `error_type`, `flow`,
`flow_state`, `handler`, `kid`, `kind`, `method`, `operation`, `outcome`, `path_template`,
`post_id`, `request_id`, `root_id`, `seq`, `server_address`, `server_port`, `server_version`,
`status`, `team_id`, `token_sha256`, `transport`, `user_id`.

- **Being loggable does not make a field a label.** An identifier in that second list may appear in
  a log record and in an observability record, and may become a metric label only if it is also in
  the label allow-list of
  [ADR-0051](0051-first-party-observability-plugin.md), which a test keeps disjoint from this list.

## Considered options

- *One list over all three sinks, with `message` on it* — rejected: `ApiError` would lose the field
  Mattermost uses to say why a call failed, and ADR-0027, ADR-0034 and `ST-ERR-08` would all be
  rewritten to remove a deliberate affordance.
- *One list over all three sinks, with `message` off it* — rejected: `message` is also the
  `CreatePost` body field, so nothing would catch the post text by name and `semgrep:ST-LOG-02`
  would lose its best rule.
- *Qualified names in the list (`dialog.state`, `event.data`)* — rejected: the tier of `ST-LOG-04`
  is `tool`, and a test sees a key in `extra` and not where the value came from, so the qualifier
  could never be checked and the rule would decay to review.
- *A second, positive allow-list of everything that may appear in `extra`* — rejected: it is
  stricter, and it contradicts both "there is exactly one list" and "the list may only grow", and
  every new safe fact in any of thirty components would edit a shared constant.
- *Dropping the names of people and places, since ADR-0024 permits the corresponding ids* —
  rejected: OWASP and ASVS V16.2.5 treat personal data separately from identifiers, and `UserRef`
  makes `Email` and `FullName` first-class resolvable types, so they will be at hand for whoever
  writes the next log line.

## Consequences

- `message` is doubly refused: it is on this list, and `Logger.makeRecord` raises
  `KeyError("Attempt to overwrite 'message' in LogRecord")` for it outright, along with every other
  reserved `LogRecord` attribute name — which `ST-LOG-05` now states as a limit with its source.
- The test the `tool` tier requires asserts non-intersection for log records and for observability
  record types; typed outcomes that legitimately carry content to their caller —
  `Verified(claims)`, `Conflict` — are not records and are outside its scope, and the rule says so
  rather than leaving it to be discovered.
