# 11. Risks and technical debt

_Status: reviewed (#42)._

What is known to be unfinished or uncertain in the 0.5.0 design, in one place. A **risk** may go
wrong and is largely not ours to fix; a **debt** was chosen, is paid in instalments, and names the
ticket that retires it.

Risks are ordered by how much of this catalogue a row would rewrite if it came true — an undecided
behaviour above a dependency that may drift above a cost a mechanism already bounds. Debt is ordered
by what a reader of 0.5.0 notices first. That order is the priority arc42 asks for; there is no
severity scale, because a probability this design could defend does not exist for a single row.

A row names its risk and links to where it is already described. Nothing here restates a failure
mode of the runtime view, a limit of a cross-cutting concept or a scenario of the quality
requirements — those sections own them, and a row that repeated one would go stale on its own.

## 11.1 Risks

| Risk | Described in | What holds it today | Retired by |
|---|---|---|---|
| Two store-unreachable behaviours are undecided: what a `State` plugin does, and what either process reports when the lease cannot be taken | [§6.4](06-runtime-view.md), [§6.8](06-runtime-view.md) | nothing — the rows say `undecided` | #107 |
| Authorising *who* may press a button is not decided, in the concept whose goal is security | [§8.13](08-cross-cutting-concepts.md) | the Callback token proves the button was ours, never who pressed it | on the map's frontier |
| [ADR-0057](../adr/0057-reliability-middlewares-and-error-reporting-stay-outside.md) keeps reliability middleware outside the framework on a premise still under review | [`TRACKER.md` §D](TRACKER.md) | the ADR stands; its concern row reads `in progress` | #104 |
| The deprecation window the semver promise depends on is not decided | [`TRACKER.md` §D](TRACKER.md) | [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md) fixes what *public* means; the window is open | #28 |
| Mattermost publishes its OpenAPI specification unversioned from `master` while the server releases monthly, and forward compatibility against a newer server is unknown | [ADR-0025](../adr/0025-generated-dataclass-models-with-a-codec-protocol.md) | a pinned ESR floor and a nightly diff of the specification | — |
| The same specification declares `required` on 21 of its 221 schemas, so generated optionality is a guess | [§2.1](02-constraints.md), [research 05](../research/05-mattermost-rest-typing-codegen.md) | the overlay, and optionality decided at the wire edge | — |
| `httpx2` is a young fork and may be abandoned | [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md), [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) | the `HTTPTransport` seam, which both faces share, and an exact pin | — |
| `httpx2` states nothing about client thread safety and runs no free-threaded job, while our floor guarantees one | [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) | a documented promise of one client per thread, not a mechanism | — |
| `ty` and `pyrefly` move weekly and follow no semantic versioning, and two of the four type checkers are them | [ADR-0009](../adr/0009-four-strict-type-checkers.md) | exact pins bumped in dedicated commits | — |
| 136 claims across 37 research notes are marked `[unverified]`, and none is marked as such where the design acts on it — eight of them underwrite a platform constraint | [research index](../research/README.md), [§2.1](02-constraints.md) | the marker in the note, which no document carries forward | — |
| A deployment that runs two consumer replicas without a shared store processes every event twice, silently | [§7.4](07-deployment-view.md) | the consumer lease, and a start-up Check on the shared store | — |
| A `Cooldown` or a delivery-dedup limit not shared across replicas is multiplied by the replica count | [§7.4](07-deployment-view.md) | the same Check, which cannot see a store that is merely separate | — |
| `FloodControl` fails open when its store is unreachable, so a limit silently stops being enforced | [§6.4](06-runtime-view.md) | one `WARNING` per occurrence; the Event is admitted | — |
| A consumer has no inbound traffic, so a wedged process is indistinguishable from an idle one | [§7.1](07-deployment-view.md) | the Health plugin, which the host must actually probe | — |
| Mermaid marks all five C4 diagram types experimental, and every structural diagram of this document is one | [`diagrams.md`](diagrams.md) | shapes copied from committed diagrams rather than invented | — |
| `mkdocs-material` has been in maintenance mode since 9.7.0 | [research 04](../research/04-modern-python-library-engineering-2026.md) | nothing yet — no decision has chosen a documentation stack | #26 |
| No maintained asyncio circuit-breaker library exists, so the recipe that needs one can name none | [ADR-0057](../adr/0057-reliability-middlewares-and-error-reporting-stay-outside.md) | the recipe describes the shape instead of naming a package | #26 |
| Four fast-moving type checkers have bugs of their own, which is why a Quarantine exists at all | [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md) | the Quarantine, bounded and ratcheted | — |
| PEP 771 is still a Draft, so the default install cannot be expressed as a default extra | [ADR-0041](../adr/0041-default-dependencies-and-one-extra-per-optional-library.md) | four plain runtime dependencies instead | — |
| The one written component document already carries two open questions blocked on component documents not yet started | [`components/event.md`](components/event.md) | the writing order of [ADR-0035](../adr/0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md) | #61, #69 |

## 11.2 Technical debt

| Debt | What it costs | Retired by |
|---|---|---|
| 15 of the 89 payloads the webapp knows are typed for 0.5.0 | every other payload arrives as a `RawEvent` and a bot handles it untyped | #45 |
| Declarative multi-step conversation flows are not built | a scene is assembled by hand from Flow and Filter | #48 |
| Resync backfill ships only in part | the loss window a `Resynced(since)` Signal reports is not recovered for the caller | #55 |
| Cursor pagination is not implemented; `since`, `before` and `after` stay page methods | a caller walking a large history writes the loop itself | — |
| The generated model overlay is hand-maintained | one human pass over the overlay per Mattermost server release | — |
| The Quarantine is a budgeted concession to third-party typing gaps | suppressions exist, in one place, and the budget only ever shrinks | — |
| No performance target exists for 0.5.0 | no throughput, latency or memory number can be regressed against, and §10 measures the paths the framework owns instead | — |
