---
status: accepted
date: 2026-09-08
ticket: "#57"
---

# `Event.derive` is the only way to obtain an enriched envelope, and `dataclasses.replace` on an `Event` is banned

[ADR-0020](0020-two-layer-middleware-chain.md) lets a Middleware "pass a derived envelope with
enriched `meta`" and forbids it to alter the payload, because "handlers must trust what they
receive". As written, that invariant is a review note: `Event` is a frozen dataclass, so
`dataclasses.replace(event, payload=other)` type-checks, runs, and hands the next link an envelope
whose `kind` and `payload` no longer agree. The `ST-TYP-16` example in
[`engineering-style.md`](../design/engineering-style.md) reaches for exactly that spelling. We
decided to make the invariant a signature:

- **`Event.derive(*, meta: EventMeta[R]) -> Event[P, R]`** is the whole enrichment surface. It
  accepts a replacement `EventMeta` and nothing else, so the ADR-0020 rule cannot be broken through
  the public API. `EventMeta` itself is enriched with `dataclasses.replace`, which is safe there:
  every field of `EventMeta` is metadata a Middleware is allowed to touch.
- **`dataclasses.replace` on an `Event` is a banned spelling**, enforced as `semgrep:ST-TYP-17` and
  listed in the pattern catalogue of `engineering-style.md` §3.3 when #36's rulebook next moves.
  The rule is narrow: it names `Event` and no other frozen type.

## Considered options

- *`dataclasses.replace` only, no method of our own* — rejected: it adds no public name and it is
  what `ST-TYP-16` already shows, but it leaves the one invariant nine downstream documents depend
  on to a review checklist. An immutable envelope whose payload can be swapped in flight is the
  defect ADR-0020 rules out, one indirection later.
- *`derive(**meta_fields)`, flattening the metadata fields onto the call* — rejected: it reads
  better at the call site and it duplicates the field list of `EventMeta` in a second signature, so
  adding a metadata field becomes a two-file change and the two can disagree.
- *A mutable `Event` with an `enrich()` method* — rejected by ADR-0006 tenet 5; it also removes the
  free sharing across tasks that makes the envelope safe on the free-threaded build
  ([ADR-0008](0008-python-floor-3-12-with-typing-extensions.md)).

## Consequences

- `Event` carries exactly one method. Everything else about it is data, which keeps it readable as
  the value it is.
- The Middleware document (#78) states the ordering of enrichment; this ADR only fixes what the
  envelope permits.
