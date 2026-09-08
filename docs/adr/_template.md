---
status: proposed | accepted
date: YYYY-MM-DD
ticket: "#N"
amends: [ADR-NNNN]        # optional: ADRs this decision rewrites
amended-by: [ADR-NNNN]    # optional: ADRs that rewrote this one
---

# <One decision stated as a sentence; a semicolon means two ADRs>

<One to three sentences: the context, what we decided, and why. Present tense; the current
decision only. Link every ADR and research note you rely on; never restate them.>

## Considered options

<Only when a rejected alternative is worth remembering: one line each, with the reason it lost.>

## Consequences

<Only when a non-obvious downstream effect must be called out. Mechanics belong to the component
design document, not here.>

<!--
Write an ADR only when all three hold: hard to reverse, surprising without context, a real
trade-off. Otherwise record the choice in the ticket resolution and move on.
When this decision changes an earlier ADR, rewrite that ADR in the same commit so it states the
current decision, add this ADR to its `amended-by` and it to this `amends`. When it withdraws an
earlier decision in full, delete that file and point its index row here.
Add a row to README.md and to docs/design/TRACKER.md §B in the same commit.
-->
