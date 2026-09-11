---
name: hld-author
description: "Use when writing or reviewing a numbered arc42 section of the architecture document under docs/design/ — a ticket that writes one, or a review of an existing section."
---

# HLD author

Produce one arc42 section that passes the checklist. This is the *Resolve* step of a
`design-session`; claiming, verifying, recording and closing are the session's.

This skill carries the rules of the arc42 template itself, measured from the template, its tips and
its FAQ. Read it instead of the notes under `.agents/research/`: a note is the provenance of a rule
here, read only when the rule has to change.

## Procedure

1. Read the section's row in *What each section owes* before drafting. **A section with no row has
   not been measured against the template.** Raise a research ticket that measures it, block the
   current ticket on it and wait — the precedents are #98 and #105 — rather than inferring the rules
   from a neighbouring section.
2. Draft from the ADRs the ticket lists and from `docs/design/05-building-block-view.md`. A section
   states the design and never decides: a choice that surfaces while drafting becomes an ADR of its
   own in the same commit, and the section links it with a one-sentence gist and nothing more.
3. Ask the maintainer only what the ADRs leave open, in the playbook's rounds.
4. Every diagram follows `docs/design/diagrams.md`, *Renderer limits* included. Mermaid does not
   render in this environment, so that list is the only check that exists — copy the shape of a
   diagram already committed rather than inventing one.
5. Set `reviewed (#N)` only when `.agents/design-quality-checklist.md` is fully true for the
   section, and move its row in `docs/design/TRACKER.md` §A in the same commit.

## What each section owes

| § | The rule that binds it hardest | What arc42 says about quantity | Measured in |
|---|---|---|---|
| 6 Runtime view | Every participant is an element of the building block view — tip 6-1, tagged `essential`, is the only §6 rule phrased with *always*. A scenario is admitted by its *architectural relevance* and by nothing else | 1–3 scenarios kept, "several dozens during design" (tip 6-2). A table is offered nowhere for §6 and used by none of the eleven measured documents; the sanctioned non-graphical form is a numbered list of steps | `.agents/research/37` |
| 7 Deployment view | Technical infrastructure **and** the mapping of artefacts onto it, over exactly two levels. Level 1 owes an overview diagram, a motivation, quality or performance features, and the mapping of building blocks | No arc42 page requires a diagram and tip 7-7 sanctions a table instead. Only "those elements of an infrastructure that are needed to show a deployment of your building blocks" | `.agents/research/28` |
| 8 Cross-cutting concepts | The template ships no slots at all, and instructs "Pick **only** the most-needed topics for your system". Once a decision register exists, a concept is left with its mechanism, the grid of building blocks it binds, its limits and the domain model — ADR-0062 | Median 7 concepts across the eleven measured documents, range 2–17; tip 8-3 offers "more than 20 proposals" and no measured document takes them all | `.agents/research/28` |

**§1, §2, §3, §4, §5, §10 and §11 have no row**, so step 1 applies to every one of them. §3, §4 and
§5 were written before the measuring started, which is a reason to measure before *changing* one,
not a reason to treat them as measured.

## What the measuring found that a section author gets wrong

- **An error is a scenario, not a branch.** arc42 asks for "error and exception scenarios" once, as
  the fourth content area of §6, and nowhere as an alternative inside a picture; `diagrams.md` asks
  a sequence diagram for its failure path as well. Both hold, and they are different obligations —
  the section decides which of the two a given failure earns.
- **The same failure is asked for by three sections, and arc42 never draws the line.** §6 wants the
  interaction that fails, §8 wants the rule (tip 8-10, "what errors to handle"), §10 wants the
  measurable stimulus and response (tip 10-7). No arc42 page contrasts them, so the line is this
  catalogue's to state and it is stated in `docs/design/06-runtime-view.md`.
- **A picture without text is not a section.** The template's own fill-in line asks for "the notable
  aspects of the interactions between the building block instances depicted in this diagram" — in
  practice a numbered step list keyed to building blocks, or a paragraph after the figure. A caption
  does not discharge it, and exactly one measured document of eleven ships a diagram with no text.
- **Saying why a scenario or a concept is here is arc42's own criterion and almost nobody does it.**
  Three of eleven documents write the reason down. It is the sentence that separates a runtime view
  from an illustration.
- **arc42 sanctions deleting a §6 scenario once it is implemented** (tip 6-5, tip 6-9) and ranks §8
  above §5 and §6 for what to keep in step with code (FAQ H-3). A scenario that is expensive to
  maintain and cheap to lose is a scenario that should not have been written down.
