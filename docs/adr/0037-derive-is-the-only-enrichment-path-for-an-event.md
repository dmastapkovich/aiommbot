---
status: accepted
date: 2026-09-08
ticket: "#57"
amends: [ADR-0012, ADR-0020]
---

# `Event.derive` is the only way to obtain an enriched envelope, and `dataclasses.replace`, `copy.replace` and `__replace__` on an `Event` are banned

[ADR-0020](0020-two-layer-middleware-chain.md) lets a Middleware "pass a derived envelope with
enriched `meta`" and forbids it to alter the payload, because "handlers must trust what they
receive". On a frozen dataclass alone that invariant is a review note: `dataclasses.replace(event,
payload=other)` type-checks, runs, and hands the next link an envelope whose `kind` and `payload` no
longer agree. We decided to make the invariant a signature:

- **`Event.derive(self, *, meta: EventMeta[R2]) -> Event[P, R2]`** is the whole enrichment surface.
  It accepts a replacement `EventMeta` and nothing else, so the
  [ADR-0020](0020-two-layer-middleware-chain.md) rule cannot be broken through the public API. The
  result is typed by the `EventMeta` it receives, because an envelope's `R` is nothing but the `R`
  of its `meta`, and `reply` is one of the fields of `EventMeta` that a Middleware is allowed to
  touch; a Middleware that passes `replace(event.meta, seq=…)` gets `Event[P, R]` back unchanged.
  This is the one signature all four checkers accept together with the declared contravariance of
  [ADR-0036](0036-reply-slot-as-a-second-type-parameter-over-a-core-owned-reply-channel.md)
  ([`docs/research/20`](../research/20-reply-slot-variance-and-capability-typing.md) §1.2, variant
  C′). `EventMeta` itself is enriched with `dataclasses.replace`, which is safe there: every field
  of `EventMeta` is metadata a Middleware is allowed to touch.
- **`dataclasses.replace`, `copy.replace` and `__replace__` on an `Event` are banned spellings** —
  one operation under three names on 3.13 — enforced as `semgrep:ST-TYP-17` and listed in the
  pattern catalogue of [`engineering-style.md`](../design/engineering-style.md) §3.3. The rule is
  narrow: it names `Event` and no other frozen type.

## Considered options

- *`dataclasses.replace` only, no method of our own* — rejected: it adds no public name, but it
  leaves the one invariant every downstream document depends on to a review checklist. An immutable
  envelope whose payload can be swapped in flight is the defect
  [ADR-0020](0020-two-layer-middleware-chain.md) rules out, one indirection later.
- *`derive(**meta_fields)`, flattening the metadata fields onto the call* — rejected: it reads
  better at the call site and it duplicates the field list of `EventMeta` in a second signature, so
  adding a metadata field becomes a two-file change and the two can disagree.
- *`derive(*, meta: EventMeta[R]) -> Event[P, R]`, holding `R` fixed* — rejected: with `R` declared
  contravariant, ty reports the signature as inconsistent with the variance of `R`, and it says less
  than the truth — the result's `R` is the `R` of the `meta` passed in
  ([`docs/research/20`](../research/20-reply-slot-variance-and-capability-typing.md) §1.2, variant
  C).
- *A mutable `Event` with an `enrich()` method* — rejected by
  [ADR-0006](0006-architectural-tenets-of-the-core.md) tenet 5; it also removes the free sharing
  across tasks that makes the envelope safe on the free-threaded build
  ([ADR-0008](0008-python-floor-3-12-with-typing-extensions.md)).

## Consequences

- `Event` carries exactly one method. Everything else about it is data, which keeps it readable as
  the value it is.
- `derive` can attach or drop a Reply channel by passing an `EventMeta` with a different `R`. Who
  may do so, and in what order enrichment runs, is the Middleware document's (#78); this ADR only
  fixes what the envelope permits.
