# AGENTS.md

Entry point for any AI coding agent working in this repository. Read this file, then the documents
it points to, before touching anything.

## What this repository is right now

`aiommbot` 0.5.0 is being **designed, not implemented**. There is no package code, on purpose. The
work is a wayfinder map — GitHub issue #1, label `wayfinder:map` — whose child issues are decision
tickets. Each session resolves **one** ticket with the maintainer and leaves the design catalogue
one node richer. The deliverable of this phase is documentation; code starts on a separate map.

## Warm-up, in order

1. `gh issue view 1` — the map: Destination, Notes, Decisions so far, fog, out of scope.
2. `docs/design/TRACKER.md` — readiness of every document the catalogue must contain. Nothing is
   done until its row says so.
3. `.agents/session-playbook.md` — the steps for the ticket type you are about to work.
4. `.agents/design-quality-checklist.md` — the bar a reviewed document must clear.
5. The ticket (`gh issue view N --comments`) and the resolution comments of every closed ticket it
   was blocked by, then the ADRs and research notes those resolutions name.

Every other document that describes the warm-up points here instead of repeating the list.

## Where things live

| Material | Location | Owner |
|---|---|---|
| Decisions | `docs/adr/NNNN-slug.md` | the ticket that made them |
| Vocabulary | `CONTEXT.md` | every ticket, inline |
| Architecture document (arc42, HLD) | `docs/design/*.md` | HLD tickets |
| Component design documents (LLD) | `docs/design/components/<term>.md` | `LLD: <component>` tickets |
| Engineering style rulebook | `docs/design/engineering-style.md` | style ticket |
| Diagram conventions | `docs/design/diagrams.md` | fixed |
| Research findings | `docs/research/NN-*.md` | research tickets |
| Documentation standard (types, naming, status, linking, target-state rule, discovery protocol) | `docs/documentation-style.md` | fixed |
| Catalogue index | `docs/README.md` | every new document type |
| Readiness tracker | `docs/design/TRACKER.md` | every ticket, same commit |
| Tracker conventions | `.agents/issue-tracker.md`, `.agents/domain.md` | fixed |
| Backlog ideas that are not decisions | GitHub issues labelled `enhancement` + a fog line in #1 | maintainer |

## Standing rules

- **Five ticket types, by label:** `wayfinder:research`, `wayfinder:grilling`, `wayfinder:prototype`,
  `wayfinder:task`, `wayfinder:lld`. The playbook has a section per type; the `design-session` skill
  runs every type and, for an LLD ticket, hands its *Resolve* step to the `lld-author` skill.
- One ticket per session, claimed before any work. Research tickets are the exception and may run
  in parallel as background agents.
- **Target state only.** A document says what the design is, never what it was. A changed decision
  rewrites the document it changes in the same commit; nothing refers to a predecessor code base,
  an internal deployment or bot, a local path, or compatibility with anything outside this
  repository. Evidence from such sources may inform the session and is never written down. Git is
  the history (`docs/documentation-style.md` §9).
- **No junk.** No placeholders, no "TBD", no dated amendment sections, no workaround notes, no
  copy of a rule that lives elsewhere. If a document cannot be finished, its status line says
  `in progress (#N)` and the ticket says why.
- Decisions live in exactly one place — their ADR. The map, the tracker and the arc42 sections
  link to it with a one-sentence gist and never restate it. Vocabulary uses `CONTEXT.md` terms with
  no synonyms; the glossary wins over every other document, titles included.
- Every grilling, prototype, LLD and task resolution is **one commit**: ADR + `CONTEXT.md` +
  arc42/LLD section + `TRACKER.md` row + research links, message `docs(<area>): <what was decided>
  (#N)`. A research ticket commits one note plus its index row. The maintainer has approved
  committing and pushing **documents** to `main` for this effort; anything else needs a fresh yes.
- Verify against the checklist **before** the commit that sets a status; push after.
- English in everything committed and in issues. The maintainer converses in Russian; questions to
  them are asked in Russian, interactively, in rounds of at most four, each with the recommended
  answer first.
- Quality by mechanism, not by memory: patterns are named as on refactoring.guru with the rejected
  alternative, SOLID is argued per component, diagrams are C4 in Mermaid, and a document is
  *reviewed* only when the checklist says so.
- Never commit secrets or personal data; never paste tokens, cookies, private URLs or local paths
  into documents or issues.
- GitHub writes go through `gh api`, one command per call; the exact forms are in
  `.agents/issue-tracker.md`. If a write is blocked, hand the maintainer the exact command.
- Anything the design did not foresee goes through the discovery protocol in
  `.agents/session-playbook.md` — one home per finding, current ticket unchanged.

## Skills in this repository

`.agents/skills/` holds the process skills (`design-session`, `lld-author`); `.claude/skills/`
symlinks them for Claude Code. They are the executable form of the playbook.
