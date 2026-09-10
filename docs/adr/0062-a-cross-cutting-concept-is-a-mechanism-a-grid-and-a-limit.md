---
status: accepted
date: 2026-09-10
ticket: "#40"
---

# A §8 concept states the mechanism as it stands, the components that carry it and where it stops — never the decision, the rule or the term

Every cross-cutting concern of this design is already written down three times over: the choice is
an ADR, the rule it becomes is an `ST-<AREA>-NN` line of
[`engineering-style.md`](../design/engineering-style.md), and the word is a `CONTEXT.md` entry. A
§8 that adds a fourth copy breaks the linking rule of
[`documentation-style.md`](../documentation-style.md) §6; a §8 that only links becomes an index, and
the one measured arc42 document whose §8 is nothing but links annotates itself "Not written yet"
([`docs/research/28`](../research/28-arc42-deployment-view-and-cross-cutting-concepts.md) §6.5). We
decided what a concept section contains:

- **One concept per registered concern, and the register is
  [`TRACKER.md`](../design/TRACKER.md) §D.** A concern is admitted to §8 by having a row there, not
  by appearing on arc42's suggested checklist — the template's own instruction is "Pick **only** the
  most-needed topics for your system" and "DO NOT ATTEMPT to cover all of the topics" (same note,
  §2). The register is therefore both the table of contents and the completeness test: a row whose
  *Described in* names §8 has a section, and a section with no row is a bug in one of the two.
- **Four sentences of mechanism, then three labelled lines.** The prose says how the concern works
  in this system *now*; `_Decided in_` links the ADRs, `_Ruled by_` links the rulebook rules, and
  `_Carried by_` names the components. Nothing else. arc42's own test for what earns a concept is
  length of explanation, not subject — "if (extensive-explanation-required) then concept else
  decision" ([tip 8-9](https://docs.arc42.org/tips/8-9/)) — and the mechanism is the part no
  per-decision record holds.
- **A head table mapping every concern to the components that carry it, by layer.** This grid exists
  nowhere else in the catalogue: §5 lists components and their decisions, §D lists concerns and
  their decisions, and neither joins the two. It is what
  [tip 8-1](https://docs.arc42.org/tips/8-1/) means by material that "would have to be repeated in
  each" building block, and it is the reason an `LLD: <component>` ticket can be told exactly which
  concepts bind its component before it writes a line.
- **Where the concept stops is part of the concept.** Applicability and limits are what
  [FAQ C-8-5](https://faq.arc42.org/questions/C-8-5/) asks for — "In what cases … will the concept
  fail or cease to work?" — and they are the sentences a reader cannot reconstruct from an ADR that
  argues one choice against another.
- **§8 holds no topology and §7 holds no concept.** The boundary is the checklist's
  ([`.agents/design-quality-checklist.md`](../../.agents/design-quality-checklist.md)) and it is
  arc42's: §7 is infrastructure and the mapping of artefacts onto it, and its influence on the
  concepts is a §7 sentence pointing here (same note, §3).

## Considered options

- *One table, concern → ADR → components, and no prose* — rejected: it is the NFDI4Earth shape, the
  only pure-link §8 among eleven measured documents, and its own first four words are "Not written
  yet".
- *Concepts only for concerns that cross several components* — rejected: it takes the *Described in*
  column of §D away from §8 for eight rows and gives them to a rulebook that documents rules rather
  than mechanisms, which is a different question.
- *A file per concept under `design/concepts/`* — rejected: arc42 recommends sub-headings in one
  section and none of its eleven `tips/8-*` pages mentions splitting (same note, §7); the catalogue
  already has a directory per document type and this would add a ninth for paragraphs.
- *Opening §8 with a domain model, as five of the measured examples do* — rejected: the
  ubiquitous language is [`CONTEXT.md`](../../CONTEXT.md), which is this document's §12, and the
  structural model is [§5](../design/05-building-block-view.md); arc42's own tips defer term
  definitions to §12.

## Consequences

- §8 is the longest section of the architecture document, and that is the normal shape: §8 exceeds
  §7 in eight of eleven measured arc42 documents (same note, §5).
- Adding a cross-cutting concern is now three edits in one commit — the ADR, the §D row, the §8
  section — and the head table makes the fourth, the component list, mechanical.
