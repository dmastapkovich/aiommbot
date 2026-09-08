---
status: accepted
date: 2026-09-08
ticket: "#57"
---

# The reply slot is a second type parameter on `Event` typed by a Core-owned `ReplyChannel[R]` Protocol — the Core's twelfth seam

[ADR-0012](0012-generic-event-envelope-with-adapter-payloads.md) put "an optional typed reply
channel with a deadline" in `Event.meta` and [ADR-0024](0024-webhook-ingress-and-callback-security.md)
bound the reply type to the payload — `ActionReply` for an `InteractiveAction`, `DialogReply` for a
`DialogSubmission`. Neither said how the Core spells that type, and the Core may import neither
value: both live in the adapter-specific Webhook plugin
([ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md)). With `Any` and
`TYPE_CHECKING` imports both forbidden in the public contract
([ADR-0006](0006-architectural-tenets-of-the-core.md) tenet 7), the slot's type has to be a
Protocol the Core owns. We decided:

- **`class Event[P, R = Never]`**, `meta: EventMeta[R]`, `meta.reply: ReplyChannel[R] | None`. The
  PEP 696 default comes from the one compat module
  ([ADR-0008](0008-python-floor-3-12-with-typing-extensions.md)), so `Event[Posted]` is written as
  before and a callback is written `Event[InteractiveAction, ActionReply]`. `Never` is not a
  placeholder: `ReplyChannel[Never]` has no callable `send`, so "this delivery cannot be answered"
  is a fact the type checker enforces rather than a runtime `None` check somebody forgets.
  Because `R` appears only in an argument position, `Event` is contravariant in it, which is what
  lets a Handler that ignores the slot keep annotating `Event[InteractiveAction]`.
- **`ReplyChannel[R]` is a Core Protocol, the twelfth**, sized to its single consumer, the Handler:
  `send`, `sent`, `deadline` and nothing else. It is specified in
  [`components/event.md`](../design/components/event.md); the Webhook plugin implements it and the
  testing toolkit doubles it. `send` returns `None | ReplyAlreadySent` — "already answered" is a
  branch the immediate caller takes in normal operation — and raises when the write itself fails,
  which keeps one representation per failure
  ([ADR-0034](0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md)).
- **`ReplyAlreadySent` creates no ordering edge.** It is named in `event.md`'s §3 as the fieldless
  marker `webhook.md` owns, which is the class
  [ADR-0035](0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md) exempts
  when it rules that the exception roots of ADR-0021 "are markers. Neither orders anything."
  `event.md` therefore stays in wave 1 and `webhook.md` keeps the value.
- **§5.4 and §5.10 of the building-block view now undercount.** They say eleven seam rows and
  thirteen Protocols, and the figure is repeated in ADR-0006 and in `engineering-style.md` §1.
  Following the precedent [ADR-0035](0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md)
  set — [§5](../design/05-building-block-view.md) is reviewed and owned by #38, so an ADR records
  the correction instead of editing it — this ADR is the authority for the twelfth seam, and a
  task ticket reconciles the four places that carry the count.

## Considered options

- *A non-generic `ReplyChannel` whose `send` takes a marker base `Reply`* — rejected: it is shorter
  to read and it lets a Handler send a `DialogReply` into an `InteractiveAction` slot, which is
  exactly the binding ADR-0024 chose to make explicit. The mistake would surface as a Mattermost
  400 rather than as a checker error.
- *A generic `EventMeta[R]` with `Event[P]` unparametrised* — rejected: `R` has nowhere to come
  from, so every Handler receives `ReplyChannel[Never]` and the option collapses into the previous
  one with extra syntax.
- *The reply channel as a built-in injectable instead of a field of `meta`* — rejected: it
  contradicts ADR-0012 and the `EventMeta` row of
  [ADR-0019](0019-handler-parameter-resolution-rules.md), and it would make the slot invisible to
  the Inbound middleware that ADR-0020 allows to derive an enriched envelope.

## Consequences

- `ReplyChannel` and its conformance suite join the substitution surface: the suite is the testing
  toolkit's (#25) and must cover single use, the deadline, concurrent `send` and cancellation.
- The nine documents that name `Event` in their own contract carry the second parameter. Where they
  do not care about the slot they write `Event[P]`, which the contravariance makes correct rather
  than merely tolerated.
