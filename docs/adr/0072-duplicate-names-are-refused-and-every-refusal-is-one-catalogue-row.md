---
status: accepted
date: 2026-09-14
ticket: "#102"
---

# A duplicate plugin name and a duplicate handler name are refused, a second Transport is not a conflict, and every refusal the check phase makes is one row of one catalogue

The check phase is where a conflicting declaration is refused
([ADR-0016](0016-three-phase-start-with-checks.md)), and the refusals existed — scattered over five
ADRs, with four declarations covered nowhere. A conflict is refusable only where the host owns the
namespace being claimed, and where the key is derived rather than declared the collision resolves in
silence ([`docs/research/34`](../research/34-plugin-conflicts-and-prohibitions.md)). We decided the
four open cases by asking which namespace is ours:

- **Two Plugins with the same `PluginSpec` name — refused.** The Bot owns the plugin-name namespace:
  it is what a log record and a Check message identify a Plugin by. One error-severity Check.
- **Two Handlers with the same qualified name — refused.** The Router owns it: a `HandlerSpec` name
  under a router path is what `bot.routes()` publishes and what every dispatch record names, so two
  a reader cannot tell apart is the defect pytest carries with same-name fixtures, where the last
  registration silently wins and nothing reports the shadowing
  ([`docs/research/34`](../research/34-plugin-conflicts-and-prohibitions.md)).
- **A third-party Transport composed beside one of ours — not a conflict.** Several Transports in
  one process is the design ([ADR-0005](0005-one-ingress-many-workers.md)), and the `independence`
  contract that keeps ours apart is about imports, not about composition. Nothing is refused, and
  the silence that invited the question is what this line ends.
- **A generic Plugin that turns out to need the Adapter — refused by the build, with no new Check.**
  The only way to need one is to import it, and `layers` plus `independence` fail before a test runs
  ([ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md),
  [§10.5](../design/10-quality-requirements.md#105-modifiability)). The declaration answer is to
  become adapter-specific with `for_adapter`, or to receive the fact through a seam or a typed
  setting.

**The full list of refusals is one catalogue** — id, severity, message, hint and the party that
contributes it, one row each — and it lives in `components/bot.md`, because a Check is a part of the
Bot and mechanics belong to a component design document. A guard test reads the catalogue and the
code in both directions, the way
[ADR-0053](0053-log-records-are-a-documented-contract.md) does for log records. Each ADR keeps its
decision and stops being the place a reader goes to enumerate what start-up refuses.

## Considered options

- *The catalogue in [§8.6](../design/08-cross-cutting-concepts.md)* — rejected: a §8 concept is a
  mechanism, a grid and a limit ([ADR-0062](0062-a-cross-cutting-concept-is-a-mechanism-a-grid-and-a-limit.md)),
  and a table of messages is neither.
- *The catalogue in this ADR* — rejected: ids, messages and hints are mechanics, and an ADR carries
  decisions.
- *Warning instead of refusing on a duplicate name* — rejected on the recorded precedent: Sphinx's
  `add_directive` warns "will not be overridden" and then overrides on the next line, which leaves
  the operator's model wrong in a way that either raising or overriding quietly does not.
