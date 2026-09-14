---
status: accepted
date: 2026-09-14
ticket: "#103"
amends: [ADR-0043]
---

# The plugin API is a named section of the one reference page, the distribution convention is `aiommbot-<name>`, and no scaffold ships

[ADR-0043](0043-explicit-re-export-with-a-reference-page-as-the-public-list.md) knows two pages, the
reference and the internal API, and a third-party plugin author reads neither as addressed to them.
Three questions were open — whether a plugin-API page exists, whether a distribution-name convention
is stated, and whether a scaffold ships
([`docs/research/35`](../research/35-the-third-party-author-kit.md)). Each is answered by what the
field already does.

- **One list, with the plugin API as a named section of it.** django-modern-rest keeps its plugin
  surface as a section of its single public-API page, and pytest keeps its hooks as a section of its
  single API Reference; Django goes further and makes membership of the documentation the definition
  of stable. A second hand-written list is what ADR-0043 already rejected for `__all__` — "a second
  list of the same names beside the first", whose drift has a direction — and the reasoning does not
  change because the second list would be prose. Our page is machine-readable, so the section is a
  field on the row rather than a heading, and the two-way guard test of ADR-0043 keeps reading one
  table once.
- **The audience is recorded because a deprecation window may differ by it.** Sphinx and Home
  Assistant are the two hosts that split the page, and both give developer-facing API a longer
  promise; Home Assistant is the only host in the survey stating it in months — twelve against six
  — and the only one saying the period "is never shortened" (`docs/research/35` §4). Whether ours
  differ by audience is **#28**'s, and this decision gives #28 a set it can name.
- **The distribution convention is `aiommbot-<name>`, and the import package `aiommbot_<name>`.**
  That is Django's exact form, down to the worked example. Nothing keys off it: PyPI implements no
  namespaces — PEP 752 is `Accepted` with a resolution and PEP 755's index policy is still `Draft` —
  so a convention is the whole available mechanism, and pytest's `pytest-` prefix binds only as an
  admission rule to an organisation. No `Framework :: aiommbot` trove classifier exists; the list is
  curated and asking for one is not this decision's.
- **No scaffold.** Two of the surveyed hosts have one and neither is a distributable author tool:
  pytest's lives in a separate repository with one development lead, and Home Assistant's refuses to
  run outside a core checkout and generates tests that need a fixture excluded from the wheel.
  django-modern-rest, Litestar, FastStream and Sphinx ship none, and Sphinx teaches with copyable
  example modules instead. The importable `examples/` of
  [ADR-0039](0039-src-layout-with-tests-and-examples-beside-the-package.md) already hold a working
  plugin and run in CI, which is that shape with a test around it.
- **What already exists is named as done rather than decided again**: the plugin-lifecycle
  conformance suite as a factory over the author's factory
  ([ADR-0047](0047-a-conformance-suite-per-core-seam.md)), the toolkit activated by one
  `conftest.py` line ([ADR-0044](0044-the-testing-toolkit-requires-pytest-and-is-activated-explicitly.md)),
  `MissingExtraError` at construction, a `PluginSpec` readable without running code, and the
  `independence` and `forbidden` contracts. **Ours ships inside the distribution**, where Home
  Assistant's is excluded from the wheel and a third-party author gets it from a personal repository
  instead.

## Considered options

- *A separate hand-written plugin-API page with its own two-way guard test* — rejected: two lists of
  the same names, two tests, and a name forgotten in the second silently loses its promise. It is
  ADR-0043's own argument against `__all__`, unchanged.
- *No distinction at all, pytest's and Django's answer* — rejected: it works for them because their
  promise is defined by membership of the documentation as a whole, and #28 then has no way to name
  the developer-facing subset even if it wants to treat it differently.
- *A scaffold generating a plugin project* — rejected: a separate artefact with its own release
  cycle that goes stale quietly, in exchange for what a tested example already gives.

## Consequences

- The reference page's row gains an audience field, which is a change to its shape and therefore to
  ADR-0043's description of it; the guard test and the page's renderer (#26) read the same table.
- A third-party author is told the convention and told that nothing enforces it, which is the honest
  version of every convention in this survey.
