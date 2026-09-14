# 44. How a project keeps a documented list of configuration fields in step with its code

**Question.** Where does a project write the field names of a configuration object for a reader, and
what — if anything — fails when the code and that document disagree?

[`22`](22-public-import-surface-of-modern-libraries.md) measured the public *import* surface and the
tests that guard it. This note asks the same question one level down, about names that are not
importable at all: the fields of a settings object. It is the evidence for whether a field name can
join the public list of
[ADR-0043](../adr/0043-explicit-re-export-with-a-reference-page-as-the-public-list.md), and by what
mechanism.

The decision this note is evidence for is
[ADR-0077](../adr/0077-a-field-of-a-public-frozen-dataclass-is-a-public-name.md).

Findings only, and no recommendation. Sources are primary — project source at the commit named
below, each project's documentation build configuration and its CI workflows — read on 2026-09-14.
Anything a primary source did not confirm is marked **[unverified]**.

`.refs/hynek/structlog` holds a stub `.git` and no working tree, so structlog is **unmeasured**
here rather than absent.

## 1 Where the field names are written, and what guards them

| Project | Where a reader finds the fields | Generated or hand-written | The gate |
|---|---|---|---|
| django-modern-rest | one `.. data:: dmr.settings.Settings.<name>` with a `Default:` line, per key | hand | **none for the page** — `Settings` is autoclass'd without `:members:`, so a new key emits no warning; `nitpicky` catches dangling references only |
| pydantic | a trailing string literal after each `TypedDict` key | generated | strict mkdocs in CI; fails on a broken anchor, not on an undocumented key |
| celery | 207 `.. setting::` directives over 4559 lines | hand | a **two-way `configcheck` builder** exists — and CI never selects it |
| django | 210 `.. setting::` directives over 4179 lines | hand | **none**; nothing in the code or the tests reads `docs/ref/settings.txt` |
| litestar | a trailing string literal per field | **generated** by `automodule :members:` | none needed — the list cannot drift |
| faststream | an `Args:` block in the broker's `__init__` docstring | generated into gitignored stubs | none — the docs workflow fires only on a published release |
| httpx | markdown prose, disconnected from the code | hand | none; `Client.__init__`'s own parameter docstring is already stale |
| redis-py | `autoclass :members:` over a source that documents 3 of ~30 parameters | generated from an empty source | none effective |
| sqlalchemy | hand-typed `:param:` entries inside `create_engine`'s docstring | hand, inside a docstring | none — `nitpicky=False`, and no documentation workflow at all |
| attrs | a Google `Args:` block | generated | `sphinx-build -n -T -W` in CI; nitpicky is not missing-parameter detection |
| msgspec | a C string literal hand-listing each keyword, beside the `.pyi` stub | mechanically rendered from hand-written C | fails on warnings; nothing cross-checks the C text against the stub |
| opentelemetry | a docstring per constant | generated with `:undoc-members:` | the **name** cannot drift, only the prose |

The pattern is that a hand-written list has no gate almost everywhere, and a generated one needs
none. Three of the twelve keep the prose beside the field and render it; the rest write it twice.

## 2 Comparing a document against the code: the mechanism exists, and CPython owns it

**CPython scrapes its own prose and symmetric-diffs it, in a build step CI enforces.**

```python
    with open(token_py_file) as fp:
        ...
    documented = set()
    for line in doc_file:
        if m := re.fullmatch(r'.. data:: ([0-9A-Z_]+)\s*', line):
            documented.add(m.group(1))
    ...
    if undocumented := tokens - documented:
        exit(f"Undocumented tokens: {undocumented}")
    if nonexistent := documented - tokens:
        exit(f"Documented nonexistent tokens: {nonexistent}")
```

([`Tools/build/generate_token.py`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/Tools/build/generate_token.py#L236-L253),
reading `Doc/library/token.rst`.) It runs under `make regen-all`, and the workflow fails on any
resulting diff
([`build.yml`](https://github.com/python/cpython/blob/52ffffe0a23bf0f4a57ee00377c5aeb965b3a29a/.github/workflows/build.yml#L120)).
Both directions are reported **by name**, which is what makes the failure actionable.

Four more comparisons against prose exist:

| Project | Where | What against what | Direction |
|---|---|---|---|
| pydantic | `tests/test_docs.py:252-260` | `PydanticErrorCodes.__args__` against `## … {#id}` headings scraped from a markdown page | two-way, and **ordered** — a tuple comparison, so reordering the page fails |
| pydantic | `tests/test_docs.py:262-293` | `core_schema.ErrorType.__args__` against `` ## `name` `` headings, plus "is each code shown in an example" | two-way |
| datamodel-code-generator | `tests/skills/.../test_skill_flag_drift.py:101-118` | `--flag` tokens scraped from four hand-written markdown pages against live `--help` | one-way |
| celery | `docs/conf.py:90-104`, the `configcheck` builder | `flatten(NAMESPACES)` against the `.. setting::` targets in the Sphinx std domain, symmetric difference, with an `ignored_settings` escape hatch | two-way |

**celery's is the closest in shape to a settings page and it has rotted**: the builder is correct,
`tox -e configcheck` selects it, and `grep configcheck .github/` returns nothing, so no pull request
has ever been failed by it. A gate CI does not run is a gate that exists only in the repository's
self-image.

The commoner form compares code to **another code literal**, never to prose: pydantic's
`test_config_wrapper_match` and `test_config_defaults_match`
([`tests/test_config.py`](https://github.com/pydantic/pydantic/blob/831893ed0411d45c20aacae88e067c9c33a89501/tests/test_config.py#L521-L581)),
datamodel-code-generator's hand-maintained 1320-line signature baseline, and the
`__all__`-versus-fixture tests in redis-py, httpx, litestar, anyio, websockets and trio.

**django-modern-rest asserts at import time, in shipped code**, and binds three code artefacts —
the `StrEnum` of keys, a `TypedDict`, and a defaults mapping:

```python
assert SettingsDict.__optional_keys__ == set(Settings), \
    'Settings enum and its type SettingsDict have different keys'
```

([`dmr/settings.py`](https://github.com/wemake-services/django-modern-rest/blob/218b65a3c75b103b6289b8db54ea426c1365e89d/dmr/settings.py#L134),
with a one-way defaults check at
[`:172`](https://github.com/wemake-services/django-modern-rest/blob/218b65a3c75b103b6289b8db54ea426c1365e89d/dmr/settings.py#L165-L175)
and a second two-way check at
[`dmr/validation/settings.py:38`](https://github.com/wemake-services/django-modern-rest/blob/218b65a3c75b103b6289b8db54ea426c1365e89d/dmr/validation/settings.py#L30-L45).)
A mis-wired key is a hard failure on `import`, in every user's process, rather than at test time.
Its costs: `python -O` strips it, and none of the three reaches the documentation page, so the page
can still drift silently — which is exactly the gap a page-versus-code comparison closes.

## 3 A frozen dataclass as public configuration

| Project | Class | Shape | Fields documented how |
|---|---|---|---|
| **django-modern-rest** | `OpenAPIConfig` | frozen, slots, **kw_only** | a Google `Attributes:` block in the class docstring, rendered by `autoclass` |
| litestar | `DTOConfig` | frozen, not kw_only | a trailing string literal per field, rendered by `automodule :members:` |
| stamina | `RetryDetails`, `RetryHookFactory` | frozen | a Google `Attributes:` block plus `.. versionadded::` |
| litestar `config/` | `AppConfig`, `CORSConfig` | plain `@dataclass`, deliberately mutable | a trailing string literal per field |
| faststream | `BrokerConfig` | kw_only, not frozen, `_internal/` | undocumented |
| hikari | `HTTPSettings` | `attrs.define(kw_only=True)`, not frozen | a trailing string literal |
| anyio, trio, opentelemetry | `*Statistics`, `NumberDataPoint` | frozen | output value objects rather than settable configuration |
| httpx, prometheus client, msgspec, attrs, pydantic | — | — | **a measured absence** — none exposes a frozen dataclass as public configuration |

**Four forms of per-field documentation exist**, and one dominates:

1. **A trailing string literal after the field** — litestar, pydantic, opentelemetry, hikari. Read
   natively by Sphinx autodoc and by griffe/mkdocstrings, and pydantic even reuses it at runtime:
   `use_attribute_docstrings` turns the string into a field's `description`.
2. **A Google `Attributes:` block** in the class docstring — django-modern-rest's `OpenAPIConfig`
   and stamina, through `sphinx.ext.napoleon`.
3. **`Annotated[T, Doc("…")]`** — FastAPI alone, through `griffe_typingdoc`; **zero other
   adopters** in the corpus.
4. **A `#:` comment before the attribute** — 120 non-test files, led by celery and pytest.

**`metadata={}` on a field carrying documentation is a measured absence**: every occurrence in the
corpus carries behaviour, never prose, and no tool renders it.

## 4 Renaming a field

**Nobody in the corpus renamed a field of a frozen dataclass behind an alias.** litestar did it as a
hard break — `DTOConfig.field_mapping` became `rename_fields`, tagged `:breaking:` in the changelog,
and `__post_init__` carries no alias logic, so old code gets `TypeError: unexpected keyword
argument`.

Every shimmed precedent lives in a dictionary or namespace configuration, where a shim is possible
at all:

- **celery** keeps a true functional alias, `Option.old` feeding `_TO_OLD_KEY`/`_TO_NEW_KEY`, plus a
  warning naming the replacement and the removal version — and a `celery upgrade settings` command
  that rewrites the user's file
  ([`app/defaults.py`](https://github.com/celery/celery/blob/3e40f4332479ccd83527908dc9249c54531380de/celery/app/defaults.py#L42-L48)).
- **pydantic** warns and does **not** bridge: `V2_RENAMED_KEYS` drives a deprecation message while
  `prepare_config` returns the dictionary untouched, so `orm_mode=True` is inert.
- **django** hardcodes a branch per name, raising `ImproperlyConfigured` when both the old and the
  new setting are present
  ([`conf/__init__.py`](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/django/conf/__init__.py#L158-L178)).
- **attrs** ran `convert` → `converter` as a `DeprecationWarning` for about two years and then
  removed it, recording both dates in the class docstring.

django-modern-rest has renamed eleven things in its changelog and **not one of them is a settings
key**, and it ships no `.. deprecated::` directive anywhere.

## 5 What the evidence supports

- Comparing a hand-written page against the code is a real mechanism with a first-class precedent:
  CPython scrapes one directive per name out of its own prose, symmetric-diffs it, names both
  directions in the failure, and enforces it in CI. pydantic does the same against markdown
  headings, twice.
- The two-way form is what makes the comparison worth having, and the failure has to name the
  offenders. CPython prints *Undocumented* and *Documented nonexistent* as separate sets; a boolean
  gate would leave the author to find the difference.
- A gate that CI does not select rots in place. celery's `configcheck` is correct, symmetric, and
  carries an ignore list for the settings it knowingly omits — and no pull request has ever failed
  on it.
- Generating the page removes the need for a gate and removes the ability to decide what is public.
  litestar and opentelemetry cannot drift because the field list comes from the source; the price is
  that documentation stops being a separate act.
- An import-time `assert` in shipped code is a stronger gate than a test for the artefacts it binds,
  and reaches no document. django-modern-rest binds enum, `TypedDict` and defaults this way and
  leaves its own page outside the loop.
- A frozen keyword-only dataclass as public configuration is rare but present, and where it exists
  the fields are documented in the class rather than on a page — a `Attributes:` block for
  django-modern-rest's own `OpenAPIConfig`, a trailing string literal for litestar's `DTOConfig`.
- Renaming such a field has no alias precedent. The only frozen-dataclass rename in the corpus was
  shipped as a breaking change and labelled one; every alias in the corpus belongs to a dictionary
  configuration, where the old key can be mapped to the new one because keys are data.

## Sources

Every claim above carries its own link inline. This section names what was read.

Comparisons against prose:

- <https://github.com/python/cpython> — `Tools/build/generate_token.py`, `Makefile.pre.in`,
  `.github/workflows/build.yml`, `Lib/test/test_enum.py`
- <https://github.com/pydantic/pydantic> — `pydantic/config.py`, `pydantic/_internal/_config.py`,
  `tests/test_config.py`, `tests/test_docs.py`, `mkdocs.yml`
- <https://github.com/celery/celery> — `celery/app/defaults.py`, `celery/app/utils.py`,
  `docs/conf.py`, `docs/userguide/configuration.rst`, `Makefile`, `tox.ini`
- <https://github.com/koxudaxi/datamodel-code-generator> —
  `tests/main/test_public_api_signature_baseline.py`

Hand-written pages with no gate:

- <https://github.com/django/django> — `django/conf/__init__.py`, `docs/ref/settings.txt`,
  `docs/_ext/djangodocs.py`
- <https://github.com/encode/httpx> — `httpx/_client.py`, `docs/advanced/resource-limits.md`,
  `CHANGELOG.md`
- <https://github.com/redis/redis-py> — `redis/connection.py`, `docs/connections.rst`
- <https://github.com/sqlalchemy/sqlalchemy> — `lib/sqlalchemy/engine/create.py`,
  `doc/build/conf.py`

Generated pages:

- <https://github.com/litestar-org/litestar> — `litestar/config/cors.py`, `litestar/dto/config.py`,
  `docs/reference/dto/config.rst`, `docs/release-notes/2.x-changelog.rst`
- <https://github.com/open-telemetry/opentelemetry-python> —
  `opentelemetry-sdk/src/opentelemetry/sdk/environment_variables/__init__.py`,
  `docs/sdk/environment_variables.rst`
- <https://github.com/ag2ai/faststream> — `docs/create_api_docs.py`
- <https://github.com/python-attrs/attrs> — `src/attr/_make.py`, `src/attr/_next_gen.py`
- <https://github.com/jcrist/msgspec> — `src/msgspec/_core.c`, `msgspec/__init__.pyi`

Frozen dataclasses as configuration:

- <https://github.com/wemake-services/django-modern-rest> — `dmr/openapi/config.py`,
  `dmr/settings.py`, `dmr/validation/settings.py`, `docs/pages/configuration.rst`, `docs/conf.py`
- <https://github.com/hynek/stamina> — `src/stamina/instrumentation/_data.py`, `noxfile.py`
- <https://github.com/fastapi/fastapi> — `fastapi/param_functions.py`, `docs/en/mkdocs.yml`
- <https://github.com/hikari-py/hikari> — `hikari/impl/config.py`
