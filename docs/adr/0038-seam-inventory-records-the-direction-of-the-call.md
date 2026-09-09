---
status: accepted
date: 2026-09-08
ticket: "#84"
---

# The Core's seam inventory records the direction of the call — eleven required Protocols and one provided

[ADR-0036](0036-reply-slot-as-a-second-type-parameter-over-a-core-owned-reply-channel.md) makes
`ReplyChannel[R]` the Core's twelfth seam, and [§5.4](../design/05-building-block-view.md) has to
hold it. A seam inventory organised on substitutability — Feathers' direction-neutral definition
([`docs/research/19`](../research/19-provided-and-required-protocol-inventories.md)) — admits it; one
organised on the supply side, "every Protocol the Core owns, who implements it", cannot, and is
false anyway: the six `Contributes*`/`HasLifecycle` Protocols of
[ADR-0015](0015-plugin-contract-and-composition.md) are Core-owned and are not rows. The twelfth
Protocol makes the difference visible, because it is the first whose caller is user code. We
decided:

- **§5.4 carries a *Direction* column with UML's pair, `required` and `provided`.** A `required`
  seam is one the Core calls out through and an outside party implements — the eleven existing rows.
  A `provided` seam is one the Core hands to user code as a typed capability, which user code then
  calls — `ReplyChannel[R]`, and today nothing else. The vocabulary is chosen because **every
  doctrine that distinguishes these at all uses the same discriminator — the direction of the call —
  and none discriminates on who supplies the implementation**: Cockburn's primary/secondary rests on
  "who triggers or is in charge of the conversation", Martin's Input/Output Port on flow of control
  *because* source dependencies are made uniform, DDD's Open Host Service on being upstream. UML is
  the sharpest of them and the closest fit: `provided` and `required` are two derived properties of
  **one port**, with two glyphs on one diagram. Evidence:
  [`docs/research/19`](../research/19-provided-and-required-protocol-inventories.md) §2.
- **One table, not two.** UML keeps both directions on one diagram and Cockburn keeps both flavours
  in one hexagon, separated by position rather than by artefact. A second table would also make one
  row a section of its own, and §5.4's job is to be the single place a reader can count the
  substitution surface.
- **The count is stated as "fourteen Protocols on twelve seams — eleven required, one provided".**
  Rows and Protocols differ because two rows pair an asynchronous and a synchronous Protocol
  (`HTTPTransport`/`SyncHTTPTransport`, `TokenProvider`/`SyncTokenProvider`). Wherever the figure is
  repeated — §5.10, `TRACKER.md`, `engineering-style.md` §1, ADR-0006 — it carries the split, so a
  reader never learns the number without learning that it has two kinds in it.
- **`seam` remains a single rank in §5.0.** Direction is an attribute of a seam, not a fourth rank:
  the rank table answers "does this get a design document of its own", and both directions answer
  no. The three ranks stay component, part and seam.
- **§5.4's membership rule is stated positively, replacing "every Protocol the Core owns".** A
  Core-owned Protocol is a §5.4 row when it is ranked `seam` — that is, when it is not itself a
  component and not a part of one. `Filter`, `Extractor` and `Middleware` are components,
  `Provider` and `Check` are parts, and the IdentityCache Protocol is excluded by ownership because
  it is the Adapter's. The six `Contributes*`/`HasLifecycle` Protocols are ranked by nothing today;
  that gap is a discovery of this ticket and is routed to its own ticket rather than settled here.
- **The *Specified in* column is authoritative, and §5 now says so itself.** ADR-0035 ruled that the
  prose "a Protocol is specified inside the document of the component that consumes it" loses to the
  column, having found it false for five of eleven rows. `ReplyChannel` breaks the same prose a
  third way: its document is `event.md`, which is neither the consumer's — the consumer is the
  Handler, user code, which has no document — nor the implementation's. Rather than record a third
  correction in a third ADR, this one lifts ADR-0035's ruling into §5.0 and §5.4 as the rule, so the
  prose that keeps being wrong stops being written. ADR-0035 counted six rows where the prose held and
  five where it did not; its conclusion is unchanged.

## Considered options

- *One more ordinary row, no column* — rejected, though it is the cheapest and the closest to
  ADR-0036's letter. It leaves the title-versus-introduction disagreement unresolved, and a reader
  of a flat table concludes that a Handler substitutes a `ReplyChannel` implementation the way an
  application substitutes a `KeyValueStore`. It never does; the Webhook plugin supplies the only
  one it will ever see.
- *Keep `ReplyChannel` out of §5.4 as a part of `Event`* — rejected on cost, not on principle. It
  has the strongest ecosystem support: no project surveyed puts a handed-out capability in the same
  inventory as its pluggable backends, and several name the split in their own vocabulary
  ([`docs/research/19`](../research/19-provided-and-required-protocol-inventories.md) §3). But
  those projects all type the handed-out capability
  as a **concrete class**, which [ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md)
  forbids us: the Core may not name the Webhook plugin's reply types. Having been forced into a
  Protocol with a shipped double and a conformance suite, we would then be hiding the one Protocol
  that most looks like the others. It also saves no reconciliation: `engineering-style.md` §1 and
  ADR-0006 both claim a *substitution surface*, which ADR-0036 grows regardless of the table the row
  lands in — and it would need an ADR overriding ADR-0036's own framing, committed in six places.
- *Two blocks inside §5.4 instead of a column* — rejected: it is what the peer projects and the one
  published extension-point inventory do, but it makes a heading and a table for a single row, and
  the two doctrines with the most precise vocabulary both keep the two kinds in one picture.
- *A generic `Kind` column keyed on who implements the Protocol* — rejected: it is the axis none of
  the splitting doctrines uses, it does not separate `ReplyChannel` from `TokenProvider` (whose
  shipped implementations are already "none — the application's") or from `RequestObserver` (already
  plural and application-implemented), and it would invite the six `Contributes*` Protocols in as a
  second class of six, turning a reconciliation into a scope decision that belongs to `bot.md`.

## Consequences

- The inventory is expected to stay at one `provided` row. The condition that produces one is
  narrow and conjunctive — a Core-owned data type with a field whose value comes from a higher layer
  and is *called*, not merely read, by user code — and everything else a Handler receives arrives by
  type-keyed dependency injection, where the key is the concrete type and the Core never has to name
  it. `EventMeta`'s field list is closed at five data fields and one callable, and
  [ADR-0037](0037-derive-is-the-only-enrichment-path-for-an-event.md) fixes the envelope at
  "exactly one method. Everything else about it is data". A second request/response Transport
  reuses `ReplyChannel[R]` with a new `R` and adds no row. See `docs/research/19` §3.2.
- A column with eleven identical cells is the price of the twelfth being legible. It is paid once,
  and it makes the axis explicit for every seam added later, which is the property the flat table
  did not have.
- `engineering-style.md` §1 states the substitution surface with both directions. The rules it is
  held by — `ST-SOL-04`, `ST-SOL-05` — are unchanged: `ReplyChannel` is sized to one consumer and
  names its conformance suite.
- The six `Contributes*`/`HasLifecycle` Protocols are Core-owned public API under semantic
  versioning with no rank anywhere in §5. Ranking them is #85's question; this ADR only records that §5.4's membership rule does not silently include them. On the
  *Direction* axis they are `required` — the Bot calls them — so the discriminator this ADR adds
  does not by itself admit them.
