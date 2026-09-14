---
status: accepted
date: 2026-09-14
ticket: "#102"
amends: [ADR-0015]
---

# Plugins do not collaborate: a capability two Plugins need is a Core Protocol, and the composition hands the same instance to each of them

[ADR-0015](0015-plugin-contract-and-composition.md) said plugins "collaborate only through
Core-owned Protocols" and named no channel through which one reaches another. Three were in use
without being ranked — a `Provider` through `ContributesDependencies`, an object arriving in a
settings field, and the frozen `bot.stats()` snapshot of
[ADR-0050](0050-bounded-resource-state-is-read-not-pushed.md).

We decided there is **no plugin-to-plugin channel at all**. A capability two Plugins need is a
Protocol the Core owns — which is `ST-MOD-10` of
[`engineering-style.md`](../design/engineering-style.md) already — and the **application**
constructs the implementation and hands it to each Plugin that consumes it, in that Plugin's typed
frozen settings. This is what
[ADR-0060](0060-flood-control-and-delivery-dedup-are-one-generic-plugin.md) already does with
FloodControl's platform-identity callable and
[ADR-0061](0061-health-is-a-generic-plugin-over-application-supplied-checks.md) with Health's
`ReadinessCheck`s; State receiving a `KeyValueStore` is the same move, and the gap this ticket found
was that nobody had written it down.

- **No lookup exists.** There is no `bot.plugins.get(...)`, no registry, no name-keyed or type-keyed
  resolution between Plugins, and nothing to consult during compose.
- **Absence is not a runtime branch.** A settings field is typed and required, so a Plugin that
  cannot work without a capability does not construct without it. No Plugin ever holds `None` where
  a capability should be, and no Plugin asks whether one is present.
- **Where the implementation is itself a Plugin** — the storage backends are, because they have a
  lifecycle and contribute a Check of their own
  ([ADR-0066](0066-the-in-memory-backends-own-the-single-process-check.md)) — the application names
  the same object twice: once in `plugins=[...]` and once in the settings of each consumer. A Check
  of the check phase enforces that the two are **the same instance**, which is a stronger statement
  than a declared dependency could make.
- **`bot.stats()` stays, and is not a second channel**: it is a read of a bounded resource whose
  producing type the reader may not name across an import rank (ADR-0050), answered by the Bot
  rather than by a Plugin.

## Considered options

- *A host-owned registry, the shape every surveyed host sanctions* — rejected on the measurement:
  the one Python precedent for a type-keyed one, Sentry's `get_integration`, reduces the class to
  `cls.identifier` and looks it up in a `dict[str, Integration]`, so a `Protocol` cannot be a key at
  all; Litestar's keys on the exact `type(p)`, so a Protocol misses; and Litestar assigns
  `app.plugins` only after the whole init chain has run, so a lookup during compose sees a
  half-built registry ([`docs/research/33`](../research/33-the-plugin-to-plugin-channel.md)). A
  registry also does not buy isolation: inside `sentry_sdk/integrations/` there are 54 cross-unit
  imports, including a subclass across the boundary
  ([`client.py`](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/client.py)).
- *Type-keyed dependency injection between Plugins, with the graph proving presence at compose time*
  — rejected as a mechanism we would be adding alone: it works, and dishka proves it works in Python
  ([`docs/research/33`](../research/33-the-plugin-to-plugin-channel.md)), but no host in the survey
  routes extension units through its container, and the same guarantee is available here from a
  typed settings field plus one Check, without changing `HasLifecycle`.
- *A named capability namespace on `PluginSpec`* — rejected: a second namespace beside the Core
  Protocols, both ours, with a duplicate to refuse in each.

## Consequences

- `ContributesDependencies` is unchanged and keeps its purpose: a Plugin contributes Providers for
  the **application's** Handlers and Middleware
  ([ADR-0018](0018-core-owned-type-keyed-dependency-injection.md)), not for other Plugins.
- Substituting an implementation is composition, not declaration: the application constructs a
  different object behind the same Core Protocol and hands that one instead. This is why no
  `provides` is needed for it.
- The rule django-modern-rest reaches from the other side holds here too — its
  `plugins-independence` contract carries no `ignore_imports` and what two plugins share moves down
  into a layer both may import
  ([`.importlinter`](https://github.com/wemake-services/django-modern-rest/blob/master/.importlinter)).
  For us that layer is the Core, and the contract is already written
  ([ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md), `ST-MOD-10`).
