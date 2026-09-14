---
status: accepted
date: 2026-09-14
ticket: "#37"
---

# A §10 scenario is a registered concern in context, measured by a number an ADR already fixed or by a named check that will run

arc42 asks a quality scenario to "allow to decide whether they are fulfilled" and never asks for a
number; its own published examples measure by a test suite, by conformance across named targets and
by an invariant
([`.agents/research/40`](../../.agents/research/40-arc42-quality-requirements.md) §14). It also
publishes no bound on how many scenarios §10 holds, deprecates the graphical quality tree in favour
of a table, and leaves the split between §1.2 and §10 stated in one direction only (same note, §13,
§15; [`.agents/research/39`](../../.agents/research/39-arc42-goals-and-constraints.md) §4). This
design will never produce an operational number — `aiommbot` is a library, so nothing in it is
deployed, observed or benchmarked by us. We decided what a scenario is in this catalogue,
completing the series that
[ADR-0062](0062-a-cross-cutting-concept-is-a-mechanism-a-grid-and-a-limit.md) started for §8 and
[ADR-0067](0067-a-runtime-scenario-is-one-order-between-boxes.md) continued for §6:

- **A concern of [`TRACKER.md`](../design/TRACKER.md) §D admits a scenario, and nothing else does.**
  The register that is §8's table of contents is §10's: every row owes one scenario and there is no
  scenario without a row. §D already carries a *Quality scenario* column, so the register is the
  completeness test in both directions and neither table can drift silently.
- **A row is context, stimulus, response and measure.** That is arc42's own short form — the one it
  marks as its house style, "Context/Background, Source/Stimulus, Metric/Acceptance Criteria" — with
  the response named separately so a behavioural outcome stays visible beside the criterion that
  decides it. The three-term "stimulus → response → measure" this catalogue used before appears
  nowhere in arc42 and drops the context, which is what makes a scenario decidable rather than a
  slogan (note 40 §12).
- **A number only where a decision already fixed one.** The Drain, the stop, the Shutdown budget,
  the heartbeat, the silence monitor, the backoff ceiling, the reply deadline and the body cap were
  chosen for stated reasons; §10 measures against them and may neither restate nor re-choose them.
- **Everywhere else the measure is a named check that will run** — a Conformance suite of
  [ADR-0047](0047-a-conformance-suite-per-core-seam.md), an `ST-<AREA>-NN` rule of
  [`engineering-style.md`](../design/engineering-style.md), a `tests/typing` case or an
  import-linter contract. arc42 licenses this: its field is "**the criteria** or metric", its FAQ
  asks for measurability "in some fashion", and its own §10.2 example measures correctness by
  "automated positive and negative tests"; across the seventy classifiable scenarios of the eleven
  measured documents, thirty-one measure by a gate against twenty-eight by a number. The obligation
  it attaches is to name the rig, so a measure names *which* suite, *which* rule, *which* contract
  (note 40 §14).
- **[§1.2](../design/01-introduction-and-goals.md#12-quality-goals) ranks and §10 holds.** All
  seventeen scenarios live in §10 and §1.2 links into it, which is the direction
  [tip 1-17](https://docs.arc42.org/tips/1-17/) sanctions; the template's §10 line prefers the
  opposite and would split one register across two sections. §10.1 is a table rather than a
  graphical tree, as arc42 now advises, and its single purpose is the absence check: a goal with no
  concern under it is a goal nothing tests.
- **Performance is not a goal and gets no scenario.** No target exists, and inventing one to fill
  the slot would put the only unmeasured number in the section. The question stays open on the map.

## Considered options

- *Every measure a number* — rejected: thirteen of the seventeen registered concerns have no
  duration to measure, so §10 would cover four of them and three of the five ranked goals would have
  no scenario at all.
- *Every measure the name of a check, the fixed durations included* — rejected: it hides thresholds
  chosen for reasons worth reading, and §7's arithmetic would become the only place a reader could
  find the 25 / 28 / 30 second chain.
- *The five top scenarios in §1.2 and the other twelve in §10*, which is the template's own wording
  — rejected: it splits the §D register across two sections, so the *Quality scenario* column would
  point at two documents and the completeness test would stop being mechanical.
- *Tagging a concern with every goal it serves, as arc42's Q42 model does instead of a hierarchy* —
  rejected for this register: with seventeen concerns and five goals a single parent partitions the
  set cleanly, and the absence check that tip 10-4 keeps the tree for works on single parents.
- *Scenarios written per component instead of per concern* — rejected: a concern is cross-cutting by
  construction, so a per-component scenario would be written once per carrier, and
  [§8.0](../design/08-cross-cutting-concepts.md#80-which-components-carry-which-concept) already
  holds that mapping.

## Consequences

- [`design-quality-checklist.md`](../../.agents/design-quality-checklist.md)'s §10 line changes with
  this ADR: a scenario is context → stimulus → response → measure, not the three-term form it named
  before.
- Adding a cross-cutting concern is now four edits in one commit — the ADR, the §D row, the §8
  section and the §10 scenario — and the last of them names a check that has to exist.
- §10 becomes the acceptance list the implementation map inherits: every measure is either a
  threshold to assert or a suite to write.
