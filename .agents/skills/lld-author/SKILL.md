---
name: lld-author
description: "Use when writing or reviewing a component design document under docs/design/components/ — an LLD: <component> ticket, a request to describe the node, or a review of an existing component document."
---

# LLD author

Produce one component design document that passes the checklist. This is the *Resolve* step of a
`design-session`; claiming, verifying, recording and closing are the session's.

1. Start from `docs/design/components/_template.md`; name the file after the component's
   `CONTEXT.md` term in kebab-case; set the status line to `_Status: in progress (#N)._`.
2. Fill sections 1–3 (purpose, responsibilities, public contract) from
   `docs/design/05-building-block-view.md` and the ADRs the ticket lists — no questions yet.
3. Grill sections 4–11 in the playbook's order (`.agents/session-playbook.md`, *LLD ticket*).
   For every pattern: the refactoring.guru name, the problem it solves *here*, the rejected
   alternative. For SOLID: one argued paragraph per principle. For failure modes: timeout,
   cancellation, dependency outage, bad input, concurrent use. For typing, async, error, naming,
   layout, logging, documentation and testing: cite the `ST-<AREA>-NN` rules of
   `docs/design/engineering-style.md` §12.1 that bind this component and state only what is
   specific here.
4. Draw diagrams per `docs/design/diagrams.md`: a C4 Component (or Code) diagram for structure,
   a `sequenceDiagram` per scenario with its failure branch, a `stateDiagram-v2` when the node
   holds state.
5. Cross-check with `docs/design/06-runtime-view.md` and the neighbouring component documents that
   exist; fix the wrong side; record each missing neighbour as a deferral in the ticket. Set
   `reviewed (#N)` only when `.agents/design-quality-checklist.md` (*Component design
   document*) is fully true; update the row in `docs/design/TRACKER.md` §C in the same commit.
