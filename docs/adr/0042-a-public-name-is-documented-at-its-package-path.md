---
status: accepted
date: 2026-09-09
ticket: "#24"
---

# A public name is documented at its package path, and a module path is never part of the public surface

Criterion 3 of [ADR-0007](0007-tiny-public-root-with-explicit-subpackages.md) makes every public
name reachable from the `__init__` of the subpackage that owns it, and the root re-export adds a
second reachable path, so two paths exist mechanically whatever we write; criterion 4 — the
reference documentation — is the only lever that says which one we promise
([`docs/research/22`](../research/22-public-import-surface-of-modern-libraries.md) §6.1). We decided
that the documented path is the **package** path, in one of these five forms and no other:

```text
aiommbot.<Name>                  the closed headline set of ADR-0007
aiommbot.core.<Name>             every other public Core name
aiommbot.mattermost.<Name>       the Adapter
aiommbot.plugins.<name>.<Name>   a generic Plugin
aiommbot.testing.<Name>          the testing toolkit
```

A module path — `aiommbot.core.key_value_store.KeyValueStore` — is never documented and never
promised, because a module is a file and `ST-MOD-09` *requires* that it be split the moment it holds
more than one component or part. Every measured case where changing a public surface hurt was
exactly that: a module moving inside a stable package — websockets carried its module aliases for
five years and three months, litestar 66 shim modules covering 259 names, pydantic twelve shims and
a 226-entry table, structlog three years and seven months with no warning at all. Not one of the
fifteen libraries measured ever had to move a *package*, because a package is named after the
architecture (`docs/research/22` §4, §6.2). Documenting the package path makes every future split a
non-event and costs the reader nothing: `from aiommbot.core import KeyValueStore` is shorter than
the module path it replaces.

The root list stays **closed**: a name belongs there only if a user writing their first bot must
name it in the first file they write, and adding to it amends ADR-0007. Which names pass that test
is #31's prototype to settle; this decision fixes the test and the paths. The observed band for a
framework's curated root is fourteen to twenty names, so ADR-0007's ten to fifteen is the low end of
practice rather than below it (`docs/research/22` §6.3). A root name is an alias the library can
repoint, so nothing that selects an implementation goes there.

## Considered options

- *Document module paths as well, and let the root be a convenience* — rejected: it is what most of
  the measured libraries do, and it is where every measured cost came from; our own `ST-MOD-09`
  guarantees that the module paths we would be promising are the ones that move.
- *Re-export the whole Core surface — some thirty-five names — from the root and make every module
  under `core/` private by name* — rejected: it is the httpx and anyio shape and it does give one
  path per name by construction, but it puts the root outside ADR-0007's decided band, and the
  libraries measured at that size pay for it with lazy-import machinery that a Core with no
  third-party dependency has no reason to build (`docs/research/22` §3.1, §3.2).

## Consequences

- The guard test of
  [ADR-0043](0043-explicit-re-export-with-a-reference-page-as-the-public-list.md) also fails a
  reference page that names a module path.
- A name that has to leave its package keeps working through the shim shape `docs/research/22` §6.4
  measured — the old path as a module whose body is a module-level `__getattr__` that warns and
  forwards, plus an `if TYPE_CHECKING:` import of the new home so checkers still see the type — with
  a project subclass of `DeprecationWarning` carrying the deprecating version, the removing version
  and the new path. The removal window over that mechanism is #28's.
