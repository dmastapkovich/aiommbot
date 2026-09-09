---
status: accepted
date: 2026-09-08
ticket: "#57"
amends: [ADR-0012, ADR-0024]
---

# The reply slot is a second, declared-contravariant type parameter on `Event` typed by a Core-owned `ReplyChannel[R]` Protocol — the Core's twelfth seam

[ADR-0012](0012-generic-event-envelope-with-adapter-payloads.md) puts an optional typed Reply
channel with a deadline in `Event.meta`, and
[ADR-0024](0024-webhook-ingress-and-callback-security.md) binds the reply type to the payload —
`ActionReply` for an `InteractiveAction`, `DialogReply` for a `DialogSubmission`. Both values live
in the adapter-specific Webhook plugin, which the Core may not import
([ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md)), and `Any` and
`TYPE_CHECKING` imports are both forbidden in the public contract
([ADR-0006](0006-architectural-tenets-of-the-core.md) tenet 7), so the slot's type is a Protocol the
Core owns. We decided:

- **`Event[P, R]`, with `R` declared contravariant and defaulted to `Never`.** `R = TypeVar("R",
  contravariant=True, default=Never)` comes from the one compat module
  ([ADR-0008](0008-python-floor-3-12-with-typing-extensions.md)); `Event(Generic[P, R])`,
  `EventMeta(Generic[R])` and `ReplyChannel(Protocol[R])` share it, and `meta.reply` is
  `ReplyChannel[R] | None`. `Event[Posted]` is written as before; a callback is written
  `Event[InteractiveAction, ActionReply]`. The variance is *declared* because inference is not
  available to us: the `R = Never` default in PEP 695 syntax is 3.13-only and the floor is 3.12; the
  compat `TypeVar` cannot carry `infer_variance` under mypy; and on 3.13 the dataclass-synthesised
  `__replace__` puts `R` in a parameter position, so pyright and ty infer a frozen `EventMeta[R]`
  invariant ([`docs/research/20`](../research/20-reply-slot-variance-and-capability-typing.md) §1).
  Contravariance is what lets a Handler that ignores the slot annotate `Event[InteractiveAction]`
  and receive an `Event[InteractiveAction, ActionReply]`; `Never` is not a placeholder, because
  `ReplyChannel[Never]` has no callable `send`, so "this delivery cannot be answered" is a fact the
  type checker enforces rather than a runtime `None` check somebody forgets. These three types are
  the one permanent exception to the PEP 695 rule of the engineering style; `components/event.md` §9
  records it.
- **`ReplyChannel[R]` is a Core Protocol — the twelfth seam, and the one *provided* seam of the
  inventory ([ADR-0038](0038-seam-inventory-records-the-direction-of-the-call.md))**, sized to its
  single consumer, the Handler: `send`, `sent`, `deadline` and nothing else. It is specified in
  [`components/event.md`](../design/components/event.md). The Webhook plugin implements
  `ReplyChannel[ActionReply]` and `ReplyChannel[DialogReply]` and owns those two reply values; the
  testing toolkit ships the recording implementation. `send` returns `None | ReplyAlreadySent` —
  "already answered" is a branch the immediate caller takes in normal operation — and raises when
  the write itself fails, which keeps one representation per failure
  ([ADR-0034](0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md)).
- **`ReplyAlreadySent` is Core-owned, defined beside `ReplyChannel`.** It is the fieldless unit
  variant of the closed union `send` returns — a Typed outcome, not an error. A name in a Core
  return annotation is a real import, and the vocabulary a seam names belongs to the layer that owns
  the seam ([`docs/research/20`](../research/20-reply-slot-variance-and-capability-typing.md) §2);
  the Webhook document describes when the value is produced and never redefines it. The marker
  clause of [ADR-0035](0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md)
  governs the writing order of documents, not the import graph, and is untouched.

## Considered options

- *`class Event[P, R = Never]` with the variance inferred* — rejected: the spelling is unavailable
  on the 3.12 floor, and where it is available three of four checkers infer `R` invariant, because
  `EventMeta[R]` in a parameter of `derive` and the synthesised `__replace__` both put `R` in an
  input position ([`docs/research/20`](../research/20-reply-slot-variance-and-capability-typing.md)
  §1.2, variants A and B).
- *A non-generic `ReplyChannel` whose `send` takes a marker base `Reply`* — rejected: it is shorter
  to read and it lets a Handler send a `DialogReply` into an `InteractiveAction` slot, which is
  exactly the binding [ADR-0024](0024-webhook-ingress-and-callback-security.md) makes explicit. The
  mistake would surface as a Mattermost 400 rather than as a checker error.
- *A generic `EventMeta[R]` with `Event[P]` unparametrised* — rejected: `R` has nowhere to come
  from, so every Handler receives `ReplyChannel[Never]` and the option collapses into the previous
  one with extra syntax.
- *Invariant `R` plus an explicit widening operation such as `without_reply() -> Event[P]`* —
  rejected: the Dispatcher, or every Handler author, must call it, and the widening has to rebuild
  `EventMeta[Never]` field by field, which duplicates the field list of `EventMeta` — the objection
  [ADR-0037](0037-derive-is-the-only-enrichment-path-for-an-event.md) raises against
  `derive(**fields)`
  ([`docs/research/20`](../research/20-reply-slot-variance-and-capability-typing.md) §1.2, variant
  D).
- *The reply channel injected beside the envelope as a separate Handler parameter, or as a built-in
  injectable* — rejected: it loses the payload-to-reply binding of
  [ADR-0024](0024-webhook-ingress-and-callback-security.md) under all four checkers, since
  `handler(event: Event[Posted], reply: ReplyChannel[ActionReply])` type-checks and only the DI
  could reject it at start-up; it also contradicts
  [ADR-0012](0012-generic-event-envelope-with-adapter-payloads.md) and the `EventMeta` row of
  [ADR-0019](0019-handler-parameter-resolution-rules.md), and makes the slot invisible to the
  Inbound middleware that [ADR-0020](0020-two-layer-middleware-chain.md) allows to derive an
  enriched envelope
  ([`docs/research/20`](../research/20-reply-slot-variance-and-capability-typing.md) §1.2, variant
  E).
- *`ReplyAlreadySent` owned by the Webhook plugin* — rejected: the Core Protocol names it in a
  return annotation, so the Core would import upward, which the `forbidden` contract of
  [ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md) rejects on day one.

## Consequences

- `ReplyChannel` and its conformance suite join the substitution surface: the suite is the testing
  toolkit's ([ADR-0047](0047-a-conformance-suite-per-core-seam.md)) and covers single use, the
  deadline, concurrent `send` and cancellation, run against the Webhook slot and the recording slot
  alike.
- Every document that names `Event` in its own contract carries the second parameter. Where it does
  not care about the slot it writes `Event[P]`, which the declared contravariance makes correct
  rather than merely tolerated.
- Adding a third type parameter is one line after `R`, with its own default and declared variance;
  no existing annotation changes.
