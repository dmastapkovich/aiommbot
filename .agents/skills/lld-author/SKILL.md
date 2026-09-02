---
name: lld-author
description: Use when writing or reviewing a component design document under docs/design/components/ — an "LLD: <component>" ticket, a request to "describe the node", or a review of an existing component document.
---

# LLD author

Produce one component design document that passes the checklist.

1. Start from `docs/design/components/_template.md`; name the file after the component's
   `CONTEXT.md` term in kebab-case; set the status line to `in progress (#N)`.
2. Fill sections 1–3 (purpose, responsibilities, public contract) from
   `05-building-block-view.md` and the ADRs the ticket lists — no questions yet.
3. Grill sections 4–11 in the playbook's order (`docs/agents/session-playbook.md`, *LLD ticket*).
   For every pattern: the refactoring.guru name, the problem it solves *here*, the rejected
   alternative. For SOLID: one argued paragraph per principle. For failure modes: timeout,
   cancellation, dependency outage, bad input, concurrent use.
4. Draw diagrams per `docs/design/diagrams.md`: a C4 Component (or Code) diagram for structure,
   a `sequenceDiagram` per scenario with its failure branch, a `stateDiagram-v2` when the node
   holds state.
5. Cross-check with `06-runtime-view.md` and the neighbouring component documents; fix the wrong
   side. Set `reviewed` only when `docs/agents/design-quality-checklist.md` (*Component design
   document*) is fully true; update the row in `docs/design/TRACKER.md` §C.
