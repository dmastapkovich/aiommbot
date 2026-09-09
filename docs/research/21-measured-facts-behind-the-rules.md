# Measured facts behind the rules: the strictly typed peer, fact by fact (Sep 2026)

Research date: 2026-09-09, for ticket #36. One question: what does the strictly typed peer that the
engineering rulebook and four ADRs cite as evidence actually contain, measured rather than recalled?
The peer is django-modern-rest (`wemake-services/django-modern-rest`), a Django REST layer that
keeps its rules in an agent-facing skill file, its architecture in `.importlinter` and its
public-API definition in the CHANGELOG preamble. Every claim below has a source; every number
states the method that produced it. Where a citing document overstates, this note says so and
marks the claim **[not confirmed: …]**; anything not checked against the source is
**[unverified]**.

The citing documents are the five callouts in
[`engineering-style.md`](../design/engineering-style.md) (`ST-TYP-09`, `ST-TYP-16`, `ST-ERR-09`,
`ST-DOC-02`, `ST-TST-01`) and [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md),
[ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md),
[ADR-0018](../adr/0018-core-owned-type-keyed-dependency-injection.md),
[ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md),
[ADR-0033](../adr/0033-identified-tiered-rules-with-a-derived-review-checklist.md) and
[ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md).

## Measurement basis

- **Commit**: `79d03b5f4492611327af7f20cb8eb6c64e6e6807`, committed 2026-09-08T06:10:56Z, the
  head of the default branch on the research date. `pyproject.toml` declares `version = "0.14.0"`;
  the latest release tag is `0.14.0` (2026-08-14); `CHANGELOG.md` opens a `0.15.0 WIP` section, so
  the tree measured is 0.14.0 plus unreleased work.
- **Method**: the commit's tarball was fetched through the GitHub API and searched with
  `grep -rn … --include='*.py'`. "In the package" means the installed package directory `dmr/`
  (194 Python files); tests (243 files under `tests/`), `docs/`, `benchmarks/`,
  `django_test_app/` and `typesafety/` are excluded unless a row says otherwise. Line counts are
  `wc -l`.
- **Toolchain, for context**: `requires-python = ">=3.11"`; the CI matrix runs 3.11, 3.12, 3.13,
  3.14 and 3.14t (`.github/workflows/test.yml:23-26`). `just type-check` runs four checkers —
  mypy (`strict = true`), pyright (`strict` on `dmr/**`), pyrefly (`--remove-unused-ignores`) and
  ty (`--error=all`) (`justfile:43-47`). `just lint` runs ruff (`preview = true`, 42 rule
  families selected, `target-version = "py311"`), flake8 with wemake-python-styleguide, slotscheck
  and `import-linter lint` (`justfile:30-35`). pytest runs with `--cov-branch`,
  `--cov-fail-under=100` over `dmr`, `django_test_app` **and `tests`**,
  `filterwarnings = ["error"]`, `xfail_strict = true` and `pytest-timeout` as a dev dependency
  (`pyproject.toml:516-560`).

## Summary

| Fact as cited | Cited by | Measured | Status |
|---|---|---|---|
| 62 direct `typing_extensions` import sites | `ST-TYP-09` | 62 statements in 62 files | confirmed |
| ten names, only `TypedDict` protected | `ST-TYP-09` | 10 names; one `banned-api` entry | confirmed |
| 100 `type: ignore`, almost all `[attr-defined]`, from stashing | `ST-TYP-16` | 101; 26 `[attr-defined]`; 16 stashes | **[not confirmed: "almost all"]** |
| flat hierarchy, no root, `status_code`, two hand-synced tuples | `ST-ERR-09` | 11 `@final` `Exception` subclasses; 8 with `status_code`; two `NOTE` sites | confirmed, shape stated in §3 |
| executable docstrings, `.rst` and README | `ST-DOC-02` | three doctest options; 99 `>>>` in 11 `.rst`, 13 in README | confirmed |
| two `unittest.mock` files vs ~18 conforming doubles | `ST-TST-01` | 2 files; 40 doubles in 23 files | **[not confirmed: "eighteen"]** |
| Protocols for foreign shapes, abstract grids for own families | [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md) | 12 Protocols (3 mixin self-types); 71 `@abstractmethod`; no `abc.ABC` | confirmed, one nuance |
| ~16 root exports, unstable internal API, four criteria, no `__all__` | [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md) | exactly 16; `internal-api.rst`; criteria 1–4; 0 `__all__` | confirmed |
| `Annotated`-marker request components | [ADR-0018](../adr/0018-core-owned-type-keyed-dependency-injection.md) | six `Annotated` aliases | confirmed |
| flake8-async, almost no carve-outs; no loop opinion | [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md) | one ignore (`ASYNC119`), no `noqa`; no uvloop mention | confirmed |
| ~1,570-line rules document; no prose styleguide, architecture doc or ADRs; import-linter contracts | [ADR-0033](../adr/0033-identified-tiered-rules-with-a-derived-review-checklist.md) | 1,570 lines; 31 rules, 26 pairs, 21 Limitations, 25 links; 9 contracts | confirmed; template not uniform |
| auth chain `Self` / `None` / raise; runner raises; one value-returning counterpart | [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md) | docstrings and loop match; `ThrottlingReport` | confirmed; **[not confirmed: "exactly one"]** |

## 1. `typing_extensions` import sites (`ST-TYP-09`)

- **62 import statements in 62 files** of `dmr/`: `grep -rn "from typing_extensions import"
  dmr --include='*.py' | wc -l` gives 62, and `grep -rl` gives 62 files — one statement per file.
  The whole repository has 180 such lines in 180 files (tests, the test app and `typesafety/`
  bring 118).
- **Ten distinct names**, counted by splitting every statement on commas and reading the one
  multi-line block in `dmr/types.py:15-20`: `override` (43 files), `TypedDict` (11), `Sentinel`
  (10), `TypeVar` (6), `ParamSpec` (2), `deprecated` (2), `get_type_hints` (2), `Protocol` (1),
  `Format` (1), `get_original_bases` (1).
- **One name is mechanically protected.** The only `banned-api` entry is
  `"typing.TypedDict".msg = "Use typing_extensions.TypedDict instead."`
  (`pyproject.toml:292-293`). Nothing in the ruff, flake8 or import-linter configuration names
  the other nine. On the 3.11 floor, `typing` has no `override` (3.12), `deprecated` (3.13, in
  `warnings`), `get_original_bases` (3.12, in `types`) or `Format` (3.14, in `annotationlib`), and
  `Sentinel` has no standard-library spelling at all; `TypeVar` with `default=` is 3.13. So a
  `from typing import override` written by a contributor is caught by nothing until the 3.11 job of
  the test matrix fails to import the module — a test-time signal, not a lint-time one. That is
  the spread the rulebook describes: one decision in 62 places, guarded once.

## 2. `type: ignore` and stashing on foreign objects (`ST-TYP-16`)

- **101 `type: ignore` comments in `dmr/`** (`grep -rn "type: ignore" dmr --include='*.py' |
  wc -l`), none bare; 318 in the whole repository. Alongside them, 72 `pyright: ignore` and 254
  `noqa` comments in `dmr/`.
- **By error code** (`grep -rho "type: ignore\[[a-z, -]*\]" … | sort | uniq -c`): `attr-defined`
  26, `no-any-return` 18 (plus 3 combined with `misc`), `arg-type` 10, `return-value` 6, `misc` 6,
  `assignment` 6, `operator` 3, and 19 codes with one or two occurrences each.
- **The stash attributes are named `__dmr_*__`**, not `__x_*__`: 16 distinct names, 57
  occurrences, 11 of them `getattr` reads that need no suppression because `getattr` returns
  `Any` — `__dmr_auth__` (6), `__dmr_renderer__` (5), `__dmr_payload__` (5),
  `__dmr_nonstreaming_renderer__` (5), `__dmr_force_list__` (5), `__dmr_parser__` (4),
  `__dmr_jwt__` (4), `__dmr_endpoint__` (4), `__dmr_token__` (3), `__dmr_split_commas__` (3),
  `__dmr_parsed_as_post__` (3), `__dmr_allauth_session__` (3), `__dmr_external_openapi__` (2),
  `__dmr_converter_schema__` (2), `__dmr_cast_null__` (2), `__dmr_throttling__` (1).
- **16 of the 26 `[attr-defined]` suppressions are such stashes** on a Django `HttpRequest`, a
  view function or a URL callback (`dmr/endpoint.py:368, 408, 465, 515, 1154`,
  `dmr/negotiation.py:88, 198, 214`, `dmr/security/jwt/auth/base.py:369`,
  `dmr/security/token/request.py:99`, `dmr/security/allauth/auth.py:263`,
  `dmr/internal/django.py:180`, `dmr/internal/routing.py:32`, `dmr/openapi/collector.py:87`,
  `dmr/test/auth.py:93`). The other ten touch Django's private attributes (`request._post`,
  `_files`, `_mark_post_parse_error`, `response._json`) or untyped third-party attributes.
- **Verdict on the callout.** Stashing framework state on a foreign object is the single largest
  cause of suppression in the package (16 of 101, 16 %), and `[attr-defined]` is the largest single
  code (26 of 101). "Almost all `[attr-defined]`" is **[not confirmed: 26 %]**; the callout should
  read "the largest single source", not "almost all".

## 3. The exception hierarchy (`ST-ERR-09`)

- **`dmr/exceptions.py` holds 11 classes; all 11 are `@final` and all 11 subclass `Exception`
  directly.** There is no shared root. Eight carry `status_code` — seven as a class attribute
  (`DataRenderingError`, `InternalServerError`, `RequestSerializationError`, `ResponseSchemaError`,
  `NotAcceptableError`, `NotAuthenticatedError`, `TooManyRequestsError`) and `ValidationError` as an
  instance attribute set in `__init__`. The three without one (`UnsolvableAnnotationsError`,
  `EndpointMetadataError`, `DataParsingError`) are programmer-facing. Six more exception classes
  live elsewhere (`APIError`, `RedirectTo`, `ProblemDetailsError`, `JWTokenError`,
  `StreamingCloseError`, `UnsafeCacheBackendWarning`), again without a common root.
- **The classification is tuple membership, and the tuple lists exactly the eight classes with
  `status_code`.** `global_error_handler` does `if isinstance(exc, _default_handled_excs): return
  controller.to_error(…, status_code=exc.status_code, …)` and otherwise re-raises
  (`dmr/errors.py:318-326`); `dmr/problem_details.py:198` reads `getattr(error, 'status_code',
  None)`. Nothing asks "is this user-visible?" of the exception itself.
- **Two places are kept in step by hand.** `_default_handled_excs: Final = (…)` with eight members
  carries `# NOTE: keep this tuple in sync with format_error()` (`dmr/errors.py:233-243`);
  `format_error()` carries `# NOTE: keep this function in sync with _default_handled_excs`
  (`dmr/errors.py:112`) and spreads the same eight classes over three `isinstance` checks — one
  class alone, a five-member tuple, a two-member tuple (`dmr/errors.py:115-140`). The rulebook's
  "two hand-maintained tuples" is one tuple plus one function holding two; the duty is as stated.

## 4. Executable documentation (`ST-DOC-02`)

- `[tool.pytest.ini_options].addopts` includes `--doctest-modules`, `--doctest-glob=*.rst` and
  `--doctest-glob=README.md`; `pythonpath = ["django_test_app", "docs"]` so that `.rst` doctests
  import `examples.*` "the same way our sphinx extension does" (`pyproject.toml:510-522`).
- Volume: 99 `>>>` lines across 11 `.rst` files under `docs/`, 13 in `README.md`, and doctests in
  package docstrings (for example `global_error_handler`, `dmr/errors.py:279-309`).
- Coverage is measured over the tests as well as the package (`--cov=tests`), with
  `--cov-branch --cov-fail-under=100` (`pyproject.toml:526-533`).

## 5. Mocks versus conforming doubles (`ST-TST-01`)

- **Two files in `tests/` import `unittest.mock`** (`grep -rln "unittest.mock" tests`):
  - `tests/test_unit/test_security/test_token/test_token_admin.py:5` uses `Mock()` to replace
    Django's `ModelAdmin.message_user` on a `TokenAdmin` instance — a Django seam;
  - `tests/test_unit/test_testing/test_request_factory.py:3, 32` uses
    `patch('dmr.internal.json._json_dumps', _compact_json_dumps)` to run the standard-library
    fallback as if the `msgspec` extra were absent — the optional-dependency seam, reached by
    patching the package's own module attribute.
- `monkeypatch` appears in four test files: two `setenv('DMR_USE_COMPILED', …)`, one `setattr` on
  `dmr.internal.jwt.json_dumps_bytes` and `json_loads` (the same `msgspec` seam), one `setattr` on
  `dmr_export_schema.import_string`, and one `setattr` on
  `ResponseValidator._should_validate_responses` — the last is a patch of the package's own class.
- **Conforming doubles: 40 classes in 23 test files** subclass a package base to stand in for one
  behaviour. Method: `^class …(` lines in `tests/` whose base is a package auth, parser, renderer,
  serializer or throttle class. By base: `HttpBasicSyncAuth` 6, `Serializer` 5, `SyncAuth` 4,
  `PydanticSerializer` 4, `Parser` 4, `HttpBasicAsyncAuth` 4, `Renderer` 3, `SupportsFileParsing`
  2, `HeaderJWTSyncAuth` 2, and one each of `CookieJWTSyncAuth`, `AsyncAuth`, the two JWT
  blocklist mixins, `BaseThrottleSyncBackend`, `BaseThrottleAsyncBackend`, `BaseThrottleAlgorithm`.
  The auth family alone is 20. The rulebook's "roughly eighteen" is **[not confirmed: 40
  measured]**; the ratio the rule rests on — a handful of mocks against dozens of real
  implementations — holds.
- The package also ships its doubles: `dmr/test/` provides `DMRClient`, `DMRAsyncClient`,
  `DMRRequestFactory`, `DMRAsyncRequestFactory`, a test auth and a throttling helper
  (`dmr/test/client.py:123-183`, `dmr/test/auth.py`, `dmr/test/throttling.py`).

## 6. Protocols for foreign shapes, abstract grids for own families

Cited by [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

- **Twelve `Protocol` classes in the package** — 11 at module level, one nested under
  `TYPE_CHECKING`. What each describes:
  - a foreign library's shape: `JsonModule` (any `dumps`/`loads` module, `dmr/internal/json.py:12`),
    `_FieldLike` (pydantic's `Field` or the fallback, `dmr/internal/dataclass_aliases.py:5`),
    `_ValidateSpecProto` (an `openapi_spec_validator` function, `dmr/openapi/openapi.py:19`);
  - a user-supplied callable: `FormatError` (`dmr/internal/types.py:7`), `SchemaCallback`
    (`dmr/openapi/core/registry.py:9`), `ModifySyncCallable`, `ModifyAsyncCallable`,
    `ModifyAnyCallable` (`dmr/internal/endpoint.py:19-81`);
  - a user-defined object: `SSE` — "we encourage them to create their own event ADT and models"
    (`dmr/streaming/sse/metadata.py:7-13`);
  - the package's own classes, once: `_JWTAuth`, `_JWTSyncAuth`, `_JWTAsyncAuth` type the `self` of
    a mixin that is "always mixed in as the first base"
    (`dmr/security/jwt/blocklist/auth.py:15-45`). This is the one exception to "foreign only",
    and it exists to type a mixin, not to define an extension point.
- **Own implementation families are abstract-method grids on plain classes.** 71 `@abstractmethod`
  decorators in 20 files; zero classes inherit `abc.ABC` or set `ABCMeta`, so the abstract methods
  are enforced by the checkers, not at instantiation. The grids: `_BaseAuth` → `SyncAuth` /
  `AsyncAuth` with a `SyncOrAsyncAuth` resolver (`dmr/security/base.py:108-229`);
  `_BaseThrottle[BackendT]` → `SyncThrottle` / `AsyncThrottle` (`dmr/throttling/base.py:60-381`);
  `_BaseThrottleBackend` → `BaseThrottleSyncBackend` / `BaseThrottleAsyncBackend`
  (`dmr/throttling/backends/base.py:28-105`); `_BaseJWTAuth` and `_BaseTokenAuth` each → a sync
  and an async subclass; `Parser`, `Renderer`, `BaseSerializer` and `ComponentParser` as
  single-colour families.

## 7. The public surface

Cited by [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md).

- **`dmr/__init__.py` re-exports exactly 16 names, every one as `X as X`**: `Body`, `Cookies`,
  `FileMetadata`, `Headers`, `Path`, `Query`, `Controller`, `CookieSpec`, `NewCookie`, `modify`,
  `validate`, `HeaderSpec`, `NewHeader`, `ResponseSpec`, `APIError`, `RedirectTo`. Ruff's
  `PLC0414` is ignored so that the `as` re-export form passes (`pyproject.toml:357`).
- **No `__all__` anywhere**: `grep -rn "__all__" . --include='*.py'` returns nothing in the
  whole repository.
- **Four criteria, all required** (`CHANGELOG.md:10-15`): "What is a public API for us (all
  criteria must be met)? 1. Things that have public names 2. Things that live in public modules
  3. Things that don't live in `internal/` or `compiled/` 4. Things that are explicitly documented
  in the docs." The reference page is `docs/pages/deep-dive/public-api.rst`.
- **The internal API is documented separately as unstable**: "API documented here is not public,
  it can change at any time. Please, do not use it directly. However, it is documented so people
  and LLMs can better understand the code." (`docs/pages/deep-dive/internal-api.rst:4-7`). The
  promise itself starts later: "Public API stability is guaranteed from 1.0.0 release"
  (`docs/index.rst:171`).

## 8. `Annotated` markers for request components

Cited by [ADR-0018](../adr/0018-core-owned-type-keyed-dependency-injection.md).

Six aliases of the form `Name: TypeAlias = Annotated[_T, NameComponent()]` — `Query`, `Body`,
`Headers`, `Path`, `Cookies`, `FileMetadata` (`dmr/components.py:325, 480, 550, 677, 742, 956`);
each `*Component` is a `ComponentParser` subclass holding the parsing behaviour the marker selects.

## 9. flake8-async and the event loop

Cited by [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md).

- `"ASYNC"` is in ruff's `select` (`pyproject.toml:298`). The global `ignore` list carries one
  `ASYNC` entry, `ASYNC119` — "`contextlib.aclosing` is not detected" (`pyproject.toml:342`); no
  `per-file-ignores` entry names an `ASYNC` rule; `grep -rn "noqa:.*ASYNC" dmr` returns nothing.
  `RUF029` is also ignored, with the reason "we decide `async` functions based on API, not `await`
  usage" (`pyproject.toml:362`).
- **No loop opinion.** `grep -rni "uvloop|winloop|event_loop_policy|loop_factory"` over every
  `.py`, `.rst`, `.md` and `.toml` file outside `uv.lock` returns nothing. The library runs under
  whatever ASGI server Django is given and neither selects nor recommends a loop.

## 10. Rules as an agent-facing document, architecture as contracts

Cited by [ADR-0033](../adr/0033-identified-tiered-rules-with-a-derived-review-checklist.md).

- **`.agents/skills/dmr/SKILL.md` is 1,570 lines** (`wc -l`). It has 14 `##` sections and **31
  `###` rule headings, every one imperative** ("Do not use `@validate`, when `@modify` is enough",
  "Never return Django `HttpResponse` directly — use `to_response`, `to_error`, or `APIError`",
  "Protect auth endpoints with throttling BEFORE authentication", …). Under a heading: a reason
  paragraph of one to four sentences, then `Wrong:` and `Correct:` code blocks (26 pairs), then
  `**Limitations:**` (21 occurrences), then `Docs: https://django-modern-rest.readthedocs.io/…`
  (25 lines). So 26 of 31 rules carry the full pair, 21 the limitations and 25 the deep link — the
  template is the norm, not a uniform. Four further skills (168–222 lines each) cover migrations
  and a spec-first flow; `.claude-plugin/marketplace.json` lists them and `docs/pages/ai/`
  documents them.
- **No prose styleguide, architecture document or decision record.** `docs/pages` holds user
  documentation only (getting started, configuration, routing, validation, auth, throttling,
  streaming, OpenAPI, testing, a `deep-dive` with public and internal API reference, security,
  performance, changelog and contributing). The words "style", "architecture" and "decision
  record" appear in `docs/` and `README.md` only as the wemake-python-styleguide badge and in
  `queryset.rst` prose about application architecture in general.
- **Architecture is nine import-linter contracts** in `.importlinter`: three `layers` (`dmr` with
  17 layers, `dmr.streaming`, `dmr.openapi`), two `forbidden` (optional dependencies confined to
  plugins; `dmr.security.token.auth` kept independent of the `Token` model), four `independence`
  (`dmr.plugins.*`, `dmr.openapi.generators.*`, `.objects.*`, `.views.*`). Every `ignore_imports`
  line carries a comment saying why the exception exists — for example "The default error handler
  adds `WWW-Authenticate` to `401` responses, it needs the auth chain to know what challenge to
  send: `dmr.errors -> dmr.security.base`".

## 11. The authentication chain and the throttle report

Cited by
[ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md).

- **The participant's contract is in its own docstring**, identically for the sync and async
  bases (`dmr/security/base.py:178-194, 208-224`), on a method typed `-> Self | None`:
  "Return `self` if the login attempt was successful. Return `None` if login attempt failed and we
  need to try another authes. Raise `NotAuthenticatedError` to immediately fail the login without
  trying other authes. Raise `APIError` if you want to change the return code, for example, when
  some data is missing or has wrong format." The fourth sentence — a second raise for a different
  status — is not in the ADR's summary above and does not change the split.
- **The runner, not the participant, raises after every participant declined**: `for auth in
  self.metadata.auth: … if authed_by is not None: request.__dmr_auth__ = authed_by; return` then
  `raise NotAuthenticatedError` (`dmr/endpoint.py:461-467`, and `511-517` for the async twin).
- **The value-returning counterpart names its reason**: `ThrottlingReport` — "Unlike
  `dmr.exceptions.TooManyRequestsError`, which reports the first stat for throttle that is
  failing, it reports all stats for all throttles." (`dmr/throttling/base.py:405-416`). It is the
  only docstring in the package that contrasts itself with an exception (`grep -rn "Unlike :exc:"
  dmr` returns this one line). Whether it is "exactly one place" that returns a value rather than
  raising is **[not confirmed: not measurable by search]**; the documented contrast is unique.

## Sources

- django-modern-rest at commit `79d03b5f4492611327af7f20cb8eb6c64e6e6807` (2026-09-08),
  https://github.com/wemake-services/django-modern-rest — `pyproject.toml:20, 257-260, 292-298,
  336-369, 429-488, 510-560`; `justfile:30-47`; `.github/workflows/test.yml:23-26`;
  `.importlinter`; `CHANGELOG.md:1-17`; `.agents/skills/dmr/SKILL.md`;
  `.claude-plugin/marketplace.json`; `dmr/__init__.py`; `dmr/exceptions.py`;
  `dmr/errors.py:112-140, 233-243, 246-326`; `dmr/problem_details.py:198`; `dmr/types.py:15-20`;
  `dmr/components.py:325-956`; `dmr/endpoint.py:172, 368-517, 1154`; `dmr/negotiation.py:88-214`;
  `dmr/security/base.py:108-229`; `dmr/security/http.py:128-135`;
  `dmr/security/jwt/blocklist/auth.py:15-45`; `dmr/throttling/base.py:60-460`;
  `dmr/throttling/backends/base.py:28-105`; `dmr/internal/json.py:12`; `dmr/internal/types.py:7`;
  `dmr/internal/dataclass_aliases.py:5`; `dmr/internal/endpoint.py:19-81`;
  `dmr/openapi/openapi.py:19`; `dmr/openapi/core/registry.py:9`; `dmr/streaming/sse/metadata.py:7`;
  `dmr/test/client.py:123-183`; `docs/index.rst:171`; `docs/pages/deep-dive/public-api.rst`;
  `docs/pages/deep-dive/internal-api.rst:4-7`; `docs/pages/ai/`;
  `tests/test_unit/test_security/test_token/test_token_admin.py`;
  `tests/test_unit/test_testing/test_request_factory.py`;
  `tests/test_unit/test_security/test_jwt/test_jwt_json_backend.py:75-76`;
  `tests/test_unit/test_compiled/test_negotiate_compiled.py:84, 170`;
  `tests/test_integration/test_management/test_dmr_export_schema.py:137`;
  `tests/test_integration/test_openapi/test_schema.py:34`
- Release metadata: https://github.com/wemake-services/django-modern-rest/releases/tag/0.14.0
  (2026-08-14)
- Litestar's loop position, for the comparison in
  [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md):
  [`18-execution-model-in-practice.md`](18-execution-model-in-practice.md) §3 and its
  Recommendation 6
