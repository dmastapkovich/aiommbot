---
status: accepted
date: 2026-09-09
ticket: "#24"
---

# The repository is a `src/` layout, with tests, runnable examples and the catalogue beside the package

`uv_build` takes `module-root = "src"` as its default, while the library we measure our strictness
against keeps its package flat at the repository root
([`docs/research/04`](../research/04-modern-python-library-engineering-2026.md),
[`docs/research/21`](../research/21-measured-facts-behind-the-rules.md)), so neither the toolchain
nor the precedent settles the question. We decided **`src/aiommbot/`**, because the checks that keep
this design honest all rest on importing the *installed* distribution: the smoke import of the Core
with no extras installed ([ADR-0002](0002-core-scope-two-condition-test.md)), the per-extra smoke
imports of [ADR-0041](0041-default-dependencies-and-one-extra-per-optional-library.md), and the four
checkers of [ADR-0009](0009-four-strict-type-checkers.md). A `src/` layout makes that true by
construction — the working tree is not importable — where a flat layout makes it true only while
everyone remembers.

| Path | Holds |
|---|---|
| `src/aiommbot/` | the distribution; its internal layout is [ADR-0040](0040-one-package-directory-per-import-rank.md)'s |
| `tests/unit/` | one module per component, no I/O |
| `tests/integration/` | a real socket, a real Redis, a real ASGI host |
| `tests/conformance/` | the suites `aiommbot.testing` ships, run against every first-party implementation |
| `tests/typing/` | the type-checked, never-executed assertions of `ST-TYP-13` |
| `tests/smoke/` | the import of every public module with no extras installed, and one per extra |
| `tests/examples/` | the test that runs every module under `examples/` |
| `examples/` | importable example modules — one bot per file, no snippets in prose |
| `docs/` | the design catalogue, and later the user documentation (#26) |
| `.agents/`, `.claude/` | the process documents and the skills that run a session |
| repository root | `pyproject.toml`, `justfile`, `.semgrep/`, `.github/`, the community kit |

**An example is a module, not a snippet.** Every file under `examples/` imports as it stands and is
executed by `tests/examples/`, so an example that stops compiling fails CI rather than rotting in a
page. How the documentation includes those modules is #26's; that they are importable modules is
this decision.

## Considered options

- *Flat `aiommbot/` at the repository root* — rejected: it is the benchmark's shape and shortens
  every path, but it leaves the working tree importable, which is exactly the accident the smoke
  imports exist to catch.
- *Snippets under `docs_src/` instead of `examples/`* — rejected: an example nobody sees when they
  open the repository is an example that only the documentation build reads; the inclusion mechanism
  is #26's problem, the visibility is ours.
- *Typing tests in a top-level `typesafety/`* — rejected: `ST-TYP-13` already names
  `tests/typing/`, and one root fewer is one root fewer.
