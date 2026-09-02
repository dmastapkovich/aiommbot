# Session playbook

The steps for one map ticket, by ticket type. Each step ends on its completion criterion; the
session ends only when the final step's criterion holds.

## Every ticket

1. **Warm up.** Read `docs/agents/context-brief.md`, the map (`gh issue view 1`),
   `docs/design/TRACKER.md`, then the ticket with `gh issue view N --comments` and the resolution
   comments of every closed ticket it was blocked by. Open the research files and ADRs those
   resolutions name. *Done when you can state, in three sentences, the question, the inputs, and
   the settled decisions it must not contradict.*
2. **Claim.** `gh issue edit N --add-assignee @me`. *Done when the assignee shows.*
3. **Resolve** — see the type-specific section below.
4. **Record.** In one commit: new ADR(s) in `docs/adr/` (format in `docs/agents/domain.md`),
   `CONTEXT.md` terms, the arc42 section or component document the ticket owns, the
   `docs/design/TRACKER.md` rows it changes, links to the research it used. Message:
   `docs(<area>): <what was decided> (#N)`. Push. *Done when `git status` is clean and the
   push succeeded.*
5. **Verify.** Walk `docs/agents/design-quality-checklist.md` for every document touched; fix
   before closing. Confirm no existing ADR is contradicted, or write the superseding ADR and mark
   the old one `superseded by`. *Done when every checklist line for the touched documents is true.*
6. **Close.** Comment `## Resolution` on the ticket (gist plus links to the files), close it, add
   one line to the map's *Decisions so far* (title as link, one-line gist, file pointer). *Done
   when the map body shows the new line.*
7. **Clear the fog.** Graduate anything the answer made specifiable into new tickets
   (create, then wire `blocked_by`, then add as sub-issues of #1); remove the graduated line from
   *Not yet specified*; rule mis-scoped tickets out of scope by closing them with a line in *Out of
   scope*; update or delete tickets the decision invalidated. *Done when the map's frontier is
   the true set of takeable work.*
8. **Report** to the maintainer in Russian: what was decided, files changed, the next frontier
   tickets. *Done when the message stands alone for someone who did not watch the session.*

## Grilling ticket

The default type: a decision made in conversation.

1. **Build the design tree** before asking anything: the sub-decisions this ticket implies, which
   are facts (find them yourself — subagent, `gh`, web, the 0.4.8 code) and which are choices
   (the maintainer's). *Done when every node is labelled fact or choice and every fact has a
   finder dispatched or answered.*
2. **Grill in rounds.** Ask the whole current frontier of choices in one round — at most four
   questions, in Russian, via `AskUserQuestion`, each with the recommended answer first and the
   reason in one line, alternatives after. Wait. Recompute the frontier from the answers; a
   question that depends on an answer still pending belongs to a later round. Challenge vague
   terms and propose the canonical `CONTEXT.md` word on the spot; stress-test relationships with
   concrete scenarios; check claims against the 0.4.8 code and the research. *Done when the
   frontier is empty and the maintainer confirms shared understanding.*
3. **Draft the artefacts while grilling**, not after: an ADR paragraph the moment a hard-to-reverse
   choice lands, a glossary entry the moment a term is resolved. *Done when every choice in the
   tree maps to an ADR line, a glossary term, or an explicit "easy to reverse, no ADR".*
4. Continue at *Every ticket*, step 4.

## Research ticket

Autonomous; may run several in parallel as background agents.

1. Write the brief: the question, the primary sources to read (source code, official docs, PEPs),
   the output file `docs/research/NN-<slug>.md`, the required sections (findings with URLs per
   claim, a comparison table where things are compared, a recommendation section, Sources), and
   the instruction to write incrementally and mark anything unverified. *Done when a reader of
   the brief alone could judge whether the report answered it.*
2. Dispatch; on completion commit the file, add its row to `docs/research/README.md`, comment the
   resolution gist on the ticket, close it, add the map line and the tracker row. *Done when the
   file is on `main` and the ticket is closed.*

## Prototype ticket

1. Produce the cheapest artefact that makes the question concrete — code sketches under
   `docs/design/prototypes/`, a Mermaid diagram, a stub `pyproject.toml` — clearly marked
   throwaway. *Done when the maintainer can react to it line by line.*
2. Grill on the reaction (rounds as above); revise the artefact until it reads right. Record the
   decisions it settles as ADRs and glossary terms; the prototype itself is linked from the ticket,
   never treated as a specification. *Done when the artefact and the ADRs agree.*
3. Continue at *Every ticket*, step 4.

## LLD ticket (`LLD: <component>`)

1. Create `docs/design/components/<term>.md` from `_template.md`; set the status line to
   `in progress (#N)`; fill sections 1–3 from the building-block view and the ADRs before asking
   anything. *Done when purpose, boundaries and contract are drafted from existing decisions only.*
2. Grill sections 4–11 in rounds, in this order: internal structure, interactions (main path,
   then each failure path), patterns with rejected alternatives, SOLID, failure modes and
   invariants, typing/async rules, testing, open questions. Draw every diagram per
   `docs/design/diagrams.md`; use only `CONTEXT.md` terms. *Done when every template section is
   filled and no section says "TBD".*
3. Cross-check against the runtime view and the neighbouring component documents; fix whichever
   is wrong. Set the status line to `reviewed` only when the checklist passes. *Done when the
   component's row in `TRACKER.md` reads `reviewed`.*
4. Continue at *Every ticket*, step 4.

## Task ticket

Manual work that unblocks a decision. Do it (or hand the maintainer a precise checklist when only
they can), record what was created and any facts later tickets depend on in the resolution
comment, close. *Done when the blocked decision can proceed.*

## Discovery protocol

Something surfaces that no ticket, arc42 section, ADR or template anticipates — a capability, a
mechanism, a detail, a whole document type. Classify it, file it where its class lives, link it
from the current ticket, and return to the current ticket without designing the discovery in
passing.

| Class | Test | Where it goes |
|---|---|---|
| Out of scope | It lies beyond the Destination | one line in the map's *Out of scope*; if a ticket already exists for it, close that ticket |
| Fog | In scope, but the question cannot yet be stated precisely | one line in the map's *Not yet specified* |
| Sharp question | The question can be stated now, even if it cannot be answered now | a new wayfinder ticket: create, wire `blocked_by`, add as sub-issue of #1; a `TRACKER.md` row in §B, §D or §E if it is a decision, a concern or a 0.4.8 capability |
| Backlog idea | A feature or tool, not a design decision | an `enhancement` issue plus one fog line in the map (precedent: #34) |
| Gap in the catalogue itself | The document type, template or rulebook cannot hold the finding | a task ticket to extend `docs/documentation-style.md`, the template or the tracker; the finding is parked as fog until the gap is closed |

*Done when the discovery has exactly one home, the current ticket links to it, and the current
ticket's question is unchanged.*

