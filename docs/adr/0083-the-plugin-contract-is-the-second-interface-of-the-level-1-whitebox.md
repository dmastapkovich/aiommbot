---
status: accepted
date: 2026-09-15
ticket: "#85"
amends: [ADR-0015, ADR-0035, ADR-0038, ADR-0050]
---

# The plugin contract is the level-1 whitebox's second interface, listed at §5.1.2 and specified where each contribution is handled

The seven Contribution Protocols of
[ADR-0015](0015-plugin-contract-and-composition.md) are Core-owned public API under semantic
versioning that appeared in no row of [§5](../design/05-building-block-view.md) at all:
[ADR-0038](0038-seam-inventory-records-the-direction-of-the-call.md) found the gap while stating
§5.1.1's membership rule positively and routed it here rather than settling it in passing. They are
not a substitution surface — a Plugin implementing one **adds** a contribution where an
implementation of a seam **replaces** a realisation, and arbitrarily many Plugins implement each. We
decided:

- **They are the level-1 whitebox's second interface, at
  [§5.1.2](../design/05-building-block-view.md#512-the-plugin-contract) *The plugin contract*.** The
  arc42 template gives the level-1 whitebox `<Name interface 1>` … `<Name interface m>` as
  subsections beside the blackbox descriptions
  ([`arc42-template`, §5](https://github.com/arc42/arc42-template/blob/master/EN/adoc/05_building_block_view.adoc)),
  which is the slot
  [ADR-0081](0081-the-building-block-levels-count-source-code-and-level-n-lives-in-section-5-n.md)
  took for §5.1.1; a second interface is the template's own plural, and the slot's admission test —
  "important interfaces, that are not explained in the black box templates of a building block" —
  is what these Protocols pass and a part of one component would fail. **Not** seam rows: arc42
  sanctions no interface entry for a contract that many contained blocks implement at once, every
  worked interface example in its corpus has one providing block, and none of the eight published
  arc42 documents lists such a contract in an interface slot.
- **Each Protocol is specified in the document where its contribution is handled**, and the
  *Specified in* column of §5.1.2 is authoritative about which, exactly as it is for §5.1.1
  ([ADR-0035](0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md),
  ADR-0038). arc42 says so itself for a contract that recurs across blocks — "Describe the interface
  in detail at the level where it is actually handled … At all other occurrences … add references to
  the detailed description" ([FAQ C-5-10](https://faq.arc42.org/questions/C-5-10/)) — and it is what
  Django, the oldest plugin host in the corpus, does with every contribution interface it has:
  system checks in the check-framework reference, signals in the signals reference, middleware in
  the middleware reference, `AppConfig` in the applications reference, and no page for the surface
  as a whole.
- **§5.1.2 is an index a reader can finish without leaving it.** Every row says what a Plugin
  returns and when the Bot asks for it, because the contract is specified across five documents and
  this table is the only place it is visible whole. Litestar is the warning: seven narrow
  pick-what-you-need contracts, a collective *Plugins* page that covers four of them, `CLIPlugin`
  documented inside the CLI page and `OpenAPISchemaPlugin` — a public member of
  `litestar.plugins.__all__` — on no usage page at all.
- **`PluginSpec` and the seven are one contract in two places, and §5.1.2 says which is which.** The
  declaration is a value a Plugin carries, so it stays a part of `Bot` in §5.2.1; the Protocols are
  what the Core calls, so they are an interface. ADR-0015 pairs them and neither is the other.
- **Nothing recounts.** The substitution surface is still sixteen Protocols on thirteen seam rows,
  and [ADR-0047](0047-a-conformance-suite-per-core-seam.md) is still fourteen suites, because its
  rule keys on §5.1.1. `HasLifecycle` is the one Contribution Protocol with a suite of its own:
  entering and leaving a lifecycle has behaviour to check, while returning a list has none. No
  project in the corpus ties a conformance suite to a contribution interface — SQLAlchemy's eleven
  `*Events` classes have none, and its one compliance suite serves the `Dialect` port and is
  partitioned by database feature rather than by interface.
- **§5.1.2 creates no writing-order edge.** ADR-0035's rule names §5.1.1 and the *Document* column
  of §5.2.1–5.2.5, and §5.1.2 joins neither: each Protocol has one member whose meaning ADR-0015
  fixes and whose shape `ST-MOD-13` freezes, so a Plugin document that names one has nothing to wait
  for — ADR-0035's own *structural need, not mention* clause. The map already runs this way, with
  `LLD: KeyValueStore and LockProvider backends` in the first wave although its backends implement
  `ContributesChecks`.

## Considered options

- *Parts of the `Bot` component, specified in `bot.md`* — rejected. It is the cheapest option and
  arc42's own C-5-10 would allow it, but of the seven corpus projects that separate a contribution
  contract from their substitutable ports, all seven give the contract a place of its own — Litestar
  a *Plugins* page beside *Stores*, Rasa a `custom-graph-components` page while its five ports sit
  under a category named *Architecture*, SQLAlchemy two `events` pages beside the dialect manual,
  import-linter `custom_contract_types.md`, dishka a `provider/` tree beside `container/`,
  discord.py `cogs.rst`, mmpy_bot `plugins.rst`. The one project that keeps them together —
  structlog — never separated them in the first place. A part row also buries a public surface under
  one component of thirty-two.
- *Seven rows in §5.1.1* — rejected, and not only on cost. It would make
  [`engineering-style.md`](../design/engineering-style.md) §1's "the whole substitution surface"
  false, restate the count in eleven places and the conformance-suite figure in nine, and rewrite
  seven ADRs — but the measurement is against it first: arc42 routes a contract shared by many
  blocks to a cross-cutting concept with a stereotype left in §5 (tips 5-10, 5-28, 8-11), and both
  published arc42 documents describing an extensible system do exactly that and give the extension
  contract no §5 row.
- *No presence in §5 at all, with §8.6 carrying the concept* — rejected on arc42's only
  call-for-completeness: "There shall be an architecture building block for every single line of
  source code that is created specifically for that system" (tip 5-18, repeated by FAQ C-5-3). The
  Protocols are source code of the Core.
  [§8.6](../design/08-cross-cutting-concepts.md) keeps the concept and gains nothing else:
  [ADR-0062](0062-a-cross-cutting-concept-is-a-mechanism-a-grid-and-a-limit.md) leaves a concept
  section with a mechanism and three labelled lines, and no inventory.

## Consequences

- Four component documents acquire a contract they did not know they owned: `router.md`,
  `middleware.md`, `dependency-provider.md` and `event-registry.md` each specify one Contribution
  Protocol, and `bot.md` the remaining three. The obligation is visible in §5.1.2 and in each
  ticket.
- The contract that
  [ADR-0069](0069-the-plugin-contract-carries-no-version-and-grows-by-adding-a-protocol.md) holds as
  one thing — `ST-MOD-13` snapshots the members of every `Contributes*` Protocol together —
  is specified in five documents. §5.1.2 is what keeps it countable, which is why its rows carry the
  contribution and not only a link.
- An eighth Contribution Protocol is one row of §5.1.2 and one sentence in the document that handles
  it. Nothing else moves, which is the property ADR-0069's append-only rule needs.
