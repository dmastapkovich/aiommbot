---
status: accepted
date: 2026-09-15
ticket: "#109"
---

# §4 ties its approaches to the five ranked quality goals in one table with a decision column, and motivates nothing item by item

Tip 4-2 is the only `essential` tip of §4 and it is a form rather than a content rule — the table
*Quality goal · Scenario · Solution approach · Link to details*, with a plain list offered beside it
— while [§4](../design/04-solution-strategy.md) named no quality goal at all and linked neither
[§1.2](../design/01-introduction-and-goals.md#12-quality-goals) nor
[§10](../design/10-quality-requirements.md), both of which exist now. We decided what §4 owes:

- **§4 opens with one table, one row per goal, in §1.2's rank order.** Five rows, because §1.2 ranks
  five goals; the table is an index into the approach items below it and states no approach of its
  own.
- **The columns are *Quality goal · The approaches that serve it · Why those · ADR*** — the column
  set of the published `doctoolchain-v4` document, the one arc42 document of the nine measured that
  keeps a decision register of its own and therefore had our problem. Tip 4-2's *Scenario* column is
  dropped: a scenario belongs to §10
  ([ADR-0068](0068-a-quality-scenario-is-a-registered-concern-measured-by-a-fixed-number-or-a-named-check.md))
  and tip 4-4 forbids repeating what a view already holds.
- **A goal with no approach beside it is a hole in the strategy, and writing the table found two.**
  Testability and Security had no approach item to point at, so §4 gained the platform double with a
  conformance suite per seam, and the observability boundary with the log contract.
- **No approach is motivated item by item.** arc42 asks for it nowhere: every obligation in the §4
  corpus is collective — "Motivate what was decided and why it was decided that way" in the template
  chapter, "State these decisions" in FAQ C-4-2 — and 0 of its 12 pages prescribes a per-item
  justification. The *why* of one decision is its ADR, which is also where tip 4-4 and C-4-2 send
  the detail and the rejected alternative.
- **§4 links §1.2 and nothing further.** No arc42 page names §10 as a link target from §4, and §1.2
  already links a goal to its scenarios, so a second path would be a copy that drifts.

## Considered options

- *Tip 4-2's table verbatim, the `essential` form* — rejected on its *Scenario* column: §10 holds
  seventeen scenarios and §4 would carry an abridged copy that goes stale silently. 0 of the 9
  published documents measured takes the four columns as written.
- *A goal tag inside each approach item, as the published `fin-mig` document does* — rejected: it
  reads forward from an approach to a goal but gives no reverse check, so a goal nothing serves
  stays invisible, which is the failure this ticket found.
- *One paragraph naming §1.2's rank, as 3 of the 9 published documents do* — rejected as the
  cheapest and the weakest: a reader still cannot get from a goal to the approach bought for it.

## Consequences

- Three tables now test each other for completeness: §1.2's five goals, §10.1's filing of every
  registered concern under one of them, and this one. Nothing enforces the agreement, so a renamed
  goal breaks all three at once and only reading catches it.
- §4 holds nineteen approach items. It grows when a goal gains an approach that is fundamental, and
  arc42 sanctions that growth explicitly (tip 4-5, "don't try to decide everything up-front").
