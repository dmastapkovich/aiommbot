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
   not been measured against the template.** Measure it in this session rather than inferring the
   rules from a neighbouring section: the template chapter, every `tips/<N>-*` page and every
   `C-<N>-*` FAQ question are cached under `.refs/arc42/` — run `.agents/scripts/sync-refs.sh` if
   they are not — and the row goes into the table below in the same commit as the section. Raise a
   research ticket and block the current ticket only when the measurement needs the eleven published
   arc42 documents, which the cache does not hold, or when it contradicts an accepted ADR. The
   precedents are #98, #105 and #108.
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
| 1 Introduction and goals | §1.2 carries the quality goals of the **architecture**, each stated as a concrete situation rather than a noun and ordered by priority — a goal that is a word has failed the section. §1.3's *Expectations* are the documents a stakeholder needs from this catalogue, never requirements on the system (FAQ C-1-5) | §1.2: "the top three (max five)", arc42's own number in nine places — three is the target, five the cap. §1.1: max 3–5 use cases, features or functions, and "less than one page if possible". §1.3: no count, a 40-role catalogue to search against, and a licence to omit the table for a cross-reference | `.agents/research/39` |
| 2 Constraints | A constraint is whatever **removes freedom from a later design, implementation or process decision**. arc42 defines the section by that effect and never by origin, and *conventions* — programming style, naming, versioning, documentation guidelines — are one of its own named categories, so a rule this project wrote for itself belongs here. A row is admitted when it shaped an important decision **and** helps a reader understand the architecture (FAQ C-2-3) | None in either direction, and no sentence makes the section mandatory. The only sizing instruction runs the other way: link rather than copy what someone else has already documented | `.agents/research/39` |
| 10 Quality requirements | A scenario must let a reader **decide whether it is fulfilled**. Everything else in §10 is negotiable and this is not — and its corollary is that §10 *references* §1.2's top goals rather than restating them | No bound either way: "dozens (or even hundreds)" expected, ">100" in real systems, and one licence to write none if §10.1 is itself precise and measurable. The "top 3-5" of the corpus belongs to §1.2 and never here. Three scenario kinds — usage, change, failure | `.agents/research/40` |
| 6 Runtime view | Every participant is an element of the building block view — tip 6-1, tagged `essential`, is the only §6 rule phrased with *always*. A scenario is admitted by its *architectural relevance* and by nothing else | 1–3 scenarios kept, "several dozens during design" (tip 6-2). A table is offered nowhere for §6 and used by none of the eleven measured documents; the sanctioned non-graphical form is a numbered list of steps | `.agents/research/37` |
| 7 Deployment view | Technical infrastructure **and** the mapping of artefacts onto it, over exactly two levels. Level 1 owes an overview diagram, a motivation, quality or performance features, and the mapping of building blocks | No arc42 page requires a diagram and tip 7-7 sanctions a table instead. Only "those elements of an infrastructure that are needed to show a deployment of your building blocks" | `.agents/research/28` |
| 8 Cross-cutting concepts | The template ships no slots at all, and instructs "Pick **only** the most-needed topics for your system". Once a decision register exists, a concept is left with its mechanism, the grid of building blocks it binds, its limits and the domain model — ADR-0062 | Median 7 concepts across the eleven measured documents, range 2–17; tip 8-3 offers "more than 20 proposals" and no measured document takes them all | `.agents/research/28` |

**§3, §4, §5 and §11 have no row**, so step 1 applies to every one of them. §3, §4 and §5 were
written before the measuring started, which is a reason to measure before *changing* one, not a
reason to treat them as measured.

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
- **A quality goal that is a noun has failed §1.2.** arc42 asks for a concrete scenario per goal and
  says "avoid buzzwords"; six of the eleven measured documents write the word and nothing else.
- **"Stimulus → response → measure" is nobody's form.** arc42 publishes a three-part short form —
  *Context → Source/Stimulus → Metric/Acceptance Criteria* — and the SEI's eight-field long one. The
  three-term compression drops the context both make first-class, which is what turns a scenario
  into a slogan. This catalogue's own form is ADR-0068's.
- **The measure need not be a number, and a gate is more common than one.** Across the seventy
  classifiable scenarios of the eleven documents, thirty-one measure by a check and twenty-eight by
  a number. The obligation the licence carries is to name the rig — which suite, which rule, which
  command — because a gate without a name is as undecidable as a duration without one.
- **The graphical quality tree is deprecated by arc42 itself**, in favour of a simple table; its one
  surviving use is as a checklist that makes a missing scenario visible.
- **§1.3's *Expectations* column is the commonest §1 error.** It holds the documents a stakeholder
  needs, not the requirements they place on the system — arc42 keeps a whole FAQ question
  (C-1-5) for that confusion alone.
