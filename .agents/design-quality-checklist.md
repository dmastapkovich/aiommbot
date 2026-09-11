# Design quality checklist

A document is *reviewed* only when every applicable line below is true. Apply it in the *Verify*
step of the playbook, before the commit that sets the status, and again in the hand-off ticket
(#33). A line that cannot apply yet (a neighbouring document does not exist) is recorded as a
deferral in the ticket, not silently skipped.

## Any document

- Status line present and in the form `docs/documentation-style.md` §3 fixes.
- States only the target design: no history narrative, no superseded prose, no reference to a
  predecessor code base, an internal deployment or compatibility with anything outside this
  repository (`docs/documentation-style.md` §9).
- Uses `CONTEXT.md` terms exactly; introduces no synonym the glossary avoids.
- Every decision it relies on is linked to its ADR; the document never restates the decision.
- Every fact it relies on is linked to a `docs/research/` file or a primary source.
- Every ticket reference points at open work; closed work is stated as a decision with its link.
- Every relative link resolves to a committed file; a planned document is named in a code span,
  unlinked, until its file exists (`docs/documentation-style.md` §6).
- Prose wraps at 100 columns; no placeholder text; identifiers in code spans
  (`docs/documentation-style.md` §8).
- Diagrams are Mermaid, follow `docs/design/diagrams.md`, and agree with the building-block view.
- No secret, token, private URL, local path or personal data.
- English; committed with `docs(<area>): … (#N)` and the `TRACKER.md` row in the same commit.

## ADR

- Title states one decision, not a topic.
- Context, decision and why fit in one to three sentences; considered options and consequences
  appear only when the rejected alternative or a downstream effect is worth remembering.
- Passes all three triggers: hard to reverse, surprising without context, a real trade-off.
- Agrees with every accepted ADR; where it changes one, that ADR is rewritten in the same commit
  and both carry the `amends` / `amended-by` link.
- Carries decisions, not mechanics: signatures, defaults and algorithms live in the component
  design document.

## arc42 section

- Answers only its own arc42 question; cross-cutting material lives in §8 (or is deferred to #40
  explicitly), decisions in ADRs.
- §5 (building blocks): every box has a responsibility, an owner document and an allowed-dependency
  direction consistent with the import-linter contract to be.
- §6 (runtime): every participant is an element of the building block view (arc42 tip 6-1,
  `essential`); each scenario says why it is architecturally relevant; each shows the failure branch
  that motivated the design. The template's rules for the section are in the `hld-author` skill.
- §10 (quality): each scenario is stimulus → response → measure, and at least one scenario exists
  per top quality goal.

## Component design document (LLD)

- All eleven template sections filled; *Open questions* names a ticket for each item.
- Public contract lists Protocols, types and errors; everything else is `_internal`.
- Interactions agree with §6 runtime views and with the neighbouring component documents that
  exist; each missing neighbour is a recorded deferral.
- Patterns, SOLID, failure modes, typing, async, error, naming, layout, logging, documentation and
  testing: the document passes §12.1 of
  [`../design/engineering-style.md`](../docs/design/engineering-style.md), the single source for those
  rules. Cite rule identifiers; do not restate the rules.

## Engineering style rulebook

- Every rule is positive ("do X"), has a one-line reason, and a do/don't pair.
- Every rule carries a stable `ST-<AREA>-NN` identifier, its limitations (or the words "no
  exceptions"), its enforcement tier, where it is checked, and the ADR or research note it descends
  from.
- Pattern catalogue names welcome, restricted and banned patterns with the reason and the place.
- Review checklist at the end is derived from the rules above it and nothing else, in two blocks
  — design review over every `LLD`-tagged rule, code review over `review`-tier rules only — and
  every checklist line names the identifiers it covers.
- Tool configuration is not restated: the tier names the tool,
  [ADR-0011](../docs/adr/0011-lint-format-and-architecture-toolchain.md) owns the configuration.
