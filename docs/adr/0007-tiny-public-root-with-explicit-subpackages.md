---
status: accepted
date: 2026-09-03
ticket: "#13"
---

# The public API is a tiny root namespace plus explicit subpackages; everything else is internal

0.4.8 exported 39 names from `aiommbot`, including thirteen request classes; django-modern-rest
exports about sixteen and documents its internal API separately as unstable. We decided that the
root `aiommbot` namespace exports only Core concepts (on the order of ten to fifteen names), the
Mattermost Adapter lives in `aiommbot.mattermost`, each first-party Plugin in its own subpackage,
and the testing toolkit in `aiommbot.testing`. Everything else is `_internal`, excluded from the
semantic-versioning promise, and the public list is documented explicitly and guarded by a test.

## Consequences

- The concrete layout, `__all__` policy and extras are designed in #24; the semver definition of
  "public" in #28.
