---
status: accepted
date: 2026-09-03
ticket: "#21"
---

# Mattermost models are generated from a pinned, overlaid OpenAPI spec into standard-library dataclasses; serialisation goes through a Core-owned `Codec` Protocol with msgspec as the shipped implementation

The Mattermost OpenAPI spec is complete in coverage — 600 operations, every endpoint a bot needs —
but weak in precision: 21 of 221 schemas declare `required`, `Post.props` and dialog `submission`
are bare objects, `Post.type` and `Channel.type` have no enums, `hashtag` is misspelled against the
wire, and the spec is published unversioned from `master` while the server releases monthly
(`docs/research/05`). 0.4.8 hand-wrote 71 pydantic models and drifted. msgspec, the serialiser the
earlier research recommended for the hot path, entered maintenance mode in February 2026 and has
had no release since April (`docs/research/05`, fact pack in the #21 resolution). We decided:

- **Models are generated, never hand-maintained.** Inputs are versioned in the repository: the spec
  rebuilt from `api/v4/source` at the tag of the **latest Mattermost ESR** current at release time,
  and an **overlay in OpenAPI Overlay Specification 1.0** format (`spec/overlays/*.yaml`) that adds
  `required` from the Go structs, enums, renames, missing fields and our extensions
  (`x-aiommbot-paginated`, `x-aiommbot-idempotency-key`, `x-aiommbot-response-required`). A
  ~100-line script applies the overlay; `datamodel-code-generator` emits the models; the output is
  **committed**, regenerated idempotently, and checked in CI and pre-commit (`--check`), so a
  hand edit of a generated file fails the build. The overlay is the only surface a human touches
  on a server release.
- **The model type is the standard library.** Generated models are
  `@dataclass(frozen=True, slots=True, kw_only=True)`: no third-party base class in any public
  type, understood by all four checkers without plugins (ADR-0009), and immune to the fate of any
  serialisation library. Hand-written models for what the spec leaves as `object` — `Post.props`
  well-known keys, attachments, dialog elements — use the same shape.
- **Optionality has two rules.** Response models that handlers read (`Post`, `User`, `Channel`,
  `FileInfo`, `Team`, `AppError`, …) get `required` from the overlay and `T | None` elsewhere;
  `post.id` is a `str`, never `str | Unset`. Request models use `UNSET` with omit-on-encode so a
  `PATCH` can tell "leave untouched" from "set to null" — the `exclude_none` shortcut of 0.4.8 could
  not.
- **Serialisation is a Core-owned Protocol.** `Codec` — `encode(obj) -> bytes`,
  `decode(data, type) -> T`, `convert(obj, type) -> T`, strict types (no `str`→`int` coercion),
  unknown fields ignored — lives in the Core so generic plugins (State's `Flow` data, dedup keys)
  can serialise without knowing the implementation. The Adapter supplies **`MsgspecCodec` as the
  sole shipped implementation** and registers it as an App-scoped `Provider[Codec]`; msgspec is the
  Adapter's dependency, not the Core's (ADR-0002). msgspec decodes dataclasses natively, honours
  `UNSET` on them, and its `dec_hook` unpacks Mattermost's JSON-in-JSON fields (`data.post`) into
  the generated `Post`. Replacing msgspec with pydantic's `TypeAdapter` is one module, not a major
  version.
- **Server version policy.** Supported: the pinned ESR and newer. Forward compatibility is unknown
  fields ignored in production and `forbid_unknown_fields` in the test build. A nightly job diffs
  `api/v4/source`, `websocket_events.ts` and `websocket_messages.ts` against `master` and opens an
  issue on drift, so keeping up with the server is a mechanism, not a memory.
- **Conformance without infrastructure in CI.** Every PR: generated models round-trip against the
  overlaid spec (`hypothesis-jsonschema`) and decode committed fixtures with unknown fields
  forbidden. Fixtures are recorded by a script against a `mattermost-team-edition` container on the
  pinned ESR and committed; no Docker in the PR pipeline.
- WebSocket payloads (ADR-0012) are dataclasses decoded by the same `Codec` and reuse the generated
  REST models; the full catalogue is #45.

## Considered options

- *`msgspec.Struct` as the model type* — rejected: fastest and most ergonomic, but every public type
  would inherit from a library in declared maintenance mode, without 3.15 wheels and with a release
  pipeline broken since August 2026.
- *pydantic v2 everywhere* — rejected: healthiest ecosystem and 0.4.8's choice, but `BaseModel` in
  every public type, a heavy import, a checker plugin, and a heavy dependency for the generic State
  plugin.
- *Hand-written models for the bot subset* — rejected: 40 spec commits in four months make a
  hand-written layer the drift source; the overlay is the smaller human surface.
- *`UNSET` everywhere, as the spec implies* — rejected: `str | Unset` on `post.id` in every handler
  contradicts ADR-0006.
- *`None` everywhere* — rejected: `PATCH` cannot express "leave untouched".
- *Bespoke override YAML or Python post-hooks instead of OpenAPI Overlay* — rejected: a standard
  format is read by other tools and diffs against upstream as data.
- *Several spec pins per server version* — rejected: a version swamp without demand.
- *A Mattermost container in every PR* — rejected: minutes and flakes per PR for a check that
  recorded fixtures give deterministically.
