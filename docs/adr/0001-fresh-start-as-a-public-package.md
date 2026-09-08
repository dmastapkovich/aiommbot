---
status: accepted
date: 2026-09-02
ticket: "#1"
---

# aiommbot 0.5.0 is designed from scratch as a public package with no compatibility promise toward any earlier release

The package is named `aiommbot` and its first public version is **0.5.0**. No earlier version
number is a compatibility promise: nothing outside this repository constrains the design, and the
library may break any interface, its core vocabulary included, in favour of a cleaner one. The
project is public from its first commit — MIT licence, English, community files, semantic
versioning from 0.5.0 — and every decision is made and recorded here, in the open, before
implementation starts.

## Considered options

- *Start at 1.0* — rejected: a 1.0 label promises stability the design has not earned.
- *A new name* — rejected: the concept and audience are the same; a new name would fragment search
  and memory for no design benefit.

## Consequences

- The catalogue states only the target design and never argues from compatibility
  ([`documentation-style.md`](../documentation-style.md) §9).
- The version number is free to move to 1.0 only when the public API has a stability record.
