---
status: accepted
date: 2026-09-14
ticket: "#102"
amends: [ADR-0015, ADR-0016, ADR-0060]
---

# Plugins start in the order the composition lists them and declare no dependency on each other

[ADR-0015](0015-plugin-contract-and-composition.md) gave `PluginSpec` a hard `requires` and a soft
`after`, both naming other plugins **by name**, and ordered activation topologically over them. With
no channel between Plugins ([ADR-0070](0070-plugins-do-not-collaborate-the-composition-hands-one-instance-to-both.md))
neither declaration buys data any more, and naming another plugin invites a third party to depend on
the name of ours instead of on a contract. Litestar, FastStream and django-modern-rest — the three
hosts closest to this design — declare neither, and order what they order by list position.

We decided the same: **`PluginSpec` carries no `requires` and no `after`**. Plugins enter their
lifecycles in the order `plugins=[...]` lists them and stop in reverse, so there is no topological
sort, no dependency graph over plugins and no cycle to refuse.

Litestar's cost for this shape is that coordination is delegated to prose — "plugin authors should
make it clear in their documentation if their plugin should be invoked before or after other
plugins" ([`docs/research/33`](../research/33-the-plugin-to-plugin-channel.md)) — and that cost is
not ours: Litestar's order matters because an `InitPlugin` rewrites a shared `AppConfig`, and no
Plugin here can touch another's contributions
([ADR-0073](0073-what-a-plugin-may-not-do.md)). The one place order is observable is a Plugin
handed an object that is itself a Plugin, and there **the Check phase decides it rather than a
declaration**: an object in a Plugin's settings that also appears in `plugins=[...]` must appear
there *before* the Plugin it was handed to, and the error names both and says how to fix the list.

## Considered options

- *Keep `requires` and narrow its meaning in prose to order plus presence* — rejected: two
  mechanisms for one property, free to disagree. `requires=("redis-backend",)` passes while the
  settings hold a different store entirely, whereas the instance Check of ADR-0070 cannot.
- *Withdraw `requires`, keep `after`, and derive the hard edge from the composition* — rejected as
  half a step: once the order is checked rather than declared, the remaining declaration orders
  nothing a reader of `plugins=[...]` cannot already see.
- *A capability namespace, so `requires` names what is needed rather than who provides it* —
  rejected with `provides` in ADR-0070.

## Consequences

- [ADR-0060](0060-flood-control-and-delivery-dedup-are-one-generic-plugin.md) declared that
  FloodControl's dedup runs before its cooldown "with the `after` mechanism of ADR-0015". That order
  is between two Middleware of one Plugin, so it belongs to the declared Middleware ordering of
  [ADR-0020](0020-two-layer-middleware-chain.md), which is where it now lives.
- `ST-MOD-10`'s deliberate-duplication clause is unaffected: two Plugins that need one capability
  still reach it through a Core Protocol, and neither knows the other exists.
- The composition is read top to bottom and that is the whole ordering story, which is what makes a
  third-party Plugin drop into a list written before it existed.
