---
status: accepted
date: 2026-09-09
ticket: "#24"
amended-by: [ADR-0044, ADR-0051, ADR-0058]
---

# The distribution installs the four libraries a Mattermost bot cannot run without, and every other library is an extra named after it

The catalogue said `msgspec`, `httpx2` and `websockets` are "the shipped implementation" without
saying how they arrive, and
[ADR-0026](0026-standalone-typed-api-client-over-an-http-transport-protocol.md) and
[ADR-0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md) read differently on httpx2.
We decided that **`pip install aiommbot` installs `typing_extensions`, `msgspec`, `httpx2` and
`websockets`**, because a bot that cannot decode an event, call the REST API or open a socket is not
a working install, and an extra on the only path through the code is a step in every tutorial that
nobody may skip. `typing_extensions` remains the Core's own single dependency
([ADR-0008](0008-python-floor-3-12-with-typing-extensions.md)) and the Core imports none of the
other three ([ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md)); the other three
belong to the Adapter and to the WebSocketTransport, which is why the smoke import of the Core with
no extras installed keeps working ([ADR-0002](0002-core-scope-two-condition-test.md)).

**One optional library, one extra, named after the library.** Nothing else is a valid extra name: a
capability name would have to choose between the two libraries that realise it, and both of our
replaceable seams have two.

| Extra | Installs | Serves |
|---|---|---|
| `redis` | `redis` | the Redis `KeyValueStore` and `LockProvider` backends ([ADR-0022](0022-state-plugin-model.md)) |
| `picows` | `picows` | the second `WebSocketConnection` implementation ([ADR-0023](0023-websocket-gateway-resilience.md)) |
| `paseto` | `pyseto` | the PASETO `CallbackTokenCodec` ([ADR-0024](0024-webhook-ingress-and-callback-security.md)) |
| `dishka` | `dishka` | the dishka `DependencyProvider` bridge ([ADR-0018](0018-core-owned-type-keyed-dependency-injection.md)) |
| `wireup` | `wireup` | the wireup `DependencyProvider` bridge (ADR-0018) |
| `pytest` | `pytest` | `aiommbot.testing`, which imports it ([ADR-0044](0044-the-testing-toolkit-requires-pytest-and-is-activated-explicitly.md)) |
| `opentelemetry` | `opentelemetry-api` | the `OpenTelemetryPlugin` ([ADR-0051](0051-first-party-observability-plugin.md)) |
| `prometheus` | `prometheus-client` | the `PrometheusPlugin` (ADR-0051) |
| `click` | `click` | the `aiommbot` command ([ADR-0058](0058-the-command-is-a-console-script-behind-the-click-extra.md)) |

`paseto` is the one extra named for a standard rather than a package, because that is the word the
person asking for it uses; ADR-0024 fixed the name and it stays. Three more extras join the table
under the same rule, in the spelling the ecosystem uses for the library: `opentelemetry` installs
`opentelemetry-api` and `prometheus` installs `prometheus-client`, both for the observability Plugin
([ADR-0051](0051-first-party-observability-plugin.md)), and `click` installs the argument parser the
`aiommbot` command is written on
([ADR-0058](0058-the-command-is-a-console-script-behind-the-click-extra.md)).

`click` is the one extra whose absence a **console script** reports rather than a constructor,
because an extra cannot gate an entry point
([`docs/research/25`](../research/25-cli-entry-points-and-what-clis-configure.md) §1); ADR-0058
states that limit of `ST-MOD-08`.

**No aggregate extra.** `websockets` and `picows` are alternatives, so are `dishka` and `wireup`; an
`all` that installs both halves of two either-or choices teaches nobody anything and becomes the
answer to every import error.

**A library is an extra when a published module of ours imports it, and a dependency group when
only we run it.** The line is what the wheel contains, not what the library is for: `pytest` is a
test runner and also the import of `aiommbot.testing`, so it is an extra, while the tooling that
never appears in a published module — `lint`, `typing`, `test`, `docs`, `codegen`, and `dev`
including the rest — lives in PEP 735 `[dependency-groups]`, which are not published in the wheel's
metadata while extras are
([`docs/research/04`](../research/04-modern-python-library-engineering-2026.md)).

A missing extra is reported as `MissingExtraError`, a subclass of `AiommbotError`, raised in the
constructor of the object that needs the library and carrying the extra's name and the install
string (`ST-MOD-08`). `deptry` and one smoke import per extra keep the declarations honest
([ADR-0011](0011-lint-format-and-architecture-toolchain.md)).

## Considered options

- *A bare install of the Core, with `aiommbot[mattermost]` for the three libraries* — rejected: it
  is the most faithful reading of "minimise runtime dependencies", but there is exactly one Adapter
  and it is the reason the distribution exists, so the extra would be mandatory in every install and
  the package name alone would never work.
- *`[rest]` and `[websocket]` extras* — rejected: it lets a script that only sends messages skip
  `websockets`, at the price of four valid installs with different working components and a
  `MissingExtraError` as the ordinary first experience.
- *Capability-named extras (`state`, `observability`)* — rejected: the name would silently pick
  one of two libraries, and the day the preferred library changes the extra means something else.
- *An `all` extra for convenience* — rejected above.
- *Default extras, so a bare install stays lean and still pulls the three* — unavailable:
  [PEP 771](https://peps.python.org/pep-0771/) is a Draft whose implementations are proofs of
  concept, so a design that needs it cannot be built.
- *An `aiommbot[http2]` extra* — rejected: HTTP/2 stays off by default
  ([ADR-0026](0026-standalone-typed-api-client-over-an-http-transport-protocol.md)) and the switch
  is upstream's `httpx2[http2]`, not ours to mirror.
