# 2. Constraints

_Status: reviewed (#37)._

What removes freedom from a decision taken later. A constraint earns a row here by having shaped an
architectural decision and by helping a reader understand the result; where it did, the row says
which freedom it takes away and links the decision it shaped rather than restating it. Origin is
not the filter — a rule this project wrote for itself binds the next decision exactly as a platform
fact does.

## 2.1 Platform constraints

Given by Mattermost. These are the facts the design could not choose, and they shape more of it
than anything else in this section; the interfaces they travel over are
[§3.2](03-context-and-scope.md#32-technical-context)'s.

| Constraint | What freedom it removes | Shaped |
|---|---|---|
| Every WebSocket connection of a bot account receives every event ([`docs/research/01`](../research/01-mattermost-websocket-protocol.md)) | Identical replicas cannot share the stream, so scaling out cannot mean running the consumer twice | [ADR-0005](../adr/0005-one-ingress-many-workers.md), [ADR-0023](../adr/0023-websocket-gateway-resilience.md) |
| A revoked session keeps its socket open and produces no event ([`docs/research/15`](../research/15-mattermost-session-revocation.md)) | Loss of authorisation cannot be detected by an error, so silence has to be interpreted and probed | [ADR-0023](../adr/0023-websocket-gateway-resilience.md) |
| An interactive callback arrives over HTTP and never over the event stream ([`docs/research/11`](../research/11-webhook-ingress-patterns.md)) | A bot that answers buttons needs an inbound HTTP surface, so the framework cannot be socket-only | [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md) |
| A callback carries no server signature, is delivered once with no retry, and shares a 30 s timeout and a 1 MiB reply cap with `trigger_id` ([`docs/research/16`](../research/16-webhook-callback-standards.md)) | Authenticity has to be self-issued rather than verified, and the reply deadline is the platform's, not ours | [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md) |
| The published OpenAPI specification declares `required` on 21 of its 221 schemas ([`docs/research/05`](../research/05-mattermost-rest-typing-codegen.md)) | Models cannot be generated from the specification as published, so an overlay is part of the build rather than an option | [ADR-0025](../adr/0025-generated-dataclass-models-with-a-codec-protocol.md) |

## 2.2 Technical constraints

| Constraint | What freedom it removes | Decided in |
|---|---|---|
| Python `>=3.12`, supported until each version's upstream EOL | No language or typing feature newer than 3.12 may be used unguarded; `typing_extensions` is the only backport route | [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md) |
| The Core's runtime dependencies are the standard library and `typing_extensions` | A Core design may not reach for a library; an answer shaped like one becomes a Plugin, an Extra or a documented recipe | [ADR-0002](../adr/0002-core-scope-two-condition-test.md), [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md) |
| Four type checkers run beyond their strict presets, all blocking | A construct any one of the four rejects cannot ship, whatever the other three say | [ADR-0009](../adr/0009-four-strict-type-checkers.md) |
| No suppression exists in the package outside a Quarantine module | A typing problem is solved or quarantined; it is never silenced where it appears | [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md) |
| One toolchain for style, complexity, architecture and dependencies, with `just` as its single entry point | A check that cannot be expressed in that toolchain is not a check this project enforces | [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md) |
| One distribution, enabled by explicit composition, with no compatibility promise toward any earlier release | Capability cannot be gated by packaging, so every optional capability has to be a composition decision | [ADR-0001](../adr/0001-fresh-start-as-a-public-package.md), [ADR-0002](../adr/0002-core-scope-two-condition-test.md) |

## 2.3 Organisational constraints

| Constraint | What freedom it removes | Decided in |
|---|---|---|
| Public from the first commit, MIT, English in every committed artefact, semantic versioning from 0.5.0 | Nothing internal, unpublishable or licence-incompatible may enter the repository or the design | [ADR-0001](../adr/0001-fresh-start-as-a-public-package.md) |
| A hard-to-reverse decision is recorded before the code that implements it | A decision cannot be made inside an implementation diff; it is made, recorded and only then built | [`documentation-style.md`](../documentation-style.md) |

## 2.4 Conventions

| Convention | What freedom it removes | Fixed by |
|---|---|---|
| [`CONTEXT.md`](../../CONTEXT.md) is the vocabulary, and it wins over every other document, titles included | A document may not introduce a synonym for a term that already exists, however natural the synonym reads | [`documentation-style.md`](../documentation-style.md) |
| A decision lives in exactly one place — its ADR — and every other document links it with a gist | A section cannot argue a decision; it can only state the design the decision produced | [`documentation-style.md`](../documentation-style.md) §6 |
| The architecture document follows arc42 and its diagrams are C4 in Mermaid | A view cannot be invented where arc42 has a section for it, and a diagram cannot use a notation the rulebook has not measured | [`diagrams.md`](diagrams.md) |
| Every rule carries a stable `ST-<AREA>-NN` identifier, an enforcement tier and the place it is checked | A preference cannot become a rule without naming what enforces it | [ADR-0033](../adr/0033-identified-tiered-rules-with-a-derived-review-checklist.md) |
| A pattern is named as on refactoring.guru, with the problem it solves here and the alternative that lost | A structure cannot be justified by familiarity; a component document has to name what it rejected | [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md) |
| A public name is documented at its package path, re-exported explicitly and listed on a reference page a guard test reads both ways | A name cannot become public by accident, and the public surface cannot drift from its list | [ADR-0042](../adr/0042-a-public-name-is-documented-at-its-package-path.md), [ADR-0043](../adr/0043-explicit-re-export-with-a-reference-page-as-the-public-list.md) |
