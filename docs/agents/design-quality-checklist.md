# Design quality checklist

A document is *reviewed* only when every applicable line below is true. Apply it in the *Verify*
step of the playbook and again in the hand-off ticket.

## Any document

- Status line present and accurate (`not started | in progress (#N) | reviewed`).
- Uses `CONTEXT.md` terms exactly; introduces no synonym the glossary avoids.
- Every decision it relies on is linked to its ADR; the document never restates the decision.
- Every fact it relies on is linked to a `docs/research/` file or a primary source.
- Diagrams are Mermaid, follow `docs/design/diagrams.md`, and agree with the building-block view.
- No secret, token, private URL or personal data.
- English, Conventional Commit, `TRACKER.md` row updated in the same commit.

## ADR

- Title states the decision, not the topic.
- Context, decision and why fit in one to three sentences; considered options and consequences
  appear only when the rejected alternative or a downstream effect is worth remembering.
- Passes all three triggers: hard to reverse, surprising without context, a real trade-off.
- Does not contradict an accepted ADR, or supersedes it explicitly.

## arc42 section

- Answers only its own arc42 question; cross-cutting material lives in §8, decisions in ADRs.
- §5 (building blocks): every box has a responsibility, an owner document and an allowed-dependency
  direction consistent with the import-linter contract to be.
- §6 (runtime): each scenario shows the failure branch that motivated the design.
- §10 (quality): each scenario is stimulus → response → measure, and at least one scenario exists
  per top quality goal.

## Component design document (LLD)

- All eleven template sections filled; *Open questions* names a ticket for each item.
- Public contract lists Protocols, types and errors; everything else is `_internal`.
- Every applied pattern is named as on refactoring.guru, with the problem it solves here and the
  rejected alternative; considered-and-unused patterns are listed.
- SOLID: one argued paragraph per principle; a bent principle says where and why.
- Failure modes cover timeout, cancellation, dependency outage, bad input, concurrent use; each one
  says whether it is a typed outcome or an exception and which boundary converts it.
- Typing, async, error, naming, layout, logging, documentation and testing rules: the document
  passes §12.1 of [`../design/engineering-style.md`](../design/engineering-style.md), which is the
  single source for those rules. Do not restate them here.
- Interactions agree with §6 runtime views and with the neighbouring component documents.

## Engineering style rulebook

- Every rule is positive ("do X"), has a one-line reason, and at least one do/don't example.
- Every rule carries a stable `ST-<AREA>-NN` identifier, its limitations (or the words "no
  exceptions"), its enforcement tier, where it is checked, and the ADR it descends from.
- Pattern catalogue names welcome, restricted and banned patterns with the reason and the place.
- Review checklist at the end is derivable from the rules above it and nothing else, in two blocks
  — design review over every `LLD`-tagged rule, code review over `review`-tier rules only — and
  every checklist line names the identifiers it covers.
- Tool configuration is not restated: the tier names it, [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md) owns it.
