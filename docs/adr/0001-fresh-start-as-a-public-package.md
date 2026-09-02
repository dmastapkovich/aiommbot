---
status: accepted
date: 2026-09-02
---

# aiommbot 0.5.0 is a from-scratch public rewrite with no compatibility with 0.4.x

`aiommbot 0.4.x` is an internal framework (private GitLab, ~20k LOC) used by eleven company bots.
It works, but its design has accumulated debt that cannot be refactored away incrementally: a
`Bot(Router)` god object, thirteen parallel request classes, hundreds of `Any`, hand-rolled
webhook cryptography, and a documentation set that has drifted from the code.

We decided to start a **new public repository with a clean history**, keep the name `aiommbot`,
and begin versioning at **0.5.0** so the lineage is visible while the break is unmistakable. The
0.4.x line is frozen in maintenance mode. **No compatibility layer** will be built: the eleven bots
migrate in a separate effort, if at all, and their migration is not a constraint on 0.5.0 design.

## Considered options

- *Incremental refactor of 0.4.x in place* — rejected: every change is bounded by consumers, and the
  core problems are structural.
- *`aiommbot 1.0` in the same repository* — rejected: a public project deserves a public history
  without internal artefacts, and a 1.0 label would promise stability the redesign has not earned.
- *A new name* — rejected: the concept and audience are the same; a new name would fragment search
  and memory for no design benefit.

## Consequences

- The design may break anything, including core vocabulary. Ideas from 0.4.x are re-decided one
  ticket at a time.
- The library is written to open-source standards from day one: MIT licence, English, community
  files, semantic versioning.
