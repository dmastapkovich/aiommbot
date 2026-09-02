# Mattermost REST API typing: codegen feasibility and generator choice

Research date: 2026-09-02. Resolves issue #7. Primary sources only: mattermost/mattermost `api/v4/source/*.yaml`
at commit `f6f2719` (master, 2026-09-02), the server Go `model` package and webapp TypeScript client, generator
repos/docs, PyPI metadata. Items marked **[unverified]** could not be confirmed against a primary source during this
session. Spec metrics and generator results come from a throwaway script and actual generator runs in this session
(spec merged in `api/Makefile` order; the published artifact was also downloaded and run through the generators).

Question: can a typed Mattermost REST client layer for aiommbot 0.5.0 be *generated* rather than hand-written, and
with which tool?

**Short answer.** Yes for the REST surface — `datamodel-code-generator` (msgspec `Struct` output; mypy `--strict` clean, 4
pyright errors fixable in the override layer) for models plus a thin hand-written transport, fed by the published
`mattermost-openapi-v4.yaml` through an aiogram-butcher-style override layer. The spec is complete in *coverage*
(600 operations, all bot-relevant endpoints present) but weak in *precision*: 21/221 schemas declare `required`,
`Post.props`/`User.props`/dialog `submission` are bare `type: object`, `Post.type`/`Channel.type` have no enums, and
`Post.hashtag` is misspelled versus the wire. WebSocket events are prose-only in the spec but fully typed in the
webapp's `websocket_messages.ts`, which is the right source of truth for hand-written event models.

## 1. The spec: what `api/v4/source/*.yaml` actually contains

**How it is built and published.** `api/README.md`: "All the documentation is written in YAML and found in the
v4/source directories … To build the full YAML, run `make build` and it will be output to
`v4/html/static/mattermost-openapi-v4.yaml`. This will also check syntax using swagger-cli." The `Makefile` is a
plain `cat` of `introduction.yaml` + 57 path files + `definitions.yaml` (58 files, listed explicitly), then
`cd server && go run . $(V4_YAML)` to inject code samples, then `swagger-cli validate`; Playbooks paths/definitions are
fetched from GitHub at build time and merged. `v4/html/static/*mattermost-openapi-v4.yaml` is gitignored, so **no
built artifact is in the repo**. `.github/workflows/api.yml` runs `make build` on push/PR (README: "Deployment is handled automatically by our
Github Actions"; the deploy step itself was not located **[unverified]**). The Stoplight
Elements page at `developers.mattermost.com/api-documentation/` loads
`apiDescriptionUrl="https://developers.mattermost.com/mattermost-openapi-v4.yaml"` — this is the **only public
artifact** (HTTP 200, `application/yaml`, 1,189,700 bytes, 36,142 lines; `api.mattermost.com/static/…yaml` serves
the HTML docs page, not YAML). It is unversioned (`info.version: 4.0.0` is static) and tracks master: the path set equals master source
exactly plus 33 Playbooks paths (measured). GitHub releases (`v11.10.1`, `v11.7.10`, …) carry only SBOM/SLSA assets,
no spec. A per-server-version spec exists only implicitly: read `api/v4/source` at a release tag
(`…/posts.yaml?ref=v11.10.1` works). Releases are monthly (v11.8.0 2026-06-09, v11.9.0 2026-07-08, v11.10.0
2026-08-04); the spec changed in 40 commits between 2026-05-06 and 2026-08-31.

**Measured shape (master source, merged; published artifact in brackets):**

| Metric | Value |
|---|---|
| OpenAPI version | 3.0.0; `servers[0].url` = `{your-mattermost-url}`; all paths carry the `/api/v4` prefix |
| Paths / operations | 479 / 600 [512 / 644] — get 240, post 225, put 63, delete 57, patch 11, head 4; 3 deprecated; every op has `operationId` |
| Tags | 40 [45]; bot-core tags: users 79, channels 62, teams 38, posts 28, files 13, webhooks 11, commands 10, bots 9, emoji 9, threads 7, status 7, preferences 5, bookmarks 5, integration_actions 4, uploads 3, reactions 3 |
| Component schemas | 221 [240]; **21 have `required`** (9.5 %) |
| Properties in components | 1,682; 11 are bare `type: object` (no `properties`/`additionalProperties`); 0 lack a type; 8 `additionalProperties: true/{}` |
| Inline (path-level) properties | 723; 14 bare objects; 2 without type; 30 enums; 4 `nullable` |
| Enums | 22 in components + 30 inline (e.g. `PostPriority.priority`, `PostMetadata.embeds[].type`) |
| `nullable: true` | 14 in components + 4 inline |
| Composition | `allOf` 8, `oneOf` 0, `anyOf` 0, no discriminators |
| Formats | `int64` ×148 (all timestamps are epoch-ms integers), `uri` ×2, no `date-time` |
| Error responses | 10 shared `components.responses` (`BadRequest` 456 refs, `Unauthorized` 510, `Forbidden` 465, `NotFound` 193, `NotImplemented` 179, `InternalServerError` 113, `TooLarge` 11, `Conflict` 3, `TooManyRequests` 1, `BadGateway` 1), all `$ref: AppError` |
| Ops with no 2xx `content` | 63 (10.5 %) — e.g. `UpdateUserCustomStatus`, `UnsetUserCustomStatus` return 200 with no schema |
| Validity | `swagger-cli validate` is the upstream gate; `openapi-spec-validator` rejects both: published — "Path parameter 'user_id' … `/api/v4/users/{user_id}/reset_failed_attempts` was not resolved"; source — stray `body:` key at `bookmarks.yaml:64,143,269` |

**Bot-relevant coverage is complete.** Checked by path: posts (create, ephemeral, get/put/delete, patch, thread,
pin/unpin, reactions, ack, schedule, channel posts), channels (direct, group, members, bookmarks, by-name), files
(multipart `format: binary`, get/link/thumbnail, uploads), users (by usernames/ids/username, status, custom status,
image, typing, threads), bots, teams by name, `/actions/dialogs/open|submit|lookup|execute`, emoji, `/system/ping`,
`GET /websocket`. There is no `/users/me` path; `me` is a documented `user_id` value (`users.yaml:1072`). Important
request bodies are typed (`CreatePost` requires `channel_id`,`message`; `OpenInteractiveDialog` requires
`trigger_id`,`url`,`dialog`).

## 2. Generator candidates

All evaluated by actually running them on the published artifact (Python 3.13, mypy 1.19.1 `--strict`,
pyright 1.1.408).

| Tool | Status (Sep 2026) | Output / typing | Async+sync | Models | Override layer | Result on Mattermost spec |
|---|---|---|---|---|---|---|
| **openapi-python-client** 0.29.1 (2026-08-30; 1,985★, 116 open issues) | Active; 0.x, "breaking changes … several times a year"; 0.29.1 fixed an arbitrary-code-generation advisory | attrs classes with `UNSET`/`Unset` sentinel, `to_dict`/`from_dict`, `StrEnum`, httpx `Client`/`AuthenticatedClient` | Yes: `sync`, `sync_detailed`, `asyncio`, `asyncio_detailed` per operation per operation | attrs only (pydantic is a generator dependency, not output) | `--config`: `class_overrides`, `literal_enums`, `post_hooks`, content-type overrides; `--custom-template-path` ("beta … undocumented and unstable") | Exit 2: `PluginManifest` "duplicate models with name PluginManifestWebapp" → 3 schemas dropped; 1,365 files (661 models). mypy strict and pyright: 14 errors each, all `client.py` `__exit__(*args: object)` plus the dropped import. `Post.props` → `PostProps(additional_properties: dict[str, Any])`; every field `X \| Unset` because `Post` has no `required` |
| **datamodel-code-generator** 0.76.1 (2026-09-02; pushed 2026-09-02, 4,007★, 35 open) | Very active; used by Airflow, OpenTelemetry-python, E2B (README) | `--output-model-type` ∈ `pydantic_v2.BaseModel` (default), `pydantic_v2.dataclass`, `dataclasses.dataclass`, `typing.TypedDict`, **`msgspec.Struct`**; `--strict-nullable`, `--use-annotated`, `--use-union-operator`, `--use-standard-collections`, `--target-python-version` | Models only — no client | msgspec or pydantic v2 | `--custom-template-dir`, `--extra-template-data`, `--openapi-scopes`, `--use-operation-id-as-name`; pyproject config | msgspec run: 6,969 lines, 321 classes, 12 s; **mypy strict: 0 errors; pyright: 4 errors** (one `allOf` chain, `DataRetentionPolicyWithoutId` field-override-without-default). `Post.props: dict[str, Any] \| UnsetType = UNSET`, `metadata: PostMetadata \| UnsetType`, `type: str` (no enum). pydantic v2 run: 5,654 lines, 325 classes, `Post.id: str \| None = None` |
| **openapi-generator** 7.25.0 (2026-08-24; monthly releases) | `python` generator STABLE, Python 3.10+, pydantic v2 (this *is* the former `python-nextgen`; `python-nextgen.md` no longer exists); `python-pydantic-v1` still shipped STABLE | pydantic models + generated `ApiClient`; `library` = `urllib3` (default) / `asyncio` / `httpx`; `supportHttpxSync` adds `_sync` twins | One library per run; httpx+`supportHttpxSync` gives both | pydantic v2 (or v1) | Mustache templates, `.openapi-generator-ignore`; Java runtime required | Not run (Java dependency; heavy runtime with `ApiClient`/`Configuration`/`rest.py` that conflicts with the "small core, own transport" requirement) |
| **Speakeasy / Stainless / Fern** (commercial SDK-as-a-product) | Speakeasy docs: "Pydantic models and associated TypedDicts. Async and Sync methods for all endpoints", httpx, OpenAPI Overlays; site now leads with "AI Control Plane", SDK pricing **[unverified]**. Stainless: Python listed, "Add custom code" documented, Free = $0 / "Up to 5 generators" / "≤25 endpoints" / custom code "Limited files only"; openai-python shows the output (sync + `AsyncOpenAI`, pydantic, httpx). Fern: `fern-api/fern` Apache-2.0, pushed 2026-09-02, 3,770★, Python config `pydantic_config`, `use_typeddict_requests`; Hobby $0 (SDK limits **[unverified]**) | pydantic models + generated client, standalone SDK repo | httpx sync+async | pydantic v2 | overlays / custom-code files | All emit a standalone SDK repo, not a library-internal model layer; Stainless Free excludes a 600-op spec |
| **aiogram "butcher"** approach | In-repo generator inputs `.butcher/{enums,methods,schema,templates,types}`; each method/type has `entity.json` (parsed upstream) + hand YAML: `methods/sendMessage/default.yml` (defaults), `types/Message/replace.yml` (`date: parsed_type: DateTime`), `aliases.yml`; `aiogram/tg-codegen` last pushed 2022-12-08 (tool moved in-repo) | pydantic models + `TelegramMethod` classes | — | pydantic | Overrides are data, not templates; regen is idempotent | Not a tool but the **pattern** to copy: keep `entity` = spec snapshot, keep `replace/default` overrides in-repo, regenerate |
| **Hand-written msgspec + conformance tests** | msgspec 0.21.1 (2026-04-12); schemathesis 4.25.2 (2026-08-24, 3,577★); hypothesis-jsonschema 0.23.1 (2024-02-28, repo pushed 2025-12-05) | Whatever you write | n/a | msgspec | n/a | Maximum control, maximum drift risk: 221 schemas × monthly spec changes |

**Reading.** Two tools produce type-checker-clean model code today: `datamodel-code-generator` (msgspec or
pydantic) and, minus one `client.py` bug and one duplicate-name crash, `openapi-python-client`. The latter also
generates the transport (attrs + httpx, four functions per operation) — more than a bot framework wants to own — and
its `UNSET`-everywhere API follows directly from the spec's missing `required`. openapi-generator and the commercial
generators assume "the SDK is the product"; here the SDK is an internal adapter behind a protocol.

## 3. Existing Python Mattermost clients

| Package | Last release | Repo state | Typing model |
|---|---|---|---|
| `mattermostdriver` (Vaelor) | 7.3.2, 2022-01-21 (48 releases since 2017) | **Archived 2026-06-22** ("Archive Project" commit), 202★, 24 open issues; requests + websockets | Untyped hand-written endpoint classes: `def create_post(self, options): return self.client.post(self.endpoint, options=options)` |
| `mattermostautodriver` (embl-bio-it, fork of Vaelor) | 11.10.1, 2026-09-01; "follows releases of the official Mattermost server" (version = server version) | Active (pushed 2026-08-24, 26★, 2 open); maintainer changed 2026-06-01; httpx 0.28 + aiohttp | **Generated from the spec** by `bin/generate_endpoints_ast.py` (Python `ast` builder over the built `openapi.json`; tags → module, `operationId` → snake_case method, path params → args, `requestBody.properties` → kwargs). 69 endpoint modules. Parameters are typed (`channel_id: str`, `props: dict[str, Any] \| None`) but **no return types, no response models**; `Base` has an untyped `client`; bare `type: object` becomes `dict[str, Any]`. 11.8.1 removed dict-based `Driver` in favour of `TypedDriver` without a version signal ("this backwards-incompatible change is not signalled by the version number") |
| `python-mattermost-autodriver` | not a PyPI name (the PyPI package is `mattermostautodriver`; the GitHub repo is `python-mattermost-autodriver`) | — | — |
| `mattermost-api-python-driver` | not found on PyPI **[unverified which project the issue meant]**; the closest is PyPI `mattermost` 10.11.0 (2025-08-24, somenet, requests + websockets) | — | untyped |

Lesson: the one generated client proves the spec is *sufficient for method/parameter generation* (it tracks every
server release with a ~300-line AST script) and *insufficient for response typing* unless someone adds the missing
`required`/enum information — which nobody upstream has done.

## 4. WebSocket events: prose-only, so how do we keep hand-written models honest?

The spec documents WebSocket only as Markdown inside `introduction.yaml:181-345`: the frame shape
(`event`/`data`/`broadcast`/`seq`), an auth-challenge example, a flat list of **49 event names** (`:240-290`) and
3 API actions (`user_typing`, `get_statuses`, `get_statuses_by_ids`). No `data` schema per event.

Sources of truth, in order:

1. **Server Go `model` package** (`server/public/model/websocket_message.go`): `WebsocketEventType` has **108
   constants** (`typing`, `posted`, … `channel_join_request_updated`, lines 17-126) — more than double the prose
   list; wire struct `webSocketEventJSON{Event, Data map[string]any, Broadcast *WebsocketBroadcast, Sequence int64
   \`json:"seq"\`}` (`:235-240`); `WebsocketBroadcast` (`:149`) and `WebSocketResponse{status, seq_reply, data, error *AppError}` (`:446`). `Add(key string, value any)` (`:292`) is untyped, so payload shapes live in app
   code: `server/channels/app/post.go:788-792` does `postJSON, _ := post.ToJSON(); message.Add("post", postJSON)` —
   **`data.post` is a JSON string, not an object** (same for `post_edited` `:822-826`, `post_deleted` `:842-846`,
   ephemeral `:2941-2945`); `notification.go:691-712` adds `channel_type`, `channel_display_name`, `channel_name`,
   `sender_name`, `team_id`, `set_online`, and string `"true"` for `otherFile`/`image`.
2. **Webapp TypeScript client** (`webapp/platform/client/src/`): `websocket_events.ts` enumerates **103** events;
   `websocket_message.ts` defines `BaseWebSocketMessage<Event, T> = {event; data: T; broadcast; seq}`,
   `WebSocketBroadcast`, `JsonEncodedValue<T> = string`, and the discriminated union `WebSocketMessage`;
   **`websocket_messages.ts` types the `data` of 89 events**, e.g. `Posted = { channel_type: ChannelType;
   channel_display_name; channel_name; sender_name; team_id; set_online: boolean; otherFile?: boolean; image?:
   boolean; post: JsonEncodedValue<Post>; mentions?: JsonEncodedValue<string[]>; followers?: … }`, `Typing =
   {parent_id; user_id}`, `Hello = {server_version; connection_id; server_hostname?}`. Note the TS says
   `otherFile?: boolean` while Go sends `"true"` — a real discrepancy to test, not trust.
   `webapp/channels/src/actions/websocket_actions.ts` confirms double-encoding with `JSON.parse(msg.data.post)`,
   `.channel`, `.team`, `.request`, `.channelMember`.
Keeping hand-written event models honest:

- Pin the model files to a server tag and store the **pinned SHA + tag** next to `events.py`; a CI job diffs
  `websocket_events.ts`/`websocket_messages.ts`/`websocket_message.go` against the pin and fails on change.
- Generate a **parity test** from `websocket_events.ts`: every enum value must map to a `msgspec.Struct` (tagged
  union on `event`) or to an explicit `UnknownEvent` fallback; unknown events must never raise.
- Record **fixtures from a real server** (docker `mattermost/mattermost-team-edition`, one bot + one user) for the
  ~15 bot-critical events and decode them with `msgspec.json.decode(..., type=WebSocketMessage,
  strict=True)` plus `forbid_unknown_fields=True` in the test build only, so new server fields surface as failures
  rather than silent drops.
- Treat `JsonEncodedValue` fields as a first-class type: a `msgspec` `dec_hook`/wrapper that decodes the inner JSON
  string into `Post`/`Channel`/`Team` so handlers never see raw strings.

## 5. Recommendation: pipeline, remaining hand-written surface, and the ugliest spec holes

**Pipeline (all inputs versioned in-repo, regeneration idempotent):**

1. `spec/mattermost-openapi-v4.<server-tag>.yaml` — the published artifact, downloaded and pinned (or rebuilt from
   `api/v4/source` at a tag when a per-version spec is required; strip the 33 Playbooks paths).
2. `spec/overlays/*.yaml` — an **override layer in data, butcher-style** (or OpenAPI Overlay format, which
   Speakeasy also consumes): add `required`, enums (`Post.type` ← `post.go` 36 `PostType*` consts; `Channel.type`
   ← 7 `ChannelType*`), rename `hashtag`→`hashtags`, add missing `Post` fields, type `PostMetadata.images` as
   `additionalProperties: PostImage`, fix `bookmarks.yaml` `body:` keys, drop `PluginManifest` if using
   openapi-python-client. Applied by a ~100-line script; the diff of overlay vs upstream is the maintenance surface.
3. `datamodel-codegen --output-model-type msgspec.Struct --strict-nullable --use-annotated --use-union-operator
   --use-standard-collections --target-python-version 3.13` → `aiommbot/mattermost/_generated/models.py`
   (proven: mypy strict 0, pyright 4 fixable via overlay). Optionally `--openapi-scopes paths` for request bodies.
4. Operation table: a second small generator (or `openapi-python-client` with `--meta none` restricted to
   `models`+`api` templates) emitting `Final` operation descriptors — method, path template, param names, body
   model, response model — consumed by **one hand-written transport** (`Protocol`-backed, sync/async without
   duplication per CLAUDE.md), not 2,400 generated functions.
5. Conformance tests: (a) generated models round-trip against the *overlayed* spec with `hypothesis-jsonschema`
   (last release 2024-02, still functional) or schemathesis' `schema.parametrize()`; (b) recorded fixtures from a real
   server decoded with `forbid_unknown_fields`; (c) WebSocket parity test against `websocket_events.ts`.

**Hand-written surface that remains (estimate):** transport + auth + retries (~400 lines), overlay script
(~100), WebSocket frame structs and ~15-20 event `data` structs from `websocket_messages.ts` (~300-400),
`JsonEncodedValue` decode hook (~30), dialog/attachment/`props` payload models the spec leaves as `type: object`
(~200-300), error taxonomy over `AppError` (~50). Roughly 1,200-1,500 hand-written lines against ~7,000 generated;
the overlay is what needs a human on every monthly server release.

**The ugliest spec holes (master `api/v4/source`, commit `f6f2719`):**

1. `definitions.yaml:443-486` `Post` has no `required` (every generated field is `X | Unset`/`None`, including
   `id`, `channel_id`, `create_at`) and misses `is_pinned`, `reply_count`, `last_reply_at`, `participants`,
   `is_following`, `remote_id`, `message_source` that `post.go` serialises.
2. `definitions.yaml:475-476` `Post.props: type: object` (bare; Go `map[string]any` with undocumented well-known
   keys); `:105-106` `User.props: type: object` although Go `StringMap` is `map[string]string`.
3. `definitions.yaml:477` `hashtag` — the wire field is `hashtags` (`post.go` `Hashtags string \`json:"hashtags"\``).
4. `definitions.yaml:473-474` `Post.type: string` without enum; `post.go` defines 36 `PostType*` constants.
5. `definitions.yaml:207-208` `Channel.type: string` without enum; `channel.go:28-34` has `O P D G S BO BP`.
6. `definitions.yaml:882-883` `PostMetadata.embeds[].data: type: object`; `:903` `images: type: object` — Go has
   `map[string]*PostImage`.
7. `definitions.yaml:2762-2771` `AppError` lacks `required` and `detailed_error`/`props` (present in
   `utils.go` `AppError`); all 10 shared error responses depend on it.
8. `posts.yaml:58-63` `CreatePost` body `props`/`metadata` bare objects; `posts.yaml:114-115` `CreatePostEphemeral`
   `post: type: object` instead of `$ref: Post`.
9. `actions.yaml:52-66` `OpenInteractiveDialog` `dialog.elements[]: type: object` ("see
    docs.mattermost.com/developer/interactive-dialogs.html"); `actions.yaml:122-123` `submission: type: object`.
10. `introduction.yaml:240-290` lists 49 WebSocket events vs 108 Go constants / 103 TS enum members; `data` never
    schematised; double-encoded `post` undocumented.

## Sources

- Spec source & build: https://github.com/mattermost/mattermost/tree/master/api ·
  https://github.com/mattermost/mattermost/blob/master/api/README.md ·
  https://github.com/mattermost/mattermost/blob/master/api/Makefile ·
  https://github.com/mattermost/mattermost/blob/master/api/.gitignore ·
  https://github.com/mattermost/mattermost/blob/master/.github/workflows/api.yml ·
  https://github.com/mattermost/mattermost/blob/master/api/v4/source/introduction.yaml ·
  https://github.com/mattermost/mattermost/blob/master/api/v4/source/definitions.yaml ·
  https://github.com/mattermost/mattermost/blob/master/api/v4/source/posts.yaml ·
  https://github.com/mattermost/mattermost/blob/master/api/v4/source/actions.yaml ·
  https://github.com/mattermost/mattermost/blob/master/api/v4/source/bookmarks.yaml
- Published artifact & releases: https://developers.mattermost.com/api-documentation/ ·
  https://developers.mattermost.com/mattermost-openapi-v4.yaml ·
  https://api.github.com/repos/mattermost/mattermost/releases ·
  https://api.github.com/repos/mattermost/mattermost/commits?path=api/v4/source
- Server model / app code: https://github.com/mattermost/mattermost/blob/master/server/public/model/websocket_message.go ·
  https://github.com/mattermost/mattermost/blob/master/server/public/model/websocket_client.go ·
  https://github.com/mattermost/mattermost/blob/master/server/public/model/post.go ·
  https://github.com/mattermost/mattermost/blob/master/server/public/model/post_metadata.go ·
  https://github.com/mattermost/mattermost/blob/master/server/public/model/user.go ·
  https://github.com/mattermost/mattermost/blob/master/server/public/model/channel.go ·
  https://github.com/mattermost/mattermost/blob/master/server/public/model/utils.go ·
  https://github.com/mattermost/mattermost/blob/master/server/channels/app/post.go ·
  https://github.com/mattermost/mattermost/blob/master/server/channels/app/notification.go
- Webapp TypeScript: https://github.com/mattermost/mattermost/blob/master/webapp/platform/client/src/websocket_events.ts ·
  https://github.com/mattermost/mattermost/blob/master/webapp/platform/client/src/websocket_message.ts ·
  https://github.com/mattermost/mattermost/blob/master/webapp/platform/client/src/websocket_messages.ts ·
  https://github.com/mattermost/mattermost/blob/master/webapp/channels/src/actions/websocket_actions.ts
- Generators: https://github.com/openapi-generators/openapi-python-client (README, CHANGELOG 0.29.1) ·
  https://pypi.org/project/openapi-python-client/ · https://github.com/koxudaxi/datamodel-code-generator ·
  https://pypi.org/project/datamodel-code-generator/ ·
  https://github.com/OpenAPITools/openapi-generator/blob/master/docs/generators/python.md ·
  https://github.com/OpenAPITools/openapi-generator/blob/master/docs/generators/python-pydantic-v1.md ·
  https://github.com/OpenAPITools/openapi-generator/releases ·
  https://www.speakeasy.com/docs/languages/python/methodology-python · https://www.speakeasy.com/openapi/overlays ·
  https://www.stainless.com/docs/sdks/configure/custom-code/ · https://www.stainless.com/pricing ·
  https://github.com/openai/openai-python/blob/main/README.md ·
  https://buildwithfern.com/learn/sdks/generators/python/configuration · https://buildwithfern.com/pricing ·
  https://github.com/fern-api/fern
- aiogram butcher: https://github.com/aiogram/aiogram/tree/dev-3.x/.butcher ·
  https://github.com/aiogram/aiogram/blob/dev-3.x/.butcher/methods/sendMessage/default.yml ·
  https://github.com/aiogram/aiogram/blob/dev-3.x/.butcher/types/Message/replace.yml ·
  https://github.com/aiogram/tg-codegen
- Existing clients: https://github.com/Vaelor/python-mattermost-driver · https://pypi.org/project/mattermostdriver/ ·
  https://github.com/embl-bio-it/python-mattermost-autodriver (README.rst, `bin/generate_endpoints_ast.py`,
  `scripts/generate_endpoints.sh`, `src/mattermostautodriver/endpoints/posts.py`) ·
  https://pypi.org/project/mattermostautodriver/ · https://pypi.org/project/mattermost/
- Conformance tooling: https://pypi.org/project/msgspec/ · https://pypi.org/project/schemathesis/ ·
  https://github.com/schemathesis/schemathesis · https://pypi.org/project/hypothesis-jsonschema/ ·
  https://github.com/Zac-HD/hypothesis-jsonschema · https://pypi.org/project/openapi-spec-validator/
