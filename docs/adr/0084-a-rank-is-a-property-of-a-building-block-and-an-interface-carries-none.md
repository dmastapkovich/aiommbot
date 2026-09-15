---
status: accepted
date: 2026-09-15
ticket: "#85"
amends: [ADR-0038]
---

# A rank is a property of a building block: §5's two interface inventories carry none

[ADR-0038](0038-seam-inventory-records-the-direction-of-the-call.md) kept `seam` as a third rank
beside `component` and `part` on the argument that the rank table answers one question — does this
get a design document of its own — and that both directions of a seam answer no. With
[ADR-0083](0083-the-plugin-contract-is-the-second-interface-of-the-level-1-whitebox.md) adding a
second interface inventory at [§5.1.2](../design/05-building-block-view.md#512-the-plugin-contract),
a rank named after one of the two inventories stops classifying anything. We decided:

- **The rank table covers building blocks and has two rows**: `component`, which gets a document of
  its own under `components/`, and `part`, which is described inside the document of the component
  it belongs to. That is the whole question the table was written to answer.
- **An interface is not a building block and carries no rank.** §5.1.1 and §5.1.2 list the Protocols
  the Core owns, and each row is described in the document its *Specified in* column names. What
  distinguishes the two inventories is the inventory: §5.1.1 holds the Protocols whose
  implementations are substituted and carries the *Direction* column of ADR-0038; §5.1.2 holds the
  Protocols a Plugin implements to add a contribution.
- **`seam` stays the word for a row of §5.1.1** — it is the name §5.1.1's heading uses and the word
  every ADR that added one is written in. It is no longer a rank, and §5.1.1's membership rule is
  restated without that word: a Core-owned Protocol is a §5.1.1 row when it is neither a component
  nor a part of one **and** implementations of it are substituted.

This follows the template rather than departing from it. arc42 keeps interfaces in a slot of their
own, separate from *Contained Building Blocks*
([`arc42-template`, §5](https://github.com/arc42/arc42-template/blob/master/EN/adoc/05_building_block_view.adoc)),
and the FAQ's whitebox template names that slot *Internal relationships (interfaces)*
([FAQ B-11](https://faq.arc42.org/questions/B-11/)). Neither the blackbox template's six slots nor
the whitebox template's five nor the tabular schema — *Name* and *Responsibility*, extensible only
to *Interfaces* and *Code* — carries a kind or type field, and arc42 defines no taxonomy of element
ranks anywhere: whitebox, blackbox and the levels are its whole apparatus.

## Considered options

- *A fourth rank, `contribution`, for the rows of §5.1.2* — rejected. It is what
  [`docs/research/19`](../research/19-provided-and-required-protocol-inventories.md) §3.1 already
  calls the class, and tips 5-20 and 5-24 do permit marking a different kind of element as long as a
  legend explains it. But none of the eight published arc42 documents classifies its blocks by kind
  at all — their only qualifier is arc42's own blackbox/whitebox pair, which is a level of detail —
  and [FAQ K-2](https://faq.arc42.org/questions/K-2/) asks that customisations stay in subsections
  and leave the structure alone. ADR-0038's own criterion also defeats it: `contribution` answers
  "does this get a document of its own" exactly as `seam` does, and the two would be told apart by
  the number of the subsection that lists them, which is what the subsections already do.
- *Widening `seam` to cover both inventories, with two sub-kinds* — rejected: a reader counting
  seams would get twenty where eleven sentences say thirteen, the ideology statement of
  [`engineering-style.md`](../design/engineering-style.md) §1 would have to split "the whole
  substitution surface" into two ideas, and the distinction §5.1.2 exists to draw would be erased by
  the word that draws it.

## Consequences

- Every count in the catalogue is unchanged: sixteen Protocols on thirteen seam rows, twelve
  required and one provided, and fourteen conformance suites.
- A reading guide with two ranks and two interface inventories is still this catalogue's own
  construction, as the three-rank table was. arc42 has neither, and §5 is the inventory behind
  thirty-two `LLD: <component>` tickets, which is what the guide is for
  ([ADR-0081](0081-the-building-block-levels-count-source-code-and-level-n-lives-in-section-5-n.md)).
