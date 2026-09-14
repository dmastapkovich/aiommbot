---
status: accepted
date: 2026-09-14
ticket: "#102"
amends: [ADR-0015, ADR-0016]
---

# The plugin contract carries no version number: it grows by adding a contribution Protocol and never by changing one

[ADR-0015](0015-plugin-contract-and-composition.md) put a contract version on `PluginSpec` and said
it was "checked at start-up" without saying what the number was. Measured against the hosts this
design reads, the number turns out to be the rare answer and the wrong one for an in-process Python
library: of the fifteen extension hosts read for this ticket **none carries a number that names the
contract offered to extensions separately from its own release**, and of the five in-process Python
hosts of [`docs/research/30`](../research/30-plugin-contract-versioning.md) four ask for no number
at all, because the gate that catches host-plugin skew in this ecosystem is structural — pluggy's
argument-name difference, Litestar's `isinstance`, mypy's ladder over the shape of the entry point.

We decided that **`PluginSpec` carries no contract version and the framework compares none**, and
that compatibility is held instead by the discipline that keeps the one measured protocol number in
this family frozen: Mattermost's plugin hook table is append-only — "Feel free to add more, but do
not change existing assignments" — its six retired hook ids stay reserved rather than reused, and
its `ProtocolVersion` has never moved
([`hooks.go`](https://github.com/mattermost/mattermost/blob/master/server/public/plugin/hooks.go)).
So:

- **A new capability is a new `Contributes*` Protocol, never a new member of an existing one.** We
  have already done this once without naming it:
  [ADR-0050](0050-bounded-resource-state-is-read-not-pushed.md) grew the set from six Protocols to
  seven, and every plugin written against the six stayed valid.
- **A withdrawn Protocol keeps its name**, which is never reused for anything else.
- **The mechanism is `ST-MOD-13`** of [`engineering-style.md`](../design/engineering-style.md): a
  snapshot over the members of every `Contributes*` Protocol, so adding a Protocol passes and
  changing one fails.
- **The window in which a plugin built against the old shape keeps working is #28's**, the
  deprecation policy, not this decision's. The two are different mechanisms and this ADR owns
  neither the window nor a blocklist.

## Considered options

- *An integer the framework publishes, with a set of served numbers* — rejected: it is what no host
  in the survey does, and the set would have to be maintained by hand for a check that, under the
  append-only rule, can never fire.
- *The plugin declares a range of framework releases — the `min_server_version`, `engines.vscode`,
  `requires_ansible`, `minAppVersion` shape* — rejected twice over: it is a floor, so it protects
  the plugin from an old framework rather than the framework from an old plugin, which is the
  direction this ticket needed; and comparing release strings without `packaging` or
  `AwesomeVersion`, which [ADR-0002](0002-core-scope-two-condition-test.md) forbids the Core, is the
  bug `docs/research/30` found in Sphinx's `needs_sphinx`, where `'10.0' > '8.3.0'` is false and the
  gate silently does not fire.
- *Nothing written down at all* — rejected: `ST-MOD-13` costs one rule and one snapshot, and the one
  recorded incident in this space, the pytest 8.1.0 yank, happened precisely because the only guard
  was a warning and the warning silently stopped firing
  ([`docs/research/30`](../research/30-plugin-contract-versioning.md)).

## Consequences

- Refusing a third-party plugin by version is not available in 0.6 and will not become available,
  because 0.5.0 asks a plugin to declare no number. Should a specific release of a specific plugin
  ever break a bot, the answer available is the one Home Assistant reached — a hand-maintained
  block-list keyed on the plugin name — and it would be a decision of its own.
- The append-only rule makes withdrawing a `Contributes*` Protocol deliberately expensive, which is
  the point: the seven Protocols are a public surface under
  [ADR-0007](0007-tiny-public-root-with-explicit-subpackages.md)'s four criteria.
