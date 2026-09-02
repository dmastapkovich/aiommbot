# AGENTS.md

Entry point for any AI coding agent working in this repository. Read this file, then the documents
it points to, before touching anything.

## What this repository is right now

`aiommbot` 0.5.0 is being **designed, not implemented**. There is no package code, on purpose. The
work is a wayfinder map — GitHub issue #1, label `wayfinder:map` — whose child issues are decision
tickets. Each session resolves **one** ticket with the maintainer and leaves the design catalogue
one node richer. The deliverable of this phase is documentation; code starts on a separate map.

## Warm-up, in order

1. `docs/agents/context-brief.md` — what is settled, what the research found, how the maintainer
   works. Everything a fresh session needs to sound like the previous one.
2. `gh issue view 1` — the map: Destination, Notes, Decisions so far, fog, out of scope.
3. `docs/design/TRACKER.md` — readiness of every document the catalogue must contain. Nothing is
   done until its row says so.
4. `docs/agents/session-playbook.md` — the steps for the ticket type you are about to work.
5. `docs/agents/design-quality-checklist.md` — the bar a reviewed document must clear.

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
| Documentation standard (types, naming, linking, status, discovery protocol) | `docs/documentation-style.md` | fixed |
| Catalogue index | `docs/README.md` | every new document type |
| Readiness tracker | `docs/design/TRACKER.md` | every ticket, same commit |
| Tracker conventions | `docs/agents/issue-tracker.md`, `docs/agents/domain.md` | fixed |
| Backlog ideas that are not decisions | GitHub issues labelled `enhancement` + a fog line in #1 | maintainer |

## Standing rules

- One ticket per session, claimed (`gh issue edit N --add-assignee @me`) before any work.
  Research tickets are the exception and may run in parallel as background agents.
- Decisions live in exactly one place — their ADR. The map, the tracker and the arc42 sections
  link to it and never restate it. Vocabulary uses `CONTEXT.md` terms with no synonyms.
- Every resolution is one commit: ADR + `CONTEXT.md` + arc42/LLD section + `TRACKER.md` row +
  research links, Conventional Commits message referencing the issue. The maintainer has approved
  committing and pushing **documents** to `main` for this effort; anything else needs a fresh yes.
- English in everything committed and in issues. The maintainer converses in Russian; questions to
  them are asked in Russian, interactively, a few at a time, each with a recommended answer first.
- Quality by mechanism, not by memory: patterns are named as on refactoring.guru with the rejected
  alternative, SOLID is argued per component, diagrams are C4 in Mermaid, and a document is
  *reviewed* only when the checklist says so.
- Never commit secrets or personal data; never paste tokens, cookies or private URLs into issues.
- Anything the design did not foresee goes through the discovery protocol in
  `docs/agents/session-playbook.md` — one home per finding, current ticket unchanged.

## Skills in this repository

`.agents/skills/` holds the process skills (`design-session`, `lld-author`); `.claude/skills/`
symlinks them for Claude Code. They are the executable form of the playbook.
