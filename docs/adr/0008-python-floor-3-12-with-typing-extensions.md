---
status: accepted
date: 2026-09-03
ticket: "#23"
amends: ADR-0002
---

# Python 3.12 is the floor, supported until its EOL, with typing_extensions as the Core's only runtime dependency

On 2026-10-01 the CPython bugfix branches become 3.14 and 3.15; 3.12 is already security-only and
3.13 joins it. A new framework could start at 3.13 and stay standard-library-only, but 3.12 is
still the version most operating-system images and corporate base images ship, and the 0.5.0
audience includes those environments. We decided **`requires-python = ">=3.12"`**, and to keep
the typing surface modern (PEP 696 TypeVar defaults, `TypeIs`, `ReadOnly`, `warnings.deprecated`)
we admit **`typing_extensions` as the single runtime dependency of the Core**, amending ADR-0002's
"standard library only" rule with exactly this exception. It is maintained by the CPython typing
council, has no transitive dependencies, and disappears from the dependency list the day 3.12 is
dropped.

Rules that come with the decision:

- **Support policy**: a Python version is supported until its upstream EOL (3.12 → October 2028);
  a new version enters the CI matrix at its first release candidate. Matrix for 2026-10: 3.12,
  3.13, 3.14, 3.15.
- **Free-threading is a blocking job**: the suite runs on the free-threaded 3.14t build and must
  pass. Pure-Python code stays free-threading-safe by having no mutable module state (ADR-0006).
- **Annotations are read lazily**: runtime introspection (dependency injection by annotation,
  handler metadata) uses `typing.get_type_hints` / `annotationlib` and never `__annotations__`
  directly, so PEP 649 deferred evaluation on 3.14+ changes nothing.
- **Compatibility imports live in one module**: names that differ between 3.12 and later come from
  a single `_internal/compat/typing.py`, never from `typing_extensions` scattered through the code.

## Considered options

- *≥ 3.13, standard library only* — rejected for reach: 3.13-only would cut the environments the
  first adopters run, for typing features that a one-dependency backport provides.
- *≥ 3.14* — rejected: buys nothing a library needs at runtime and excludes most current images.
- *≥ 3.12 without the backport* — rejected: a public contract without `TypeIs`, TypeVar defaults and
  `ReadOnly` is weaker than the tenets in ADR-0006 demand.
