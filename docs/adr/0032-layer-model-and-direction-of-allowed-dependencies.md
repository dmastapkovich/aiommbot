---
status: accepted
date: 2026-09-04
ticket: "#38"
---

# Allowed dependencies run Core → (Adapter | generic plugins) → adapter-specific plugins → testing toolkit, and a generic Plugin may never import the Adapter

[ADR-0002](0002-core-scope-two-condition-test.md) put the Core, the Adapter and the first-party
Plugins in one distribution and said the boundaries are import-linter contracts;
[ADR-0015](0015-plugin-contract-and-composition.md) said a Plugin is either generic (depends on the
Core only) or bound to an adapter, and that plugins collaborate only through Core-owned Protocols.
Neither fixed the layer list, and the two statements do not fit one linear order: a generic Plugin
sits *above* the Core but must not sit above the Adapter. We decided the layer model of the
building-block view, which is also the import-linter contract to be:

| Layer | Contains | May import |
|---|---|---|
| Testing toolkit | `aiommbot.testing` | everything below |
| Adapter-specific plugins | WebSocketTransport, Webhook, IdentityCache | the Adapter and the Core |
| Adapter · generic plugins | the Mattermost Adapter · State, storage backends, DI bridges, the observer extra | the Core only — **and never each other** |
| Core | envelope, routing, dispatch, middleware, DI, lifecycle, the Protocols | the standard library and `typing_extensions` |

- **The Adapter and the generic plugins are one rank, not two.** A generic Plugin that could import
  the Adapter would be generic in name only, and ADR-0015's promise — a second platform adapter is
  an addition, not a rewrite — would be enforced by review instead of by mechanism. The rank is
  written as two independent siblings, so the checker rejects `State → aiommbot.mattermost` the day
  it is written rather than the day a second adapter is attempted.
  The case that proves it is the State plugin: it needs a `StateKey` built from Mattermost
  identifiers and still may not import the Adapter, so it consumes the Core `StateKeyProvider` seam
  and receives the Adapter's implementation by injection
  ([ADR-0022](0022-state-plugin-model.md)). Where an adapter-specific plugin is consulted by the
  Adapter rather than the reverse — IdentityCache and the Workspace
  ([ADR-0028](0028-runtime-helpers-and-identity-resolution.md)) — the Protocol is Adapter-owned, so
  the import still runs upward.
- **Plugins are mutually independent within a rank as well as across ranks** (ADR-0015): an
  `independence` contract over every first-party Plugin. A plugin needing another plugin's
  capability depends on the Core Protocol that capability implements — Webhook's nonce store and
  IdentityCache both reach `KeyValueStore`, never the State plugin that also uses it.
- **The Core imports no third-party package at all**, a `forbidden` contract plus the smoke import
  of ADR-0002; `typing_extensions` is the single exception
  [ADR-0008](0008-python-floor-3-12-with-typing-extensions.md) admits.
- **The testing toolkit is a layer, not a rank of plugins.** It may import everything because its
  job is to double everything; nothing may import it, which is what keeps test doubles out of the
  shipped runtime.

The direction on every arrow of the building-block view is this table, and a diagram that
contradicts it is a bug in one of the two.

## Considered options

- *One `plugins` layer above the Adapter* — rejected: the contract is shorter and reads more
  easily, but the generic/adapter-specific line then exists only as prose in `PluginSpec`, and the
  one violation that matters (a generic plugin reaching into Mattermost vocabulary) is exactly the
  one it stops catching.
- *A sixth rank below the Core holding only the Protocols* — rejected: it is the purest reading of
  DIP, but the Core's Protocols are consumed by the Core's own components, so the extra rank buys
  nothing that `forbidden` does not already buy, and six ranks for one wheel read as ceremony.
- *Separate distributions per layer* — rejected in ADR-0002; the contracts give the same isolation
  inside one wheel.

## Consequences

- #24 maps these layers onto package paths, `__all__` and extras; this ADR names the layers and
  their direction, #24 names the directories. Where the two documents meet, the layer name is this
  ADR's line and the path is #24's.
- The `independence` contract makes a shared helper between two plugins impossible by construction:
  such a helper belongs to the Core behind a Protocol, or it is duplicated on purpose.
