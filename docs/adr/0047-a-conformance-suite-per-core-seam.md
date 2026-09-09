---
status: accepted
date: 2026-09-09
ticket: "#25"
amends: [ADR-0015]
---

# Every Core seam has a conformance suite, delivered as a factory over the implementer's factory, and tightening one is a change to the Protocol

`ST-SOL-03` makes an implementation substitutable only once it passes its Protocol's conformance
suite and `ST-DOC-03` makes every Protocol docstring name that suite, while
[ADR-0015](0015-plugin-contract-and-composition.md) had enumerated four suites, which leaves eight
seams whose implementers are told to pass something that does not exist. We decided **one suite per
seam row of [§5.4](../design/05-building-block-view.md), plus one for the plugin lifecycle** —
thirteen — so the rule needs no threshold and no per-component argument, and the two rows that carry
a paired Protocol are one suite parametrised over the asynchronous and the synchronous face
([ADR-0029](0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md)).

- **A suite is a function of the implementer's factory, and the implementer names the result**:
  `test_redis_store_conforms = key_value_store_conformance(lambda: RedisKeyValueStore(url=URL))`,
  the form `ST-TST-02` already fixes. Nothing is subclassed, which is `ST-PAT-07`, and nothing is
  collected out of our package, so the implementer's own suite stays in their own file with their
  own name on the failure.
- **An optional capability is an argument, not a fork.** `ST-SOL-03` allows a Protocol to declare a
  capability optional — `KeyValueStore`'s TTL is the case — so the factory takes the capabilities
  the implementation declines and the suite asserts the declining rather than skipping the subject.
- **A case has a name, and the name is part of the contract**, because it is what the implementer
  reads in the failure and what they cite when they disagree with it.
- **The suites are public API on the same terms as the rest** of `aiommbot.testing`: one row per
  name on the reference page, checked in both directions by the guard test of
  [ADR-0043](0043-explicit-re-export-with-a-reference-page-as-the-public-list.md). A case added for
  behaviour the Protocol already promises is an ordinary fix; a case that demands something new is a
  change to the Protocol and travels by the Protocol's own rules, never quietly through the suite.

## Considered options

- *Base classes the implementer subclasses, as SQLAlchemy's dialect suite and fsspec's abstract
  tests do* — rejected: it enumerates every case for free and is the most widespread shape, but it
  makes one of our classes an inheritance extension point, which `ST-PAT-07` bans and `ST-SOL-03`
  does not need.
- *Suites collected from inside our package with `pytest --pyargs aiommbot.testing…`* — rejected:
  it is pytest's documented way to run tests that live in an installed distribution
  ([pytest, *Changing standard test discovery*](https://docs.pytest.org/en/stable/example/pythoncollection.html)),
  but the implementer then has no place to name their factory, and rootdir and ini resolution follow
  the argument as a path
  ([pytest#2820](https://github.com/pytest-dev/pytest/issues/2820)).
- *A suite only where a second implementation exists* — rejected: `ST-TST-02` already allows that
  exception for a Protocol with one implementation and no extension point, and taking it as the rule
  reopens the question in every component document — for seams whose only implementer is the
  application, such as `TokenProvider`, it would answer it wrongly.
- *`verifyObject`-style structural assertion instead of a behavioural suite* — rejected: the four
  checkers of [ADR-0009](0009-four-strict-type-checkers.md) already prove the shape statically, and
  the promise worth checking is the behaviour.

## Consequences

- [ADR-0015](0015-plugin-contract-and-composition.md)'s enumeration of four suites is rewritten
  there to point here.
- A third-party plugin, storage backend or socket library ships its own test file with as many
  lines as it has seams, and needs nothing from us but the factories and
  [ADR-0044](0044-the-testing-toolkit-requires-pytest-and-is-activated-explicitly.md)'s one
  `conftest.py` line.
- A conformance case reports what it expected and what it observed as typed data rather than
  through a bare `assert`, because assertion rewriting cannot reach our package
  ([ADR-0044](0044-the-testing-toolkit-requires-pytest-and-is-activated-explicitly.md)).
- The suite for `Transport` and the one for the plugin lifecycle are what a third-party Transport
  runs; `FakeMattermost`'s ports run the `HTTPTransport` and `WebSocketConnection` suites like any
  other implementation
  ([ADR-0045](0045-one-stateful-fake-mattermost-is-the-only-platform-double.md)).
