---
status: accepted
date: 2026-09-14
ticket: "#102"
amends: [ADR-0017, ADR-0021]
---

# A Plugin contributes by returning values and reaches nothing it did not contribute; the closed list of what it may not do is five prohibitions made unreachable, one Check and one rule

Seven narrow `Contributes*` Protocols were chosen so that no Plugin has the power of a Litestar
`InitPlugin`, which rewrites the whole `AppConfig`
([ADR-0015](0015-plugin-contract-and-composition.md)) — and that boundary was never written down.
The categories every surveyed host prohibits first are process-global state, side effects during
registration and internal setters
([`docs/research/34`](../research/34-plugin-conflicts-and-prohibitions.md)), and the note's own
conclusion is that these are the ones an API has to make hard to reach rather than merely document.

The general rule is that **a Plugin contributes by returning a value and never by mutating the
composition**; there is no `AppConfig`-shaped object anywhere for it to reach. The closed list
follows, with how each prohibition is held:

| A Plugin may not | Held by |
|---|---|
| remove or replace the `ErrorBoundary` | unreachable: no `Contributes*` Protocol yields it, and the Bot installs it outside both Middleware layers |
| register a second Adapter, or replace the composed one | unreachable: the Adapter is a constructor argument of the Bot, not a contribution |
| include a Router into another Plugin's subtree | unreachable: `ContributesRouters` returns routers the Bot attaches, and no Plugin holds a handle on another's |
| veto a Signal it subscribes to | unreachable: a subscriber returns nothing and the publisher branches on no subscriber's wish |
| read or write another Plugin's settings object | a Check: a Provider whose key is the contributing Plugin's own settings type is an error, so settings stay private to the thing they configure |
| touch process-global state | `ST-MOD-12` of [`engineering-style.md`](../design/engineering-style.md), tier `tool` |

**Contributing a `Check` about another Plugin is allowed**, deliberately: a Check is a pure question
about the frozen composition, which is exactly how the in-memory backends refuse a replicated
process on behalf of every consumer of the seam
([ADR-0066](0066-the-in-memory-backends-own-the-single-process-check.md)). Its `id` is prefixed with
the name of the Plugin that contributed it, so an operator reading the failure list sees who
refused.

Import-time side effects are not on the list because they are already `ST-MOD-07`'s, and this
decision cites that rule rather than restating it.

## Considered options

- *Document all seven and add no mechanism* — rejected: `docs/research/34` names the three
  categories a plugin API must make hard to reach rather than document, and two of them are on this
  list.
- *Refuse a Check that names another Plugin* — rejected: it would withdraw ADR-0066, whose whole
  point is that being process-local is a fact about the storage rather than about any of its
  consumers.

## Consequences

- [ADR-0017](0017-typed-async-lifecycle-signals.md) collected subscriber failures and returned them
  in a typed outcome without saying whether a subscriber could stop what it was notified about. It
  now says so: a Signal is a notification and its outcome reports failures to the publisher, which
  acts on them itself.
- [ADR-0021](0021-core-error-boundary.md) called the `ErrorBoundary` non-removable of the Middleware
  chain. It now says it of a Plugin too, which is where the question actually arises.
- `ST-MOD-12` closes a named list — logging configuration, `warnings` filters, `sys.path`, signal
  handlers ([ADR-0064](0064-run-owns-the-stop-signals-and-serve-owns-none.md)), the event-loop
  policy ([ADR-0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md)) and
  `os.environ` — each of which some surveyed CLI or plugin host mutates and each of which belongs
  to the application ([`docs/research/25`](../research/25-cli-entry-points-and-what-clis-configure.md)).
