---
status: accepted
date: 2026-09-11
ticket: "#39"
---

# A §6 scenario is one order between boxes, drawn once, with the branch that motivated the design in the picture and the rest in a table

arc42 admits a runtime scenario by "architectural relevance" and by nothing else, asks that every
participant be an element of the building block view, and expects one to three of them to survive
into the document
([`.agents/research/37`](../../.agents/research/37-arc42-runtime-view.md) §2, §4). It also asks for
"error and exception scenarios" as a content area of its own, while
[`diagrams.md`](../design/diagrams.md) asks a sequence diagram for its failure path as an
`alt`/`else`; both obligations hold and neither page says which a given failure earns. Nothing in
the template offers a table for §6 and none of the eleven measured documents uses one. We decided
what a scenario is in this catalogue:

- **A scenario is admitted when it fixes an order between boxes that no single component owns.**
  Eight qualify, and each is the only place its order is written down: start-up, dispatch, the
  callback reply, reconnect, state isolation, the stop phase, the failure trail, and the consumer
  lease. This is above arc42's one-to-three, deliberately: a framework's hard-to-reverse decisions
  are almost all decisions about order, and two of the eleven measured documents already hold four
  and five.
- **§6 answers "in which order do the boxes call each other", once per scenario.** A component
  design document draws the same interaction only where it opens a step invisible from outside the
  box — an internal state, a part, an invariant of its own — and links here otherwise. Where the two
  disagree about the order, §6 is right and the component document is fixed.
- **One failure branch is drawn and the rest are tabled.** The picture carries the branch that
  motivated the design, as a single `alt`/`else`; every other outcome is a row of a branch table
  under it — branch point, trigger, outcome, and the document that owns the detail. Reconnect alone
  has five outcomes, which folds into a two-level `alt` at the reading limit
  ([`.agents/research/38`](../../.agents/research/38-mermaid-sequence-diagram-limits.md) §6 rule 6)
  and stops the diagram answering one question.
- **The text beside a diagram says what the picture cannot show.** The template's fill-in line asks
  for "the notable aspects of the interactions", not a caption and not a transcript of the arrows;
  a sentence saying why the scenario is here is arc42's own admission criterion and three of eleven
  documents write it down.
- **The same failure reaches three sections on three different questions**: §6 states the order and
  where it splits, §8 states the rule the mechanism follows, §10 states the measurable stimulus and
  response. No arc42 page contrasts them, so the line is this catalogue's and this is it.

## Considered options

- *Three scenarios, strictly inside tip 6-2* — rejected: five of the eight orders would then be
  written down nowhere, because no component document can hold an order that crosses boxes.
- *A diagram per failure branch, which is arc42's own "an error is a scenario"* — rejected: it
  multiplies the section by three to four and contradicts tip 6-2 at any scenario count.
- *Every outcome as an `alt` branch inside one picture* — rejected: reconnect needs five branches
  over two levels, and `diagrams.md` requires one diagram to answer one question.
- *A numbered step list beside each diagram, the template's sanctioned non-graphical form* —
  rejected here because the diagram is present: the list would repeat its arrows one for one, which
  [`documentation-style.md`](../documentation-style.md) §6 forbids.
- *§6 owning every interaction exclusively, component documents linking to it* — rejected: it takes
  the *Interactions* section out of
  [`components/_template.md`](../design/components/_template.md) for every component whose main path
  crosses a box boundary, which is most of them.

## Consequences

- The branch table is a form arc42 offers nowhere for §6. It is ours, and it is the only place an
  outcome that is neither the main path nor the motivating failure is recorded at all.
- §6 is expected to shrink rather than grow: arc42 sanctions deleting a scenario once it is
  implemented (tips 6-5 and 6-9), and a scenario expensive to keep in step with code is one that
  should not have been written down.
- Every `LLD: <component>` ticket inherits a test for its own §5: draw only what the box hides.
