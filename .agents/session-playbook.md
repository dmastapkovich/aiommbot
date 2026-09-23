# Session playbook

The steps for one map ticket, by ticket type. Each step ends on its completion criterion; the
session ends only when the final step's criterion holds. The ticket type is its `wayfinder:*`
label; the `design-session` skill runs these steps.

## Every ticket

1. **Warm up** in the order `AGENTS.md` gives. *Done when you can state, in three sentences, the
   question, the inputs, and the settled decisions it must not contradict.*
2. **Claim.** Assign the ticket to yourself (`.agents/issue-tracker.md`, *Writes*). *Done when
   the assignee shows.*
3. **Resolve** — see the type-specific section below.
4. **Verify.** Run `.agents/scripts/check-docs.py` and `.agents/scripts/check-index.py`, which
   mechanise the checklist's width, link, anchor and index lines over the whole catalogue; then walk
   `.agents/design-quality-checklist.md` by hand for every document touched. Fix before anything is
   committed. Diagrams are checked by `.agents/scripts/check-diagrams.py`, which needs a renderer no
   session has, so a new diagram is read here and parsed by CI. The remaining checks of
   `docs/documentation-style.md` §11 — markdownlint, the spell check, workflow hygiene — are hooks
   and fire on the commit of step 5; run them early with `pre-commit run --all-files` rather than
   meeting them there. Where the decision changes an accepted ADR, rewrite that ADR so it states the
   current decision and link the two (`amends` / `amended-by`). *Done when both scripts exit 0 and
   every checklist line for the touched documents is true or recorded as a deferral in the ticket.*
5. **Record.** One commit: new ADR(s) in `docs/adr/`, `CONTEXT.md` terms, the arc42 section or
   component document the ticket owns, the `docs/design/TRACKER.md` rows it changes, links to the
   research it used. Message: `docs(<area>): <what was decided> (#N)`. Push. *Done when
   `git status` is clean and the push succeeded.*
6. **Close.** Draft the `## Resolution` comment (gist plus links to the files) and the map line
   into files first; then post the comment, close the ticket, add the line to the map's
   *Decisions so far* — the title as a link, a gist of at most two lines, the file pointers — and
   detach the ticket from the map, which keeps only open sub-issues
   (`.agents/issue-tracker.md`). *Done when the map body shows the new line.*
7. **Clear the fog.** Graduate anything the answer made specifiable into new tickets (create, then
   wire `blocked_by`, then add as sub-issues of #1); remove the graduated line from *Not yet
   specified*; rule a wrongly scoped ticket out of scope by closing it with a line in *Out of
   scope*;
   update or delete tickets the decision invalidated. *Done when the map's frontier is the true set
   of takeable work.*
8. **Report** to the maintainer in Russian: what was decided, files changed, the next frontier
   tickets. *Done when the message stands alone for someone who did not watch the session.*

## Design by reference

The rule that shapes every ticket type, and the reason the measurement step comes before the
questions.

- **The references are the material, not the illustration.** `.agents/references.md` names the
  curated primary sources and `.refs/` holds them. A design question is answered by reading what
  mature projects already solved and what each solution cost them, not by reasoning from first
  principles and then looking for agreement.
- **Reuse the concept; do not reinvent it.** Where a shape is proven, take it and say whose it is.
  Where a decision needs several, take each from the project that does that part best and attribute
  them one by one. Assembling proven parts is reuse; a part nothing demonstrates is an invention and
  is labelled as one, with the size of the search that found nothing.
- **Maturity is the ranking.** Between two workable shapes, the one to take is the one carried
  furthest by a serious project — most used, most documented, most repaired. A shape a project
  adopted and then regretted in writing is evidence against it, and the regret is worth quoting.
- **No workarounds.** A mechanism that needs a special case, a flag, a second code path or a comment
  apologising for itself is not the design; find the shape that does not need one, or record
  plainly that none exists.
- **Measure the absence too.** "No project in N paths across M clones does this" is a finding of the
  same standing as a positive one, and it belongs in the ADR where the decision rests on it.
- **The maintainer decides, the corpus informs, and neither is asked to do the other's job.** A
  question is for what the corpus cannot settle. An answer that arrives as a criterion rather than a
  choice is applied to the measurement, and the result comes back as a question with the premise
  corrected.

## Grilling ticket (`wayfinder:grilling`)

The default type: a decision the references settle and the maintainer confirms. Conversation is the
last step rather than the first — see *Design by reference* below.

A grilling ticket that also writes a numbered arc42 section — as #38, #39 and #40 do — writes it
with the `hld-author` skill, which carries the template's own measured rules. The grilling below is
what settles the choices the ADRs leave open; the skill is what shapes the section around them.

1. **Build the design tree** before asking anything: the sub-decisions this ticket implies, each
   labelled with what would settle it. *Done when every node is labelled and every one of them has a
   finder dispatched or answered.*
2. **Measure the references before asking anything.** The curated sources of
   `.agents/references.md`, cloned into `.refs/`, are the material: a sub-decision the corpus
   answers is answered by the corpus, recorded with the project, the file and the line that answers
   it, and never put to the maintainer as an open choice. Dispatch background subagents for the
   measurement, read-only, in parallel, and send them back when an answer arrives as a criterion
   rather than a choice. *Done when every node of the tree carries either a reference that settles
   it or the count of paths in which the corpus was searched and found silent.*
3. **Ask only what the measurement leaves open** — where the corpus is silent, where it is split,
   or where an accepted ADR of ours contradicts what the field does. In Russian, via
   `AskUserQuestion`, at most four questions in a round, each opening with the decisions it must not
   contradict and offering the recommended answer first. Every option names the project it is taken
   from and the cost it carries; an option no reference demonstrates says so in those words, with
   the size of the search behind it. Wait, then recompute. Challenge vague terms and propose the
   canonical `CONTEXT.md` word on the spot. *Done when the frontier is empty and the maintainer
   confirms shared understanding.*
4. **Draft the artefacts as the answers land**, not after: an ADR paragraph the moment a
   hard-to-reverse choice is settled — by the corpus or by the maintainer — and a glossary entry the
   moment a term is resolved. Each element of the decision names the project it was taken from.
   *Done when every choice in the tree maps to an ADR line, a glossary term, or an explicit "easy to
   reverse, no ADR".*
5. Continue at *Every ticket*, step 4.

## Research ticket (`wayfinder:research`)

Autonomous; may run several in parallel as background agents.

1. Write the brief: the question, the primary sources to read (source code, official docs, PEPs),
   the output file `docs/research/NN-<slug>.md`, the required sections (findings with URLs per
   claim, a comparison table where things are compared, a recommendation section, Sources), and
   the instruction to write incrementally and mark anything unverified. Peers are evidence, never
   authority; nothing outside this repository's public sources is cited. *Done when a reader of the
   brief alone could judge whether the report answered it.*
2. Dispatch; on completion commit the note with its row in `docs/research/README.md`, comment the
   resolution gist on the ticket, close it, add the map line. *Done when the file is on `main` and
   the ticket is closed.*

## Prototype ticket (`wayfinder:prototype`)

1. Produce the cheapest artefact that makes the question concrete — a code sketch, a Mermaid
   diagram, a stub `pyproject.toml` — attached to the ticket, never committed. *Done when the
   maintainer can react to it line by line.*
2. Grill on the reaction (rounds as above); revise the artefact until it reads right. Record the
   decisions it settles as ADRs and glossary terms; the prototype itself stays on the ticket and is
   never treated as a specification. *Done when the artefact and the ADRs agree.*
3. Continue at *Every ticket*, step 4.

## LLD ticket (`wayfinder:lld`, titled `LLD: <component>`)

Resolved with the `lld-author` skill inside a `design-session`.

1. Create `docs/design/components/<term>.md` from `_template.md`; set the status line to
   `in progress (#N)`; fill sections 1–3 from the building-block view and the ADRs before asking
   anything. *Done when purpose, boundaries and contract are drafted from existing decisions only.*
2. Grill sections 4–11 in rounds, in this order: internal structure, interactions (main path,
   then each failure path), patterns with rejected alternatives, SOLID, failure modes and
   invariants, the rules of `engineering-style.md` §12.1 that bind this component, testing, open
   questions. Draw every diagram per `docs/design/diagrams.md`; use only `CONTEXT.md` terms.
   *Done when every template section is filled.*
3. Cross-check against the runtime view and the neighbouring component documents that exist; fix
   whichever is wrong; record each missing neighbour as a deferral in the ticket. Set the status
   line to `reviewed (#N)` only when the checklist passes. *Done when the component's row in
   `TRACKER.md` §C reads `reviewed`.*
4. Continue at *Every ticket*, step 4.

## Task ticket (`wayfinder:task`)

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
| Sharp question | The question can be stated now, even if it cannot be answered now | a new wayfinder ticket: create, wire `blocked_by`, add as sub-issue of #1; a `TRACKER.md` row in §B or §D if it is a decision or a concern |
| Backlog idea | A feature or tool, not a design decision | an `enhancement` issue plus one fog line in the map (precedent: #34) |
| Gap in the catalogue itself | The document type, template or rulebook cannot hold the finding | a task ticket to extend `docs/documentation-style.md`, the template or the tracker; the finding is parked as fog until the gap is closed |

*Done when the discovery has exactly one home, the current ticket links to it, and the current
ticket's question is unchanged.*
