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
- Failure modes cover timeout, cancellation, dependency outage, bad input, concurrent use; states
  what is logged (never message text, tokens, PII) and what reaches observability.
- Typing and async rules: no `Any`, `cast`, `getattr`; cancellation-safe; timeouts explicit; sync
  face, if any, produced by the mechanism the execution-model ADR fixed.
- Testing: unit, contract suite for pluggable implementations, integration path, typing tests.
- Interactions agree with §6 runtime views and with the neighbouring component documents.

## Engineering style rulebook

- Every rule is positive ("do X"), has a one-line reason, and at least one do/don't example.
- Pattern catalogue names welcome and discouraged patterns with the reason and the place.
- Review checklist at the end is derivable from the rules above it and nothing else.
