---
status: accepted
date: 2026-09-03
ticket: "#13"
---

# The public API is a tiny root namespace plus explicit subpackages; everything else is internal

A root namespace that re-exports dozens of names, one per platform event class, makes each of them
a compatibility promise; django-modern-rest exports about sixteen and documents its internal API
separately as unstable. We decided that the
root `aiommbot` namespace exports only Core concepts (on the order of ten to fifteen names), the
Mattermost Adapter lives in `aiommbot.mattermost`, each first-party Plugin in its own subpackage,
and the testing toolkit in `aiommbot.testing`. Everything else is `_internal`, excluded from the
semantic-versioning promise, and the public list is documented explicitly and guarded by a test.

## Consequences

- The concrete layout, `__all__` policy and extras are designed in #24; the semver definition of
  "public" in #28.

## Amended by #36 on 2026-09-07: what makes a name public

This ADR said the public list is documented and guarded by a test but gave no criterion. A name is
public when **all four** of these hold, and it is internal the moment one fails:

1. the name itself is public — no leading underscore;
2. it lives in a public module — not under `_internal`;
3. it is re-exported from the subpackage that owns it, explicitly (`X as X`);
4. it is **documented in the reference documentation**.

Criterion 4 makes the reference page load-bearing: a name absent from it is not public even if it
imports cleanly, which is what keeps the semantic-versioning promise (#28) bounded to a list
somebody wrote on purpose. The mechanisms are the guard test this ADR already required, plus ruff
`SLF001` and `PLC2701` package-wide and the import-linter contracts of ADR-0032; the rules are
[`engineering-style.md`](../design/engineering-style.md) §8. The reference implementation we
measured states the same conjunction in four numbered criteria and carries no `__all__` at all.
