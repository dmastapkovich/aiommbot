---
status: accepted
date: 2026-09-07
ticket: "#41"
---

# The order in which component design documents are written is a topological sort of structural §3 dependencies, not the layer table

[ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md) fixes the direction of every
allowed *import*, and it is tempting to read it as the order in which the 27 component design
documents should be *written*. It is not: a document is ordered by what its **§3 Public contract**
cannot be written without, and that graph does not follow the layer table. We decided the ordering
rule to be:

> Document **X** is written after document **Y** if, and only if, §5.4 or the *Document* column of
> §5.5–5.9 names **Y** as the document that specifies a Protocol or part appearing in **X**'s §3 as
> a parameter type, as a return or raised type with structure, or as a Protocol **X** implements or
> consumes as a seam.

- **Structural need, not mention.** A name that appears in §3 only as a key, a label or an element
  of a list creates no edge, because its meaning is fixed by an ADR and there is nothing for the
  other document to elaborate. The built-in injectable keys of
  [ADR-0019](0019-handler-parameter-resolution-rules.md) are a list; the exception roots
  `AiommbotError`, `FatalError` and `AiommbotWarning` of
  [ADR-0021](0021-core-error-boundary.md) are markers. Neither orders anything. Without this
  clause the rule contradicts itself: `dependency-provider.md` would depend on `bot.md`, which
  depends on it, and the Core would depend on the Adapter through the injectable `Runtime`.
- **Collaboration is not contract.** A component named only in §4, §5 or §8 imposes no order. A
  document links its neighbours in both directions whatever the order, so only §3 can carry one.
  §5.6 calls the two Faces "thin I/O layers over the Exchange", and that reads like an edge; it is
  not one. A Face performs I/O beneath the Exchange and its own contract is the four transport and
  token Protocols of §5.4, so `face.md` waits for nothing and the apparent
  `face → exchange → api-client → face` cycle never forms.
- **An emitted artefact is a return with structure.** `model-generator.md` waits for
  `generated-model.md`, because the generator's public contract is the shape of what it emits and
  that shape is the other document's. The clause is narrow: it covers a build-time component whose
  output another document specifies, not one that merely passes values of an imported type.
- **A part borrowed into another layer's document does not move that document.** §5.6 assigns
  "Platform filters and router aliases" to `filter.md` and `router.md`, so that the alias story
  sits with the mechanism it reduces to. That does not put the Core's `Filter` and `Router` behind
  `event-registry.md`: the rule is stated over the §3 of the component a document is *named for*,
  and the Adapter's `Text` and `ChatType` are not the Core `Filter`'s public contract. They are
  described further down the same file.
- **The error boundary is not a link of the Middleware chain.** §5.5 calls it "the outermost link",
  but [ADR-0021](0021-core-error-boundary.md) has it return `Failed` to the *Transport*, which puts
  it around the chain rather than inside it. `error-boundary.md` waits only for `dispatcher.md`,
  which owns `Outcome`.
- **In §5.4 the *Specified in* column is authoritative, not the prose above it.** That prose says a
  Protocol is specified in the document of the component that *consumes* it, which holds for six of
  the eleven rows. In the other five the seam is named after its implementation and the document is
  the implementation's — `DependencyProvider`, `KeyValueStore`, `LockProvider`, `Codec`,
  `CallbackTokenCodec`. Reading the prose instead of the column inverts three pairs, putting
  `Router` before `Filter` and `Extractor`, `Webhook` before `Callback token`, and `Exchange` before
  `API client`. [§5.0 and §5.4](../design/05-building-block-view.md) state the column's authority
  themselves ([ADR-0038](0038-seam-inventory-records-the-direction-of-the-call.md)); this ADR
  records the ruling. The *Consumed by* column of the same table is authoritative in the same way
  about who waits: it names Webhook on the `KeyValueStore` row and the Transports on the `Codec`
  row, and those edges hold even where the consumer reaches the seam through a part of a third
  document.
- **Two documents may be written in parallel exactly when neither is named as specifying a contract
  in the other's §3** — the same rule read sideways. It is carried by GitHub's native `blocked_by`
  dependencies on the `LLD:` tickets, so the frontier is computed rather than remembered, and by
  the `Wave` column of [`components/README.md`](../design/components/README.md), which is derived
  from those edges and from nothing else.

## Considered options

- *Cite only contracts that are already written* — rejected: unachievable. `dispatcher.md` owns
  `Outcome`, which `error-boundary.md` returns as `Failed`; `error-boundary.md` owns the exception
  roots that `dispatcher.md` must name. Under the strict reading the two block each other, and the
  same closes between `Router`, `Dispatcher` and `Middleware`.
- *Bottom-up along the [ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md) layer
  table, with the seam-owning consumer first within a rank* — rejected: it is the reading suggested
  when #36 closed, and it rests on the §5.4 prose the column contradicts. It also costs roughly two
  extra waves by holding back four documents that depend on nothing at all — `generated-model`,
  `codec`, `face` and the storage backends.
- *The layer table as a soft tie-breaker inside a wave* — rejected: it changes no edge and adds a
  second source of truth for a question the graph already answers.
- *No order at all, 27 equal tickets* — rejected: the order is the decision #41 exists to make, and
  without it every author re-derives the same graph.

## Consequences

- The 27 documents fall into **six waves**, the first of which holds seven documents that wait for
  nothing. The layer ranks interleave: `codec` and the storage backends open on the same day as
  `event`, and `api-client` opens before `dispatcher`.
- Two results are counter-intuitive and are consequences, not choices. `state` is written in the
  last wave because its §3 exposes `InState`, a `Filter`, and an isolation Inbound `Middleware` —
  two Core Protocols it implements. `api-client` is written before `exchange` because §5.6 assigns
  `RetryPolicy` and the `ApiError` hierarchy to the client, and the sans-I/O Exchange classifies
  responses into them.
- The rule is stated over §3 alone, so a document that grows its public contract later can acquire
  an edge that did not exist when its ticket was cut. The `Wave` block of each ticket names the
  reason for every edge so that such a change is visible as a contradiction rather than as a
  surprise.
