---
status: accepted
date: 2026-09-14
ticket: "#103"
amends: [ADR-0053]
---

# `ST-LOG-01` binds the name a component builds when none is supplied, and a third-party Plugin names its logger after its own package

`ST-LOG-01` prescribed `aiommbot.<component>` with the words **no exceptions**, and a third-party
Plugin is not `aiommbot.*` — the silence [ADR-0015](0015-plugin-contract-and-composition.md) left
and the question this ticket was raised to answer. Now that a logger can also arrive from the
composition ([ADR-0078](0078-a-logger-is-a-capability-the-composition-supplies.md)), the rule has to
say what it binds.

- **The rule binds the *form* of a built name, not a literal prefix.** One logger per component,
  named after the component's `CONTEXT.md` term in snake case and never after a module path, so
  splitting a module never breaks an operator's configuration. For our components the package is
  `aiommbot`; for a third-party Plugin it is that Plugin's own top-level import package —
  `aiommbot_metrics.collector` and not `aiommbot.metrics.collector`. Where a logger *is* supplied,
  the name is the application's and the rule has nothing to say about it.
- **We do not take the third party's namespace.** `ST-LOG-08` makes the record catalogue a contract
  checked against the code **in both directions**, and a record we did not write, appearing under a
  name we document, breaks that closure. The one host that forces its prefix, Sphinx, publishes no
  catalogue at all — the two go together. celery's alternative keeps its own catalogue closed by
  *re-parenting* a third party's logger rather than renaming it, which is the better mechanism and
  is still closed to us: setting `logger.parent` is logging configuration, which `ST-LOG-10` and
  `ST-MOD-12` place with the application ([`docs/research/43`](../research/43-who-owns-a-librarys-logger.md)).
- **The catalogue survives a supplied logger, because of a rule we already have.** `ST-LOG-08`
  requires a constant message with the variable data in `extra`. That is exactly the precondition
  FastStream fails — several of its records interpolate an exception into the message, so its record
  set is not finite even in principle and it has no catalogue. Ours is finite whoever owns the
  logger object, so the two-way check is unaffected.
- **A third-party Plugin is told the same rule and promised nothing.** The plugin-API section of the
  reference page ([ADR-0080](0080-the-plugin-api-is-a-section-of-the-reference-page.md)) states the
  convention and says that an author documenting their own records is how an operator learns them.
  No host in the survey says anything at all to a plugin author about a logger name.

**The cost is named rather than hidden**: an application that supplies a logger trades the
per-component name for one sink, and `logging.getLogger("aiommbot.dispatcher").setLevel(WARNING)`
stops being the handle for the component it substituted. This is measured rather than supposed —
FastStream's unit of silencing is the broker, not the component, because there is no `logger=` below
the broker.

## Considered options

- *Force `aiommbot.plugins.<name>`, Sphinx's shape* — rejected: it is the one option that breaks the
  closure `ST-LOG-08` depends on, and it would need a carve-out in a rule that currently has none.
  An operator reading `ERROR aiommbot.plugins.metrics` would also read a third party's defect as
  ours.
- *Re-parent the third party's logger, celery's shape* — rejected on our own rules rather than on
  its merits: it is the only hard enforcement of a logger name in the corpus and it keeps the
  catalogue closed, and it works by assigning `logger.parent`, which is a mutation of process-global
  logging state.
- *Say nothing, pytest's answer* — rejected: pytest has no record catalogue to protect and no rule
  claiming no exceptions. Ours has both, so silence would leave `ST-LOG-01` making a claim about
  names it cannot reach.

## Consequences

- `ST-LOG-01`'s limits change from "no exceptions" over a literal prefix to "no exceptions" over the
  form, with the package named by whoever built the logger; `ST-LOG-08` states that it binds the
  records of this distribution.
- [ADR-0053](0053-log-records-are-a-documented-contract.md)'s catalogue is unchanged in substance and
  gains the reason it survives: the constant-message rule is what makes the record set finite.
